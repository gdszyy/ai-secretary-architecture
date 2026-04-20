"""
daily_progress_updater.py
=========================
项目进度更新模块 —— 跑批 Step 3

功能：
  1. 拉取所有群组「最近 N 小时」的新消息（增量，基于本地游标）
  2. 用 LLM 从消息中提取各模块的进展更新
  3. 将进展写入 data/dashboard_data.json 的 weekly_updates 字段
  4. 同步更新 Bitable 话题表（新话题写入、已有话题状态更新）

游标机制：
  data/fetch_cursor.json 存储每个群组的「最后拉取时间戳」，
  每次只拉取上次之后的新消息，避免重复处理。

用法：
  python3 daily_progress_updater.py              # 正式运行
  python3 daily_progress_updater.py --dry-run    # 预览，不写入文件
  python3 daily_progress_updater.py --hours 48   # 拉取最近 48 小时（默认 26 小时）
"""

import os
import sys
import json
import time
import logging
import argparse
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("daily_progress_updater")

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

REPO_ROOT      = Path(__file__).parent.parent
DATA_DIR       = REPO_ROOT / "data"
DASHBOARD_FILE = DATA_DIR / "dashboard_data.json"
CURSOR_FILE    = DATA_DIR / "fetch_cursor.json"

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

APP_ID     = os.environ.get("LARK_APP_ID",     "cli_a9d985cd40f89e1a")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "UNemS0zPnUuXhONgkuuprgdK3SrVx05T")

BASE_ID  = "CyDxbUQGGa3N2NsVanMjqdjxp6e"
TABLE_ID = "tblKscoaGp6VwhQe"

# 默认拉取最近 26 小时（覆盖昨天全天，防止时区偏差）
DEFAULT_HOURS = 26

# 群组列表（chat_id → 群名）
CHAT_GROUPS = {
    "oc_ba6f8baec0bd9566ed885d98cd3b8614": "XP产品设计",
    "oc_aba6f4b7f76c8bd6e72db298aa54b53c": "产运群",
    "oc_bfa55e46c000eb3943c2c07b989121f3": "小组长",
    "oc_266b6b295f4fb6e6ef5579ea372c7c1c": "设计稿优化对接",
    "oc_7f1872531b4664eadd4ba991cf485567": "GoToBet项目沟通群",
    "oc_bb4eb1c864720348de517027069de5a2": "风控运营合作",
    "oc_5b35ab3e1d6a407701c64df5a853c3df": "上线前前端优化需求",
    "oc_405bc9126a5ec41b5f77dd429e1731cb": "Lsport数据源",
}

# 模块 ID → 模块名（用于 LLM 分类）
MODULE_MAP = {
    "mod_data_ingestion":    "数据接入层",
    "mod_sr_ts_matching":    "SR→TS 匹配引擎",
    "mod_ls_ts_matching":    "LS→TS 匹配引擎",
    "mod_sports_betting_core": "体育博彩核心",
    "mod_user_system":       "用户系统",
    "mod_wallet_finance":    "钱包与财务",
    "mod_activity_platform": "运营活动平台",
    "mod_casino":            "游戏（Casino）",
    "mod_ads_system":        "投放系统",
    "mod_uiux_design":       "UI/UX 设计",
    "mod_platform_setting":  "平台系统管理",
    "mod_im_cs":             "站内信与客服",
}

# API 调用间隔
API_INTERVAL = 0.5

# ---------------------------------------------------------------------------
# 飞书 API 工具
# ---------------------------------------------------------------------------

_token_cache = {"token": None, "expires_at": 0}


def get_token() -> str:
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]
    r = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expires_at"] = now + data.get("expire", 7200) - 300
    return _token_cache["token"]


def lark_get(url: str, params: dict = None) -> dict:
    headers = {"Authorization": f"Bearer {get_token()}"}
    r = requests.get(url, headers=headers, params=params or {}, timeout=15)
    r.raise_for_status()
    return r.json()


def extract_msg_text(msg: dict) -> str:
    """从飞书消息中提取纯文本"""
    msg_type = msg.get("msg_type", "")
    body_str = msg.get("body", {}).get("content", "")
    try:
        body = json.loads(body_str)
    except Exception:
        return body_str or ""

    if msg_type == "text":
        text = body.get("text", "")
        text = re.sub(r"<at[^>]*>[^<]*</at>", "@someone", text)
        return text.strip()
    elif msg_type == "post":
        texts = []
        for line in body.get("content", []):
            for node in line:
                if node.get("tag") == "text":
                    texts.append(node.get("text", ""))
                elif node.get("tag") == "at":
                    texts.append(f"@{node.get('user_name', '')}")
        return " ".join(texts).strip()
    elif msg_type in ("image", "file", "sticker"):
        return ""
    else:
        return ""


# ---------------------------------------------------------------------------
# 游标管理
# ---------------------------------------------------------------------------

def load_cursor() -> Dict[str, int]:
    """加载各群组的最后拉取时间戳（秒）"""
    if not CURSOR_FILE.exists():
        return {}
    try:
        return json.loads(CURSOR_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cursor(cursor: Dict[str, int]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CURSOR_FILE.write_text(
        json.dumps(cursor, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# 消息拉取
# ---------------------------------------------------------------------------

def fetch_recent_messages(
    chat_id: str,
    start_ts_s: int,
    end_ts_s: int,
    max_msgs: int = 300,
) -> List[Dict]:
    """拉取指定时间范围内的群消息"""
    url = "https://open.larksuite.com/open-apis/im/v1/messages"
    messages = []
    page_token = None

    while len(messages) < max_msgs:
        params = {
            "container_id_type": "chat",
            "container_id": chat_id,
            "start_time": str(start_ts_s),
            "end_time": str(end_ts_s),
            "page_size": 50,
            "sort_type": "ByCreateTimeAsc",
        }
        if page_token:
            params["page_token"] = page_token

        try:
            data = lark_get(url, params)
            code = data.get("code", -1)
            if code == 230050:
                logger.warning("群 %s 历史消息受限", chat_id)
                break
            if code != 0:
                logger.warning("拉取消息失败: chat=%s, code=%s", chat_id, code)
                break

            items = data.get("data", {}).get("items", [])
            messages.extend(items)

            if not data.get("data", {}).get("has_more"):
                break
            page_token = data.get("data", {}).get("page_token")
            time.sleep(API_INTERVAL)
        except Exception as e:
            logger.error("拉取消息异常: %s", str(e))
            break

    return messages


# ---------------------------------------------------------------------------
# LLM 进展提取
# ---------------------------------------------------------------------------

client = OpenAI()

PROGRESS_EXTRACT_PROMPT = """你是一个AI项目秘书，负责从飞书群聊记录中提取各模块的项目进展。

已知模块列表：
{module_list}

请从群聊记录中提取有实质内容的进展信息，输出以下 JSON：
{{
  "has_updates": true/false,
  "updates": [
    {{
      "module_id": "对应的模块ID（从上面列表中选，若不明确填unknown）",
      "module_name": "模块名称",
      "summary": "进展摘要（2-4句话，说清楚做了什么、结论是什么、下一步是什么）",
      "topics": [
        {{
          "title": "话题标题（10字以内）",
          "summary": "话题摘要（1-2句话）",
          "status": "resolved/in_progress/pending",
          "action_items": ["待办事项"]
        }}
      ]
    }}
  ],
  "day_summary": "今日整体进展一句话总结（若无实质内容则为空字符串）"
}}

注意：
- 只提取有实质内容的进展，忽略纯闲聊、表情包、打招呼
- 同一模块的多条消息合并为一个 update
- 若消息量极少或无实质内容，has_updates=false，updates=[]
- 必须输出合法 JSON"""


def extract_progress_from_messages(
    group_name: str,
    messages: List[Dict],
) -> Dict:
    """用 LLM 从消息列表中提取进展"""
    if not messages:
        return {"has_updates": False, "updates": [], "day_summary": ""}

    # 构建消息文本
    lines = []
    for m in messages[:200]:  # 最多 200 条
        text = extract_msg_text(m)
        if not text or len(text) < 3:
            continue
        ts = m.get("create_time", "")
        try:
            ts_str = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%H:%M")
        except Exception:
            ts_str = ""
        sender = m.get("sender", {}).get("id", "")[-6:]  # 只取后6位
        lines.append(f"[{ts_str}] {sender}: {text}")

    if not lines:
        return {"has_updates": False, "updates": [], "day_summary": ""}

    module_list = "\n".join(f"- {mid}: {name}" for mid, name in MODULE_MAP.items())
    msg_text = "\n".join(lines)

    user_prompt = f"""群组：{group_name}
消息数量：{len(lines)} 条

群聊记录：
{msg_text[:6000]}

请提取进展信息并输出 JSON。"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": PROGRESS_EXTRACT_PROMPT.format(module_list=module_list),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error("LLM 提取进展失败: %s", str(e))
        return {"has_updates": False, "updates": [], "day_summary": ""}


# ---------------------------------------------------------------------------
# 看板写入
# ---------------------------------------------------------------------------

def get_iso_week() -> str:
    """返回当前 ISO 周标识，如 2026-17"""
    now = datetime.now(timezone.utc)
    year, week, _ = now.isocalendar()
    return f"{year}-{week:02d}"


def update_dashboard(progress_by_module: Dict[str, List[str]], dry_run: bool = False) -> int:
    """
    将各模块的进展摘要写入 dashboard_data.json 的 weekly_updates 字段。
    progress_by_module: {module_id: [summary1, summary2, ...]}
    返回更新的模块数量。
    """
    if not DASHBOARD_FILE.exists():
        logger.warning("dashboard_data.json 不存在，跳过看板更新")
        return 0

    with open(DASHBOARD_FILE, encoding="utf-8") as f:
        data = json.load(f)

    week_key = get_iso_week()
    updated_count = 0

    for module in data.get("modules", []):
        mid = module.get("id", "")
        if mid not in progress_by_module:
            continue

        summaries = progress_by_module[mid]
        if not summaries:
            continue

        combined = " | ".join(summaries)

        # 更新 weekly_updates（同一周的合并）
        weekly = module.setdefault("weekly_updates", [])
        existing = next((w for w in weekly if w.get("week") == week_key), None)

        if existing:
            existing["update"] = combined
        else:
            weekly.insert(0, {"week": week_key, "update": combined})

        # 同步更新 current_summary
        module["current_summary"] = summaries[-1][:100]

        updated_count += 1
        logger.info("  ✅ 更新模块 [%s]: %s", mid, combined[:60] + "...")

    # 更新 last_updated
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    if dry_run:
        logger.info("[DRY-RUN] 将写入 %d 个模块的进展到 dashboard_data.json", updated_count)
    else:
        with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("dashboard_data.json 已更新，共 %d 个模块", updated_count)

    return updated_count


def write_topics_to_bitable(
    topics: List[Dict],
    chat_id: str,
    group_name: str,
    period_label: str,
    dry_run: bool = False,
) -> int:
    """
    将 LLM 提取的新话题写入 Bitable 话题表。
    返回写入数量。
    """
    if not topics:
        return 0

    url = (
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}"
        f"/tables/{TABLE_ID}/records/batch_create"
    )
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    }

    records = []
    now_ms = int(time.time() * 1000)

    for t in topics:
        status_map = {
            "resolved": "已完成",
            "in_progress": "跟进中",
            "pending": "待跟进",
        }
        status = status_map.get(t.get("status", "pending"), "待跟进")
        todos = "\n".join(f"• {a}" for a in t.get("action_items", []))

        records.append({
            "fields": {
                "话题标题":  t.get("title", ""),
                "群组名称":  group_name,
                "所属模块":  t.get("module_name", "unknown"),
                "话题摘要":  t.get("summary", ""),
                "待办事项":  todos,
                "状态":      status,
                "来源周期":  period_label,
                "发现时间":  now_ms,
                "chat_id":   chat_id,
            }
        })

    if dry_run:
        logger.info("[DRY-RUN] 将写入 %d 条新话题到 Bitable", len(records))
        return len(records)

    try:
        r = requests.post(url, headers=headers, json={"records": records}, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == 0:
            count = len(data.get("data", {}).get("records", []))
            logger.info("  ✅ 写入 %d 条新话题到 Bitable", count)
            return count
        else:
            logger.error("写入 Bitable 失败: code=%s, msg=%s", data.get("code"), data.get("msg"))
            return 0
    except Exception as e:
        logger.error("写入 Bitable 异常: %s", str(e))
        return 0


# ---------------------------------------------------------------------------
# 周期标签
# ---------------------------------------------------------------------------

def get_current_period_label() -> str:
    """生成当前周的周期标签，如「第5周 (04/20~04/27)」"""
    today = datetime.now(timezone.utc).date()
    # 找到本周一
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # 计算是第几周（从项目开始的第1周 03/17 算起）
    project_start = datetime(2026, 3, 17, tzinfo=timezone.utc).date()
    week_num = ((monday - project_start).days // 7) + 1

    return f"第{week_num}周 ({monday.strftime('%m/%d')}~{sunday.strftime('%m/%d')})"


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------

def run(hours: int = DEFAULT_HOURS, dry_run: bool = False) -> Dict:
    """
    主执行函数。
    """
    logger.info("=== 项目进度更新 开始 (hours=%d, dry_run=%s) ===", hours, dry_run)

    cursor = load_cursor()
    now_ts = int(time.time())
    start_ts = now_ts - hours * 3600

    period_label = get_current_period_label()
    logger.info("当前周期: %s", period_label)

    # 按模块汇总进展
    progress_by_module: Dict[str, List[str]] = {}
    total_messages = 0
    total_new_topics = 0
    groups_with_updates = 0

    for chat_id, group_name in CHAT_GROUPS.items():
        # 使用游标（取游标和 start_ts 的较大值）
        cursor_ts = cursor.get(chat_id, 0)
        effective_start = max(cursor_ts, start_ts)

        logger.info("拉取群 [%s] 消息 (从 %s 起)...",
                    group_name,
                    datetime.fromtimestamp(effective_start, tz=timezone.utc).strftime("%m-%d %H:%M"))

        messages = fetch_recent_messages(chat_id, effective_start, now_ts)
        msg_count = len(messages)
        total_messages += msg_count

        if msg_count == 0:
            logger.info("  → 无新消息，跳过")
            continue

        logger.info("  → 拉取到 %d 条消息，开始 LLM 提取...", msg_count)

        # LLM 提取进展
        result = extract_progress_from_messages(group_name, messages)

        if not result.get("has_updates"):
            logger.info("  → LLM 判断无实质进展，跳过")
            # 更新游标
            if not dry_run:
                cursor[chat_id] = now_ts
            continue

        groups_with_updates += 1
        updates = result.get("updates", [])

        # 按模块汇总
        for upd in updates:
            mid = upd.get("module_id", "unknown")
            summary = upd.get("summary", "")
            if mid != "unknown" and summary:
                progress_by_module.setdefault(mid, []).append(summary)

            # 写入话题到 Bitable
            topics = upd.get("topics", [])
            for t in topics:
                t["module_name"] = upd.get("module_name", "unknown")
            written = write_topics_to_bitable(
                topics, chat_id, group_name, period_label, dry_run=dry_run
            )
            total_new_topics += written

        logger.info("  → 提取到 %d 个模块更新，%s",
                    len(updates), result.get("day_summary", ""))

        # 更新游标
        if not dry_run:
            cursor[chat_id] = now_ts

        time.sleep(API_INTERVAL)

    # 写入看板
    updated_modules = update_dashboard(progress_by_module, dry_run=dry_run)

    # 保存游标
    if not dry_run:
        save_cursor(cursor)
        logger.info("游标已保存")

    summary = {
        "total_messages":    total_messages,
        "groups_with_updates": groups_with_updates,
        "updated_modules":   updated_modules,
        "new_topics":        total_new_topics,
    }

    logger.info(
        "=== 项目进度更新 完成: 消息=%d, 有更新群=%d, 更新模块=%d, 新话题=%d ===",
        summary["total_messages"],
        summary["groups_with_updates"],
        summary["updated_modules"],
        summary["new_topics"],
    )
    return summary


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="项目进度更新：拉取群消息→LLM提取→写入看板")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入文件")
    parser.add_argument("--hours", type=int, default=DEFAULT_HOURS,
                        help=f"拉取最近 N 小时的消息，默认 {DEFAULT_HOURS}")
    args = parser.parse_args()

    summary = run(hours=args.hours, dry_run=args.dry_run)

    print("\n" + "=" * 50)
    print("项目进度更新摘要")
    print("=" * 50)
    print(f"处理消息总数:   {summary['total_messages']}")
    print(f"有更新的群组:   {summary['groups_with_updates']}")
    print(f"更新的模块数:   {summary['updated_modules']}")
    print(f"新写入话题数:   {summary['new_topics']}")


if __name__ == "__main__":
    main()

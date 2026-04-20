"""
stale_topic_followup.py
=======================
话题收尾跟进脚本 —— 跑批流程的最后一步

功能：
  扫描飞书多维表格中的话题记录，识别"过期话题"（来源周期已超过阈值天数，
  且状态仍为"跟进中"或"待跟进"），在对应群组中 @VoidZ 发送带上下文的
  咨询消息，请求确认话题最终结论。

过期判定逻辑：
  - 话题的"来源周期"字段包含起止日期（如"第1周 (03/17~03/24)"）
  - 以周期结束日期为基准，超过 STALE_THRESHOLD_DAYS 天视为过期
  - 状态为"已完成"或"已归档"的话题跳过

防重复发送：
  - 使用 Bitable 同一张表的"最后追问时间"字段（如不存在则跳过写入）
  - 也可通过本地 JSON 文件（stale_followup_sent.json）记录已发送的 record_id
  - 两种方式均支持，优先使用本地文件（无需修改 Bitable 表结构）

用法：
  # 正式发送
  python3 stale_topic_followup.py

  # 仅预览，不实际发送消息
  python3 stale_topic_followup.py --dry-run

  # 调整过期阈值（默认14天）
  python3 stale_topic_followup.py --threshold 7

  # 强制重发（忽略已发送记录）
  python3 stale_topic_followup.py --force

环境变量（可选，若未配置则使用硬编码凭证）：
  LARK_APP_ID, LARK_APP_SECRET
"""

import os
import sys
import json
import argparse
import logging
import re
import time
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("stale_topic_followup")

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 飞书应用凭证（优先读取环境变量，回退到硬编码）
APP_ID     = os.environ.get("LARK_APP_ID",     "cli_a9d985cd40f89e1a")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "UNemS0zPnUuXhONgkuuprgdK3SrVx05T")

# 话题表配置
BASE_ID  = "CyDxbUQGGa3N2NsVanMjqdjxp6e"
TABLE_ID = "tblKscoaGp6VwhQe"

# 负责人 open_id（当前为 VoidZ）
VOIDZ_OPEN_ID = "ou_d06d8df64bc40ed44f8e8df3f4be3403"
VOIDZ_NAME    = "VoidZ"

# 过期阈值（天）：来源周期结束日超过此天数视为过期
STALE_THRESHOLD_DAYS = 14

# 需要跟进的状态（不在此列表中的状态跳过）
STALE_STATUSES = {"跟进中", "待跟进", ""}

# 已发送记录文件（防止重复发送）
SENT_RECORD_FILE = Path(__file__).parent.parent / "data" / "stale_followup_sent.json"

# 消息发送间隔（秒），避免频率限制
MESSAGE_SEND_INTERVAL = 1.5

# ---------------------------------------------------------------------------
# 飞书 API 客户端
# ---------------------------------------------------------------------------

_token_cache = {"token": None, "expires_at": 0}


def get_token() -> str:
    """获取并缓存 tenant_access_token"""
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
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {data.get('msg')}")

    token = data["tenant_access_token"]
    _token_cache["token"] = token
    _token_cache["expires_at"] = now + data.get("expire", 7200) - 300
    return token


def get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    }


def list_all_records() -> List[Dict]:
    """拉取话题表全部记录"""
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records"
    all_records = []
    page_token = None

    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token

        r = requests.get(url, headers=get_headers(), params=params, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", {})
        all_records.extend(data.get("items", []))

        if not data.get("has_more"):
            break
        page_token = data.get("page_token")

    logger.info("共拉取 %d 条话题记录", len(all_records))
    return all_records


def send_message(chat_id: str, text: str, dry_run: bool = False) -> bool:
    """
    向指定群组发送文本消息（支持 @mention）。

    text 中可使用 <at user_id="xxx">Name</at> 语法实现 @。
    """
    if dry_run:
        logger.info("[DRY-RUN] 将发送到群 %s:\n%s", chat_id, text)
        return True

    url = "https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}, ensure_ascii=False),
    }

    try:
        r = requests.post(url, headers=get_headers(), json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == 0:
            logger.info("消息发送成功: chat_id=%s", chat_id)
            return True
        else:
            logger.error("消息发送失败: code=%s, msg=%s", data.get("code"), data.get("msg"))
            return False
    except Exception as e:
        logger.error("消息发送异常: %s", str(e))
        return False


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def extract_text(v) -> str:
    """从飞书字段值中提取纯文本"""
    if not v:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list):
        return "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in v
        ).strip()
    return str(v).strip()


def parse_period_end_date(period_str: str) -> Optional[date]:
    """
    从来源周期字符串中提取结束日期。

    支持格式：
      "第1周 (03/17~03/24)"  → date(当前年, 3, 24)
      "第2周 (03/24~03/31)"  → date(当前年, 3, 31)
    """
    if not period_str:
        return None

    # 匹配 MM/DD~MM/DD 格式
    m = re.search(r"(\d{2})/(\d{2})~(\d{2})/(\d{2})", period_str)
    if not m:
        return None

    end_month = int(m.group(3))
    end_day   = int(m.group(4))
    year = date.today().year

    try:
        return date(year, end_month, end_day)
    except ValueError:
        return None


def load_sent_records() -> set:
    """加载已发送的 record_id 集合"""
    if not SENT_RECORD_FILE.exists():
        return set()
    try:
        with open(SENT_RECORD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("sent_ids", []))
    except Exception as e:
        logger.warning("读取已发送记录文件失败: %s", str(e))
        return set()


def save_sent_records(sent_ids: set) -> None:
    """保存已发送的 record_id 集合"""
    SENT_RECORD_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(SENT_RECORD_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "sent_ids": sorted(sent_ids),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info("已发送记录已保存: %d 条", len(sent_ids))
    except Exception as e:
        logger.error("保存已发送记录失败: %s", str(e))


def build_followup_message(topic: Dict) -> str:
    """
    构建 @VoidZ 的话题收尾追问消息。

    消息结构：
      1. @VoidZ
      2. 话题背景（标题 + 摘要）
      3. 未完成的待办事项
      4. 明确的追问问题
    """
    title   = topic.get("title", "（无标题）")
    summary = topic.get("summary", "")
    todos   = topic.get("todos", "")
    module  = topic.get("module", "")
    period  = topic.get("period", "")
    status  = topic.get("status", "")
    age_days = topic.get("age_days", 0)

    at_mention = f'<at user_id="{VOIDZ_OPEN_ID}">{VOIDZ_NAME}</at>'

    lines = [
        f"{at_mention}",
        f"",
        f"🤖 检测到一个已超过 {int(age_days)} 天、尚未闭环的话题，需要确认最终结论：",
        f"",
        f"📌 **话题**：{title}",
    ]

    if module and module != "unknown":
        lines.append(f"🗂 **所属模块**：{module}")

    if period:
        lines.append(f"📅 **来源周期**：{period}（当前状态：{status}）")

    if summary:
        lines.append(f"")
        lines.append(f"**背景摘要**：")
        lines.append(summary)

    if todos:
        lines.append(f"")
        lines.append(f"**当时的待办事项**：")
        lines.append(todos)

    lines.extend([
        f"",
        f"请问：",
        f"1. 这个话题目前的结论是什么？是否已经解决或有定论？",
        f'2. 如果已完成，可以直接回复"已完成"，我会更新记录。',
        f"3. 如果仍在推进中，预计什么时候有结果？",
        f"",
        f"（直接回复本条消息即可，感谢！）",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------

def find_stale_topics(
    records: List[Dict],
    threshold_days: int = STALE_THRESHOLD_DAYS,
    sent_ids: set = None,
    force: bool = False,
) -> List[Dict]:
    """
    从全部记录中筛选过期话题。

    过期条件：
      1. 来源周期结束日距今超过 threshold_days 天
      2. 状态为"跟进中"或"待跟进"（非已完成/已归档）
      3. 未在 sent_ids 中（除非 force=True）
    """
    today = date.today()
    stale = []

    for rec in records:
        record_id = rec.get("record_id", "")
        f = rec.get("fields", {})

        # 提取字段
        title   = extract_text(f.get("话题标题", ""))
        status  = extract_text(f.get("状态", ""))
        period  = extract_text(f.get("来源周期", ""))
        module  = extract_text(f.get("所属模块", ""))
        summary = extract_text(f.get("话题摘要", ""))
        todos   = extract_text(f.get("待办事项", ""))
        chat_id = extract_text(f.get("chat_id", ""))
        group   = extract_text(f.get("群组名称", ""))

        # 跳过已完成/已归档
        if status in ("已完成", "已归档"):
            continue

        # 跳过状态不在追踪范围内的
        if status not in STALE_STATUSES:
            logger.debug("跳过状态 '%s' 的话题: %s", status, title)
            continue

        # 解析周期结束日
        end_date = parse_period_end_date(period)
        if not end_date:
            logger.debug("无法解析来源周期 '%s'，跳过: %s", period, title)
            continue

        # 计算距今天数
        age_days = (today - end_date).days
        if age_days < threshold_days:
            continue

        # 防重复发送
        if not force and sent_ids and record_id in sent_ids:
            logger.debug("已发送过追问，跳过: %s (record_id=%s)", title, record_id)
            continue

        stale.append({
            "record_id": record_id,
            "title": title,
            "status": status,
            "period": period,
            "module": module,
            "summary": summary,
            "todos": todos,
            "chat_id": chat_id,
            "group": group,
            "age_days": age_days,
            "end_date": end_date.isoformat(),
        })

    # 按过期天数降序排列（最老的优先处理）
    stale.sort(key=lambda x: x["age_days"], reverse=True)
    logger.info("找到 %d 条过期话题（阈值 %d 天）", len(stale), threshold_days)
    return stale


def run(
    threshold_days: int = STALE_THRESHOLD_DAYS,
    dry_run: bool = False,
    force: bool = False,
) -> Dict:
    """
    主执行函数。

    返回执行摘要字典：
      {
        "total_stale": int,      # 过期话题总数
        "sent_count": int,       # 本次成功发送的消息数
        "skipped_count": int,    # 跳过（已发送过）的数量
        "failed_count": int,     # 发送失败的数量
        "stale_topics": [...],   # 过期话题列表
      }
    """
    logger.info("=== 话题收尾跟进 开始 (threshold=%d天, dry_run=%s, force=%s) ===",
                threshold_days, dry_run, force)

    # 1. 加载已发送记录
    sent_ids = load_sent_records()
    logger.info("已有 %d 条已发送记录", len(sent_ids))

    # 2. 拉取全部话题
    records = list_all_records()

    # 3. 筛选过期话题
    stale_topics = find_stale_topics(records, threshold_days, sent_ids, force)

    if not stale_topics:
        logger.info("没有需要跟进的过期话题")
        return {
            "total_stale": 0,
            "sent_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "stale_topics": [],
        }

    # 4. 按群组分组，每个群组发送一条汇总消息（避免刷屏）
    # 同时也支持逐条发送（当前实现：按群组分组汇总）
    by_chat: Dict[str, List[Dict]] = {}
    for topic in stale_topics:
        chat_id = topic.get("chat_id", "")
        if not chat_id:
            logger.warning("话题 '%s' 没有 chat_id，跳过", topic.get("title"))
            continue
        by_chat.setdefault(chat_id, []).append(topic)

    sent_count   = 0
    failed_count = 0
    newly_sent_ids = set()

    for chat_id, topics in by_chat.items():
        group_name = topics[0].get("group", chat_id)
        logger.info("处理群组 [%s] (%s)，共 %d 条过期话题", group_name, chat_id, len(topics))

        # 逐条发送（每条话题单独发一条消息，带完整上下文）
        for topic in topics:
            msg_text = build_followup_message(topic)
            success = send_message(chat_id, msg_text, dry_run=dry_run)

            if success:
                sent_count += 1
                newly_sent_ids.add(topic["record_id"])
                logger.info(
                    "  ✅ 已发送追问: [%d天] %s",
                    topic["age_days"], topic["title"]
                )
            else:
                failed_count += 1
                logger.error(
                    "  ❌ 发送失败: %s", topic["title"]
                )

            # 避免频率限制
            if not dry_run:
                time.sleep(MESSAGE_SEND_INTERVAL)

    # 5. 更新已发送记录
    if not dry_run and newly_sent_ids:
        sent_ids.update(newly_sent_ids)
        save_sent_records(sent_ids)

    summary = {
        "total_stale": len(stale_topics),
        "sent_count": sent_count,
        "skipped_count": len(stale_topics) - len([t for t in stale_topics if t.get("chat_id")]),
        "failed_count": failed_count,
        "stale_topics": stale_topics,
    }

    logger.info(
        "=== 话题收尾跟进 完成: 过期话题=%d, 发送=%d, 失败=%d ===",
        summary["total_stale"], summary["sent_count"], summary["failed_count"]
    )
    return summary


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="话题收尾跟进脚本：扫描过期话题并在群内 @VoidZ 发送追问消息"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=STALE_THRESHOLD_DAYS,
        help=f"过期阈值（天），默认 {STALE_THRESHOLD_DAYS} 天",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览，不实际发送消息",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重发，忽略已发送记录",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="仅列出过期话题，不发送消息（等同于 --dry-run）",
    )
    args = parser.parse_args()

    dry_run = args.dry_run or args.list_only

    summary = run(
        threshold_days=args.threshold,
        dry_run=dry_run,
        force=args.force,
    )

    # 打印摘要
    print("\n" + "=" * 60)
    print(f"话题收尾跟进摘要")
    print("=" * 60)
    print(f"过期话题总数: {summary['total_stale']}")
    print(f"成功发送:     {summary['sent_count']}")
    print(f"发送失败:     {summary['failed_count']}")
    print()

    if summary["stale_topics"]:
        print("过期话题列表：")
        for t in summary["stale_topics"]:
            status_icon = "✅" if t["record_id"] in load_sent_records() else "📌"
            print(f"  {status_icon} [{t['age_days']}天] [{t['status']}] {t['title']}")
            print(f"     群组: {t['group']} | 模块: {t['module']} | 周期: {t['period']}")


if __name__ == "__main__":
    main()

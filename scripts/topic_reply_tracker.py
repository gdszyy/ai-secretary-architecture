"""
topic_reply_tracker.py
======================
话题追踪模块 —— 跑批 Step 2

功能：
  1. 扫描 Bitable 话题表中「追问消息ID」不为空的记录（即已发出追问的话题）
  2. 拉取对应群组中该消息的回复（飞书 Thread/Reply API）
  3. 用 LLM 判断回复是否包含有效结论，提取结论摘要
  4. 将结论写回 Bitable：更新「追问回复」字段，并将「状态」改为「已完成」

Bitable 字段说明（已在表中创建）：
  - 追问消息ID  (fld8jo7ecE)  : 发出追问时的消息 message_id
  - 追问时间    (flds9Q8jEC)  : 发出追问的时间戳（毫秒）
  - 追问回复    (flddHCW6PU)  : LLM 提取的结论摘要
  - 状态        (fldlBZBks3)  : 话题状态（已完成 / 跟进中 / 待跟进）

用法：
  python3 topic_reply_tracker.py              # 正式运行
  python3 topic_reply_tracker.py --dry-run    # 预览，不写回 Bitable
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timezone
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
logger = logging.getLogger("topic_reply_tracker")

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

APP_ID     = os.environ.get("LARK_APP_ID",     "cli_a9d985cd40f89e1a")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "UNemS0zPnUuXhONgkuuprgdK3SrVx05T")

BASE_ID  = "CyDxbUQGGa3N2NsVanMjqdjxp6e"
TABLE_ID = "tblKscoaGp6VwhQe"

# Bitable 字段 ID
FIELD_MSG_ID    = "fld8jo7ecE"   # 追问消息ID
FIELD_ASK_TIME  = "flds9Q8jEC"   # 追问时间
FIELD_REPLY     = "flddHCW6PU"   # 追问回复
FIELD_STATUS    = "fldlBZBks3"   # 状态
FIELD_TITLE     = "fldhqZVguX"   # 话题标题
FIELD_CHAT_ID   = "fldKw4mBtu"   # chat_id

# 视为「有效回复」的最低字符数
MIN_REPLY_LENGTH = 5

# API 调用间隔
API_INTERVAL = 0.8

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


def lark_patch(url: str, payload: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    }
    r = requests.patch(url, headers=headers, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def extract_text(v) -> str:
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


# ---------------------------------------------------------------------------
# 飞书消息回复拉取
# ---------------------------------------------------------------------------

def fetch_message_replies(message_id: str) -> List[Dict]:
    """
    拉取某条消息的所有回复（Thread 模式）。
    飞书 API: GET /im/v1/messages/{message_id}/reply
    """
    url = f"https://open.larksuite.com/open-apis/im/v1/messages/{message_id}/reply"
    try:
        data = lark_get(url, {"page_size": 50})
        if data.get("code") != 0:
            logger.warning("拉取回复失败: msg_id=%s, code=%s, msg=%s",
                           message_id, data.get("code"), data.get("msg"))
            return []
        return data.get("data", {}).get("items", [])
    except Exception as e:
        logger.error("拉取回复异常: msg_id=%s, error=%s", message_id, str(e))
        return []


def parse_reply_text(reply_item: dict) -> str:
    """从回复消息中提取纯文本"""
    import re
    body_str = reply_item.get("body", {}).get("content", "")
    try:
        body = json.loads(body_str)
        text = body.get("text", "")
        # 去除 @mention 标签
        text = re.sub(r"<at[^>]*>[^<]*</at>", "", text)
        return text.strip()
    except Exception:
        return body_str.strip()


# ---------------------------------------------------------------------------
# LLM 回复分析
# ---------------------------------------------------------------------------

client = OpenAI()

REPLY_ANALYSIS_PROMPT = """你是一个项目秘书AI，负责判断飞书群聊中对话题追问的回复是否包含有效结论。

你会收到：
1. 原始话题标题和背景
2. 追问消息内容
3. 所有回复消息

请判断回复中是否有实质性结论，并输出以下 JSON：
{
  "has_conclusion": true/false,
  "conclusion": "结论摘要（1-3句话，若无结论则为空字符串）",
  "suggested_status": "已完成" 或 "跟进中" 或 "待跟进",
  "reason": "判断理由（一句话）"
}

判断规则：
- 回复中明确说明已完成、已解决、不做了、已上线等 → has_conclusion=true, suggested_status=已完成
- 回复中说明正在推进、预计XX时间完成 → has_conclusion=true, suggested_status=跟进中
- 回复中只有"好的"、"收到"、表情包等无实质内容 → has_conclusion=false
- 无任何回复 → has_conclusion=false
只输出合法 JSON，不要有其他文字。"""


def analyze_replies_with_llm(
    topic_title: str,
    topic_summary: str,
    replies: List[str],
) -> Dict:
    """用 LLM 分析回复，判断是否有结论"""
    if not replies:
        return {
            "has_conclusion": False,
            "conclusion": "",
            "suggested_status": "待跟进",
            "reason": "无回复",
        }

    replies_text = "\n".join(f"- {r}" for r in replies if r.strip())

    user_prompt = f"""话题标题：{topic_title}
话题背景：{topic_summary or "（无摘要）"}

回复内容：
{replies_text or "（无回复）"}

请分析并输出 JSON。"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": REPLY_ANALYSIS_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=300,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error("LLM 分析回复失败: %s", str(e))
        return {
            "has_conclusion": False,
            "conclusion": "",
            "suggested_status": "跟进中",
            "reason": f"LLM 调用失败: {str(e)}",
        }


# ---------------------------------------------------------------------------
# Bitable 更新
# ---------------------------------------------------------------------------

def update_bitable_record(record_id: str, fields: dict) -> bool:
    """更新 Bitable 记录的指定字段"""
    url = (
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}"
        f"/tables/{TABLE_ID}/records/{record_id}"
    )
    try:
        data = lark_patch(url, {"fields": fields})
        if data.get("code") == 0:
            return True
        logger.error("更新 Bitable 失败: code=%s, msg=%s", data.get("code"), data.get("msg"))
        return False
    except Exception as e:
        logger.error("更新 Bitable 异常: %s", str(e))
        return False


def write_followup_msg_id(record_id: str, message_id: str, ask_time_ms: int) -> bool:
    """将追问消息ID和追问时间写入 Bitable（由 stale_topic_followup 调用）"""
    return update_bitable_record(record_id, {
        FIELD_MSG_ID: message_id,
        FIELD_ASK_TIME: ask_time_ms,
    })


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------

def list_pending_followup_records() -> List[Dict]:
    """
    拉取所有「已发出追问但尚未收到回复」的话题记录。
    条件：追问消息ID 不为空 AND 追问回复 为空 AND 状态 != 已完成
    """
    url = (
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}"
        f"/tables/{TABLE_ID}/records"
    )
    all_records = []
    page_token = None

    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        data = lark_get(url, params).get("data", {})
        all_records.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")

    pending = []
    for rec in all_records:
        f = rec.get("fields", {})
        msg_id  = extract_text(f.get("追问消息ID", ""))
        reply   = extract_text(f.get("追问回复", ""))
        status  = extract_text(f.get("状态", ""))

        if msg_id and not reply and status != "已完成":
            pending.append({
                "record_id": rec["record_id"],
                "title":     extract_text(f.get("话题标题", "")),
                "summary":   extract_text(f.get("话题摘要", "")),
                "chat_id":   extract_text(f.get("chat_id", "")),
                "msg_id":    msg_id,
                "status":    status,
            })

    logger.info("找到 %d 条待追踪回复的话题", len(pending))
    return pending


def run(dry_run: bool = False) -> Dict:
    """
    主执行函数。
    返回执行摘要。
    """
    logger.info("=== 话题追踪 开始 (dry_run=%s) ===", dry_run)

    pending = list_pending_followup_records()

    if not pending:
        logger.info("没有待追踪的话题")
        return {"total": 0, "concluded": 0, "no_reply": 0, "failed": 0}

    concluded = 0
    no_reply  = 0
    failed    = 0

    for topic in pending:
        record_id = topic["record_id"]
        title     = topic["title"]
        msg_id    = topic["msg_id"]

        logger.info("追踪话题: [%s] msg_id=%s", title, msg_id)

        # 1. 拉取回复
        reply_items = fetch_message_replies(msg_id)
        reply_texts = [parse_reply_text(r) for r in reply_items]
        reply_texts = [t for t in reply_texts if len(t) >= MIN_REPLY_LENGTH]

        if not reply_texts:
            logger.info("  → 暂无有效回复，跳过")
            no_reply += 1
            time.sleep(API_INTERVAL)
            continue

        logger.info("  → 收到 %d 条有效回复", len(reply_texts))

        # 2. LLM 分析
        analysis = analyze_replies_with_llm(
            topic_title=title,
            topic_summary=topic.get("summary", ""),
            replies=reply_texts,
        )

        logger.info(
            "  → has_conclusion=%s, suggested_status=%s, reason=%s",
            analysis.get("has_conclusion"),
            analysis.get("suggested_status"),
            analysis.get("reason"),
        )

        if not analysis.get("has_conclusion"):
            no_reply += 1
            time.sleep(API_INTERVAL)
            continue

        # 3. 写回 Bitable
        conclusion     = analysis.get("conclusion", "")
        new_status     = analysis.get("suggested_status", "跟进中")
        reply_summary  = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] {conclusion}"

        if dry_run:
            logger.info("  [DRY-RUN] 将更新: 追问回复=%s, 状态=%s", reply_summary, new_status)
            concluded += 1
        else:
            success = update_bitable_record(record_id, {
                FIELD_REPLY:  reply_summary,
                FIELD_STATUS: new_status,
            })
            if success:
                logger.info("  ✅ 已更新 Bitable: 状态→%s", new_status)
                concluded += 1
            else:
                failed += 1

        time.sleep(API_INTERVAL)

    summary = {
        "total":     len(pending),
        "concluded": concluded,
        "no_reply":  no_reply,
        "failed":    failed,
    }
    logger.info(
        "=== 话题追踪 完成: 总计=%d, 有结论=%d, 无回复=%d, 失败=%d ===",
        summary["total"], summary["concluded"], summary["no_reply"], summary["failed"]
    )
    return summary


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="话题追踪：扫描已追问话题的回复并更新状态")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写回 Bitable")
    args = parser.parse_args()

    summary = run(dry_run=args.dry_run)

    print("\n" + "=" * 50)
    print("话题追踪摘要")
    print("=" * 50)
    print(f"待追踪话题: {summary['total']}")
    print(f"已有结论:   {summary['concluded']}")
    print(f"暂无回复:   {summary['no_reply']}")
    print(f"更新失败:   {summary['failed']}")


if __name__ == "__main__":
    main()

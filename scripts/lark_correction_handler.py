"""
lark_correction_handler.py
===========================
飞书卡片回复纠正指令处理器

职责：
  1. 权限控制：只处理 AUTHORIZED_USER_IDS 中用户发送的消息
  2. 格式解析：正则匹配"纠正："/"补充："前缀指令
  3. LLM 意图解析：格式不严格时调用 GPT 解析意图和话题标题
  4. 调用 correction_writer 写入 Bitable
  5. 返回确认消息文本（由调用方发送到飞书群）

被 main.py 的 handle_message_event 调用。
"""

import os
import re
import json
import logging
from typing import Optional
from openai import OpenAI

from correction_writer import upsert_correction, normalize_intent, INTENT_ALIAS

logger = logging.getLogger("lark_correction_handler")

# ---------------------------------------------------------------------------
# 授权用户配置（只有这些 open_id 的消息才会触发纠正写入）
# 通过环境变量 AUTHORIZED_USER_IDS 配置，多个用逗号分隔
# 示例：AUTHORIZED_USER_IDS=ou_xxxxxxxxxxxxxxxx,ou_yyyyyyyyyyyyyyyy
# ---------------------------------------------------------------------------
_authorized_raw = os.environ.get("AUTHORIZED_USER_IDS", "")
AUTHORIZED_USER_IDS: set = {
    uid.strip() for uid in _authorized_raw.split(",") if uid.strip()
}

# ---------------------------------------------------------------------------
# LLM 客户端（OpenAI 兼容接口）
# ---------------------------------------------------------------------------
_llm_client: Optional[OpenAI] = None

def _get_llm_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI()  # 使用环境变量中预配置的 API Key 和 base_url
    return _llm_client


# ---------------------------------------------------------------------------
# 正则解析：严格格式
# ---------------------------------------------------------------------------

# 纠正：[话题名] 实际情况是……
_RE_CORRECT = re.compile(
    r"^纠正[：:]\s*(.+?)\s+实际情况是\s*(.+)$",
    re.DOTALL,
)

# 补充：[话题名] [意图类型] 内容是……
_RE_SUPPLEMENT = re.compile(
    r"^补充[：:]\s*(.+?)\s+(决策|里程碑|风险|任务|major_decision|milestone_fact|risk_blocker|routine_task)\s+内容是\s*(.+)$",
    re.DOTALL,
)

# 宽松匹配：只要以"纠正："或"补充："开头
_RE_LOOSE = re.compile(r"^(纠正|补充)[：:]", re.MULTILINE)


def _parse_strict(text: str) -> Optional[dict]:
    """
    尝试严格格式解析。
    返回 {"action": "update"|"create", "title": str, "intent": str, "summary": str}
    或 None（未匹配）。
    """
    text = text.strip()

    m = _RE_CORRECT.match(text)
    if m:
        return {
            "action":  "update",
            "title":   m.group(1).strip(),
            "intent":  "major_decision",  # 纠正默认不改变意图，写入时保留原有
            "summary": m.group(2).strip(),
            "confidence": 1.0,
        }

    m = _RE_SUPPLEMENT.match(text)
    if m:
        return {
            "action":  "create",
            "title":   m.group(1).strip(),
            "intent":  normalize_intent(m.group(2).strip()),
            "summary": m.group(3).strip(),
            "confidence": 1.0,
        }

    return None


def _parse_with_llm(text: str) -> dict:
    """
    使用 LLM 解析格式不严格的纠正/补充消息。
    返回与 _parse_strict 相同结构，附加 confidence 字段。
    """
    intent_options = ", ".join(list(INTENT_ALIAS.keys()) + ["major_decision", "milestone_fact", "risk_blocker", "routine_task"])
    system_prompt = f"""你是一个信息提取助手，负责从飞书群聊消息中解析"信息纠正"或"信息补充"指令。

请从用户消息中提取以下字段，以 JSON 格式返回：
- action: "update"（纠正已有话题）或 "create"（补充新话题）
- title: 话题标题（简洁，5-15字）
- intent: 意图类型，必须是以下之一：{intent_options}
- summary: 纠正/补充的完整内容描述
- confidence: 你对解析结果的置信度（0.0-1.0）
- needs_confirm: 当 confidence < 0.7 时设为 true，表示需要向用户确认

规则：
- 如果消息以"纠正："开头，action 为 "update"
- 如果消息以"补充："开头，action 为 "create"
- 如果无法判断，action 为 "update"
- 意图类型根据内容语义判断：决策/决定→major_decision，里程碑/完成→milestone_fact，风险/阻塞/问题→risk_blocker，任务/进行中→routine_task
- 只返回 JSON，不要有其他内容"""

    try:
        client = _get_llm_client()
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=512,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
        result = json.loads(raw)
        # 规范化 intent
        result["intent"] = normalize_intent(result.get("intent", "routine_task"))
        result.setdefault("confidence", 0.5)
        result.setdefault("needs_confirm", result["confidence"] < 0.7)
        logger.info(
            "LLM 解析结果: action=%s title=%s intent=%s confidence=%.2f",
            result.get("action"), result.get("title"),
            result.get("intent"), result.get("confidence"),
        )
        return result
    except Exception as e:
        logger.error("LLM 解析失败: %s", e)
        return {
            "action": "update",
            "title": "未知话题",
            "intent": "routine_task",
            "summary": text,
            "confidence": 0.0,
            "needs_confirm": True,
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# 主处理函数
# ---------------------------------------------------------------------------

def is_correction_command(text: str) -> bool:
    """判断消息是否为纠正/补充指令（宽松匹配）"""
    return bool(_RE_LOOSE.search(text.strip()))


def handle_correction(
    text: str,
    sender_open_id: str,
    sender_name: str = "unknown",
    message_id: str = "",
) -> dict:
    """
    处理飞书卡片回复中的纠正/补充指令。

    参数：
        text           : 消息文本
        sender_open_id : 发送者的 open_id（用于权限校验）
        sender_name    : 发送者名称（用于日志和确认消息）
        message_id     : 消息 ID（用于日志追踪）

    返回：
        {
            "handled": bool,           # 是否被处理（False 表示不是纠正指令或权限不足）
            "success": bool,           # 写入是否成功
            "action": "update"|"create"|None,
            "title": str,
            "reply_text": str,         # 应回复给用户的消息
            "needs_confirm": bool,     # 是否需要用户确认（LLM 置信度低时）
            "parsed": dict,            # 解析结果（调试用）
        }
    """
    text = text.strip()

    # ── 1. 权限校验 ──────────────────────────────────────────────────────────
    if AUTHORIZED_USER_IDS and sender_open_id not in AUTHORIZED_USER_IDS:
        logger.info(
            "消息来自未授权用户 open_id=%s，跳过纠正处理 (msg_id=%s)",
            sender_open_id, message_id,
        )
        return {
            "handled": False,
            "success": False,
            "action": None,
            "title": None,
            "reply_text": "",
            "needs_confirm": False,
            "parsed": {},
        }

    # ── 2. 判断是否为纠正/补充指令 ────────────────────────────────────────────
    if not is_correction_command(text):
        return {
            "handled": False,
            "success": False,
            "action": None,
            "title": None,
            "reply_text": "",
            "needs_confirm": False,
            "parsed": {},
        }

    logger.info(
        "收到纠正指令: sender=%s open_id=%s msg_id=%s text_preview=%s",
        sender_name, sender_open_id, message_id, text[:80],
    )

    # ── 3. 解析指令 ──────────────────────────────────────────────────────────
    parsed = _parse_strict(text)
    used_llm = False

    if parsed is None:
        # 严格格式未匹配，尝试 LLM 解析
        logger.info("严格格式未匹配，调用 LLM 解析")
        parsed = _parse_with_llm(text)
        used_llm = True

    # ── 4. 置信度低时，返回确认请求，不写入 ──────────────────────────────────
    if parsed.get("needs_confirm") or parsed.get("confidence", 1.0) < 0.7:
        intent_label = {
            "major_decision": "重大决策",
            "milestone_fact": "里程碑",
            "risk_blocker":   "风险/阻塞",
            "routine_task":   "常规任务",
        }.get(parsed.get("intent", ""), parsed.get("intent", ""))

        confirm_text = (
            f"⚠️ 我理解你想要{'纠正' if parsed.get('action') == 'update' else '补充'}以下信息，"
            f"但不太确定，请确认：\n\n"
            f"📌 话题：{parsed.get('title', '未识别')}\n"
            f"🏷️ 意图：{intent_label}\n"
            f"📝 内容：{parsed.get('summary', text)[:200]}\n\n"
            f"如果正确，请回复：确认纠正\n"
            f"如需修改，请使用标准格式：\n"
            f"  纠正：[话题名] 实际情况是……\n"
            f"  补充：[话题名] [决策/里程碑/风险/任务] 内容是……"
        )
        return {
            "handled": True,
            "success": False,
            "action": parsed.get("action"),
            "title": parsed.get("title"),
            "reply_text": confirm_text,
            "needs_confirm": True,
            "parsed": parsed,
        }

    # ── 5. 写入 Bitable ──────────────────────────────────────────────────────
    source = f"VoidZ飞书卡片回复"
    result = upsert_correction(
        title=parsed["title"],
        summary=parsed["summary"],
        intent=parsed["intent"],
        source=source,
    )

    # ── 6. 构造确认回复 ──────────────────────────────────────────────────────
    if result["success"]:
        action_label = "✅ 已更新" if result["action"] == "update" else "✅ 已新建"
        intent_label = {
            "major_decision": "重大决策",
            "milestone_fact": "里程碑",
            "risk_blocker":   "风险/阻塞",
            "routine_task":   "常规任务",
        }.get(parsed.get("intent", ""), parsed.get("intent", ""))
        llm_note = "（LLM 智能解析）" if used_llm else ""
        reply_text = (
            f"{action_label} Bitable 记录 {llm_note}\n\n"
            f"📌 话题：{parsed['title']}\n"
            f"🏷️ 意图：{intent_label}\n"
            f"📝 摘要：{parsed['summary'][:150]}{'...' if len(parsed['summary']) > 150 else ''}"
        )
    else:
        reply_text = (
            f"❌ 写入 Bitable 失败，请稍后重试或手动告知 Manus。\n"
            f"错误信息：{result.get('error', '未知错误')}"
        )

    return {
        "handled": True,
        "success": result["success"],
        "action": result["action"],
        "title": parsed["title"],
        "reply_text": reply_text,
        "needs_confirm": False,
        "parsed": parsed,
    }

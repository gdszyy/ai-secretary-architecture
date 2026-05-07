"""
requirement_tracker.py
======================
需求记录跟踪模块。

核心交互场景
------------
1. **私聊 / 单独 @ 机器人** (chat_type == "p2p")
   每一次 @ 都视作一条新需求或对前一条草稿需求的补充。

2. **群里 @ 机器人** (chat_type == "group" 且 mentions 包含机器人)
   机器人会拉取该群最近 N 条消息，结合 @ 时的当前消息，由 LLM 抽取
   "用户希望记录的需求"，并向该用户发起 **确认 → 入库** 的流程。

3. **每日定时跟进**（见 `requirement_followup.py`）
   扫描状态为 `draft` / `clarifying` 的需求，私聊提出者继续追问。

完善度评分
----------
基于 7 个核心字段（标题、描述、动机、模块、验收标准、优先级、期望交付时间）
满分 100，每缺一项扣相应权重。当评分 ≥ 阈值后，机器人会要求用户确认入库。

Bitable 记录字段（建议手动建表，字段名见 BITABLE_FIELDS_SCHEMA）：
  需求ID、标题、描述、动机、涉及模块、验收标准、优先级、期望交付时间、
  状态、完善度、缺失字段、提出者open_id、提出者姓名、来源chat_id、
  来源chat_type、原始消息ID、群上下文消息IDs、跟进次数、最后跟进时间、
  创建时间、最后更新时间、备注

环境变量
--------
  BITABLE_BASE_ID                 多维表 App Token（与既有变量复用）
  BITABLE_TABLE_REQUIREMENTS      需求池表 ID（新增，需配置）
  REQUIREMENT_GROUP_CONTEXT_SIZE  群里 @ 时拉取多少条历史，默认 20
  REQUIREMENT_COMPLETE_THRESHOLD  完善度阈值，默认 80
  DASHSCOPE_API_KEY / QWEN_MODEL  LLM 配置（与既有问答模块复用）
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from lark_bitable_client import LarkBitableClient
import lark_sdk_client as sdk

logger = logging.getLogger("ai_secretary.requirement_tracker")


# ---------------------------------------------------------------------------
# 字段定义
# ---------------------------------------------------------------------------

# Bitable 字段权重（之和应为 100）
FIELD_WEIGHTS: Dict[str, int] = {
    "标题": 15,
    "描述": 25,
    "动机": 10,
    "涉及模块": 15,
    "验收标准": 20,
    "优先级": 5,
    "期望交付时间": 10,
}

# LLM 在抽取时使用的内部字段名（与 Bitable 字段一一对应）
LLM_FIELD_KEYS = list(FIELD_WEIGHTS.keys())

STATUS_DRAFT = "草稿"
STATUS_CLARIFYING = "待澄清"
STATUS_PENDING_CONFIRM = "待确认"
STATUS_CONFIRMED = "已确认"
STATUS_CANCELLED = "已取消"

ACTIVE_STATUSES = (STATUS_DRAFT, STATUS_CLARIFYING, STATUS_PENDING_CONFIRM)


# ---------------------------------------------------------------------------
# 触发判定
# ---------------------------------------------------------------------------

# 群里仍可触发问答模块的关键词（这种情况下不路由到需求记录）
QUERY_PREFIXES = ("?", "？", "查询", "问一下", "请问", "what", "where", "how")

# 显式记录关键词
RECORD_PREFIXES = ("记录需求", "新需求", "需求：", "需求:", "/req", "登记需求", "记下", "记一下")


def is_explicit_record_intent(text: str) -> bool:
    stripped = (text or "").strip().lower()
    return any(stripped.startswith(p.lower()) for p in RECORD_PREFIXES)


def looks_like_query(text: str) -> bool:
    stripped = (text or "").strip().lower()
    return any(stripped.startswith(p.lower()) for p in QUERY_PREFIXES)


# ---------------------------------------------------------------------------
# Bitable 配置
# ---------------------------------------------------------------------------

def _bitable_config() -> Tuple[str, str]:
    base_id = os.environ.get("BITABLE_BASE_ID") or os.environ.get("BITABLE_APP_TOKEN", "")
    table_id = os.environ.get("BITABLE_TABLE_REQUIREMENTS", "")
    if not base_id or not table_id:
        raise RuntimeError(
            "需求池 Bitable 未配置：请设置 BITABLE_BASE_ID 与 BITABLE_TABLE_REQUIREMENTS"
        )
    return base_id, table_id


def _get_bitable_client() -> LarkBitableClient:
    return LarkBitableClient()


# ---------------------------------------------------------------------------
# LLM 调用
# ---------------------------------------------------------------------------

_llm_client: Optional[OpenAI] = None


def _get_llm() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY 未配置")
        _llm_client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    return _llm_client


_QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")


_EXTRACT_SYSTEM_PROMPT = f"""你是一名严谨的项目需求秘书，负责把用户表达的需求拆解为结构化字段。
请输出 JSON（不要 markdown 代码块），字段如下：
{{
  "is_requirement": true/false,           // 用户是否在描述「想要做的事 / 想记录的需求」
  "fields": {{
    "标题": "...",
    "描述": "...",
    "动机": "...",
    "涉及模块": "...",
    "验收标准": "...",
    "优先级": "P0/P1/P2/P3 之一，留空表示未给出",
    "期望交付时间": "YYYY-MM-DD 或留空"
  }},
  "summary": "一句话概括用户的需求，便于复述"
}}

规则：
- 没有信息的字段填空字符串 ""，**不要编造**。
- "标题" 是从用户描述中提炼的短句（≤ 20 字），不是你自己拟的产品名。
- "描述" 写得比标题更详细，包含核心 What。
- "动机" 是 Why（为什么要做、解决什么问题），用户没提就留空。
- "涉及模块" 优先复用项目中已有模块前缀（mod_casino / mod_activity / mod_settlement /
  mod_riskcontrol / mod_customer_service 等），未给出请留空。
- "验收标准" 是 How（如何判定做完了），用户没提就留空。
- "优先级" 字段值固定为 P0/P1/P2/P3 之一或空字符串。
- 如果输入是单纯的查询、闲聊、问候，将 is_requirement 置为 false，fields 全部留空。
"""


_GROUP_CONTEXT_SYSTEM_PROMPT = """你是一名项目需求秘书。用户在群里 @ 了你，希望你"读取上下文"
把他想表达的需求记录下来。
你将看到：(1) 该用户 @ 你时的那条消息；(2) 群里最近一段消息历史。

请聚焦该用户视角，抽取他**真正想要登记的需求**：
- 优先采纳该用户自己说过的话；
- 当用户的 @ 消息含有 "前面/上面/上述/这个/前面提到的" 等指代时，从历史里找到对应内容；
- 忽略与需求无关的闲聊、表情、附议消息。

输出 JSON：
{
  "is_requirement": true/false,
  "fields": { 标题/描述/动机/涉及模块/验收标准/优先级/期望交付时间 },
  "summary": "一句话复述这条需求",
  "context_message_ids": ["你引用了哪些 message_id"]
}

无法从上下文还原出明确需求时 is_requirement = false，并在 summary 中写"未识别到清晰需求"。
"""


def _llm_extract(user_text: str, group_context: Optional[List[Dict]] = None) -> Dict:
    """让 LLM 抽取结构化需求字段。"""
    sys_prompt = _GROUP_CONTEXT_SYSTEM_PROMPT if group_context else _EXTRACT_SYSTEM_PROMPT

    if group_context:
        context_lines: List[str] = []
        for m in group_context:
            sender = m.get("sender_name") or m.get("sender_id") or "用户"
            mid = m.get("message_id", "")
            content = (m.get("text") or "").replace("\n", " ").strip()
            if not content:
                continue
            context_lines.append(f"[{mid}] {sender}: {content}")
        user_payload = (
            "用户当前消息:\n" + user_text +
            "\n\n群最近消息(从旧到新):\n" + "\n".join(context_lines[-30:])
        )
    else:
        user_payload = user_text

    try:
        client = _get_llm()
        resp = client.chat.completions.create(
            model=_QWEN_MODEL,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_payload},
            ],
            temperature=0.1,
            max_tokens=600,
        )
        raw = (resp.choices[0].message.content or "").strip()
        raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning("LLM 需求抽取失败: %s", e)
        return {"is_requirement": False, "fields": {}, "summary": ""}


# ---------------------------------------------------------------------------
# 完善度评分
# ---------------------------------------------------------------------------

def score_completeness(fields: Dict[str, str]) -> Tuple[int, List[str]]:
    """
    根据字段权重计算完善度（0-100），并返回缺失字段列表（按权重降序）。
    """
    score = 0
    missing: List[Tuple[str, int]] = []
    for name, weight in FIELD_WEIGHTS.items():
        v = (fields.get(name) or "").strip()
        if v:
            score += weight
        else:
            missing.append((name, weight))
    missing.sort(key=lambda x: -x[1])
    return score, [name for name, _ in missing]


def threshold() -> int:
    return int(os.environ.get("REQUIREMENT_COMPLETE_THRESHOLD", "80"))


# ---------------------------------------------------------------------------
# Bitable 读写
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _find_active_requirement_for(open_id: str) -> Optional[Dict]:
    """查找该用户尚未确认的需求草稿。"""
    if not open_id:
        return None
    try:
        base_id, table_id = _bitable_config()
        client = _get_bitable_client()
        records = client.list_records(base_id, table_id)
    except Exception as e:
        logger.error("查询活跃需求失败: %s", e)
        return None

    candidates: List[Dict] = []
    for rec in records:
        fields = rec.get("fields") or {}
        if _flatten_text(fields.get("提出者open_id")) != open_id:
            continue
        status = _flatten_text(fields.get("状态"))
        if status in ACTIVE_STATUSES:
            candidates.append(rec)

    if not candidates:
        return None

    def _sort_key(r: Dict) -> str:
        return _flatten_text(r.get("fields", {}).get("最后更新时间")) or ""

    candidates.sort(key=_sort_key, reverse=True)
    return candidates[0]


def _flatten_text(value: Any) -> str:
    """Bitable 文本字段可能返回 [{"text":"..."}] 数组，统一转字符串。"""
    if value is None:
        return ""
    if isinstance(value, list):
        out: List[str] = []
        for seg in value:
            if isinstance(seg, dict):
                out.append(seg.get("text", ""))
            else:
                out.append(str(seg))
        return "".join(out).strip()
    return str(value).strip()


def _record_to_fields(rec: Dict) -> Dict[str, str]:
    """从 Bitable 记录中恢复内部字段字典。"""
    raw = rec.get("fields") or {}
    return {k: _flatten_text(raw.get(k, "")) for k in LLM_FIELD_KEYS}


def _build_bitable_payload(
    *,
    requirement_id: str,
    fields: Dict[str, str],
    completeness: int,
    missing: List[str],
    status: str,
    sender_open_id: str,
    sender_name: str,
    chat_id: str,
    chat_type: str,
    message_id: str,
    context_message_ids: List[str],
    follow_up_count: int,
    notes: str = "",
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "需求ID": requirement_id,
        "标题": fields.get("标题", ""),
        "描述": fields.get("描述", ""),
        "动机": fields.get("动机", ""),
        "涉及模块": fields.get("涉及模块", ""),
        "验收标准": fields.get("验收标准", ""),
        "优先级": fields.get("优先级", ""),
        "期望交付时间": fields.get("期望交付时间", ""),
        "状态": status,
        "完善度": completeness,
        "缺失字段": ", ".join(missing),
        "提出者open_id": sender_open_id,
        "提出者姓名": sender_name,
        "来源chat_id": chat_id,
        "来源chat_type": chat_type,
        "原始消息ID": message_id,
        "群上下文消息IDs": ",".join(context_message_ids or []),
        "跟进次数": follow_up_count,
        "最后跟进时间": _now_iso(),
        "最后更新时间": _now_iso(),
        "备注": notes,
    }
    return payload


def _create_record(payload: Dict[str, Any]) -> Optional[str]:
    try:
        base_id, table_id = _bitable_config()
        client = _get_bitable_client()
        payload = dict(payload)
        payload["创建时间"] = _now_iso()
        rec = client.create_record(base_id, table_id, payload)
        return rec.get("record_id", "")
    except Exception as e:
        logger.error("创建需求记录失败: %s", e)
        return None


def _update_record(record_id: str, payload: Dict[str, Any]) -> bool:
    try:
        base_id, table_id = _bitable_config()
        client = _get_bitable_client()
        client.update_record(base_id, table_id, record_id, payload)
        return True
    except Exception as e:
        logger.error("更新需求记录失败: %s", e)
        return False


# ---------------------------------------------------------------------------
# 用户回复合并 / 确认/取消识别
# ---------------------------------------------------------------------------

CONFIRM_TOKENS = ("确认", "确定", "ok", "好的", "可以", "是的", "yes", "y", "👍", "存吧", "入库")
CANCEL_TOKENS = ("取消", "不用了", "算了", "废了", "cancel", "no", "n", "❌")


def _is_confirm(text: str) -> bool:
    s = (text or "").strip().lower()
    return any(t in s for t in CONFIRM_TOKENS)


def _is_cancel(text: str) -> bool:
    s = (text or "").strip().lower()
    return any(t in s for t in CANCEL_TOKENS)


def _merge_fields(old: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
    """以新字段覆盖旧字段（仅当新值非空）。"""
    merged = dict(old)
    for k in LLM_FIELD_KEYS:
        v = (new.get(k) or "").strip()
        if v:
            merged[k] = v
    return merged


# ---------------------------------------------------------------------------
# 回复生成
# ---------------------------------------------------------------------------

def _format_summary(fields: Dict[str, str]) -> str:
    lines: List[str] = []
    for k in LLM_FIELD_KEYS:
        v = fields.get(k, "") or "（未填）"
        lines.append(f"• {k}: {v}")
    return "\n".join(lines)


def _format_clarification_questions(missing: List[str]) -> str:
    """根据缺失字段生成具体问题。"""
    prompts = {
        "标题": "这条需求适合用一句话怎么命名？",
        "描述": "能展开讲讲具体要做什么吗？",
        "动机": "为什么要做这件事？解决了什么问题 / 满足谁的诉求？",
        "涉及模块": "属于哪个模块（如 mod_casino / mod_activity / mod_settlement…）？",
        "验收标准": "如何判定这条需求做完了？给我一两条可观察的验收点。",
        "优先级": "你希望排到 P0 / P1 / P2 / P3 哪个优先级？",
        "期望交付时间": "期望什么时候上线？给个日期或大概时间窗。",
    }
    lines = [f"{i+1}. {prompts.get(m, m)}" for i, m in enumerate(missing[:3])]
    return "\n".join(lines)


def _format_intake_reply(
    summary: str,
    fields: Dict[str, str],
    completeness: int,
    missing: List[str],
    status: str,
    requirement_id: str,
) -> str:
    if status == STATUS_CONFIRMED:
        return (
            f"✅ 已入库需求 [{requirement_id}]\n"
            f"标题：{fields.get('标题', '')}\n"
            f"完善度：{completeness}\n\n"
            f"详情：\n{_format_summary(fields)}"
        )

    head = f"📝 我已暂存需求 [{requirement_id}]（完善度 {completeness}/100）"
    if summary:
        head += f"\n概要：{summary}"

    body = "\n\n📋 当前已记录：\n" + _format_summary(fields)

    if missing:
        body += "\n\n❓ 还差几个关键信息，可以补充一下吗：\n" + _format_clarification_questions(missing)
        if completeness >= threshold():
            body += "\n\n（如果先这样保存，回复「确认」即可入库）"
    else:
        body += "\n\n所有关键字段已齐全，回复「确认」即可入库；想改回复内容继续发我即可。"

    return head + body


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def handle(msg_info: Dict) -> Dict:
    """
    处理一条「@ 机器人」的消息，返回回复 payload。

    Returns:
      {
        "handled": bool,            # 是否被本模块处理
        "reply_text": str,          # 推荐回复文本（main.py 直接发送）
        "requirement_id": str,
        "status": str,
        "completeness": int,
        "missing": List[str],
      }
    """
    text = (msg_info.get("text") or "").strip()
    sender_open_id = msg_info.get("sender_id", "") or ""
    sender_name = msg_info.get("sender_name", "") or ""
    chat_id = msg_info.get("chat_id", "")
    chat_type = msg_info.get("chat_type", "")
    message_id = msg_info.get("message_id", "")

    # 去掉 @ 占位符
    cleaned = re.sub(r"@_user_\d+", "", text).strip()
    cleaned = re.sub(r"^\s*(记录需求|新需求|需求[:：]|/req|登记需求)\s*", "", cleaned).strip()

    if not cleaned:
        return _ack({
            "handled": True,
            "reply_text": "你好！把需求发给我，例如「我想加个 VIP 等级配置页，希望下周上线」，我会帮你拆解并存入需求池。",
        })

    # 先看该用户是否已有未确认的草稿
    existing = _find_active_requirement_for(sender_open_id)

    # 先识别确认 / 取消（仅当存在草稿时）
    if existing:
        if _is_cancel(cleaned):
            _update_record(existing.get("record_id", ""), {
                "状态": STATUS_CANCELLED,
                "最后更新时间": _now_iso(),
            })
            req_id = _flatten_text(existing.get("fields", {}).get("需求ID"))
            return _ack({
                "handled": True,
                "reply_text": f"已取消需求 [{req_id}]。需要重新登记直接告诉我即可。",
                "requirement_id": req_id,
                "status": STATUS_CANCELLED,
                "completeness": 0,
                "missing": [],
            })
        if _is_confirm(cleaned):
            return _confirm_existing(existing)

    # 拉取群上下文（仅在群聊场景）
    group_context: List[Dict] = []
    context_size = int(os.environ.get("REQUIREMENT_GROUP_CONTEXT_SIZE", "20"))
    if chat_type == "group" and context_size > 0:
        try:
            group_context = sdk.list_recent_messages(chat_id, page_size=context_size)
            if message_id:
                group_context = [m for m in group_context if m.get("message_id") != message_id]
        except Exception as e:
            logger.warning("拉取群上下文失败: %s", e)

    # LLM 抽取
    extracted = _llm_extract(cleaned, group_context if group_context else None)
    is_req = bool(extracted.get("is_requirement"))
    new_fields = extracted.get("fields", {}) or {}
    summary = extracted.get("summary", "")
    ctx_msg_ids = extracted.get("context_message_ids", []) or []

    # 没识别到需求且没有现存草稿 → 让上层路由继续走（不拦截）
    if not is_req and not existing:
        return {
            "handled": False,
            "reply_text": "",
            "requirement_id": "",
            "status": "",
            "completeness": 0,
            "missing": [],
        }

    if existing:
        # 合并到既有草稿
        old_fields = _record_to_fields(existing)
        merged = _merge_fields(old_fields, new_fields)
        completeness, missing = score_completeness(merged)
        follow_up = int(_flatten_text(existing.get("fields", {}).get("跟进次数")) or "0") + 1
        status = STATUS_PENDING_CONFIRM if completeness >= threshold() else STATUS_CLARIFYING
        req_id = _flatten_text(existing.get("fields", {}).get("需求ID")) or _gen_id()
        payload = _build_bitable_payload(
            requirement_id=req_id,
            fields=merged,
            completeness=completeness,
            missing=missing,
            status=status,
            sender_open_id=sender_open_id,
            sender_name=sender_name or _flatten_text(existing.get("fields", {}).get("提出者姓名")),
            chat_id=chat_id,
            chat_type=chat_type,
            message_id=message_id,
            context_message_ids=ctx_msg_ids,
            follow_up_count=follow_up,
        )
        # 不覆盖创建时间
        payload.pop("创建时间", None)
        _update_record(existing.get("record_id", ""), payload)
    else:
        # 新建草稿
        completeness, missing = score_completeness(new_fields)
        status = STATUS_PENDING_CONFIRM if completeness >= threshold() else (
            STATUS_CLARIFYING if missing else STATUS_PENDING_CONFIRM
        )
        req_id = _gen_id()
        merged = {k: new_fields.get(k, "") for k in LLM_FIELD_KEYS}
        payload = _build_bitable_payload(
            requirement_id=req_id,
            fields=merged,
            completeness=completeness,
            missing=missing,
            status=status,
            sender_open_id=sender_open_id,
            sender_name=sender_name or sdk.get_user_name(sender_open_id),
            chat_id=chat_id,
            chat_type=chat_type,
            message_id=message_id,
            context_message_ids=ctx_msg_ids,
            follow_up_count=0,
        )
        _create_record(payload)

    reply = _format_intake_reply(
        summary=summary,
        fields=merged,
        completeness=completeness,
        missing=missing,
        status=status,
        requirement_id=req_id,
    )
    return {
        "handled": True,
        "reply_text": reply,
        "requirement_id": req_id,
        "status": status,
        "completeness": completeness,
        "missing": missing,
    }


def _confirm_existing(existing: Dict) -> Dict:
    """处理用户回复"确认"：把草稿置为「已确认」。"""
    fields = _record_to_fields(existing)
    completeness, missing = score_completeness(fields)
    req_id = _flatten_text(existing.get("fields", {}).get("需求ID"))
    status = STATUS_CONFIRMED
    payload = {
        "状态": status,
        "完善度": completeness,
        "缺失字段": ", ".join(missing),
        "最后更新时间": _now_iso(),
    }
    _update_record(existing.get("record_id", ""), payload)
    return {
        "handled": True,
        "reply_text": _format_intake_reply(
            summary="",
            fields=fields,
            completeness=completeness,
            missing=missing,
            status=status,
            requirement_id=req_id,
        ),
        "requirement_id": req_id,
        "status": status,
        "completeness": completeness,
        "missing": missing,
    }


def _gen_id() -> str:
    return "REQ-" + uuid.uuid4().hex[:8].upper()


def _ack(payload: Dict) -> Dict:
    payload.setdefault("requirement_id", "")
    payload.setdefault("status", "")
    payload.setdefault("completeness", 0)
    payload.setdefault("missing", [])
    return payload


# ---------------------------------------------------------------------------
# Bitable Schema 提示（手动建表参考）
# ---------------------------------------------------------------------------

BITABLE_FIELDS_SCHEMA: List[Tuple[str, str]] = [
    ("需求ID", "Text"),
    ("标题", "Text"),
    ("描述", "Multiline Text"),
    ("动机", "Multiline Text"),
    ("涉及模块", "Text"),
    ("验收标准", "Multiline Text"),
    ("优先级", "SingleSelect: P0/P1/P2/P3"),
    ("期望交付时间", "Text (YYYY-MM-DD)"),
    ("状态", f"SingleSelect: {'/'.join([STATUS_DRAFT, STATUS_CLARIFYING, STATUS_PENDING_CONFIRM, STATUS_CONFIRMED, STATUS_CANCELLED])}"),
    ("完善度", "Number"),
    ("缺失字段", "Text"),
    ("提出者open_id", "Text"),
    ("提出者姓名", "Text"),
    ("来源chat_id", "Text"),
    ("来源chat_type", "Text"),
    ("原始消息ID", "Text"),
    ("群上下文消息IDs", "Text"),
    ("跟进次数", "Number"),
    ("最后跟进时间", "Text"),
    ("创建时间", "Text"),
    ("最后更新时间", "Text"),
    ("备注", "Multiline Text"),
]

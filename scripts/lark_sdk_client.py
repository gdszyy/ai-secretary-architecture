"""
lark_sdk_client.py
==================
基于官方 SDK `lark-oapi` (https://github.com/larksuite/oapi-sdk-python) 的
Lark 客户端封装。提供：
  - 单例 lark.Client（带 domain 自适应：FEISHU / LARK）
  - 发送文本 / Markdown / 卡片消息
  - 拉取群消息历史（用于「群里 @ 机器人时阅读上下文」）
  - 获取机器人自身 open_id（用于识别 @ 机器人）
  - 获取用户基本信息（用于在卡片中展示提出者姓名）

设计原则：
  - 与既有的 `LarkBitableClient`（直连 HTTP）共存，不破坏现有调用方。
  - 模块内部对 SDK 的网络异常做容错：返回 None 而非抛出，便于 webhook 中调用。
  - 默认使用 `LARK_DOMAIN`，可通过 `LARK_DOMAIN_TYPE=feishu` 切换到飞书国内域名。

环境变量：
  LARK_APP_ID
  LARK_APP_SECRET
  LARK_DOMAIN_TYPE     "lark"（默认）或 "feishu"
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    ListMessageRequest,
)

logger = logging.getLogger("ai_secretary.lark_sdk")


# ---------------------------------------------------------------------------
# Client 单例
# ---------------------------------------------------------------------------

_client_singleton: Optional[lark.Client] = None
_bot_open_id_cache: Optional[str] = None


def get_client() -> lark.Client:
    """构建并缓存 lark.Client 单例。"""
    global _client_singleton
    if _client_singleton is not None:
        return _client_singleton

    app_id = os.environ.get("LARK_APP_ID", "")
    app_secret = os.environ.get("LARK_APP_SECRET", "")
    if not app_id or not app_secret:
        raise RuntimeError("LARK_APP_ID / LARK_APP_SECRET 未配置")

    domain_type = os.environ.get("LARK_DOMAIN_TYPE", "lark").lower()
    domain = lark.FEISHU_DOMAIN if domain_type == "feishu" else lark.LARK_DOMAIN

    _client_singleton = (
        lark.Client.builder()
        .app_id(app_id)
        .app_secret(app_secret)
        .domain(domain)
        .log_level(lark.LogLevel.WARNING)
        .build()
    )
    logger.info("Lark SDK Client 已初始化 (domain=%s)", domain)
    return _client_singleton


# ---------------------------------------------------------------------------
# 发送消息
# ---------------------------------------------------------------------------

def _do_send(receive_id: str, receive_id_type: str, msg_type: str, content: str) -> bool:
    """统一的消息发送实现。失败仅记录日志，不抛异常。"""
    try:
        client = get_client()
        body = (
            CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type(msg_type)
            .content(content)
            .build()
        )
        req = (
            CreateMessageRequest.builder()
            .receive_id_type(receive_id_type)
            .request_body(body)
            .build()
        )
        resp = client.im.v1.message.create(req)
        if not resp.success():
            logger.error(
                "发送消息失败: code=%s msg=%s receive_id=%s",
                resp.code, resp.msg, receive_id,
            )
            return False
        return True
    except Exception as e:
        logger.error("发送消息异常: %s", e)
        return False


def send_text(receive_id: str, text: str, receive_id_type: str = "chat_id") -> bool:
    """发送纯文本消息。"""
    content = json.dumps({"text": text}, ensure_ascii=False)
    return _do_send(receive_id, receive_id_type, "text", content)


def send_card(receive_id: str, card: Dict, receive_id_type: str = "chat_id") -> bool:
    """
    发送交互式卡片。`card` 为飞书卡片 JSON dict（参考飞书卡片搭建工具）。
    receive_id_type 可为 chat_id / open_id / user_id 等。
    """
    content = json.dumps(card, ensure_ascii=False)
    return _do_send(receive_id, receive_id_type, "interactive", content)


# ---------------------------------------------------------------------------
# 群消息历史（用于「群里 @ 机器人时阅读上下文」）
# ---------------------------------------------------------------------------

def list_recent_messages(chat_id: str, page_size: int = 20) -> List[Dict]:
    """
    拉取指定群的最近若干条消息，按时间倒序后再翻转为顺序。

    返回的字段：message_id / sender_id / sender_name / text / create_time。
    遇到非文本消息（图片/文件/卡片）时，text 字段会用占位符表示。
    """
    try:
        client = get_client()
        req = (
            ListMessageRequest.builder()
            .container_id_type("chat")
            .container_id(chat_id)
            .sort_type("ByCreateTimeDesc")
            .page_size(min(page_size, 50))
            .build()
        )
        resp = client.im.v1.message.list(req)
        if not resp.success() or resp.data is None:
            logger.warning(
                "拉取群消息失败: chat_id=%s code=%s msg=%s",
                chat_id, getattr(resp, "code", "?"), getattr(resp, "msg", "?"),
            )
            return []

        items = resp.data.items or []
        result: List[Dict] = []
        for item in items:
            text = _extract_text_from_message_item(item)
            sender = item.sender or None
            sender_id = ""
            if sender is not None and getattr(sender, "id", None):
                sender_id = sender.id or ""
            result.append({
                "message_id": item.message_id or "",
                "sender_id": sender_id,
                "sender_name": "",  # 群消息列表不返回姓名，按需另查
                "text": text,
                "create_time": item.create_time or "",
                "msg_type": item.msg_type or "",
            })

        result.reverse()
        return result
    except Exception as e:
        logger.error("拉取群消息异常: chat_id=%s err=%s", chat_id, e)
        return []


def _extract_text_from_message_item(item) -> str:
    """从 SDK 返回的 Message 对象中尽力提取文本。"""
    msg_type = item.msg_type or ""
    body = item.body
    raw_content = ""
    if body is not None:
        raw_content = body.content or ""
    if not raw_content:
        return f"[{msg_type or 'unknown'}]"
    try:
        obj = json.loads(raw_content)
    except json.JSONDecodeError:
        return raw_content[:500]

    if msg_type == "text":
        return obj.get("text", "")[:1000]
    if msg_type == "post":
        title = obj.get("title", "")
        segments: List[str] = []
        for paragraph in obj.get("content", []) or []:
            for seg in paragraph or []:
                if isinstance(seg, dict) and seg.get("tag") == "text":
                    segments.append(seg.get("text", ""))
        return (title + "\n" + " ".join(segments))[:1000]
    if msg_type in ("image", "file", "audio", "video", "sticker", "media"):
        return f"[{msg_type}]"
    return f"[{msg_type}] {raw_content[:200]}"


# ---------------------------------------------------------------------------
# 机器人自身信息
# ---------------------------------------------------------------------------

def get_bot_open_id() -> str:
    """
    获取机器人自身的 open_id（带缓存）。
    通过 SDK 的 application API 取不到 bot.open_id 时回退到 /bot/v3/info HTTP 接口。
    """
    global _bot_open_id_cache
    if _bot_open_id_cache:
        return _bot_open_id_cache

    import requests as _requests

    domain_type = os.environ.get("LARK_DOMAIN_TYPE", "lark").lower()
    base = "https://open.feishu.cn" if domain_type == "feishu" else "https://open.larksuite.com"
    app_id = os.environ.get("LARK_APP_ID", "")
    app_secret = os.environ.get("LARK_APP_SECRET", "")
    try:
        token_resp = _requests.post(
            f"{base}/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10,
        )
        token = token_resp.json().get("tenant_access_token", "")
        if not token:
            return ""
        bot_resp = _requests.get(
            f"{base}/open-apis/bot/v3/info",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        _bot_open_id_cache = bot_resp.json().get("bot", {}).get("open_id", "") or ""
    except Exception as e:
        logger.warning("获取机器人 open_id 失败: %s", e)
        _bot_open_id_cache = ""
    return _bot_open_id_cache or ""


def get_user_name(open_id: str) -> str:
    """
    通过 contact API 获取用户姓名。失败返回空字符串。
    """
    if not open_id:
        return ""
    try:
        from lark_oapi.api.contact.v3 import GetUserRequest

        client = get_client()
        req = (
            GetUserRequest.builder()
            .user_id(open_id)
            .user_id_type("open_id")
            .build()
        )
        resp = client.contact.v3.user.get(req)
        if resp.success() and resp.data and resp.data.user:
            return resp.data.user.name or ""
    except Exception as e:
        logger.debug("获取用户姓名失败: %s", e)
    return ""

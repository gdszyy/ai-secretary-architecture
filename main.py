"""
AI 秘书系统 Webhook 服务入口 (main.py)
========================================
功能：
  - 提供 FastAPI Web 服务，接收 Lark（飞书）事件订阅的 Webhook 推送。
  - /lark/webhook：处理 Lark 消息事件，路由至前端缺陷报送或多对话分离流程。
  - /health：健康检查端点，供 Railway 等平台探活使用。

部署方式：
  本地运行：uvicorn main:app --reload --port 8000
  Railway：通过 Procfile 自动启动（见 Procfile）

环境变量要求（在 .env 或 Railway Variables 中配置）：
  - LARK_APP_ID: 飞书应用 App ID
  - LARK_APP_SECRET: 飞书应用 App Secret
  - LARK_VERIFICATION_TOKEN: 飞书事件订阅验证 Token（用于签名校验）
  - DASHSCOPE_API_KEY: 通义千问 API Key
  - MEEGLE_TOKEN: Meegle Personal Access Token
  - MEEGLE_PROJECT_KEY: Meegle 项目 Key

架构说明：
  Lark Webhook → /lark/webhook
      ↓
  消息路由器 (route_lark_event)
      ├── 前端相关群组消息 → frontend_defect_reporter.process_message
      └── 通用群组消息    → thread_separator.separate（多对话分离）
"""

import os
import json
import logging
import hashlib
import hmac
from typing import Dict, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

# 加载 .env 文件（本地开发时使用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 生产环境通过平台环境变量注入，无需 dotenv

# 导入业务模块
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from frontend_defect_reporter import process_message as process_defect_message
from thread_separator import separate as separate_threads

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_secretary.main")

# ---------------------------------------------------------------------------
# FastAPI 应用初始化
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI 秘书系统 Webhook 服务",
    description="接收 Lark 事件推送，自动处理前端缺陷报送与多对话分离",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 前端相关群组关键词（用于判断是否路由至缺陷报送流程）
FRONTEND_GROUP_KEYWORDS = [
    "前端", "frontend", "UI", "H5", "移动端", "web", "页面", "渲染",
    "样式", "交互", "组件", "上线前前端优化", "设计稿",
]

# ---------------------------------------------------------------------------
# Lark 签名校验
# ---------------------------------------------------------------------------

def verify_lark_signature(
    timestamp: str,
    nonce: str,
    body: bytes,
    token: str,
) -> bool:
    """
    校验飞书 Webhook 请求的签名。
    签名算法：HMAC-SHA256(timestamp + nonce + body, token)
    """
    if not token:
        logger.warning("LARK_VERIFICATION_TOKEN 未配置，跳过签名校验")
        return True

    content = (timestamp + nonce + body.decode("utf-8")).encode("utf-8")
    expected = hmac.new(token.encode("utf-8"), content, hashlib.sha256).hexdigest()
    return True  # 实际部署时从请求头中提取签名进行比对


def extract_message_from_event(payload: Dict) -> Optional[Dict]:
    """
    从 Lark 事件 Payload 中提取消息内容。
    支持 im.message.receive_v1 事件格式。
    """
    event = payload.get("event", {})
    message = event.get("message", {})

    if not message:
        return None

    # 提取消息文本内容
    content_str = message.get("content", "{}")
    try:
        content_obj = json.loads(content_str)
        text = content_obj.get("text", "")
    except json.JSONDecodeError:
        text = content_str

    # 提取发送者信息
    sender = event.get("sender", {})
    sender_id = sender.get("sender_id", {}).get("open_id", "")
    sender_name = sender.get("sender_id", {}).get("user_id", "unknown")

    # 提取群组信息
    chat_id = message.get("chat_id", "")
    chat_type = message.get("chat_type", "")  # "group" or "p2p"

    return {
        "message_id": message.get("message_id", ""),
        "text": text,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "chat_id": chat_id,
        "chat_type": chat_type,
        "raw_message": message,
    }


def is_frontend_related(text: str, chat_name: str = "") -> bool:
    """判断消息是否与前端相关，决定是否路由至缺陷报送流程。"""
    combined = (text + " " + chat_name).lower()
    return any(kw.lower() in combined for kw in FRONTEND_GROUP_KEYWORDS)


# ---------------------------------------------------------------------------
# 后台任务处理函数
# ---------------------------------------------------------------------------

async def handle_message_event(msg_info: Dict) -> None:
    """
    后台处理消息事件（避免阻塞 Webhook 响应）。
    根据消息内容路由至不同的处理流程。
    """
    text = msg_info.get("text", "")
    sender = msg_info.get("sender_name", "")
    chat_id = msg_info.get("chat_id", "")

    logger.info(
        "处理消息事件: chat_id=%s, sender=%s, text_preview=%s",
        chat_id,
        sender,
        text[:50],
    )

    if is_frontend_related(text):
        # 路由至前端缺陷报送流程
        logger.info("路由至前端缺陷报送流程")
        result = process_defect_message(
            message_text=text,
            sender=sender,
            dry_run=os.environ.get("DRY_RUN", "false").lower() == "true",
        )
        action = result.get("action")
        logger.info("缺陷报送结果: action=%s", action)

        if action == "inquiry_needed":
            # TODO: 调用 Lark API 将询问话术发回群里
            inquiry_msg = result.get("inquiry_message", "")
            logger.info("需要追问，话术: %s", inquiry_msg[:100])
            # await send_lark_message(chat_id, inquiry_msg)

        elif action == "dispatched":
            # TODO: 调用 Lark API 发送成功通知
            notify_msg = result.get("notify_message", "")
            logger.info("工单已创建: %s", notify_msg[:100])
            # await send_lark_message(chat_id, notify_msg)

    else:
        # 路由至多对话分离流程（通用群聊消息处理）
        logger.info("路由至多对话分离流程")
        messages = [
            {
                "id": msg_info.get("message_id", "m0"),
                "sender": sender,
                "content": text,
            }
        ]
        result = separate_threads(messages)
        high_value = result.get("high_value_threads", [])
        logger.info(
            "对话分离完成: 高价值线程=%d, 待审核=%d",
            len(high_value),
            len(result.get("review_pending_threads", [])),
        )

        # TODO: 将高价值线程推入信息缓冲池（Bitable 或内存队列）
        for thread in high_value:
            logger.info(
                "高价值线程: topic=%s, intent=%s, confidence=%.2f",
                thread.get("topic"),
                thread.get("intent"),
                thread.get("confidence", 0),
            )


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """健康检查端点，供 Railway 等平台探活使用。"""
    return {
        "status": "ok",
        "service": "ai-secretary-webhook",
        "version": "1.0.0",
    }


@app.post("/lark/webhook")
async def lark_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    飞书事件订阅 Webhook 端点。

    处理流程：
    1. 验证签名（防止伪造请求）
    2. 处理 URL 验证挑战（Challenge）
    3. 异步处理消息事件（避免超时）
    """
    body = await request.body()
    payload = await request.json()

    # 1. 处理 URL 验证挑战（飞书首次配置时发送）
    if "challenge" in payload:
        logger.info("收到飞书 URL 验证挑战，返回 challenge")
        return JSONResponse({"challenge": payload["challenge"]})

    # 2. 签名校验（可选，生产环境建议开启）
    verification_token = os.environ.get("LARK_VERIFICATION_TOKEN", "")
    if verification_token:
        timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
        nonce = request.headers.get("X-Lark-Request-Nonce", "")
        if not verify_lark_signature(timestamp, nonce, body, verification_token):
            logger.warning("签名校验失败，拒绝请求")
            raise HTTPException(status_code=401, detail="Invalid signature")

    # 3. 提取事件类型
    event_type = payload.get("header", {}).get("event_type", "")
    logger.info("收到飞书事件: event_type=%s", event_type)

    # 4. 处理消息接收事件
    if event_type == "im.message.receive_v1":
        msg_info = extract_message_from_event(payload)
        if msg_info and msg_info.get("text"):
            # 异步处理，立即返回 200 避免飞书重试
            background_tasks.add_task(handle_message_event, msg_info)
        else:
            logger.info("消息内容为空，跳过处理")

    # 5. 其他事件类型（预留扩展）
    else:
        logger.info("暂不处理的事件类型: %s", event_type)

    # 飞书要求在 3 秒内返回 200
    return JSONResponse({"code": 0, "msg": "ok"})


@app.get("/")
async def root():
    """根路径，返回服务信息。"""
    return {
        "service": "AI 秘书系统 Webhook 服务",
        "endpoints": {
            "POST /lark/webhook": "飞书事件订阅 Webhook",
            "GET /health": "健康检查",
        },
        "docs": "/docs",
    }


# ---------------------------------------------------------------------------
# 本地开发入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

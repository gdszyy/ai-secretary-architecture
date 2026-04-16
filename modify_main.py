import os
import re

with open('/home/ubuntu/project-repo/main.py', 'r') as f:
    content = f.read()

# 1. 修改 verify_lark_signature
old_verify = """def verify_lark_signature(
    timestamp: str,
    nonce: str,
    body: bytes,
    token: str,
) -> bool:
    \"\"\"
    校验飞书 Webhook 请求的签名。
    签名算法：HMAC-SHA256(timestamp + nonce + body, token)
    \"\"\"
    if not token:
        logger.warning("LARK_VERIFICATION_TOKEN 未配置，跳过签名校验")
        return True

    content = (timestamp + nonce + body.decode("utf-8")).encode("utf-8")
    expected = hmac.new(token.encode("utf-8"), content, hashlib.sha256).hexdigest()
    return True  # 实际部署时从请求头中提取签名进行比对"""

new_verify = """def verify_lark_signature(
    timestamp: str,
    nonce: str,
    body: bytes,
    token: str,
    signature: str,
) -> bool:
    \"\"\"
    校验飞书 Webhook 请求的签名。
    签名算法：HMAC-SHA256(timestamp + nonce + body, token)
    \"\"\"
    if not token:
        logger.warning("LARK_VERIFICATION_TOKEN 未配置，跳过签名校验")
        return True

    content = (timestamp + nonce + body.decode("utf-8")).encode("utf-8")
    expected = hmac.new(token.encode("utf-8"), content, hashlib.sha256).hexdigest()
    
    if expected != signature:
        logger.warning(f"签名校验失败: expected={expected}, actual={signature}")
        return False
        
    return True"""

content = content.replace(old_verify, new_verify)

# 2. 修改 lark_webhook 里的签名校验调用
old_webhook_verify = """    verification_token = os.environ.get("LARK_VERIFICATION_TOKEN", "")
    if verification_token:
        timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
        nonce = request.headers.get("X-Lark-Request-Nonce", "")
        if not verify_lark_signature(timestamp, nonce, body, verification_token):"""

new_webhook_verify = """    verification_token = os.environ.get("LARK_VERIFICATION_TOKEN", "")
    if verification_token:
        timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
        nonce = request.headers.get("X-Lark-Request-Nonce", "")
        signature = request.headers.get("X-Lark-Signature", "")
        if not verify_lark_signature(timestamp, nonce, body, verification_token, signature):"""

content = content.replace(old_webhook_verify, new_webhook_verify)

# 3. 添加 send_lark_message 函数并更新 handle_message_event
imports_add = """import requests
import time
from typing import Dict, Optional"""

content = content.replace("from typing import Dict, Optional", imports_add)

send_message_code = """
# ---------------------------------------------------------------------------
# Lark API 客户端 (用于发送消息)
# ---------------------------------------------------------------------------

_lark_token_cache = {
    "token": None,
    "expires_at": 0
}

def get_lark_tenant_access_token() -> str:
    \"\"\"获取并缓存飞书 tenant_access_token\"\"\"
    now = time.time()
    if _lark_token_cache["token"] and now < _lark_token_cache["expires_at"]:
        return _lark_token_cache["token"]

    app_id = os.environ.get("LARK_APP_ID")
    app_secret = os.environ.get("LARK_APP_SECRET")
    
    if not app_id or not app_secret:
        logger.error("LARK_APP_ID 或 LARK_APP_SECRET 未配置")
        return ""

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    try:
        resp = requests.post(url, json={
            "app_id": app_id,
            "app_secret": app_secret
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("code") == 0:
            token = data.get("tenant_access_token")
            # 提前 5 分钟过期
            expires_in = data.get("expire", 7200) - 300
            _lark_token_cache["token"] = token
            _lark_token_cache["expires_at"] = now + expires_in
            return token
        else:
            logger.error("获取飞书 token 失败: %s", data.get("msg"))
            return ""
    except Exception as e:
        logger.error("获取飞书 token 异常: %s", str(e))
        return ""

async def send_lark_message(chat_id: str, text: str) -> bool:
    \"\"\"发送文本消息到飞书群\"\"\"
    token = get_lark_tenant_access_token()
    if not token:
        return False

    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }

    try:
        # 在异步函数中使用同步 requests 需要注意，这里为了简单直接使用，
        # 实际高并发场景建议使用 aiohttp 或 httpx
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 0:
            logger.info("成功发送飞书消息到群 %s", chat_id)
            return True
        else:
            logger.error("发送飞书消息失败: %s", data.get("msg"))
            return False
    except Exception as e:
        logger.error("发送飞书消息异常: %s", str(e))
        return False

# ---------------------------------------------------------------------------
# 后台任务处理函数
# ---------------------------------------------------------------------------"""

content = content.replace("# ---------------------------------------------------------------------------\n# 后台任务处理函数\n# ---------------------------------------------------------------------------", send_message_code)

old_handle_event = """        if action == "inquiry_needed":
            # TODO: 调用 Lark API 将询问话术发回群里
            inquiry_msg = result.get("inquiry_message", "")
            logger.info("需要追问，话术: %s", inquiry_msg[:100])
            # await send_lark_message(chat_id, inquiry_msg)

        elif action == "dispatched":
            # TODO: 调用 Lark API 发送成功通知
            notify_msg = result.get("notify_message", "")
            logger.info("工单已创建: %s", notify_msg[:100])
            # await send_lark_message(chat_id, notify_msg)"""

new_handle_event = """        if action == "inquiry_needed":
            inquiry_msg = result.get("inquiry_message", "")
            logger.info("需要追问，话术: %s", inquiry_msg[:100])
            await send_lark_message(chat_id, inquiry_msg)

        elif action == "dispatched":
            notify_msg = result.get("notify_message", "")
            logger.info("工单已创建: %s", notify_msg[:100])
            await send_lark_message(chat_id, notify_msg)"""

content = content.replace(old_handle_event, new_handle_event)

with open('/home/ubuntu/project-repo/main.py', 'w') as f:
    f.write(content)

print("修改完成")

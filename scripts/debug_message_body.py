#!/usr/bin/env python3
"""诊断：直接拉取单条消息的完整原始结构"""
import os, json, requests
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

APP_ID = os.environ.get("LARK_APP_ID")
APP_SECRET = os.environ.get("LARK_APP_SECRET")

def get_token():
    resp = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    return resp.json()["tenant_access_token"]

def get_message(token, msg_id):
    resp = requests.get(
        f"https://open.larksuite.com/open-apis/im/v1/messages/{msg_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return resp.json()

if __name__ == "__main__":
    token = get_token()
    # 用 Step2 中拿到的第一条 text 消息 ID
    msg_id = "om_x100b5a00a8c930a0ee5141755e01867"
    result = get_message(token, msg_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))

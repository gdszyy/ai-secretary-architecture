#!/usr/bin/env python3
"""
冷启动 Step 2：拉取每个群的历史消息（最近 200 条）
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

APP_ID = os.environ.get("LARK_APP_ID")
APP_SECRET = os.environ.get("LARK_APP_SECRET")

def get_token():
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]

def fetch_messages(token, chat_id, page_size=50):
    """拉取群聊历史消息"""
    url = "https://open.larksuite.com/open-apis/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "container_id_type": "chat",
        "container_id": chat_id,
        "page_size": page_size,
        "sort_type": "ByCreateTimeDesc"  # 最新消息优先
    }
    
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    
    if data.get("code") != 0:
        print(f"  ❌ 拉取失败 (code={data.get('code')}): {data.get('msg')}")
        return []
    
    items = data.get("data", {}).get("items", [])
    return items

def extract_text(msg_body: str) -> str:
    """从消息 body content 字符串中提取纯文本"""
    try:
        # content 本身是一个 JSON 字符串，如 '{"text":"hello"}'
        inner = json.loads(msg_body)
        text = inner.get("text", "")
        # 去除 HTML 标签（如 <p>、<at> 等）
        import re
        text = re.sub(r'<[^>]+>', '', text).strip()
        return text if text else msg_body
    except Exception:
        return msg_body

if __name__ == "__main__":
    print("=== Lark 冷启动 Step 2：拉取群聊历史消息 ===\n")
    
    groups_path = os.path.join(os.path.dirname(__file__), '..', 'cold_start_groups.json')
    with open(groups_path, 'r', encoding='utf-8') as f:
        groups = json.load(f)
    
    token = get_token()
    all_data = {}
    
    for g in groups:
        chat_id = g["chat_id"]
        name = g.get("name", chat_id)
        print(f"📥 正在拉取群「{name}」({chat_id})...")
        
        messages = fetch_messages(token, chat_id, page_size=50)
        
        if not messages:
            print(f"  ⚠️  无消息或权限不足，跳过。\n")
            continue
        
        # 整理为简洁格式
        simplified = []
        for m in reversed(messages):  # 时间正序
            sender = m.get("sender", {}).get("id", "unknown")
            msg_type = m.get("msg_type", "")
            create_time = m.get("create_time", "")
            body = m.get("body", {}).get("content", "")
            text = extract_text(body) if msg_type == "text" else f"[{msg_type}]"
            simplified.append({
                "sender": sender,
                "time": create_time,
                "type": msg_type,
                "text": text,
                "msg_id": m.get("message_id", "")
            })
        
        all_data[chat_id] = {
            "name": name,
            "message_count": len(simplified),
            "latest_message_id": messages[0].get("message_id", "") if messages else "",
            "messages": simplified
        }
        
        print(f"  ✅ 获取到 {len(simplified)} 条消息")
        if simplified:
            print(f"  最新一条: {simplified[-1]['text'][:60]}\n")
    
    out_path = os.path.join(os.path.dirname(__file__), '..', 'cold_start_messages.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"📄 消息数据已保存至 cold_start_messages.json")

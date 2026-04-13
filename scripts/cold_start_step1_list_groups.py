#!/usr/bin/env python3
"""
冷启动 Step 1：验证 Lark 凭证，获取机器人所在的所有群组列表
"""
import os
import json
import requests
from dotenv import load_dotenv

# 加载 .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

APP_ID = os.environ.get("LARK_APP_ID")
APP_SECRET = os.environ.get("LARK_APP_SECRET")

def get_token():
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Token 获取失败: {data}")
    print(f"✅ Token 获取成功: {data['tenant_access_token'][:12]}...")
    return data["tenant_access_token"]

def list_bot_groups(token):
    """获取机器人所在的群列表"""
    url = "https://open.larksuite.com/open-apis/im/v1/chats"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": 100}
    
    groups = []
    page_token = None
    
    while True:
        if page_token:
            params["page_token"] = page_token
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("code") != 0:
            print(f"❌ 获取群列表失败: {data}")
            break
            
        items = data.get("data", {}).get("items", [])
        groups.extend(items)
        
        if data.get("data", {}).get("has_more"):
            page_token = data["data"]["page_token"]
        else:
            break
    
    return groups

if __name__ == "__main__":
    print("=== Lark 冷启动 Step 1：获取机器人所在群列表 ===\n")
    token = get_token()
    groups = list_bot_groups(token)
    
    if not groups:
        print("⚠️  机器人当前不在任何群组中，或权限不足。")
    else:
        print(f"\n✅ 共找到 {len(groups)} 个群组：\n")
        for g in groups:
            print(f"  - [{g.get('chat_id')}] {g.get('name', '(无名称)')}  成员数: {g.get('member_count', '?')}")
        
        # 保存到文件供下一步使用
        out_path = os.path.join(os.path.dirname(__file__), '..', 'cold_start_groups.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(groups, f, ensure_ascii=False, indent=2)
        print(f"\n📄 群组列表已保存至 cold_start_groups.json")

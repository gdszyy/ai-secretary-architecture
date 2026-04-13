#!/usr/bin/env python3
"""
冷启动 Step 4：将群组画像写入 Bitable Cursor 表
若表不存在则先创建，再写入记录
"""
import os, json, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

APP_ID = os.environ.get("LARK_APP_ID")
APP_SECRET = os.environ.get("LARK_APP_SECRET")
BASE_ID = os.environ.get("BITABLE_BASE_ID")

def get_token():
    resp = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]

def list_tables(token):
    """列出 Bitable 中已有的表"""
    resp = requests.get(
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"列出表失败: {data}")
    return data.get("data", {}).get("items", [])

def create_table(token, table_name: str, fields: list) -> str:
    """创建新表，返回 table_id"""
    resp = requests.post(
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"table": {"name": table_name, "fields": fields}}
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"创建表失败: {data}")
    table_id = data["data"]["table_id"]
    print(f"  ✅ 表「{table_name}」创建成功，ID: {table_id}")
    return table_id

def get_or_create_cursor_table(token) -> str:
    """获取或创建 Cursor 表，返回 table_id"""
    tables = list_tables(token)
    for t in tables:
        if t.get("name") == "群组调度 Cursor":
            print(f"  ✅ 已找到 Cursor 表，ID: {t['table_id']}")
            return t["table_id"]
    
    print("  📋 Cursor 表不存在，正在创建...")
    # 字段类型参考：1=文本, 2=数字, 3=单选, 5=日期, 7=复选框
    fields = [
        {"field_name": "群组名称",       "type": 1},
        {"field_name": "chat_id",        "type": 1},
        {"field_name": "群组分类",        "type": 1},
        {"field_name": "活跃度",          "type": 1},
        {"field_name": "优先级评分",      "type": 2},
        {"field_name": "建议同步间隔(分钟)","type": 2},
        {"field_name": "一句话摘要",      "type": 1},
        {"field_name": "最后拉取消息ID",  "type": 1},
        {"field_name": "下次同步时间",    "type": 1},
        {"field_name": "冷启动次数",      "type": 2},
        {"field_name": "业务关联描述",    "type": 1},
    ]
    return create_table(token, "群组调度 Cursor", fields)

def create_record(token, table_id: str, fields: dict) -> str:
    """写入一条记录"""
    resp = requests.post(
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables/{table_id}/records",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"fields": fields}
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"写入记录失败: {data}")
    return data["data"]["record"]["record_id"]

if __name__ == "__main__":
    print("=== Lark 冷启动 Step 4：写入 Bitable Cursor 表 ===\n")
    
    profiles_path = os.path.join(os.path.dirname(__file__), '..', 'cold_start_profiles.json')
    with open(profiles_path, 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    token = get_token()
    print(f"✅ Token 获取成功\n")
    
    print("🔍 检查 Cursor 表...")
    table_id = get_or_create_cursor_table(token)
    
    # 更新 .env 中的 TABLE_CURSOR
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    with open(env_path, 'r') as f:
        env_content = f.read()
    if "BITABLE_TABLE_CURSOR=" in env_content:
        lines = env_content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("BITABLE_TABLE_CURSOR="):
                new_lines.append(f"BITABLE_TABLE_CURSOR={table_id}")
            else:
                new_lines.append(line)
        with open(env_path, 'w') as f:
            f.write("\n".join(new_lines) + "\n")
        print(f"  📝 已更新 .env BITABLE_TABLE_CURSOR={table_id}\n")
    
    print("📝 写入群组画像记录...\n")
    written_ids = {}
    
    for chat_id, profile in profiles.items():
        interval = profile.get("suggested_sync_interval_minutes", 60)
        next_sync = (datetime.now() + timedelta(minutes=interval)).strftime("%Y-%m-%d %H:%M:%S")
        
        fields = {
            "群组名称":         profile.get("group_name", ""),
            "chat_id":          chat_id,
            "群组分类":          profile.get("group_category", ""),
            "活跃度":            profile.get("activity_level", ""),
            "优先级评分":        profile.get("priority_score", 50),
            "建议同步间隔(分钟)": interval,
            "一句话摘要":        profile.get("summary", ""),
            "最后拉取消息ID":    profile.get("latest_message_id", ""),
            "下次同步时间":      next_sync,
            "冷启动次数":        profile.get("cold_start_count", 1),
            "业务关联描述":      profile.get("business_relevance", ""),
        }
        
        record_id = create_record(token, table_id, fields)
        written_ids[chat_id] = record_id
        print(f"  ✅ 群「{profile['group_name']}」→ record_id: {record_id}")
        print(f"     分类: {profile['group_category']}  优先级: {profile['priority_score']}  下次同步: {next_sync}")
    
    # 保存 record_id 映射供后续使用
    out_path = os.path.join(os.path.dirname(__file__), '..', 'cold_start_record_ids.json')
    with open(out_path, 'w') as f:
        json.dump({"table_id": table_id, "records": written_ids}, f, indent=2)
    
    print(f"\n🎉 冷启动完成！Cursor 表 ID: {table_id}")
    print(f"📄 record_id 映射已保存至 cold_start_record_ids.json")

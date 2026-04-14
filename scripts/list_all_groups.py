#!/usr/bin/env python3
"""
获取机器人当前所在的所有群组，并与 Bitable Cursor 表对比，识别新增群。
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

LARK_APP_ID = os.environ["LARK_APP_ID"]
LARK_APP_SECRET = os.environ["LARK_APP_SECRET"]
BITABLE_BASE_ID = os.environ["BITABLE_BASE_ID"]
BITABLE_TABLE_CURSOR = os.environ.get("BITABLE_TABLE_CURSOR", "")


def get_token():
    resp = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
    )
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]


def list_bot_groups(token):
    """获取机器人所在的所有群组（自动翻页）"""
    groups = []
    page_token = None
    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        resp = requests.get(
            "https://open.larksuite.com/open-apis/im/v1/chats",
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )
        data = resp.json()
        if data.get("code") != 0:
            print(f"[ERROR] 获取群列表失败: {data}")
            break
        items = data.get("data", {}).get("items", [])
        groups.extend(items)
        has_more = data.get("data", {}).get("has_more", False)
        page_token = data.get("data", {}).get("page_token")
        if not has_more:
            break
    return groups


def get_existing_group_ids(token):
    """从 Bitable Cursor 表获取已知群组的 chat_id"""
    if not BITABLE_TABLE_CURSOR:
        return set()
    resp = requests.get(
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BITABLE_BASE_ID}/tables/{BITABLE_TABLE_CURSOR}/records",
        headers={"Authorization": f"Bearer {token}"},
        params={"page_size": 500}
    )
    data = resp.json()
    if data.get("code") != 0:
        print(f"[WARN] 读取 Cursor 表失败: {data.get('msg')}")
        return set()
    records = data.get("data", {}).get("items", [])
    ids = set()
    for r in records:
        fields = r.get("fields", {})
        cid = fields.get("chat_id") or fields.get("群组ID") or fields.get("group_id")
        if cid:
            ids.add(str(cid).strip())
    return ids


if __name__ == "__main__":
    token = get_token()
    all_groups = list_bot_groups(token)
    existing_ids = get_existing_group_ids(token)

    print(f"\n=== 机器人当前所在群组（共 {len(all_groups)} 个）===\n")
    new_groups = []
    for g in all_groups:
        chat_id = g.get("chat_id", "")
        name = g.get("name", "(无名)")
        is_new = chat_id not in existing_ids
        tag = "🆕 新增" if is_new else "   已知"
        print(f"  {tag} | {name:<30} | {chat_id}")
        if is_new:
            new_groups.append(g)

    print(f"\n共识别到 {len(new_groups)} 个新增群组")

    # 保存结果供后续脚本使用
    out = {
        "all_groups": all_groups,
        "new_groups": new_groups,
        "existing_ids": list(existing_ids)
    }
    out_path = os.path.join(os.path.dirname(__file__), '..', 'group_list.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存至 group_list.json")

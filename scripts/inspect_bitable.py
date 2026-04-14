#!/usr/bin/env python3
"""快速检查 Bitable 功能表中各模块的功能名称和文档链接"""
import requests, json

APP_ID     = "cli_a9d985cd40f89e1a"
APP_SECRET = "UNemS0zPnUuXhONgkuuprgdK3SrVx05T"
BASE_ID    = "CyDxbUQGGa3N2NsVanMjqdjxp6e"
TABLE_FEATURE = "tblLzX7wqGWFr9KP"

def get_token():
    r = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    return r.json()["tenant_access_token"]

def list_records(token, table_id):
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    items, page_token = [], None
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        r = requests.get(url, headers=headers, params=params, timeout=15)
        data = r.json().get("data", {})
        items.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    return items

def extract_text(v):
    if not v: return ""
    if isinstance(v, str): return v.strip()
    if isinstance(v, list):
        parts = []
        for item in v:
            if isinstance(item, dict): parts.append(item.get("text",""))
            else: parts.append(str(item))
        return "".join(parts).strip()
    return str(v).strip()

def extract_url(v):
    if not v: return None
    if isinstance(v, dict): return v.get("link") or v.get("url")
    if isinstance(v, list):
        for item in v:
            if isinstance(item, dict):
                link = item.get("link") or item.get("url")
                if link: return link
    if isinstance(v, str) and v.startswith("http"): return v
    return None

token = get_token()
records = list_records(token, TABLE_FEATURE)

# Group by module
by_module = {}
for rec in records:
    f = rec["fields"]
    fname = extract_text(f.get("功能名称",""))
    url   = extract_url(f.get("文档链接"))
    mod_raw = f.get("所属模块","")
    mod_name = ""
    if isinstance(mod_raw, list) and mod_raw:
        first = mod_raw[0]
        mod_name = (first.get("text") or "") if isinstance(first, dict) else extract_text(first)
    elif isinstance(mod_raw, str):
        mod_name = mod_raw.strip()

    if mod_name not in by_module:
        by_module[mod_name] = []
    by_module[mod_name].append({"name": fname, "url": url})

TARGET_MODULES = {"用户系统","财务系统","体育注单系统","活动系统","礼券系统","代理系统","CRM系统","内容管理","首页推荐系统"}
for mod, feats in sorted(by_module.items()):
    if mod in TARGET_MODULES or not TARGET_MODULES:
        print(f"\n=== {mod} ({len(feats)} 条) ===")
        for feat in feats[:20]:
            url_short = feat['url'][:60] if feat['url'] else "无链接"
            print(f"  [{feat['name']}] → {url_short}")

#!/usr/bin/env python3
"""
sync_bitable_docs.py
从飞书 Bitable「XPBET 全球站功能地图 v2」提取功能点文档链接，
按模块名称匹配，更新 dashboard_data.json 中各 module 的 module_docs 和 features[].docs 字段。
"""
import json
import requests
from pathlib import Path

APP_ID        = "cli_a9d985cd40f89e1a"
APP_SECRET    = "UNemS0zPnUuXhONgkuuprgdK3SrVx05T"
BASE_ID       = "CyDxbUQGGa3N2NsVanMjqdjxp6e"
TABLE_FEATURE = "tblLzX7wqGWFr9KP"
DASHBOARD_JSON = Path(__file__).parent.parent / "data" / "dashboard_data.json"

# Bitable 模块名 → dashboard_data.json module id
MODULE_NAME_MAP = {
    "用户系统":    "mod_user_system",
    "财务系统":    "mod_wallet_finance",
    "体育注单系统": "mod_sports_betting_core",
    "活动系统":    "mod_activity_platform",
    "礼券系统":    "mod_activity_platform",   # 礼券归并到运营活动平台
    "代理系统":    "mod_platform_setting",
    "CRM系统":    "mod_platform_setting",
    "内容管理":    "mod_platform_setting",
    "首页推荐系统": "mod_sports_betting_core",
    "数据接入层":   "mod_data_ingestion",
    "SR→TS 匹配引擎": "mod_sr_ts_matching",
    "LS→TS 匹配引擎": "mod_ls_ts_matching",
    # Casino管理 → 游戏模块
    "Casino管理":  "mod_casino",
    # 客服系统 → 站内信与客服
    "客服系统":    "mod_im_cs",
    # 投放中心 → 投放系统
    "投放中心":    "mod_ads_system",
    "投放系统":    "mod_ads_system",
}

def get_token():
    r = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    r.raise_for_status()
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
        r.raise_for_status()
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
            if isinstance(item, dict): parts.append(item.get("text") or "")
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

def get_module_name(field_value):
    """从关联字段中提取模块名称文本"""
    if not field_value: return ""
    if isinstance(field_value, list) and field_value:
        first = field_value[0]
        if isinstance(first, dict):
            return (first.get("text") or "").strip()
        return extract_text(first)
    if isinstance(field_value, str):
        return field_value.strip()
    return ""

def main():
    print("=== 同步 Bitable 文档链接到 dashboard_data.json ===\n")
    token = get_token()
    print(f"Token 获取成功: {token[:12]}...")

    print("\n拉取功能表...")
    feature_records = list_records(token, TABLE_FEATURE)
    print(f"  共 {len(feature_records)} 条功能记录")

    # 构建 {module_id: [{name, url}]} 映射
    module_docs: dict[str, list[dict]] = {mid: [] for mid in MODULE_NAME_MAP.values()}
    matched = 0
    unmatched = set()

    for rec in feature_records:
        fields = rec.get("fields", {})
        feature_name = extract_text(fields.get("功能名称", ""))
        doc_url = extract_url(fields.get("文档链接"))
        module_name = get_module_name(fields.get("所属模块", ""))

        if not feature_name:
            continue

        module_id = MODULE_NAME_MAP.get(module_name)
        if module_id:
            module_docs[module_id].append({
                "title": feature_name,
                "url": doc_url or "#",
            })
            matched += 1
        else:
            if module_name:
                unmatched.add(module_name)

    print(f"  成功匹配 {matched} 条功能记录")
    if unmatched:
        print(f"  未映射模块（可补充到 MODULE_NAME_MAP）: {sorted(unmatched)}")

    # 读取 dashboard_data.json
    with open(DASHBOARD_JSON, "r", encoding="utf-8") as f:
        dashboard = json.load(f)

    # 注入文档链接
    updated_modules = 0
    for module in dashboard.get("modules", []):
        mid = module["id"]
        docs = module_docs.get(mid, [])
        if not docs:
            continue

        # 1. 模块级：挂载所有功能文档（有链接的优先）
        module["module_docs"] = [d for d in docs if d["url"] != "#"] or docs

        # 2. feature 级：按名称精确/模糊匹配
        for feature in module.get("features", []):
            fname = feature.get("name", "")
            # 精确匹配
            exact = [d for d in docs if d["title"] == fname]
            if exact:
                feature["docs"] = [{"title": d["title"], "url": d["url"]} for d in exact]
                continue
            # 模糊匹配（包含关系）
            fuzzy = [d for d in docs if fname in d["title"] or d["title"] in fname]
            if fuzzy:
                feature["docs"] = [{"title": d["title"], "url": d["url"]} for d in fuzzy]

        updated_modules += 1

    print(f"\n更新了 {updated_modules} 个模块的文档链接")

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    print(f"✅ 已写入: {DASHBOARD_JSON}")

    print("\n=== 各模块文档覆盖摘要 ===")
    for module in dashboard.get("modules", []):
        total = len(module.get("features", []))
        with_docs = sum(1 for f in module.get("features", []) if f.get("docs"))
        module_level = len(module.get("module_docs", []))
        print(f"  {module['name']:22s}  feature文档: {with_docs}/{total}  模块级文档: {module_level}")

if __name__ == "__main__":
    main()

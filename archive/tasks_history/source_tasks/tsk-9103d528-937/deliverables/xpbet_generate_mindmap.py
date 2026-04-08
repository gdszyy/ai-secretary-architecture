#!/usr/bin/env python3
"""
XPBET 飞书多维表格数据提取与 MindMap JSON 生成脚本 v2.0
修复了关联字段和人员字段的解析逻辑
"""
import requests
import json
from datetime import datetime

# --- 配置参数 ---
APP_ID = "cli_a9d985cd40f89e1a"
APP_SECRET = "UNemS0zPnUuXhONgkuuprgdK3SrVx05T"
BASE_ID = "CyDxbUQGGa3N2NsVanMjqdjxp6e"
MODULE_TABLE_ID = "tblaDW4D2hQS2xCw"
FEATURE_TABLE_ID = "tblLzX7wqGWFr9KP"

# --- 颜色映射规范 ---
STATUS_COLOR_MAP = {
    '完成': '#52C41A',
    '测试中': '#13C2C2',
    '开发中': '#1890FF',
    '待技术评审': '#722ED1',
    '待需求评审': '#EB2F96',
    '规划中': '#FAAD14',
    '待规划': '#D9D9D9',
}

PRIORITY_COLOR_MAP = {
    'P0': '#F5222D',
    'P1': '#FA8C16',
    'P2': '#1890FF',
    'P3': '#8C8C8C',
}

CATEGORY_COLOR_MAP = {
    'T0基础框架': {'fill': '#E6F7FF', 'stroke': '#91D5FF'},
    'T1营销框架-获客': {'fill': '#F6FFED', 'stroke': '#B7EB8F'},
    'T1营销框架-运营': {'fill': '#FFFBE6', 'stroke': '#FFE58F'},
    'T1营销框架-数据分析': {'fill': '#FFF7E6', 'stroke': '#FFD591'},
    'T2商户管理': {'fill': '#F9F0FF', 'stroke': '#D3ADF7'},
}

CATEGORY_ORDER = [
    'T0基础框架',
    'T1营销框架-获客',
    'T1营销框架-运营',
    'T1营销框架-数据分析',
    'T2商户管理',
]

def get_token():
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("tenant_access_token")

def list_all_records(token, table_id):
    """分页获取所有记录"""
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    all_records = []
    page_token = None
    
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get("data", {})
        records = data.get("items", [])
        all_records.extend(records)
        
        if not data.get("has_more", False):
            break
        page_token = data.get("page_token")
    
    return all_records

# ============ 字段提取函数（基于实际数据格式）============

def extract_text(field_value):
    """提取文本字段值（支持字符串和富文本数组格式）"""
    if field_value is None:
        return ""
    if isinstance(field_value, str):
        return field_value.strip()
    if isinstance(field_value, list):
        parts = []
        for item in field_value:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts).strip()
    return str(field_value).strip()

def extract_single_select(field_value):
    """提取单选字段值（直接是字符串格式）"""
    if field_value is None:
        return ""
    if isinstance(field_value, str):
        return field_value.strip()
    if isinstance(field_value, dict):
        return field_value.get("value", "").strip()
    return str(field_value).strip()

def extract_person(field_value):
    """
    提取人员字段值
    格式1（模块表）: [{"name": "xxx", ...}]  — 数组格式
    格式2（功能表）: {"users": [{"name": "xxx", ...}]}  — 对象格式
    """
    if field_value is None:
        return ""
    
    persons = []
    
    # 格式2: {"users": [...]}
    if isinstance(field_value, dict) and "users" in field_value:
        for user in field_value.get("users", []):
            name = user.get("name") or user.get("enName") or user.get("en_name", "")
            if name:
                persons.append(name)
    # 格式1: [{"name": "xxx", ...}]
    elif isinstance(field_value, list):
        for person in field_value:
            if isinstance(person, dict):
                name = person.get("name") or person.get("en_name", "")
                if name:
                    persons.append(name)
    
    return ", ".join(persons)

def extract_link(field_value):
    """提取超链接字段值"""
    if field_value is None:
        return ""
    if isinstance(field_value, dict):
        return field_value.get("link", field_value.get("url", ""))
    return ""

def extract_link_text(field_value):
    """提取超链接显示文本"""
    if field_value is None:
        return ""
    if isinstance(field_value, dict):
        return field_value.get("text", "")
    return ""

def extract_linked_record_ids(field_value):
    """
    提取关联字段的记录ID列表
    格式: [{"record_ids": ["xxx", "yyy"], "table_id": "...", ...}]
    """
    if field_value is None:
        return []
    if isinstance(field_value, list):
        ids = []
        for item in field_value:
            if isinstance(item, dict):
                record_ids = item.get("record_ids", [])
                if record_ids:
                    ids.extend(record_ids)
        return ids
    return []

def get_node_style(status, priority):
    """根据状态和优先级生成节点样式"""
    fill = STATUS_COLOR_MAP.get(status, '#FFFFFF')
    stroke = '#D9D9D9'
    for prefix, color in PRIORITY_COLOR_MAP.items():
        if priority and priority.startswith(prefix):
            stroke = color
            break
    return {"fill": fill, "stroke": stroke, "lineWidth": 2}

def transform_to_mindmap(modules, features):
    """将飞书数据转换为 AntV G6 MindMap 格式"""
    
    print("\n  [Step 1] 解析功能记录...")
    feature_map = {}  # record_id -> feature_node
    for feat in features:
        record_id = feat.get("record_id", "")
        fields = feat.get("fields", {})
        
        status = extract_single_select(fields.get("状态"))
        priority = extract_single_select(fields.get("功能优先级"))
        name = extract_text(fields.get("功能名称"))
        description = extract_text(fields.get("功能说明"))
        stage = extract_single_select(fields.get("阶段"))
        iteration = extract_single_select(fields.get("迭代版本"))
        owner = extract_person(fields.get("负责人"))
        doc_link = extract_link(fields.get("文档链接"))
        doc_text = extract_link_text(fields.get("文档链接"))
        simplified = extract_text(fields.get("简化方案"))
        prereq = extract_text(fields.get("前置资源"))
        
        # 关键：从关联字段提取所属模块的record_id
        module_ids = extract_linked_record_ids(fields.get("所属模块"))
        
        feature_node = {
            "id": f"feat_{record_id}",
            "label": name or f"功能_{record_id[:8]}",
            "type": "feature",
            "style": get_node_style(status, priority),
            "data": {
                "status": status,
                "priority": priority,
                "stage": stage,
                "iteration": iteration,
                "owner": owner,
                "description": description,
                "docLink": doc_link,
                "docText": doc_text,
                "simplifiedPlan": simplified,
                "prerequisites": prereq,
            },
            "_moduleIds": module_ids,
        }
        feature_map[record_id] = feature_node
    
    print(f"     解析了 {len(feature_map)} 个功能节点")
    
    print("\n  [Step 2] 解析模块记录并按分类分组...")
    categories = {}  # category_name -> category_node
    module_map = {}  # record_id -> module_node
    
    for mod in modules:
        record_id = mod.get("record_id", "")
        fields = mod.get("fields", {})
        
        name = extract_text(fields.get("模块名称"))
        category = extract_single_select(fields.get("分类"))
        priority = extract_single_select(fields.get("优先级"))
        status = extract_single_select(fields.get("状态"))
        description = extract_text(fields.get("模块说明"))
        owner = extract_person(fields.get("负责人"))
        
        module_node = {
            "id": f"mod_{record_id}",
            "label": name or f"模块_{record_id[:8]}",
            "type": "module",
            "style": get_node_style(status, priority),
            "data": {
                "status": status,
                "priority": priority,
                "owner": owner,
                "description": description,
                "category": category,
            },
            "children": [],
        }
        module_map[record_id] = module_node
        
        # 按分类分组
        if category not in categories:
            cat_style = CATEGORY_COLOR_MAP.get(category, {'fill': '#F5F5F5', 'stroke': '#D9D9D9'})
            categories[category] = {
                "id": f"cat_{category}",
                "label": category,
                "type": "category",
                "style": {**cat_style, "lineWidth": 1},
                "data": {"category": category},
                "children": [],
            }
        categories[category]["children"].append(module_node)
    
    print(f"     解析了 {len(module_map)} 个模块节点，{len(categories)} 个分类")
    
    print("\n  [Step 3] 将功能节点挂载到对应模块...")
    assigned_count = 0
    unassigned_features = []
    
    for feat_record_id, feat_node in feature_map.items():
        module_ids = feat_node.pop("_moduleIds", [])
        
        assigned = False
        for mod_id in module_ids:
            if mod_id in module_map:
                module_map[mod_id]["children"].append(feat_node)
                assigned_count += 1
                assigned = True
                break
        
        if not assigned:
            unassigned_features.append(feat_node)
    
    print(f"     成功挂载 {assigned_count} 个功能，{len(unassigned_features)} 个未分配")
    
    print("\n  [Step 4] 按预定顺序排列分类节点...")
    ordered_categories = []
    for cat_name in CATEGORY_ORDER:
        if cat_name in categories:
            ordered_categories.append(categories[cat_name])
    for cat_name, cat_node in categories.items():
        if cat_name not in CATEGORY_ORDER:
            ordered_categories.append(cat_node)
    
    # 统计总功能数
    total_features = sum(
        len(mod["children"])
        for cat in ordered_categories
        for mod in cat["children"]
    )
    
    print("\n  [Step 5] 组装根节点...")
    root = {
        "id": "root",
        "label": "XPBET 全球站",
        "type": "root",
        "style": {
            "fill": "#001529",
            "stroke": "#001529",
            "lineWidth": 0,
        },
        "_meta": {
            "version": "1.1.0",
            "syncedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "categoryCount": len(ordered_categories),
            "moduleCount": len(module_map),
            "featureCount": total_features,
            "unassignedFeatures": len(unassigned_features),
            "source": "feishu-bitable",
            "baseId": BASE_ID,
            "moduleTableId": MODULE_TABLE_ID,
            "featureTableId": FEATURE_TABLE_ID,
        },
        "children": ordered_categories,
    }
    
    return root, unassigned_features

def print_statistics(mindmap_data):
    """打印统计信息"""
    meta = mindmap_data["_meta"]
    print("\n" + "="*60)
    print("=== XPBET 功能地图数据统计 ===")
    print("="*60)
    print(f"分类数: {meta['categoryCount']}")
    print(f"模块数: {meta['moduleCount']}")
    print(f"功能数: {meta['featureCount']}")
    print(f"未分配功能: {meta['unassignedFeatures']}")
    print(f"同步时间: {meta['syncedAt']}")
    
    print("\n--- 分类/模块/功能分布 ---")
    for cat in mindmap_data["children"]:
        cat_feat_count = sum(len(mod.get("children", [])) for mod in cat["children"])
        print(f"\n{cat['label']} ({len(cat['children'])} 模块 / {cat_feat_count} 功能):")
        for mod in cat["children"]:
            feat_count = len(mod.get("children", []))
            status = mod["data"].get("status", "")
            priority = mod["data"].get("priority", "")
            owner = mod["data"].get("owner", "")
            print(f"  ├─ {mod['label']:<15} {feat_count:>3} 功能 | {status:<6} | {priority:<8} | {owner}")

def main():
    print("=== XPBET 飞书多维表格数据提取 v2.0 ===")
    
    # 获取Token
    print("\n[1/5] 获取访问Token...")
    token = get_token()
    print(f"  ✅ Token: {token[:10]}...")
    
    # 读取模块表
    print("\n[2/5] 读取模块表...")
    modules = list_all_records(token, MODULE_TABLE_ID)
    print(f"  ✅ 读取到 {len(modules)} 个模块")
    
    # 读取功能表
    print("\n[3/5] 读取功能表...")
    features = list_all_records(token, FEATURE_TABLE_ID)
    print(f"  ✅ 读取到 {len(features)} 个功能点")
    
    # 保存原始数据
    print("\n[4/5] 保存原始数据...")
    raw_data = {
        "modules": modules,
        "features": features,
        "extractedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "baseId": BASE_ID,
        "moduleTableId": MODULE_TABLE_ID,
        "featureTableId": FEATURE_TABLE_ID,
    }
    with open("/home/ubuntu/xpbet_raw_data_v2.json", "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 原始数据已保存到: xpbet_raw_data_v2.json")
    
    # 转换为MindMap格式
    print("\n[5/5] 转换为 AntV G6 MindMap 格式...")
    mindmap_data, unassigned = transform_to_mindmap(modules, features)
    
    # 保存MindMap JSON
    with open("/home/ubuntu/xpbet_mindmap_data_v2.json", "w", encoding="utf-8") as f:
        json.dump(mindmap_data, f, ensure_ascii=False, indent=2)
    print(f"\n  ✅ MindMap数据已保存到: xpbet_mindmap_data_v2.json")
    
    # 打印统计信息
    print_statistics(mindmap_data)
    
    return mindmap_data, unassigned

if __name__ == "__main__":
    main()

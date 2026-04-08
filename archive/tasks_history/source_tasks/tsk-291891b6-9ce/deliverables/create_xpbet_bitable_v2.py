#!/usr/bin/env python3
"""
XPBET 全球站功能地图 v2 - 飞书多维表格创建脚本
根据设计文档自动创建新版多维表格，包含模块表和功能表，并导入数据。

字段类型参考（Lark API）:
  1: Text
  3: Single select
  11: User (Person)
  15: URL (Hyperlink)
  18: Single link (单向关联)
  19: Lookup
  21: Duplex link (双向关联) ← 注意：不是18
"""

import requests
import json
import time
import sys

# --- 配置参数 ---
APP_ID = "cli_a9d985cd40f89e1a"
APP_SECRET = "UNemS0zPnUuXhONgkuuprgdK3SrVx05T"
BASE_URL = "https://open.larksuite.com/open-apis"

# 原始数据文件路径
RAW_DATA_PATH = "/home/ubuntu/project-repo/tasks/tsk-9103d528-937/deliverables/xpbet_raw_data_v2.json"

# --- API 工具函数 ---
def get_token():
    """获取飞书 tenant_access_token"""
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    token = response.json().get("tenant_access_token")
    if not token:
        raise Exception(f"获取Token失败: {response.json()}")
    return token

def api_request(method, path, token, data=None, params=None):
    """通用 API 请求函数"""
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method.upper() == "PATCH":
        response = requests.patch(url, headers=headers, json=data)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers)
    
    result = response.json()
    if result.get("code") != 0:
        raise Exception(f"API错误 [{method} {path}]: code={result.get('code')}, msg={result.get('msg')}, detail={json.dumps(result)[:300]}")
    return result.get("data", {})

# --- 步骤1：创建多维表格应用 ---
def create_bitable_app(token, name):
    """创建新的多维表格应用"""
    print(f"\n[步骤1] 创建多维表格应用: {name}")
    data = api_request("POST", "/bitable/v1/apps", token, data={"name": name})
    app_token = data["app"]["app_token"]
    print(f"  ✅ 创建成功! app_token: {app_token}")
    return app_token

# --- 步骤2：管理表格 ---
def list_tables(token, app_token):
    """列出所有表格"""
    data = api_request("GET", f"/bitable/v1/apps/{app_token}/tables", token)
    return data.get("items", [])

def create_table(token, app_token, name):
    """创建新表格"""
    data = api_request("POST", f"/bitable/v1/apps/{app_token}/tables", token, 
                       data={"table": {"name": name}})
    table_id = data["table_id"]
    print(f"  ✅ 创建表格 [{name}]: {table_id}")
    return table_id

def delete_table(token, app_token, table_id):
    """删除表格"""
    api_request("DELETE", f"/bitable/v1/apps/{app_token}/tables/{table_id}", token)
    print(f"  ✅ 删除表格: {table_id}")

# --- 步骤3：字段管理 ---
def list_fields(token, app_token, table_id):
    """列出表格的所有字段"""
    data = api_request("GET", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields", token)
    return data.get("items", [])

def create_field(token, app_token, table_id, field_config):
    """创建字段"""
    data = api_request("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields", 
                       token, data=field_config)
    field_id = data["field"]["field_id"]
    field_name = field_config.get("field_name", "")
    print(f"    ✅ 创建字段 [{field_name}]: {field_id}")
    return field_id

def update_field(token, app_token, table_id, field_id, field_config):
    """更新字段"""
    data = api_request("PUT", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}", 
                       token, data=field_config)
    field_name = field_config.get("field_name", "")
    print(f"    ✅ 更新字段 [{field_name}]: {field_id}")
    return data

# --- 配置模块表字段 ---
def setup_modules_table_fields(token, app_token, table_id):
    """配置模块表字段（不含双向关联，关联字段由功能表创建时自动生成）"""
    print(f"\n[步骤3] 配置模块表字段 (table_id: {table_id})")
    
    # 获取现有字段（默认有一个文本字段）
    existing_fields = list_fields(token, app_token, table_id)
    print(f"  现有字段数: {len(existing_fields)}")
    
    # 重命名第一个字段为"模块名称"
    if existing_fields:
        first_field_id = existing_fields[0]["field_id"]
        update_field(token, app_token, table_id, first_field_id, {
            "field_name": "模块名称",
            "type": 1  # 文本类型
        })
    
    # 创建"所属分类"字段（单选）
    create_field(token, app_token, table_id, {
        "field_name": "所属分类",
        "type": 3,  # 单选
        "property": {
            "options": [
                {"name": "T0基础框架"},
                {"name": "T1营销框架-获客"},
                {"name": "T1营销框架-运营"},
                {"name": "T1营销框架-数据分析"},
                {"name": "T2商户管理"}
            ]
        }
    })
    time.sleep(0.3)
    
    # 创建"模块状态"字段（单选）
    create_field(token, app_token, table_id, {
        "field_name": "模块状态",
        "type": 3,  # 单选
        "property": {
            "options": [
                {"name": "待规划"},
                {"name": "规划中"},
                {"name": "开发中"},
                {"name": "已上线"}
            ]
        }
    })
    time.sleep(0.3)
    
    # 创建"模块优先级"字段（单选）
    create_field(token, app_token, table_id, {
        "field_name": "模块优先级",
        "type": 3,  # 单选
        "property": {
            "options": [
                {"name": "P0-1月"},
                {"name": "P1-3月"},
                {"name": "P2-6月"}
            ]
        }
    })
    time.sleep(0.3)
    
    # 创建"模块说明"字段（文本）
    create_field(token, app_token, table_id, {
        "field_name": "模块说明",
        "type": 1  # 文本
    })
    time.sleep(0.3)
    
    print(f"  ✅ 模块表基础字段配置完成（包含功能字段将在功能表创建双向关联时自动生成）")

# --- 配置功能表字段 ---
def setup_features_table_fields(token, app_token, features_table_id, modules_table_id):
    """配置功能表字段（含双向关联）"""
    print(f"\n[步骤4] 配置功能表字段 (table_id: {features_table_id})")
    
    # 获取现有字段
    existing_fields = list_fields(token, app_token, features_table_id)
    print(f"  现有字段数: {len(existing_fields)}")
    
    # 重命名第一个字段为"功能名称"
    if existing_fields:
        first_field_id = existing_fields[0]["field_id"]
        update_field(token, app_token, features_table_id, first_field_id, {
            "field_name": "功能名称",
            "type": 1  # 文本类型
        })
    time.sleep(0.3)
    
    # 创建"所属模块"字段（双向关联，type=21）
    # 注意：type=21 是 DuplexLink（双向关联），type=18 是 SingleLink（单向关联）
    link_field_id = create_field(token, app_token, features_table_id, {
        "field_name": "所属模块",
        "type": 21,  # 双向关联 (DuplexLink)
        "property": {
            "table_id": modules_table_id,
            "back_field_name": "包含功能",  # 在模块表中自动创建的反向关联字段名
            "multiple": True
        }
    })
    time.sleep(0.5)  # 等待双向关联字段创建完成
    
    # 创建"功能状态"字段（单选）
    create_field(token, app_token, features_table_id, {
        "field_name": "功能状态",
        "type": 3,  # 单选
        "property": {
            "options": [
                {"name": "待规划"},
                {"name": "规划中"},
                {"name": "待需求评审"},
                {"name": "待技术评审"},
                {"name": "开发中"},
                {"name": "测试中"},
                {"name": "完成"}
            ]
        }
    })
    time.sleep(0.3)
    
    # 创建"功能优先级"字段（单选）
    create_field(token, app_token, features_table_id, {
        "field_name": "功能优先级",
        "type": 3,  # 单选
        "property": {
            "options": [
                {"name": "P0-核心"},
                {"name": "P1-重要"},
                {"name": "P2-一般"},
                {"name": "P3-次要"}
            ]
        }
    })
    time.sleep(0.3)
    
    # 创建"里程碑阶段"字段（单选）
    create_field(token, app_token, features_table_id, {
        "field_name": "里程碑阶段",
        "type": 3,  # 单选
        "property": {
            "options": [
                {"name": "1月SR验证"},
                {"name": "3月基础上线"},
                {"name": "6月后续迭代"},
                {"name": "6月迭代"}
            ]
        }
    })
    time.sleep(0.3)
    
    # 创建"迭代版本"字段（单选）
    create_field(token, app_token, features_table_id, {
        "field_name": "迭代版本",
        "type": 3,  # 单选
        "property": {
            "options": [
                {"name": "Sprint 0"},
                {"name": "Sprint 1 (1.22-2.14)"},
                {"name": "Sprint 2 (2.24-3.9)"},
                {"name": "Sprint 3 (3.10-3.23)"},
                {"name": "上线版本 V1.0"},
                {"name": "待规划"}
            ]
        }
    })
    time.sleep(0.3)
    
    # 创建"文档链接"字段（超链接，type=15）
    create_field(token, app_token, features_table_id, {
        "field_name": "文档链接",
        "type": 15  # URL/超链接
    })
    time.sleep(0.3)
    
    # 创建"功能说明"字段（文本）
    create_field(token, app_token, features_table_id, {
        "field_name": "功能说明",
        "type": 1  # 文本
    })
    time.sleep(0.3)
    
    # 创建"简化方案"字段（文本）
    create_field(token, app_token, features_table_id, {
        "field_name": "简化方案",
        "type": 1  # 文本
    })
    time.sleep(0.3)
    
    # 创建"前置资源"字段（文本）
    create_field(token, app_token, features_table_id, {
        "field_name": "前置资源",
        "type": 1  # 文本
    })
    time.sleep(0.3)
    
    print(f"  ✅ 功能表字段配置完成")
    return link_field_id

# --- 批量导入记录 ---
def batch_create_records(token, app_token, table_id, records, batch_size=100):
    """批量创建记录"""
    total = len(records)
    created = 0
    record_ids = []
    
    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        data = api_request("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                          token, data={"records": batch})
        batch_ids = [r["record_id"] for r in data.get("records", [])]
        record_ids.extend(batch_ids)
        created += len(batch_ids)
        print(f"    批次 {i//batch_size + 1}: 创建 {len(batch_ids)} 条记录")
        time.sleep(0.3)  # 避免频率限制
    
    print(f"  ✅ 共创建 {created}/{total} 条记录")
    return record_ids

# --- 导入模块数据 ---
def import_modules(token, app_token, modules_table_id, raw_modules):
    """导入模块数据"""
    print(f"\n[步骤5] 导入模块数据 ({len(raw_modules)} 个模块)")
    
    records = []
    
    for m in raw_modules:
        fields = m["fields"]
        module_name = fields.get("模块名称", "")
        
        record_fields = {
            "模块名称": module_name
        }
        
        # 所属分类（单选）
        category = fields.get("分类", "")
        if category:
            record_fields["所属分类"] = category
        
        # 模块状态（单选）
        status = fields.get("状态", "待规划")
        if status:
            record_fields["模块状态"] = status
        
        # 模块优先级（单选）
        priority = fields.get("优先级", "P2-6月")
        if priority:
            record_fields["模块优先级"] = priority
        
        # 模块说明（文本）
        desc = fields.get("模块说明", "")
        if desc:
            record_fields["模块说明"] = desc
        
        records.append({"fields": record_fields})
    
    # 批量创建
    new_record_ids = batch_create_records(token, app_token, modules_table_id, records)
    
    # 建立模块名称 -> 新 record_id 的映射
    module_name_to_new_id = {}
    old_to_new_id = {}
    for i, m in enumerate(raw_modules):
        if i < len(new_record_ids):
            module_name = m["fields"].get("模块名称", "")
            module_name_to_new_id[module_name] = new_record_ids[i]
            old_to_new_id[m["record_id"]] = new_record_ids[i]
    
    print(f"  模块名称->新ID映射: {len(module_name_to_new_id)} 个")
    return module_name_to_new_id, old_to_new_id

# --- 导入功能数据 ---
def import_features(token, app_token, features_table_id, raw_features):
    """导入功能数据（不含关联字段，关联在下一步建立）"""
    print(f"\n[步骤6] 导入功能数据 ({len(raw_features)} 个功能)")
    
    records = []
    feature_old_to_new = {}
    
    for f in raw_features:
        fields = f["fields"]
        
        # 构建基础字段
        record_fields = {
            "功能名称": fields.get("功能名称", "") or ""
        }
        
        # 功能状态（单选）
        status = fields.get("状态", "待规划")
        if status:
            record_fields["功能状态"] = status
        
        # 功能优先级（单选）
        priority = fields.get("功能优先级", "P2-一般")
        if priority:
            record_fields["功能优先级"] = priority
        
        # 里程碑阶段（单选）
        stage = fields.get("阶段", "")
        if stage:
            record_fields["里程碑阶段"] = stage
        
        # 迭代版本（单选）
        iteration = fields.get("迭代版本", "待规划")
        if iteration:
            record_fields["迭代版本"] = iteration
        
        # 文档链接（超链接）
        doc_link = fields.get("文档链接")
        if doc_link and isinstance(doc_link, dict):
            link_url = doc_link.get("link", "")
            link_text = doc_link.get("text", "")
            if link_url:
                record_fields["文档链接"] = {"link": link_url, "text": link_text or link_url}
        
        # 功能说明（文本）
        desc = fields.get("功能说明", "")
        if desc:
            record_fields["功能说明"] = desc
        
        # 简化方案（文本）
        simplified = fields.get("简化方案", "")
        if simplified:
            record_fields["简化方案"] = simplified
        
        # 前置资源（文本）
        prereq = fields.get("前置资源", "")
        if prereq:
            record_fields["前置资源"] = prereq
        
        records.append({"fields": record_fields})
    
    # 批量创建功能记录
    new_record_ids = batch_create_records(token, app_token, features_table_id, records)
    
    # 建立旧 record_id -> 新 record_id 的映射
    for i, f in enumerate(raw_features):
        if i < len(new_record_ids):
            feature_old_to_new[f["record_id"]] = new_record_ids[i]
    
    print(f"  功能旧->新ID映射: {len(feature_old_to_new)} 个")
    return feature_old_to_new, new_record_ids

# --- 建立功能-模块关联 ---
def update_feature_module_links(token, app_token, features_table_id, raw_features, 
                                  feature_old_to_new, module_name_to_new_id):
    """更新功能的所属模块关联"""
    print(f"\n[步骤7] 建立功能-模块关联关系")
    
    update_records = []
    skipped = 0
    
    for f in raw_features:
        old_feat_id = f["record_id"]
        new_feat_id = feature_old_to_new.get(old_feat_id)
        if not new_feat_id:
            skipped += 1
            continue
        
        # 获取所属模块名称
        module_links = f["fields"].get("所属模块", [])
        if not module_links:
            skipped += 1
            continue
        
        module_name = None
        for link in module_links:
            if isinstance(link, dict) and link.get("text_arr"):
                module_name = link["text_arr"][0] if link["text_arr"] else None
                break
        
        if not module_name:
            skipped += 1
            continue
        
        new_module_id = module_name_to_new_id.get(module_name)
        if not new_module_id:
            print(f"  ⚠️ 找不到模块: {module_name}")
            skipped += 1
            continue
        
        update_records.append({
            "record_id": new_feat_id,
            "fields": {
                "所属模块": [new_module_id]
            }
        })
    
    print(f"  需要更新关联的功能: {len(update_records)} 个, 跳过: {skipped} 个")
    
    # 批量更新
    batch_size = 100
    updated = 0
    for i in range(0, len(update_records), batch_size):
        batch = update_records[i:i+batch_size]
        data = api_request("POST", f"/bitable/v1/apps/{app_token}/tables/{features_table_id}/records/batch_update",
                          token, data={"records": batch})
        updated += len(data.get("records", []))
        print(f"    批次 {i//batch_size + 1}: 更新 {len(data.get('records', []))} 条关联")
        time.sleep(0.3)
    
    print(f"  ✅ 共更新 {updated} 条功能-模块关联")
    return updated

# --- 验证导入结果 ---
def verify_import(token, app_token, modules_table_id, features_table_id):
    """验证导入结果"""
    print(f"\n[步骤8] 验证导入结果")
    
    # 验证模块表
    module_data = api_request("GET", f"/bitable/v1/apps/{app_token}/tables/{modules_table_id}/records",
                              token, params={"page_size": 500})
    module_count = len(module_data.get("items", []))
    
    # 验证功能表
    feature_data = api_request("GET", f"/bitable/v1/apps/{app_token}/tables/{features_table_id}/records",
                               token, params={"page_size": 500})
    feature_count = len(feature_data.get("items", []))
    
    print(f"  模块表记录数: {module_count}")
    print(f"  功能表记录数: {feature_count}")
    
    # 验证关联
    linked_count = 0
    for item in feature_data.get("items", []):
        if item["fields"].get("所属模块"):
            linked_count += 1
    print(f"  已建立关联的功能数: {linked_count}")
    
    return module_count, feature_count, linked_count

# --- 主程序 ---
def main():
    print("=" * 60)
    print("XPBET 全球站功能地图 v2 - 飞书多维表格创建脚本")
    print("=" * 60)
    
    # 获取 Token
    print("\n[步骤0] 获取飞书 Token")
    token = get_token()
    print(f"  ✅ Token 获取成功: {token[:15]}...")
    
    # 读取原始数据
    print(f"\n[步骤0.5] 读取原始数据: {RAW_DATA_PATH}")
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    raw_modules = raw_data["modules"]
    raw_features = raw_data["features"]
    print(f"  ✅ 读取成功: {len(raw_modules)} 个模块, {len(raw_features)} 个功能")
    
    # 步骤1：创建多维表格应用
    app_token = create_bitable_app(token, "XPBET 全球站功能地图 v2")
    
    # 步骤2：获取默认表格并删除，然后创建模块表和功能表
    print(f"\n[步骤2] 管理表格结构")
    existing_tables = list_tables(token, app_token)
    print(f"  现有表格数: {len(existing_tables)}")
    
    # 创建模块表
    modules_table_id = create_table(token, app_token, "模块表")
    time.sleep(0.5)
    
    # 创建功能表
    features_table_id = create_table(token, app_token, "功能表")
    time.sleep(0.5)
    
    # 删除默认表格（如果有）
    for table in existing_tables:
        print(f"  删除默认表格: {table['name']} ({table['table_id']})")
        delete_table(token, app_token, table["table_id"])
        time.sleep(0.3)
    
    # 步骤3：配置模块表字段
    setup_modules_table_fields(token, app_token, modules_table_id)
    time.sleep(0.5)
    
    # 步骤4：配置功能表字段（含双向关联，会在模块表自动创建"包含功能"字段）
    setup_features_table_fields(token, app_token, features_table_id, modules_table_id)
    time.sleep(0.5)
    
    # 步骤5：导入模块数据
    module_name_to_new_id, old_module_to_new_id = import_modules(
        token, app_token, modules_table_id, raw_modules)
    time.sleep(0.5)
    
    # 步骤6：导入功能数据
    feature_old_to_new, new_feature_ids = import_features(
        token, app_token, features_table_id, raw_features)
    time.sleep(0.5)
    
    # 步骤7：建立功能-模块关联
    updated_links = update_feature_module_links(
        token, app_token, features_table_id, raw_features, 
        feature_old_to_new, module_name_to_new_id)
    time.sleep(0.5)
    
    # 步骤8：验证导入结果
    module_count, feature_count, linked_count = verify_import(
        token, app_token, modules_table_id, features_table_id)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("✅ 多维表格创建完成!")
    print("=" * 60)
    access_url = f"https://kjpp4yydjn38.jp.larksuite.com/base/{app_token}"
    print(f"  app_token: {app_token}")
    print(f"  模块表 table_id: {modules_table_id}")
    print(f"  功能表 table_id: {features_table_id}")
    print(f"  访问链接: {access_url}")
    print(f"  导入统计:")
    print(f"    - 模块: {module_count} 条")
    print(f"    - 功能: {feature_count} 条")
    print(f"    - 功能-模块关联: {linked_count} 条")
    
    # 保存结果到文件
    result = {
        "app_token": app_token,
        "modules_table_id": modules_table_id,
        "features_table_id": features_table_id,
        "access_url": access_url,
        "import_stats": {
            "modules": module_count,
            "features": feature_count,
            "feature_module_links": linked_count
        }
    }
    
    with open("/home/ubuntu/bitable_v2_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n  结果已保存到: /home/ubuntu/bitable_v2_result.json")
    
    return result

if __name__ == "__main__":
    result = main()

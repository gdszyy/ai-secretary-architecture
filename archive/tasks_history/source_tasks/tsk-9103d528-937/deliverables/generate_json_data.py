#!/usr/bin/env python3
"""
XPBET 飞书多维表格数据转换脚本
将原始数据转换为 AntV G6 MindMap 所需的树状 JSON 格式
"""
import json

# 状态颜色映射（节点背景色）
STATUS_COLOR_MAP = {
    '完成': '#52C41A',
    '测试中': '#13C2C2',
    '开发中': '#1890FF',
    '待技术评审': '#722ED1',
    '待需求评审': '#EB2F96',
    '规划中': '#FAAD14',
    '待规划': '#D9D9D9',
}

# 优先级颜色映射（节点边框色）
PRIORITY_COLOR_MAP = {
    'P0': '#F5222D',
    'P1': '#FA8C16',
    'P2': '#1890FF',
    'P3': '#8C8C8C',
}

# 分类颜色映射（分类节点背景色）
CATEGORY_COLOR_MAP = {
    'T0基础框架': {'fill': '#E6F7FF', 'stroke': '#91D5FF'},
    'T1营销框架-获客': {'fill': '#F6FFED', 'stroke': '#B7EB8F'},
    'T1营销框架-运营': {'fill': '#FFFBE6', 'stroke': '#FFE58F'},
    'T1营销框架-数据分析': {'fill': '#FFF7E6', 'stroke': '#FFD591'},
    'T2商户管理': {'fill': '#F9F0FF', 'stroke': '#D3ADF7'},
}

def get_status_color(status):
    return STATUS_COLOR_MAP.get(status, '#FFFFFF')

def get_priority_color(priority):
    if not priority:
        return '#D9D9D9'
    for key, color in PRIORITY_COLOR_MAP.items():
        if key in str(priority):
            return color
    return '#D9D9D9'

def get_owner_name(owner_data):
    if not owner_data or not isinstance(owner_data, dict):
        return ''
    users = owner_data.get('users', [])
    if users and len(users) > 0:
        return users[0].get('name', '')
    return ''

def get_doc_link(doc_data):
    if not doc_data or not isinstance(doc_data, dict):
        return ''
    return doc_data.get('link', '')

def main():
    with open('/home/ubuntu/xpbet_raw_data.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    modules = raw_data['模块表']['records']
    features = raw_data['功能表']['records']

    # 构建树状结构
    root = {
        "id": "root",
        "label": "XPBET 全球站",
        "type": "root",
        "_meta": {
            "version": "1.0.0",
            "syncedAt": "2026-03-26T04:00:00Z",
            "moduleCount": 21,
            "featureCount": 114,
            "source": "feishu-bitable",
            "baseId": "CyDxbUQGGa3N2NsVanMjqdjxp6e"
        },
        "children": []
    }

    # Step 1: 按分类分组模块，构建 category 节点
    categories = {}
    for mod in modules:
        fields = mod['fields']
        mod_name = fields.get('模块名称')
        if not mod_name:
            continue  # 跳过空记录
            
        cat_name = fields.get('分类', '未分类')
        if isinstance(cat_name, list):
            cat_name = cat_name[0] if cat_name else '未分类'

        if cat_name not in categories:
            cat_style = CATEGORY_COLOR_MAP.get(cat_name, {'fill': '#F5F5F5', 'stroke': '#D9D9D9'})
            categories[cat_name] = {
                "id": f"cat_{cat_name}",
                "label": cat_name,
                "type": "category",
                "style": {
                    "fill": cat_style['fill'],
                    "stroke": cat_style['stroke'],
                    "lineWidth": 1
                },
                "children": []
            }

        mod_node = {
            "id": f"mod_{mod['record_id']}",
            "label": mod_name,
            "type": "module",
            "style": {
                "fill": get_status_color(fields.get('状态')),
                "stroke": get_priority_color(fields.get('优先级')),
                "lineWidth": 2
            },
            "data": {
                "status": fields.get('状态', ''),
                "priority": fields.get('优先级', ''),
                "owner": get_owner_name(fields.get('负责人')),
                "description": fields.get('模块说明', '') or ''
            },
            "children": []
        }
        categories[cat_name]['children'].append(mod_node)

    # Step 2: 构建模块ID到节点的快速索引
    mod_map = {}
    for cat in categories.values():
        for mod in cat['children']:
            mod_map[mod['id']] = mod

    # Step 3: 将功能节点挂载到对应模块下
    unassigned_features = []
    for feat in features:
        fields = feat['fields']
        feat_name = fields.get('功能名称')
        if not feat_name:
            continue  # 跳过空记录

        # 查找所属模块
        mod_id = None
        if '所属模块' in fields and fields['所属模块']:
            for item in fields['所属模块']:
                if isinstance(item, dict) and item.get('record_ids'):
                    mod_id = f"mod_{item['record_ids'][0]}"
                    break

        feat_node = {
            "id": f"feat_{feat['record_id']}",
            "label": feat_name,
            "type": "feature",
            "style": {
                "fill": get_status_color(fields.get('状态')),
                "stroke": get_priority_color(fields.get('功能优先级')),
                "lineWidth": 2
            },
            "data": {
                "status": fields.get('状态', '') or '',
                "priority": fields.get('功能优先级', '') or '',
                "stage": fields.get('阶段', '') or '',
                "iteration": fields.get('迭代版本', '') or '',
                "owner": get_owner_name(fields.get('负责人')),
                "description": fields.get('功能说明', '') or '',
                "docLink": get_doc_link(fields.get('文档链接')),
                "simplifiedPlan": fields.get('简化方案', '') or '',
                "prerequisites": fields.get('前置资源', '') or ''
            }
        }

        if mod_id and mod_id in mod_map:
            mod_map[mod_id]['children'].append(feat_node)
        else:
            unassigned_features.append(feat_node)

    # Step 4: 组装最终的树
    root['children'] = list(categories.values())

    # 统计信息
    total_modules = sum(len(cat['children']) for cat in root['children'])
    total_features = sum(
        len(mod['children'])
        for cat in root['children']
        for mod in cat['children']
    )

    print(f"✅ 数据转换完成:")
    print(f"   分类数: {len(root['children'])}")
    print(f"   模块数: {total_modules}")
    print(f"   功能数: {total_features}")
    if unassigned_features:
        print(f"   ⚠️ 未分配模块的功能: {len(unassigned_features)} 条")
        for f in unassigned_features:
            print(f"      - {f['label']}")

    # 写入文件
    output_path = '/home/ubuntu/xpbet_mindmap_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(root, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON数据已保存到: {output_path}")

if __name__ == "__main__":
    main()

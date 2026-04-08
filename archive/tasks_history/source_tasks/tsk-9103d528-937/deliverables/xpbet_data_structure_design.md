# XPBET 全球站功能地图管理系统 — 数据结构设计方案

> **文档版本**: v1.0  
> **作者**: data_architect (Agent ID: agt-a53c1f76-fe6)  
> **日期**: 2026-03-26  
> **数据来源**: 飞书多维表格 BASE_ID=CyDxbUQGGa3N2NsVanMjqdjxp6e

---

## 1. 概述

本文档基于 XPBET 飞书多维表格的现有数据（21 个模块、114 个功能点），设计了一套适合前端可视化渲染（以 **AntV G6 MindMap** 为目标渲染引擎）的标准化数据结构方案。该方案将飞书多维表格中扁平的双表关联数据，转换为具有明确层级关系的树状 JSON 结构，并配套定义了状态、优先级的颜色映射规范，以支持功能地图的可视化展示。

---

## 2. 原始数据结构分析

### 2.1 模块表 (tblaDW4D2hQS2xCw)

模块表代表系统的顶层功能模块，共 21 条记录，包含以下 7 个字段：

| 字段名 | 飞书类型 | 类型代码 | 说明 |
| --- | --- | --- | --- |
| 模块名称 | 文本 | 1 | 模块的唯一标识名称，如：用户系统、财务系统 |
| 分类 | 单选 | 3 | 模块所属大类，见下方枚举值 |
| 优先级 | 单选 | 3 | 模块开发优先级，见下方枚举值 |
| 状态 | 单选 | 3 | 模块当前状态，见下方枚举值 |
| 负责人 | 人员 | 11 | 模块负责人，含用户 ID、姓名、邮箱 |
| 模块说明 | 文本 | 1 | 模块的功能描述 |
| 包含功能 | 关联 | 21 | 双向关联到功能表的多条记录 |

**模块表枚举值**：

| 字段 | 枚举值 |
| --- | --- |
| 分类 | T0基础框架、T1营销框架-获客、T1营销框架-运营、T1营销框架-数据分析、T2商户管理 |
| 优先级 | P0-1月、P1-3月、P2-6月 |
| 状态 | 开发中、规划中、待规划 |

### 2.2 功能表 (tblLzX7wqGWFr9KP)

功能表代表具体的业务功能点，共 114 条记录，包含以下 13 个字段：

| 字段名 | 飞书类型 | 类型代码 | 说明 |
| --- | --- | --- | --- |
| 功能名称 | 文本 | 1 | 功能的唯一名称 |
| 功能说明 | 文本 | 1 | 功能的详细描述 |
| 状态 | 单选 | 3 | 功能当前状态，见下方枚举值 |
| 功能优先级 | 单选 | 3 | 功能优先级，见下方枚举值 |
| 阶段 | 单选 | 3 | 功能所属里程碑阶段 |
| 迭代版本 | 单选 | 3 | 功能所属迭代 Sprint |
| 所属模块 | 关联 | 21 | 双向关联到模块表的单条记录 |
| 负责人 | 人员 | 20 | 功能负责人 |
| 文档链接 | 超链接 | 15 | 相关 PRD 或设计文档链接 |
| 分类 | 公式 | 20 | 从模块表继承的分类（计算字段） |
| 简化方案 | 文本 | 1 | 功能的简化实现方案 |
| 前置资源 | 文本 | 1 | 功能依赖的前置条件或资源 |
| Parent items | 关联 | 18 | 功能的父级关联（当前数据中均为空） |

**功能表枚举值**：

| 字段 | 枚举值 |
| --- | --- |
| 状态 | 完成、测试中、开发中、待技术评审、待需求评审、规划中、待规划 |
| 功能优先级 | P0-核心、P1-重要、P2-一般、P3-次要 |
| 阶段 | 1月SR验证、3月基础上线、6月后续迭代、6月迭代 |
| 迭代版本 | Sprint 0、Sprint 1 (1.22-2.14)、Sprint 2 (2.24-3.9)、Sprint 3 (3.10-3.23)、上线版本 V1.0、待规划 |

---

## 3. 标准化数据结构设计

### 3.1 层级关系设计 (ID/ParentID)

为支持 AntV G6 MindMap 的树状渲染，数据被组织为 **4 层嵌套结构**：

```
Root (根节点)
└── Level 1: 分类节点 (Category)
    └── Level 2: 模块节点 (Module)
        └── Level 3: 功能节点 (Feature)
```

**层级说明**：

| 层级 | 节点类型 | 数据来源 | 节点数量 |
| --- | --- | --- | --- |
| 根节点 | root | 固定值 "XPBET 全球站" | 1 |
| Level 1 | category | 模块表.分类字段的唯一值 | 5 |
| Level 2 | module | 模块表的每条记录 | 21 |
| Level 3 | feature | 功能表的每条记录 | 114 |

**ID 生成规则**：

| 节点类型 | ID 格式 | 示例 |
| --- | --- | --- |
| 根节点 | `root` | `root` |
| 分类节点 | `cat_{分类名称}` | `cat_T0基础框架` |
| 模块节点 | `mod_{飞书RecordID}` | `mod_recv7D8lYjnzJs` |
| 功能节点 | `feat_{飞书RecordID}` | `feat_recv7D8msMw1hD` |

使用飞书 RecordID 作为模块和功能节点的 ID 后缀，可保证 ID 的全局唯一性，并与飞书数据源保持直接映射关系，方便数据同步更新。

### 3.2 节点数据模型 (TypeScript 接口定义)

```typescript
/**
 * 思维导图节点数据模型
 * 适用于 AntV G6 MindMap 布局
 */
interface MindMapNode {
  /** 节点唯一ID，格式见 ID 生成规则 */
  id: string;

  /** 节点显示文本（模块名称或功能名称） */
  label: string;

  /** 节点类型，决定渲染样式和交互行为 */
  type: 'root' | 'category' | 'module' | 'feature';

  /** 节点样式（由颜色映射规范自动生成） */
  style?: {
    /** 节点背景色，根据状态映射 */
    fill?: string;
    /** 节点边框色，根据优先级映射 */
    stroke?: string;
    /** 边框宽度，默认 2 */
    lineWidth?: number;
  };

  /**
   * 业务数据
   * 用于 Tooltip 悬浮展示或右侧详情面板
   */
  data?: {
    /** 状态（中文枚举值） */
    status?: string;
    /** 优先级（中文枚举值） */
    priority?: string;
    /** 负责人姓名 */
    owner?: string;
    /** 模块说明或功能说明 */
    description?: string;
    /** 里程碑阶段（仅功能节点） */
    stage?: string;
    /** 迭代版本（仅功能节点） */
    iteration?: string;
    /** PRD/设计文档链接（仅功能节点） */
    docLink?: string;
  };

  /** 子节点列表（叶子节点为空数组或省略） */
  children?: MindMapNode[];
}
```

---

## 4. 颜色映射规范

颜色映射遵循 **Ant Design 设计体系**的色彩规范，确保与主流前端 UI 框架的视觉一致性。

### 4.1 状态颜色映射（节点背景色 Fill）

状态颜色反映功能的**当前进展**，从"未开始"到"已完成"形成直观的视觉渐进。

| 状态值 | 颜色值 (Hex) | 颜色名称 | 视觉含义 |
| --- | --- | --- | --- |
| 完成 | `#52C41A` | 绿色 (Green-6) | 已完成，可交付 |
| 测试中 | `#13C2C2` | 青色 (Cyan-6) | 研发完成，测试验证中 |
| 开发中 | `#1890FF` | 蓝色 (Blue-6) | 正在研发中 |
| 待技术评审 | `#722ED1` | 紫色 (Purple-6) | 需求已定，等待技术方案 |
| 待需求评审 | `#EB2F96` | 粉红色 (Pink-6) | 需求草案，等待评审 |
| 规划中 | `#FAAD14` | 黄色 (Gold-6) | 已列入计划，尚未开始 |
| 待规划 | `#D9D9D9` | 灰色 (Gray-5) | 暂无明确计划 |
| *无状态/默认* | `#FFFFFF` | 白色 | 默认状态 |

### 4.2 优先级颜色映射（节点边框色 Stroke）

优先级颜色反映功能的**重要程度**，用边框颜色区分，避免与背景色产生视觉冲突。

| 优先级值 | 颜色值 (Hex) | 颜色名称 | 视觉含义 |
| --- | --- | --- | --- |
| P0-核心 / P0-1月 | `#F5222D` | 红色 (Red-6) | 最高优先级，必须完成 |
| P1-重要 / P1-3月 | `#FA8C16` | 橙色 (Orange-6) | 高优先级，核心功能 |
| P2-一般 / P2-6月 | `#1890FF` | 蓝色 (Blue-6) | 中等优先级，常规功能 |
| P3-次要 | `#8C8C8C` | 灰色 (Gray-8) | 低优先级，可延后 |
| *无优先级/默认* | `#D9D9D9` | 浅灰色 (Gray-5) | 默认边框 |

### 4.3 分类颜色映射（分类节点背景色）

分类节点使用固定颜色，与模块/功能节点的动态颜色区分开来：

| 分类值 | 颜色值 (Hex) | 颜色名称 |
| --- | --- | --- |
| T0基础框架 | `#E6F7FF` | 浅蓝色 |
| T1营销框架-获客 | `#F6FFED` | 浅绿色 |
| T1营销框架-运营 | `#FFFBE6` | 浅黄色 |
| T1营销框架-数据分析 | `#FFF7E6` | 浅橙色 |
| T2商户管理 | `#F9F0FF` | 浅紫色 |

---

## 5. 前端 JSON 数据格式示例

以下是符合 AntV G6 MindMap 布局所需的标准 JSON 格式示例（截取"T0基础框架"分类下的"用户系统"模块及其部分功能）：

```json
{
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
  "children": [
    {
      "id": "cat_T0基础框架",
      "label": "T0基础框架",
      "type": "category",
      "style": {
        "fill": "#E6F7FF",
        "stroke": "#91D5FF",
        "lineWidth": 1
      },
      "children": [
        {
          "id": "mod_recv7D8lYjnzJs",
          "label": "用户系统",
          "type": "module",
          "style": {
            "fill": "#1890FF",
            "stroke": "#F5222D",
            "lineWidth": 2
          },
          "data": {
            "status": "开发中",
            "priority": "P0-1月",
            "owner": "",
            "description": "登录注册、KYC、用户信息编辑、用户自我封禁"
          },
          "children": [
            {
              "id": "feat_recv7D8msMw1hD",
              "label": "登录注册流程",
              "type": "feature",
              "style": {
                "fill": "#52C41A",
                "stroke": "#F5222D",
                "lineWidth": 2
              },
              "data": {
                "status": "完成",
                "priority": "P0-核心",
                "stage": "1月SR验证",
                "iteration": "上线版本 V1.0",
                "owner": "Yark",
                "description": "手机号+验证码、三方登录、referral",
                "docLink": "https://kjpp4yydjn38.jp.larksuite.com/docx/WLdFdU0emoh1K8xiYy9j4iPTpre"
              }
            },
            {
              "id": "feat_recv7D8msMNEvJ",
              "label": "KYC流程",
              "type": "feature",
              "style": {
                "fill": "#1890FF",
                "stroke": "#F5222D",
                "lineWidth": 2
              },
              "data": {
                "status": "开发中",
                "priority": "P0-核心",
                "stage": "1月SR验证",
                "iteration": "上线版本 V1.0",
                "owner": "Yark",
                "description": "KYC 前台流程",
                "docLink": "https://kjpp4yydjn38.jp.larksuite.com/docx/PgEgdGleco9TddxCgmcjPqUSpEg"
              }
            }
          ]
        },
        {
          "id": "mod_recv7D8lYjz8UW",
          "label": "财务系统",
          "type": "module",
          "style": {
            "fill": "#1890FF",
            "stroke": "#F5222D",
            "lineWidth": 2
          },
          "data": {
            "status": "开发中",
            "priority": "P0-1月",
            "owner": "",
            "description": "支付路由、代收代付、钱包管理"
          },
          "children": [
            {
              "id": "feat_recv7D8msMtUnE",
              "label": "支付路由",
              "type": "feature",
              "style": {
                "fill": "#52C41A",
                "stroke": "#F5222D",
                "lineWidth": 2
              },
              "data": {
                "status": "完成",
                "priority": "P0-核心",
                "stage": "1月SR验证",
                "iteration": "上线版本 V1.0",
                "owner": "Yark",
                "description": "开关/限额/路由规则配置",
                "docLink": "https://kjpp4yydjn38.jp.larksuite.com/wiki/RgYGwl1naiZUtSkRTkVjbdAVpgd"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 6. 数据转换流程

### 6.1 数据提取流程

```
飞书 API (Bitable v1)
    ├── GET /apps/{base_id}/tables/{module_table_id}/records  → 模块表 21 条
    └── GET /apps/{base_id}/tables/{feature_table_id}/records → 功能表 114 条
```

### 6.2 数据转换算法

```python
def transform_to_mindmap(modules, features):
    # Step 1: 按分类分组模块，构建 category 节点
    categories = {}
    for mod in modules:
        cat_name = mod.fields['分类']
        if cat_name not in categories:
            categories[cat_name] = CategoryNode(
                id=f"cat_{cat_name}",
                label=cat_name
            )
        mod_node = ModuleNode(
            id=f"mod_{mod.record_id}",
            label=mod.fields['模块名称'],
            style=get_module_style(mod.fields)
        )
        categories[cat_name].children.append(mod_node)

    # Step 2: 构建模块ID到节点的快速索引
    mod_index = {
        mod.id: mod
        for cat in categories.values()
        for mod in cat.children
    }

    # Step 3: 将功能节点挂载到对应模块下
    for feat in features:
        parent_mod_id = f"mod_{feat.fields['所属模块'][0].record_id}"
        feat_node = FeatureNode(
            id=f"feat_{feat.record_id}",
            label=feat.fields['功能名称'],
            style=get_feature_style(feat.fields)
        )
        mod_index[parent_mod_id].children.append(feat_node)

    # Step 4: 组装根节点
    return RootNode(
        id="root",
        label="XPBET 全球站",
        children=list(categories.values())
    )
```

### 6.3 样式生成规则

```python
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
    'P0': '#F5222D',  # P0-核心 / P0-1月
    'P1': '#FA8C16',  # P1-重要 / P1-3月
    'P2': '#1890FF',  # P2-一般 / P2-6月
    'P3': '#8C8C8C',  # P3-次要
}

def get_node_style(status, priority):
    fill = STATUS_COLOR_MAP.get(status, '#FFFFFF')
    stroke = next(
        (v for k, v in PRIORITY_COLOR_MAP.items() if priority and k in priority),
        '#D9D9D9'
    )
    return {"fill": fill, "stroke": stroke, "lineWidth": 2}
```

---

## 7. AntV G6 集成指南

### 7.1 推荐配置

```javascript
import G6 from '@antv/g6';

const graph = new G6.TreeGraph({
  container: 'mindmap-container',
  width: 1600,
  height: 900,
  layout: {
    type: 'mindmap',
    direction: 'H',        // 水平布局，根节点居中
    getHeight: () => 32,
    getWidth: (node) => node.label.length * 14 + 40,
    getVGap: () => 10,
    getHGap: () => 60,
  },
  defaultNode: {
    type: 'rect',
    style: {
      radius: 4,
      cursor: 'pointer',
    },
    labelCfg: {
      style: {
        fontSize: 12,
        fill: '#333',
      },
    },
  },
  defaultEdge: {
    type: 'cubic-horizontal',
    style: {
      stroke: '#A3B1BF',
    },
  },
  modes: {
    default: ['collapse-expand', 'drag-canvas', 'zoom-canvas'],
  },
});

// 加载数据（即本文档定义的 JSON 结构）
graph.data(mindmapData);
graph.render();
graph.fitView();
```

### 7.2 节点自定义渲染建议

为了在节点上展示状态标签和优先级标识，建议注册自定义节点类型，通过 `cfg.style.fill` 和 `cfg.style.stroke` 渲染背景色和边框色，并在 Tooltip 中展示 `cfg.data` 中的业务字段（状态、负责人、文档链接等）。

---

## 8. 数据同步策略

### 8.1 增量同步

建议通过飞书 Webhook 或定时轮询实现数据同步：

```
飞书多维表格变更 → Webhook 通知 → 后端更新 JSON 缓存 → 前端实时刷新
```

### 8.2 数据版本管理

每次全量同步时，在 JSON 根节点附加 `_meta` 元数据字段，记录同步时间、数据量和数据源信息，便于前端判断数据新鲜度和调试追踪。

---

## 9. 完整数据统计

### 9.1 模块分布

| 分类 | 模块数量 |
| --- | --- |
| T0基础框架 | 8 |
| T1营销框架-获客 | 4 |
| T1营销框架-运营 | 5 |
| T1营销框架-数据分析 | 1 |
| T2商户管理 | 3 |
| **合计** | **21** |

### 9.2 模块完整列表

| 模块名称 | 分类 | 优先级 | 状态 |
| --- | --- | --- | --- |
| 用户系统 | T0基础框架 | P0-1月 | 开发中 |
| 财务系统 | T0基础框架 | P0-1月 | 开发中 |
| 体育注单系统 | T0基础框架 | P1-3月 | 开发中 |
| 客服系统 | T0基础框架 | P1-3月 | 规划中 |
| 权限系统 | T0基础框架 | P1-3月 | 规划中 |
| 国别管理系统 | T0基础框架 | P1-3月 | 待规划 |
| 风控系统 | T0基础框架 | P2-6月 | 规划中 |
| Casino管理 | T0基础框架 | P2-6月 | 待规划 |
| 分享系统 | T1营销框架-获客 | P1-3月 | 待规划 |
| 投手后台 | T1营销框架-获客 | P1-3月 | 待规划 |
| 代理系统 | T1营销框架-获客 | P1-3月 | 待规划 |
| 落地页系统 | T1营销框架-获客 | P1-3月 | 待规划 |
| 活动系统 | T1营销框架-运营 | P1-3月 | 待规划 |
| 礼券系统 | T1营销框架-运营 | P1-3月 | 待规划 |
| CRM系统 | T1营销框架-运营 | P1-3月 | 待规划 |
| 首页推荐系统 | T1营销框架-运营 | P1-3月 | 待规划 |
| 内容管理 | T1营销框架-运营 | P1-3月 | 待规划 |
| 数据分析 | T1营销框架-数据分析 | P1-3月 | 待规划 |
| 商户管理 | T2商户管理 | P2-6月 | 待规划 |
| C端包网 | T2商户管理 | P2-6月 | 待规划 |
| 聊天室系统 | T2商户管理 | P2-6月 | 待规划 |

---

## 10. 交付物清单

| 文件名 | 描述 |
| --- | --- |
| `xpbet_data_structure_design.md` | 本文档，完整的数据结构设计方案 |
| `xpbet_mindmap_data.json` | 完整的前端 JSON 数据（AntV G6 格式，含全部 21 个模块和 114 个功能） |
| `xpbet_raw_data.json` | 飞书多维表格的原始数据（含字段定义和所有记录） |
| `generate_json_data.py` | 数据转换脚本（从原始数据生成 MindMap JSON） |

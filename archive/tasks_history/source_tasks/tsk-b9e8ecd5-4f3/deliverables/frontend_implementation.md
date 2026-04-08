# XPBET 功能地图 - 前端实现文档

## 概述

本文档描述 XPBET 全球站功能地图管理系统第一层前端可视化应用的实现情况。

**技术栈：** React 19 + TypeScript + AntV G6 v5 + Tailwind CSS 4  
**项目路径：** `/home/ubuntu/xpbet-function-map`  
**访问地址：** 通过 Manus webdev 平台访问（版本 ID: 9b594a6a）

---

## 已实现功能

### P0-核心功能（全部完成）

| 功能 | 状态 | 说明 |
|------|------|------|
| AntV G6 MindMap 布局渲染 | ✅ | 4层树状：根→分类→模块→功能，支持展开/收起 |
| 节点颜色状态映射 | ✅ | 完成=#52C41A、开发中=#1677FF、测试中=#FA8C16、规划中=#8C8C8C、待规划=#D9D9D9 |
| 画布缩放（滚轮） | ✅ | zoomRange: [0.1, 4] |
| 画布平移（拖拽） | ✅ | drag-canvas 行为 |
| Fit View 按钮 | ✅ | 右上角工具栏 |
| 节点展开/收起 | ✅ | 双击节点触发（避免与单击查看详情冲突） |
| **飞书 Bitable API 实时数据** | ✅ | **v2.0 新增：并发拉取模块表和功能表全量数据，自动处理分页** |

### P1-重要功能（全部完成）

| 功能 | 状态 | 说明 |
|------|------|------|
| 多维筛选控制面板 | ✅ | 状态/优先级/分类/阶段四维筛选 |
| 关键词搜索 | ✅ | 实时过滤功能名称 |
| 节点 Tooltip | ✅ | 鼠标悬停显示：状态/优先级/负责人/迭代版本/描述 |
| 文档链接跳转 | ✅ | 单击功能节点打开飞书文档 |
| 状态图例 | ✅ | 左下角可折叠图例 |
| 统计数据展示 | ✅ | 顶部统计栏：总数/状态分布进度条 |
| **加载与错误状态 UI** | ✅ | **v2.0 新增：全屏 Loading Spinner 和错误/降级警告面板** |
| **静态数据 Fallback** | ✅ | **v2.0 新增：API 失败时自动降级到本地静态 JSON 数据** |

### P2-增强功能（部分完成）

| 功能 | 状态 | 说明 |
|------|------|------|
| 节点详情侧边栏 | ✅ | 点击功能节点后右侧滑出详情面板 |
| 布局方向切换 | ✅ | 水平/垂直切换 |
| 控制面板收起 | ✅ | 点击 ‹ 按钮收起左侧面板 |
| 操作提示 | ✅ | 图例区域显示操作说明 |

---

## 核心架构

### 文件结构

```
client/src/
├── pages/
│   └── Home.tsx              # 主页面（集成 useBitableData，处理 Loading/Error 状态）
├── components/
│   ├── GraphCanvas/          # G6 画布核心组件
│   ├── NodeTooltip/          # 节点悬浮提示
│   ├── ControlPanel/         # 左侧筛选控制面板
│   ├── Legend/               # 状态图例
│   ├── StatsBar/             # 顶部统计栏
│   ├── LoadingSpinner/       # 全屏加载动画组件
│   └── ErrorPanel/           # 错误提示与降级警告组件
├── lib/
│   ├── dataTransformer.ts    # 数据转换（Bitable扁平数据→G6树形结构）、筛选、统计
│   └── useBitableData.ts     # 飞书 API 数据拉取 Hook（含缓存与降级逻辑）
├── services/
│   └── biTableService.ts     # 飞书 Bitable API 封装（Token获取、并发拉取）
├── types/
│   └── mindmap.ts            # TypeScript 类型定义、状态颜色常量
└── data/
    └── mindmap_data.json     # 静态数据源（作为 API 失败时的 Fallback）
```

### 关键技术决策

1. **数据获取策略**：使用 `Promise.all` 并发拉取模块表和功能表，减少约 50% 的网络等待时间。
2. **Token 缓存**：在内存中缓存 `tenant_access_token`，提前 60 秒过期，避免频繁请求飞书鉴权接口。
3. **降级机制 (Fallback)**：当飞书 API 请求失败或未配置凭证时，系统会自动捕获异常，并尝试加载本地的 `mindmap_data.json`，保证应用可用性。
4. **G6 v5 数据格式**：使用 `nodes + edges` 格式（非树形 JSON），通过 `NodeData.children` 字段存储子节点 ID 数组。
5. **节点尺寸**：G6 v5 使用 `size: [width, height]` 数组，而非 `width/height` 属性。
6. **布局参数**：`@antv/hierarchy` 的 `getWidth/getHeight` 函数接收 `{ id, data: {...} }` 格式，通过 `d.data.nodeType` 访问节点类型。

### 数据流

```
[飞书 Bitable API] 或 [mindmap_data.json]
    ↓ biTableService.ts (并发拉取)
扁平记录数组 { modules[], features[] }
    ↓ dataTransformer.ts -> transformToMindMap()
嵌套树形结构 MindMapRoot
    ↓ dataTransformer.ts -> filterMindMap()
过滤后的 MindMapRoot
    ↓ dataTransformer.ts -> transformToG6Data()
G6 GraphData { nodes[], edges[] }
    ↓ Graph.setData() + Graph.render()
G6 Canvas 渲染
```

---

## 环境变量配置

系统通过环境变量控制数据源模式和飞书 API 凭证。请在项目根目录创建 `.env` 文件：

```env
# ==================== 数据源模式 ====================

# 是否使用静态 JSON 数据（开发/演示模式）
# true  = 使用本地静态 JSON 文件（无需飞书 API 凭证）
# false = 从飞书 Bitable API 实时拉取（需要配置下方凭证）
VITE_USE_STATIC_DATA=false

# ==================== 飞书 API 配置 ====================
# 仅在 VITE_USE_STATIC_DATA=false 时需要配置

# 飞书应用 App ID（在飞书开放平台创建应用后获取）
# 应用需要开通权限：bitable:app:readonly
VITE_FEISHU_APP_ID=cli_a7xxxxxxxxx

# 飞书应用 App Secret（请妥善保管，不要提交到版本控制）
VITE_FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxx
```

> **提示**：项目中已提供 `.env.example` 和 `.env.static` 作为配置参考。

---

## 多维表格配置

以下 ID 已内置在 `biTableService.ts` 的 `BITABLE_CONFIG` 常量中，通常无需手动修改：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Base ID | `BgjjbdZiJanHTpsboAzj9Gv7p6b` | 来自 tsk-291891b6-9ce 新版多维表格搭建结果 |
| 模块表 ID | `tblb9Owa8P4AhVEH` | 21 个模块 |
| 功能表 ID | `tbluOwbl2PKxIiEz` | 114 个功能 |
| 访问链接 | [飞书多维表格](https://kjpp4yydjn38.jp.larksuite.com/base/BgjjbdZiJanHTpsboAzj9Gv7p6b) | 需要飞书账号权限 |

---

## 部署信息

- **框架**：React 19 + Vite 7 + TypeScript
- **构建命令**：`pnpm build`
- **开发服务器**：`pnpm dev`（端口 3000）

---

## 下一步建议

1. **节点编辑功能**：支持直接在图上修改节点状态、优先级等属性，并调用飞书 API 回写数据。
2. **增量更新**：当前为全量拉取，当数据量极大时，可考虑基于 `last_modified_time` 的增量同步策略。
3. **导出功能**：支持导出为 PNG/SVG 或 Excel。

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

### P1-重要功能（全部完成）

| 功能 | 状态 | 说明 |
|------|------|------|
| 多维筛选控制面板 | ✅ | 状态/优先级/分类/阶段四维筛选 |
| 关键词搜索 | ✅ | 实时过滤功能名称 |
| 节点 Tooltip | ✅ | 鼠标悬停显示：状态/优先级/负责人/迭代版本/描述 |
| 文档链接跳转 | ✅ | 单击功能节点打开飞书文档 |
| 状态图例 | ✅ | 左下角可折叠图例 |
| 统计数据展示 | ✅ | 顶部统计栏：总数/状态分布进度条 |

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
│   └── Home.tsx              # 主页面（筛选状态管理、布局）
├── components/
│   ├── GraphCanvas/          # G6 画布核心组件
│   │   └── index.tsx         # 图实例创建、事件绑定、Tooltip
│   ├── NodeTooltip/          # 节点悬浮提示
│   ├── ControlPanel/         # 左侧筛选控制面板
│   ├── Legend/               # 状态图例
│   └── StatsBar/             # 顶部统计栏
├── lib/
│   └── dataTransformer.ts    # 数据转换（JSON→G6Data）、筛选、统计
├── types/
│   └── mindmap.ts            # TypeScript 类型定义、状态颜色常量
└── data/
    └── mindmap_data.json     # 静态数据源（来自飞书多维表格）
```

### 关键技术决策

1. **G6 v5 数据格式**：使用 `nodes + edges` 格式（非树形 JSON），通过 `NodeData.children` 字段存储子节点 ID 数组
2. **节点尺寸**：G6 v5 使用 `size: [width, height]` 数组，而非 `width/height` 属性
3. **布局参数**：`@antv/hierarchy` 的 `getWidth/getHeight` 函数接收 `{ id, data: {...} }` 格式，通过 `d.data.nodeType` 访问节点类型
4. **展开/收起**：`collapse-expand` 行为改为双击触发，避免与单击查看详情冲突
5. **Tooltip 坐标**：使用 `evt.client.x/y`（视口坐标）减去容器 `getBoundingClientRect()` 偏移
6. **默认折叠**：模块节点设置 `style.collapsed = true`，初始只显示3层（根→分类→模块）

### 数据流

```
mindmap_data.json
    ↓ transformToG6Data()
G6 GraphData { nodes[], edges[] }
    ↓ filterMindMap()
过滤后的 MindMapRoot
    ↓ Graph.setData() + Graph.render()
G6 Canvas 渲染
```

---

## 已知限制

1. **数据源为静态 JSON**：当前使用本地静态数据，未实现飞书 API 实时同步（P2功能，需后续迭代）
2. **Tooltip 在自动化测试中无法触发**：依赖真实鼠标悬停事件，G6 内部事件系统不响应合成 DOM 事件
3. **节点文字截断**：超长功能名称会被截断显示（通过 `labelMaxWidth` 控制）

---

## 部署信息

- **框架**：React 19 + Vite 7 + TypeScript
- **构建命令**：`pnpm build`
- **开发服务器**：`pnpm dev`（端口 3000）
- **检查点版本**：`9b594a6a`

---

## 下一步建议

1. **接入飞书 API**：实现数据实时同步，替换静态 JSON
2. **节点编辑功能**：支持直接在图上修改节点状态、优先级等属性
3. **导出功能**：支持导出为 PNG/SVG 或 Excel

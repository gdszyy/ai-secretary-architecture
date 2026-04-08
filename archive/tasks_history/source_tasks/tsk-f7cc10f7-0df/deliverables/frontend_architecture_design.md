# XPBET 全球站功能地图管理系统 — 前端可视化架构设计方案

> **文档版本**: v1.0  
> **作者**: frontend_architect (Agent ID: agt-92517928-6d0)  
> **日期**: 2026-03-26  
> **关联任务**: tsk-f7cc10f7-0df  
> **前置任务**: tsk-9103d528-937（数据结构设计）

---

## 1. 概述

本文档为 XPBET 全球站功能地图管理系统提供完整的前端可视化架构设计方案。该系统旨在将飞书多维表格中的数据（21个模块、114个功能点）渲染为可交互的功能地图（类似思维导图），作为飞书白板的替代方案，实现「**全局查看、灵活调整、细节执行**」三大核心目标。

本方案严格基于前序任务（tsk-9103d528-937）输出的数据结构设计方案（4层树状结构、颜色映射规范、TypeScript 接口定义），涵盖以下六大维度：

| 维度 | 内容摘要 |
| --- | --- |
| 技术选型 | React + AntV G6 vs React + D3.js 对比与推荐 |
| 组件架构 | 画布组件、节点组件、控制面板的层级划分与职责 |
| 数据层设计 | 飞书 API 调用、数据转换、状态管理的完整流程 |
| 交互设计 | 缩放/平移、节点跳转、颜色标记、多维视角切换 |
| 飞书集成 | 飞书小组件 (Lark Gadget) 嵌入方案与免登授权 |
| 代码框架 | 完整的 React + AntV G6 骨架代码 |

---

## 2. 技术选型对比与推荐

在前端可视化渲染引擎的选择上，主要对比 **React + AntV G6** 与 **React + D3.js** 两种方案。

### 2.1 选型对比

| 评估维度 | React + AntV G6 | React + D3.js |
| --- | --- | --- |
| **学习曲线** | 较低。封装度高，提供丰富的内置节点、边和布局算法（如 MindMap 布局）。 | 陡峭。底层 API，需要手动处理 DOM/SVG 渲染、数学计算和交互逻辑。 |
| **开发效率** | 高。开箱即用，内置缩放、平移、拖拽、展开/收起等交互行为。 | 低。所有交互和布局均需从零实现，开发周期是 G6 的 3-5 倍。 |
| **定制能力** | 强。支持通过 Canvas/SVG 自定义节点和边，满足绝大多数业务需求。 | 极强。完全控制渲染细节，适合高度定制化的创新可视化。 |
| **性能表现** | 优秀。默认 Canvas 渲染，处理 1000+ 节点性能良好，支持虚拟化。 | 优秀，但若使用 SVG 渲染大量节点，性能可能下降；需手动优化。 |
| **思维导图支持** | 原生支持 `MindMap` 布局，内置树图展开/收起、水平/垂直方向切换。 | 无内置思维导图布局，需手动实现 Reingold-Tilford 算法。 |
| **生态与社区** | 阿里蚂蚁集团开源，国内社区活跃，中文文档完善，与 Ant Design 契合度高。 | 国际标准，生态庞大，但中文资源相对分散。 |
| **飞书集成** | 无特殊障碍，标准 Web 技术栈，可直接嵌入飞书 Gadget。 | 同上，无特殊障碍。 |
| **版本稳定性** | G6 v5 已发布，API 较稳定，有长期维护承诺。 | D3 v7 稳定，但版本间 API 变化较大。 |

### 2.2 明确推荐

**推荐方案：React + AntV G6 v5**

**核心推荐理由**：

本项目的核心需求是渲染一个具有 4 层层级关系的树状思维导图（根节点 → 分类 → 模块 → 功能），AntV G6 内置了成熟的 `TreeGraph` 和 `MindMap` 布局算法，可以**零配置**实现所需的树形展开效果。相比之下，D3.js 需要手动实现 Reingold-Tilford 树布局算法，开发成本极高且容易引入 Bug。

此外，前序任务的数据结构设计已采用 Ant Design 的色彩规范，G6 作为同体系产品，在视觉风格和组件集成上更加自然。G6 的 Canvas 渲染模式在处理 21 个模块 + 114 个功能节点（共约 140+ 节点）时，性能表现充裕。

---

## 3. 组件架构设计

系统前端采用 React 函数式组件 + Hooks 架构，整体划分为三大核心模块：**画布组件**、**节点组件**、**控制面板**。

### 3.1 整体组件层级

```
App (根组件)
├── DataProvider (数据层上下文 Context)
│   ├── 状态: rawData, filteredData, loading, error
│   └── 方法: fetchData, applyFilters, refreshData
│
├── ControlPanel (控制面板)
│   ├── SearchBar (全局搜索框)
│   │   └── 支持按模块名/功能名模糊匹配
│   ├── FilterGroup (多维过滤器)
│   │   ├── StatusFilter (状态过滤: 完成/开发中/规划中等)
│   │   ├── PriorityFilter (优先级过滤: P0/P1/P2/P3)
│   │   ├── StageFilter (阶段过滤: 1月SR验证/3月基础上线等)
│   │   └── OwnerFilter (负责人过滤)
│   └── ViewSwitcher (视图切换)
│       ├── 全景视图 (MindMap 水平布局)
│       ├── 紧凑视图 (MindMap 垂直布局)
│       └── 分类聚焦 (仅展示指定分类)
│
└── GraphCanvas (G6 画布容器)
    ├── ToolBar (工具栏: 缩放+/-、适应屏幕、全屏)
    ├── MiniMap (右下角缩略图导航)
    ├── NodeTooltip (悬浮详情面板)
    └── NodeDetailPanel (右侧滑出详情面板，点击节点触发)
```

### 3.2 核心组件详细说明

#### 3.2.1 GraphCanvas (画布组件)

GraphCanvas 是整个系统的核心组件，负责初始化和管理 G6 `TreeGraph` 实例。

**职责**：
- 在组件挂载时（`useEffect`）初始化 G6 图实例，挂载到 DOM 容器。
- 监听 `filteredData` 的变化，调用 `graph.changeData()` 重新渲染。
- 注册全局事件监听（节点点击、悬浮、双击）。
- 在组件卸载时（`useEffect` cleanup）销毁 G6 实例，防止内存泄漏。

**关键配置**：

| 配置项 | 值 | 说明 |
| --- | --- | --- |
| `layout.type` | `'mindmap'` | 使用思维导图布局 |
| `layout.direction` | `'H'` | 水平方向，根节点居中 |
| `defaultNode.type` | `'xpbet-node'` | 自定义节点类型 |
| `modes.default` | `['collapse-expand', 'drag-canvas', 'zoom-canvas']` | 默认交互行为 |
| `renderer` | `'canvas'` | Canvas 渲染，性能更优 |

#### 3.2.2 CustomNode (自定义节点组件)

通过 `G6.registerNode('xpbet-node', ...)` 注册自定义节点，根据节点类型（`root`/`category`/`module`/`feature`）渲染不同样式。

**节点视觉规范**：

| 节点类型 | 宽度 | 高度 | 圆角 | 字体大小 | 特殊样式 |
| --- | --- | --- | --- | --- | --- |
| root | 160 | 48 | 8 | 16 | 加粗，深色背景 |
| category | 140 | 40 | 6 | 14 | 浅色背景（分类色） |
| module | 动态（文字宽度+40） | 36 | 4 | 13 | 状态背景色 + 优先级边框 |
| feature | 动态（文字宽度+32） | 28 | 4 | 12 | 状态背景色 + 优先级边框 |

#### 3.2.3 ControlPanel (控制面板)

控制面板通过 React Context 与数据层通信，所有过滤操作均在前端内存中完成（无需重新请求 API），确保交互响应速度低于 100ms。

**过滤逻辑**：过滤器采用 AND 逻辑，即同时满足所有选中的过滤条件的节点才会被高亮显示。当过滤结果为空时，展示友好的空状态提示。

---

## 4. 飞书 API 数据层设计

数据层负责从飞书多维表格拉取原始数据，并转换为 G6 所需的树形 JSON 结构。

### 4.1 飞书 API 调用规范

飞书开放平台的多维表格（Bitable）API 采用 REST 风格，需要通过 OAuth 2.0 获取访问令牌。

**数据源信息**（来自前序任务）：

| 参数 | 值 |
| --- | --- |
| BASE_ID | `CyDxbUQGGa3N2NsVanMjqdjxp6e` |
| 模块表 TABLE_ID | `tblaDW4D2hQS2xCw` |
| 功能表 TABLE_ID | `tblLzX7wqGWFr9KP` |

**核心 API 接口**：

```
# 获取 tenant_access_token（应用身份）
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
Body: { "app_id": "<APP_ID>", "app_secret": "<APP_SECRET>" }

# 获取多维表格记录（支持分页，每页最多 500 条）
GET https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records
Headers: Authorization: Bearer <tenant_access_token>
Query: page_size=500, page_token=<上一页的 page_token>
```

### 4.2 数据拉取流程

```
1. 应用启动
   └── 调用 /auth/v3/tenant_access_token/internal 获取 token
       └── 并发调用两个 API:
           ├── 拉取模块表全量数据 (21条，单页即可)
           └── 拉取功能表全量数据 (114条，单页即可)
               └── 调用 transformToMindMap() 转换为树形 JSON
                   └── 存入 React Context / 状态管理
                       └── G6 画布渲染
```

### 4.3 数据转换 (Transformer)

转换逻辑将飞书 Bitable 的扁平记录数组转换为 G6 MindMap 所需的嵌套树形结构，完整实现见 `src/services/transformer.ts`。

**转换步骤**：

1. 解析模块表，按「分类」字段分组，构建 Category 节点。
2. 为每个模块记录构建 Module 节点，挂载到对应 Category 下。
3. 构建模块 RecordID 到节点的快速索引（`Map<string, ModuleNode>`）。
4. 遍历功能表，解析「所属模块」关联字段，将 Feature 节点挂载到对应 Module 下。
5. 组装根节点，附加 `_meta` 元数据。

### 4.4 数据同步策略

| 同步方式 | 触发条件 | 适用场景 |
| --- | --- | --- |
| **手动刷新** | 用户点击"刷新"按钮 | 默认方式，简单可靠 |
| **定时轮询** | 每 5 分钟自动拉取 | 需要数据实时性时启用 |
| **飞书 Webhook** | 飞书多维表格数据变更时推送 | 需要后端服务接收 Webhook 并通知前端 |

---

## 5. 交互设计规范

### 5.1 画布级交互

| 交互行为 | 触发方式 | G6 实现 |
| --- | --- | --- |
| **缩放** | 鼠标滚轮 | 内置 `zoom-canvas` 行为 |
| **平移** | 按住鼠标左键拖拽 | 内置 `drag-canvas` 行为 |
| **展开/收起节点** | 点击节点旁的 +/- 图标 | 内置 `collapse-expand` 行为 |
| **自适应居中** | 点击工具栏"适应屏幕"按钮 | `graph.fitView()` |
| **回到中心** | 点击工具栏"回到中心"按钮 | `graph.fitCenter()` |
| **全屏模式** | 点击工具栏"全屏"按钮 | 浏览器 Fullscreen API |

**缩放范围限制**：最小缩放比例 0.1（防止画布过小），最大缩放比例 4（防止节点过大失去全局视角）。

### 5.2 节点级交互

**悬浮提示 (Tooltip)**：鼠标悬浮在功能节点（feature）上时，在鼠标右侧展示详情卡片，内容包括：

| 字段 | 说明 |
| --- | --- |
| 功能名称 | 加粗显示 |
| 状态 | 带颜色标签 |
| 优先级 | 带颜色标签 |
| 所属模块 | 文本 |
| 阶段 | 文本 |
| 迭代版本 | 文本 |
| 负责人 | 文本 |
| 功能说明 | 最多展示 100 字，超出省略 |
| 文档链接 | 蓝色可点击链接 |

**点击跳转飞书文档**：双击功能节点，若该节点的 `data.docLink` 字段非空，则调用 `window.open(docLink, '_blank')` 在新标签页打开对应的飞书 PRD/设计文档。若在飞书 Gadget 环境中，则调用飞书 JSSDK 的 `tt.openDocument()` 方法在飞书内打开文档。

### 5.3 颜色状态标记

颜色标记遵循前序任务定义的规范，节点背景色反映**状态**，节点边框色反映**优先级**。

**状态颜色映射**：

| 状态值 | 颜色值 | 视觉含义 |
| --- | --- | --- |
| 完成 | `#52C41A` (绿色) | 已完成，可交付 |
| 测试中 | `#13C2C2` (青色) | 研发完成，测试验证中 |
| 开发中 | `#1890FF` (蓝色) | 正在研发中 |
| 待技术评审 | `#722ED1` (紫色) | 需求已定，等待技术方案 |
| 待需求评审 | `#EB2F96` (粉红色) | 需求草案，等待评审 |
| 规划中 | `#FAAD14` (黄色) | 已列入计划，尚未开始 |
| 待规划 | `#D9D9D9` (灰色) | 暂无明确计划 |

**优先级颜色映射**（边框色）：

| 优先级 | 颜色值 | 视觉含义 |
| --- | --- | --- |
| P0-核心 / P0-1月 | `#F5222D` (红色) | 最高优先级，必须完成 |
| P1-重要 / P1-3月 | `#FA8C16` (橙色) | 高优先级，核心功能 |
| P2-一般 / P2-6月 | `#1890FF` (蓝色) | 中等优先级，常规功能 |
| P3-次要 | `#8C8C8C` (灰色) | 低优先级，可延后 |

### 5.4 多维视角切换

系统支持三种视角模式，通过控制面板的 ViewSwitcher 切换：

| 视角模式 | 布局方向 | 说明 |
| --- | --- | --- |
| **全景视图** | 水平 (H) | 默认视图，展示所有分类和模块，适合全局把控 |
| **紧凑视图** | 垂直 (V) | 适合屏幕较窄的场景，节点垂直排列 |
| **分类聚焦** | 水平 (H) | 仅展示选中分类（如 T0基础框架）的子树，适合聚焦某一领域 |

切换视角时，调用 `graph.updateLayout({ direction: 'H' | 'V' })` 并调用 `graph.fitView()` 重新适应屏幕。

---

## 6. 飞书集成方案 (Lark Gadget)

### 6.1 集成架构总览

```
飞书工作台
└── 飞书小组件 (Gadget)
    └── 内嵌 Web 页面 (HTTPS)
        ├── 引入飞书 JSSDK (tt.js)
        ├── 调用 tt.requestAuthCode() 获取授权码
        └── 前端直接调用飞书 Bitable API
            └── G6 画布渲染功能地图
```

### 6.2 飞书小组件配置步骤

1. **创建飞书企业自建应用**：登录飞书开发者后台 ([open.feishu.cn](https://open.feishu.cn))，创建企业自建应用，获取 `App ID` 和 `App Secret`。

2. **配置应用权限**：在应用权限管理中，申请以下权限：
   - `bitable:app:readonly`（读取多维表格）
   - `contact:user.base:readonly`（读取用户基本信息，用于显示负责人）

3. **启用网页能力**：在应用功能配置中，启用「网页」能力，将部署的 HTTPS 地址配置为桌面端主页 URL。

4. **发布应用**：将应用发布到企业内部，团队成员可在飞书工作台的「应用」中找到并使用。

### 6.3 前端免登授权 (SSO) 实现

飞书小组件环境下，前端通过 JSSDK 获取当前用户的授权码，无需用户手动登录：

```typescript
// 在飞书 Gadget 环境中获取当前用户信息
import tt from '@feishu/jssdk';

async function getLarkUserInfo() {
  // 1. 获取授权码
  const { code } = await tt.requestAuthCode({ appId: process.env.REACT_APP_LARK_APP_ID });
  
  // 2. 将授权码发送到后端（或直接在前端调用 API）
  // 注意：code 只能使用一次，有效期 5 分钟
  const response = await fetch('/api/auth/lark', {
    method: 'POST',
    body: JSON.stringify({ code }),
  });
  
  return response.json();
}
```

### 6.4 环境检测与降级方案

系统需要检测当前运行环境（飞书 Gadget vs 普通浏览器），并提供相应的交互方案：

| 运行环境 | 检测方式 | 文档跳转方式 |
| --- | --- | --- |
| 飞书 Gadget | `navigator.userAgent.includes('Lark')` | `tt.openDocument({ url })` 在飞书内打开 |
| 普通浏览器 | 默认 | `window.open(url, '_blank')` 新标签页打开 |

---

## 7. 项目目录结构

```
xpbet-feature-map/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── GraphCanvas/
│   │   │   ├── index.tsx          # 画布主组件
│   │   │   ├── customNodes.ts     # 自定义节点注册
│   │   │   ├── customEdges.ts     # 自定义边注册
│   │   │   └── graphConfig.ts     # G6 配置常量
│   │   ├── ControlPanel/
│   │   │   ├── index.tsx          # 控制面板主组件
│   │   │   ├── SearchBar.tsx      # 搜索框
│   │   │   ├── FilterGroup.tsx    # 过滤器组
│   │   │   └── ViewSwitcher.tsx   # 视图切换器
│   │   ├── NodeTooltip/
│   │   │   └── index.tsx          # 节点悬浮提示
│   │   └── NodeDetailPanel/
│   │       └── index.tsx          # 节点详情侧边栏
│   ├── services/
│   │   ├── feishuApi.ts           # 飞书 API 调用封装
│   │   └── transformer.ts         # 数据转换逻辑
│   ├── context/
│   │   └── DataContext.tsx        # 全局数据 Context
│   ├── hooks/
│   │   ├── useGraph.ts            # G6 图实例管理 Hook
│   │   └── useFeishuData.ts       # 飞书数据拉取 Hook
│   ├── constants/
│   │   └── colorMap.ts            # 颜色映射常量
│   ├── types/
│   │   └── index.ts               # TypeScript 类型定义
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── tsconfig.json
```

---

## 8. 技术栈汇总

| 类别 | 技术/库 | 版本 | 用途 |
| --- | --- | --- | --- |
| 框架 | React | 18.x | UI 框架 |
| 语言 | TypeScript | 5.x | 类型安全 |
| 可视化 | AntV G6 | 5.x | 图可视化引擎 |
| UI 组件库 | Ant Design | 5.x | 控制面板 UI 组件 |
| 状态管理 | React Context + useReducer | — | 轻量级状态管理 |
| HTTP 客户端 | Axios | 1.x | 飞书 API 调用 |
| 构建工具 | Vite | 5.x | 快速构建和热更新 |
| 飞书集成 | @feishu/jssdk | latest | 飞书 Gadget 免登 |

---

## 9. 参考资料

- [AntV G6 官方文档](https://g6.antv.antgroup.com/)
- [飞书开放平台 Bitable API](https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview)
- [飞书小组件开发指南](https://open.feishu.cn/document/client-docs/gadget/introduction)
- [前序任务数据结构设计文档](../tsk-9103d528-937/deliverables/xpbet_data_structure_design.md)

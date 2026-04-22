# 北极星因子分解图 (North Star Decomposition) 组件详细设计文档

## 1. 组件概述

**组件名称**：北极星因子分解图 (North Star Decomposition)
**组件 Key**：`north_star_decomposition`
**适用模块**：北极星指标归因 (North Star Attribution)
**优先级**：P0 (首屏核心组件)

本组件旨在解决现有 `NorthStarChart` 仅展示趋势而缺乏因子分解树状结构的问题。通过引入「一眼定调→悬浮概要/关键→下钻详情」三层交互模型，直观展示北极星指标的变化归因及其底层驱动因素，帮助用户快速定位业务增长或衰退的根本原因。

## 2. 三层交互模型设计

### 2.1 一眼定调 (Glance & Tone)
- **视觉形态**：采用 SVG 或 Canvas 绘制的横向树状结构图（Tree Diagram）。左侧根节点为北极星指标总变化量，向右展开为各级归因因子。
- **状态映射**：
  - **节点颜色**：基于因子的贡献量（正向/负向）或健康度状态，使用标准颜色规范（绿 `success` / 黄 `warning` / 红 `danger`）。
  - **连线粗细**：连线的粗细（Stroke Width）与该因子对父节点的绝对贡献量成正比，直观反映权重。
  - **异常标识**：对于突破预警阈值或产生重大负向影响的节点，附加显眼的警告图标（如 ⚠️）并伴随轻微的呼吸动效（Pulse）。

### 2.2 悬浮概要 (Hover Summary)
- **交互触发**：鼠标悬停（Hover）在任意节点上时触发。
- **浮层内容**：弹出一个信息丰富的 Tooltip 浮层，展示该因子的详细上下文。
- **可配置上下文类型**：
  - **关键数值**：当前值、目标值、环比变化量/率、绝对贡献量。
  - **责任归属**：该因子对应的业务模块及负责人。
  - **洞察分析**：风险描述、原因分析、解决方案（由数据洞察探针生成）。

### 2.3 下钻详情 (Drill-down Detail)
- **交互触发**：鼠标点击（Click）任意节点时触发。
- **行为逻辑**：触发 `onDrillDown` 回调函数，将当前节点的 ID 和关联的模块 ID 传递给父组件。
- **跳转目标**：由父组件（如 `WeeklyReportDashboard`）决定具体的跳转锚点或路由。例如，点击“转化率”节点可平滑滚动至“业务模块详情”中的“漏斗转化组件”。

## 3. 数据结构定义 (TypeScript Interfaces)

为了支持树状结构的渲染和丰富的交互上下文，定义以下数据接口：

```typescript
/** 趋势方向 */
export type TrendDirection = 'up' | 'down' | 'stable';

/** 节点健康度状态 */
export type NodeStatus = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

/** 因子节点上下文信息（用于 Hover 浮层） */
export interface FactorContext {
  /** 当前值（格式化字符串） */
  currentValue?: string;
  /** 目标值（格式化字符串） */
  targetValue?: string;
  /** 环比变化率（如 "+5.2%"） */
  changeRate?: string;
  /** 负责团队/人 */
  owner?: string;
  /** 风险描述或原因分析 */
  insight?: string;
}

/** 因子分解树节点 */
export interface DecompositionNode {
  /** 节点唯一 ID */
  id: string;
  /** 因子名称（如 "新用户增长"、"转化率"） */
  name: string;
  /** 对父节点的贡献量（正值为正向，负值为负向） */
  contribution: number;
  /** 节点健康度状态（决定节点颜色） */
  status: NodeStatus;
  /** 关联的业务模块 ID（用于下钻跳转） */
  moduleId?: string;
  /** 悬浮上下文信息 */
  context?: FactorContext;
  /** 子节点列表 */
  children?: DecompositionNode[];
}

/** 北极星因子分解图组件数据 */
export interface NorthStarDecompositionData {
  /** 北极星指标名称（如 "DAU"） */
  metric: string;
  /** 当前总值 */
  value: number;
  /** 单位（如 "万"） */
  unit?: string;
  /** 总环比变化量 */
  change: number;
  /** 总环比变化率 */
  changeRate: string;
  /** 总体趋势 */
  trend: TrendDirection;
  /** 目标值 */
  target?: number;
  /** 因子分解树根节点（通常代表总变化量） */
  rootNode: DecompositionNode;
}
```

## 4. 组件 Props 接口

```typescript
export interface NorthStarDecompositionProps {
  /** 组件数据 */
  data: NorthStarDecompositionData;
  /** 
   * 下钻回调函数
   * @param nodeId 被点击的节点 ID
   * @param moduleId 关联的业务模块 ID（如果有）
   */
  onDrillDown?: (nodeId: string, moduleId?: string) => void;
  /** 自定义类名 */
  className?: string;
}
```

## 5. 关键交互状态与渲染策略

### 5.1 树状图布局计算
- 使用自定义的递归算法或轻量级布局库（如 `d3-hierarchy` 的简化版，若不引入新依赖则手写递归计算坐标）计算每个节点的 `(x, y)` 坐标。
- 采用从左到右的水平布局，层级间距固定，同级节点垂直居中对齐。

### 5.2 连线渲染 (SVG Paths)
- 使用 SVG `<path>` 元素绘制贝塞尔曲线（Cubic Bezier）连接父子节点，使视觉更柔和。
- 连线的 `stroke-width` 根据 `Math.abs(child.contribution)` 占父节点总绝对贡献的比例动态计算，设置最小和最大宽度阈值（如 2px - 12px）。
- 连线颜色可采用中性色（如 `slate-300`）或继承子节点的颜色（带透明度）。

### 5.3 节点渲染 (HTML/SVG)
- 节点主体使用 HTML 元素（通过 `foreignObject` 嵌入 SVG 或绝对定位覆盖在 SVG 上）以方便实现复杂的 Hover 浮层和 Tailwind 样式。
- 节点样式：圆角矩形，背景色根据 `status` 映射（使用 `STATUS_CONFIG` 中的颜色），包含因子名称和贡献量数值。
- 警告图标：当 `status === 'danger'` 时，在节点右上角绝对定位渲染一个红色的警告图标，并添加 `animate-pulse` 类。

### 5.4 Hover 浮层 (Tooltip)
- 使用相对定位或 React Portal 实现。
- 监听节点的 `onMouseEnter` 和 `onMouseLeave` 事件，控制浮层的显示与隐藏。
- 浮层内部采用网格布局，清晰展示 `FactorContext` 中的各项数据。

## 6. 样式规范 (TailwindCSS)

- **容器**：`rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 p-5`
- **标题区**：`text-xs font-semibold uppercase tracking-widest text-sky-500`
- **正向数值**：`text-emerald-500`
- **负向数值**：`text-red-500`
- **节点基础样式**：`px-3 py-2 rounded-lg border shadow-sm cursor-pointer transition-all hover:shadow-md`

## 7. 替代方案考量

如果完全手写 SVG 树状布局过于复杂且容易出现边界情况（如节点重叠），可以考虑采用 Flexbox/Grid 结合连线组件（如 `react-xarrows`）的方案，或者简化为多级缩进的列表形态（类似现有的 `NorthStarChart` 但支持嵌套折叠）。考虑到“一眼定调”的视觉冲击力要求，首选方案仍是 SVG 树状图。

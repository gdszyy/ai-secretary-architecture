# 多维健康度雷达图 (Health Radar Chart) 详细设计文档

## 1. 组件概述

**组件名称**：多维健康度雷达图 (Health Radar Chart)
**组件 Key**：`health_radar_chart`
**适用模块**：项目健康度诊断 (Health Score)
**组件类型**：首屏模块 (Hero Component) - P0 优先级

本组件旨在通过多边形雷达图直观展示项目在各个核心维度（如增长、产品、商业化、风险等）的健康状况。通过叠加“当前状态”与“目标状态”双层多边形，并使用红色半透明遮罩标出低于警戒线的危险区域，帮助读者“一眼定调”项目的整体运行状况。

## 2. 三层交互模型设计

根据首屏组件设计原则，本组件实现“一眼定调 → 悬浮概要 → 下钻详情”的三层交互模型。

### 2.1 一眼定调 (Glance)

- **视觉形态**：多边形雷达图（Radar Chart）。
- **双层叠加**：
  - **当前状态 (Current)**：实线多边形，带有半透明填充色（如主题色 `indigo-500/20`）。
  - **目标状态 (Target)**：虚线多边形，无填充或极淡填充，表示各维度的期望得分。
- **危险区域预警**：
  - 设定一条全局或维度特定的警戒线（如 60 分）。
  - 当某维度的当前得分低于警戒线时，该维度所在的雷达图区域（或顶点）使用红色半透明遮罩（如 `red-500/30`）高亮标出，形成强烈的视觉警示。
- **整体评分**：在雷达图中心或旁边展示综合健康度评分（大字号）及趋势（上升/下降/持平）。

### 2.2 悬浮概要 (Hover)

- **触发方式**：鼠标悬浮 (Hover) 在雷达图的各个维度顶点上。
- **浮层内容 (Tooltip)**：
  - **维度名称与得分**：如“增长势能：82 / 100”。
  - **核心支撑指标简报**：该维度下最关键的 1-2 个指标及其当前值/变化率（如“DAU: 1.2w (+5%)”）。
  - **主要扣分项/风险点**：简述导致该维度失分的主要原因（如“D7 留存率低于预期”）。
- **上下文配置**：浮层内容支持通过 Props 传入，允许根据不同的业务上下文动态配置展示字段。

### 2.3 下钻详情 (Drill-down)

- **触发方式**：鼠标点击 (Click) 雷达图的各个维度顶点或整体卡片。
- **交互逻辑**：
  - 触发 `onDrillDown` 或 `onDimensionClick` 回调函数。
  - 传递当前点击的维度 ID 或名称给父组件。
  - 由父组件决定具体的跳转目标（如滚动到“业务模块详情”对应的子模块区域）。

## 3. 数据结构定义 (TypeScript Interfaces)

为了支持上述交互模型，定义以下数据接口：

```typescript
/** 趋势方向 */
export type TrendDirection = 'up' | 'down' | 'stable';

/** 雷达图单个维度数据 */
export interface RadarDimension {
  /** 维度唯一标识 */
  id: string;
  /** 维度显示名称，如"增长势能" */
  name: string;
  /** 当前得分 (0-100) */
  score: number;
  /** 目标得分 (0-100) */
  targetScore: number;
  /** 警戒线分数，低于此分数将标红预警 */
  warningThreshold: number;
  /** 核心支撑指标简报（用于 Hover 浮层） */
  keyMetrics: Array<{ label: string; value: string; trend?: TrendDirection }>;
  /** 主要扣分项/风险点描述（用于 Hover 浮层） */
  riskPoints?: string[];
}

/** 多维健康度雷达图整体数据 */
export interface HealthRadarData {
  /** 综合评分 (0-100) */
  overallScore: number;
  /** 综合评分趋势 */
  overallTrend: TrendDirection;
  /** 阶段描述，如"蓄力期" */
  phase: string;
  /** 阶段简要说明 */
  summary: string;
  /** 各维度数据列表（至少需要 3 个维度才能构成多边形） */
  dimensions: RadarDimension[];
}
```

## 4. 组件 Props 接口

```typescript
export interface HealthRadarChartProps {
  /** 雷达图数据源 */
  data: HealthRadarData;
  /** 
   * 下钻回调：点击整体卡片时触发
   * 通常用于跳转到整体健康度详情或业务模块概览
   */
  onClick?: () => void;
  /** 
   * 下钻回调：点击特定维度顶点时触发
   * @param dimensionId 被点击的维度 ID
   * 通常用于跳转到该维度对应的具体业务模块详情
   */
  onDimensionClick?: (dimensionId: string) => void;
  /** 自定义类名 */
  className?: string;
}
```

## 5. 技术实现方案

- **基础框架**：React + TypeScript。
- **样式方案**：TailwindCSS（用于外层卡片布局、排版、颜色主题）。
- **图表库**：Recharts。
  - 使用 `<RadarChart>` 作为基础容器。
  - 使用 `<PolarGrid>` 绘制雷达图网格。
  - 使用 `<PolarAngleAxis>` 绘制维度轴（标签）。
  - 使用 `<PolarRadiusAxis>` 绘制刻度轴（可隐藏以保持简洁）。
  - 使用两个 `<Radar>` 组件分别绘制“目标状态”（虚线、无填充）和“当前状态”（实线、半透明填充）。
- **危险区域预警实现**：
  - Recharts 的 `<Radar>` 组件原生不支持针对单个顶点设置不同的填充色。
  - **方案**：通过自定义 `<Tooltip>` 或在 `<PolarAngleAxis>` 的 `tick` 渲染中，对低于 `warningThreshold` 的维度标签标红。同时，在图表上方叠加自定义的 SVG 元素，或者利用 Recharts 的 `activeDot` / `dot` 属性，将低于警戒线的顶点渲染为显眼的红色警告图标。
- **悬浮概要实现**：
  - 使用 Recharts 的 `<Tooltip>` 组件，传入自定义的 `content` 渲染函数。
  - 在自定义 Tooltip 中，从 `payload` 获取当前维度的完整数据（包括 `keyMetrics` 和 `riskPoints`），并按设计规范渲染浮层。

## 6. 关键交互状态说明

1. **默认状态**：展示雷达图、综合评分、阶段描述。目标多边形用灰色虚线，当前多边形用主题色实线填充。
2. **预警状态**：若某维度 `score < warningThreshold`，该维度的顶点圆点变为红色，维度名称文本变为红色加粗。
3. **Hover 状态**：鼠标移入雷达图区域，高亮当前所在的维度轴，弹出包含指标简报和扣分项的自定义 Tooltip。
4. **Click 状态**：鼠标点击维度顶点或标签，触发 `onDimensionClick`，执行页面滚动或路由跳转。

---
*设计文档编写完成，下一步将基于此文档进行 React 组件的编码实现。*

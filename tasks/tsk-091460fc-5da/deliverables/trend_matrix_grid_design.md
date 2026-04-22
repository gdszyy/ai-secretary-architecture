# 「指标趋势矩阵」详情组件 (trend_matrix_grid) 详细设计文档

## 1. 组件概述

**组件名称**: `TrendMatrixGrid` (指标趋势矩阵)
**组件Key**: `trend_matrix_grid`
**组件类型**: 详情组件 (Detail Component)
**适用模块**: 多指标监控、业务模块详情
**核心目标**: 直观清晰地展示多个 KPI 的趋势对比，通过小倍数图 (Small Multiples) 和联动十字准星 (Synchronized Crosshair) 帮助用户快速发现同一时间点下各指标的关联与异常。

## 2. 组件布局方案

组件采用网格布局 (Grid Layout) 呈现多个小倍数图。

*   **整体容器**: 
    *   使用 CSS Grid 布局，默认在桌面端为 2 列或 3 列，移动端为 1 列。
    *   包含一个统一的图例 (Legend) 和时间范围选择器 (可选)。
*   **子图卡片 (Small Multiple Card)**:
    *   **顶部信息区**: 
        *   指标名称 (Metric Name)
        *   当前最新值 (Current Value)
        *   环比变化率 (Change Rate)，使用颜色区分涨跌 (例如：绿色上涨，红色下跌，或根据业务定义反转)。
    *   **图表区**:
        *   使用 Recharts 的 `LineChart` 或 `AreaChart`。
        *   **共享 X 轴**: 所有子图的 X 轴时间范围和刻度完全一致，但为了视觉简洁，可能只在最底部的图表或通过 Tooltip 显示具体时间。
        *   **Y 轴**: 每个子图独立自适应 Y 轴范围，以最佳展示自身趋势。
        *   **联动十字准星**: 当鼠标悬浮在任意一个子图的某个时间点时，所有其他子图在该时间点同时显示垂直参考线 (Reference Line) 和 Tooltip 锚点。

## 3. 数据结构定义

为了支持联动和统一渲染，数据结构需要包含时间序列和对应的多个指标值。

```typescript
// 趋势数据点
export interface TrendDataPoint {
  /** 时间标签，如 "2023-10-01" 或 "周一" */
  date: string;
  /** 动态键值对，键为指标 ID，值为该时间点的数值 */
  [metricId: string]: number | string;
}

// 单个指标的元数据配置
export interface MetricConfig {
  /** 指标唯一标识 */
  id: string;
  /** 指标显示名称 */
  name: string;
  /** 数值格式化函数或单位，如 "%", "万" */
  unit?: string;
  /** 趋势颜色 (Tailwind class 或 Hex) */
  color?: string;
  /** 涨跌颜色反转 (默认涨绿跌红，若为 true 则涨红跌绿，如"跳出率") */
  invertColors?: boolean;
  /** 当前最新值 (可由组件计算或外部传入) */
  currentValue?: number;
  /** 环比变化率 (可由组件计算或外部传入) */
  changeRate?: number;
}

// 组件整体数据接口
export interface TrendMatrixData {
  /** 时间序列数据数组 */
  data: TrendDataPoint[];
  /** 需要展示的指标配置列表 */
  metrics: MetricConfig[];
}
```

## 4. 组件 Props 接口

```typescript
import { HTMLAttributes } from 'react';

export interface TrendMatrixGridProps extends HTMLAttributes<HTMLDivElement> {
  /** 矩阵数据源 */
  dataset: TrendMatrixData;
  /** 网格列数，默认 2 */
  columns?: 1 | 2 | 3 | 4;
  /** 图表高度，默认 200px */
  chartHeight?: number;
  /** 是否显示面积图阴影，默认 true */
  showArea?: boolean;
  /** 联动 Tooltip 格式化函数 */
  tooltipFormatter?: (value: number, metricId: string) => string | React.ReactNode;
}
```

## 5. 联动交互说明 (Synchronized Crosshair)

实现联动十字准星的核心在于状态提升 (State Lifting)：

1.  **共享状态**: 在 `TrendMatrixGrid` 父组件中维护一个 `activeHoverIndex` 或 `activeHoverDate` 状态，记录当前鼠标悬浮的数据点索引或时间。
2.  **事件监听**: 每个子图的 Recharts 组件监听 `onMouseMove` 和 `onMouseLeave` 事件。
    *   当鼠标进入某个子图时，触发 `onMouseMove`，将当前悬浮的 `activeTooltipIndex` 更新到父组件的共享状态中。
    *   当鼠标离开时，触发 `onMouseLeave`，清空共享状态。
3.  **状态下发**: 父组件将 `activeHoverIndex` 作为 prop 传递给所有子图。
4.  **自定义渲染**:
    *   在每个子图的 Recharts 中，使用自定义的 `Tooltip` 或 `ReferenceLine`。
    *   如果 `activeHoverIndex` 存在，则在对应的数据点位置渲染一条垂直线和一个高亮的数据点圆圈。
    *   (可选) 可以在父组件层级渲染一个全局的浮动 Tooltip，展示当前时间点所有指标的数值，或者在每个子图内部渲染独立的 Tooltip。为了视觉清晰，推荐在每个子图内部高亮当前值，并在顶部信息区动态更新显示悬浮时间点的值。

## 6. 依赖与技术栈

*   **React**: 视图渲染与状态管理 (`useState`, `useCallback`, `useMemo`)。
*   **TypeScript**: 类型定义，确保数据结构严谨。
*   **TailwindCSS**: 样式布局 (Grid, Flexbox) 与主题颜色。
*   **Recharts**: 图表绘制 (`ResponsiveContainer`, `AreaChart`, `Area`, `XAxis`, `YAxis`, `Tooltip`, `ReferenceLine`)。

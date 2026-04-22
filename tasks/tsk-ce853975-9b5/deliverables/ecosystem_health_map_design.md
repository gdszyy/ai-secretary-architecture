# 创作者/供给方生态图 (Ecosystem Health Map) 详细设计文档

## 1. 组件概述

**组件名称**: `EcosystemHealthMap`
**组件 Key**: `ecosystem_health_map`
**组件类型**: 详情组件 (Detail Component)
**适用模块**: 内容与社区、平台生态

**核心目标**: 
直观反映平台创作者/供给方的生态结构健康度，对比头、腰、尾部的人数规模占比与价值贡献（如内容产出量、收入贡献等）占比。通过可视化手段预警生态固化风险（如头部过度集中），并支持时间维度（本周 vs 上周）的对比，观察生态结构变化趋势。

## 2. 视觉与布局方案

### 2.1 整体布局
组件采用卡片式布局，分为三个主要区域：
1. **头部信息区**: 包含组件标题、当前生态健康度状态标签（如“健康”、“头部固化预警”）、以及时间维度切换控件（本周/上周对比）。
2. **核心可视化区**: 采用**双向堆叠柱状图 (Bi-directional Stacked Bar Chart)** 或 **对称漏斗图**。
   - **左侧**: 展示各层级（头部、腰部、尾部）的**人数规模占比**。
   - **右侧**: 展示各层级对应的**价值贡献占比**。
   - **中间**: 标明层级名称（头部 Top 5%、腰部 Middle 20%、尾部 Long-tail 75%）。
3. **洞察与预警区**: 文本形式的自动洞察，高亮显示关键数据变化和潜在风险（如“头部 5% 创作者贡献了 82% 的价值，存在较高的单点依赖风险”）。

### 2.2 交互设计
- **Hover 提示 (Tooltip)**: 鼠标悬停在图表各层级时，显示具体的人数、贡献绝对值及环比变化率。
- **时间对比切换**: 提供 Toggle 按钮或简单的 Tab 切换，允许用户快速对比本期与上期的数据结构。
- **无三层交互限制**: 作为详情组件，重点在于信息的直接平铺展示，无需复杂的下钻逻辑。

### 2.3 颜色规范
遵循 `weekly_report_example.tsx` 中的 Tailwind 颜色规范：
- **头部 (Top)**: 使用强调色，如 `indigo-500` (深色模式下 `indigo-400`)。
- **腰部 (Middle)**: 使用辅助色，如 `sky-500` (深色模式下 `sky-400`)。
- **尾部 (Tail)**: 使用基础色，如 `slate-400` (深色模式下 `slate-500`)。
- **预警色**: 当头部贡献占比超过设定阈值（如 80%）时，触发预警，相关文本或边框使用 `red-400` 或 `amber-400`。

## 3. 数据结构定义 (Props Interface)

```typescript
/** 生态层级定义 */
export type EcosystemTier = 'top' | 'middle' | 'tail';

/** 单个层级的数据结构 */
export interface TierData {
  /** 层级标识 */
  id: EcosystemTier;
  /** 层级名称，如 "头部 (Top 5%)" */
  name: string;
  /** 人数规模绝对值 */
  population: number;
  /** 人数规模占比 (0-100) */
  populationRatio: number;
  /** 价值贡献绝对值（如发文量、GMV等） */
  contribution: number;
  /** 价值贡献占比 (0-100) */
  contributionRatio: number;
  /** 环比变化：人数占比变化 (百分点) */
  populationRatioChange?: number;
  /** 环比变化：贡献占比变化 (百分点) */
  contributionRatioChange?: number;
}

/** 生态健康度状态 */
export type EcosystemStatus = 'healthy' | 'warning' | 'danger';

/** 组件整体数据结构 */
export interface EcosystemHealthData {
  /** 价值贡献的指标名称，如 "内容产出量"、"GMV 贡献" */
  contributionMetricName: string;
  /** 当前周期数据 */
  currentPeriod: {
    label: string; // 如 "本周"
    tiers: TierData[];
  };
  /** 对比周期数据（可选） */
  previousPeriod?: {
    label: string; // 如 "上周"
    tiers: TierData[];
  };
  /** 整体生态状态评估 */
  status: EcosystemStatus;
  /** 自动生成的洞察结论或预警信息 */
  insights: string[];
  /** 头部集中度预警阈值 (0-100)，默认 80 */
  concentrationWarningThreshold?: number;
}

/** 组件 Props */
export interface EcosystemHealthMapProps {
  data: EcosystemHealthData;
  className?: string;
}
```

## 4. 技术实现细节

1. **图表库选择**: 使用 `recharts` 库实现双向条形图。
   - 利用 `BarChart` 组件，设置 `layout="vertical"`。
   - 左侧人数占比：将数值转为负数以实现向左延伸，在 Tooltip 和 Label 中格式化回正数。
   - 右侧贡献占比：正常正数向右延伸。
   - 共享同一个 Y 轴（层级名称），放置在图表中央。
2. **样式框架**: 深度集成 TailwindCSS，支持深色模式 (`dark:` 前缀)。
3. **响应式设计**: 确保在不同屏幕宽度下，图表比例协调，文字不重叠。移动端下可考虑将双向图转为上下堆叠的单向图（视具体空间而定，优先保证 PC 端体验）。
4. **状态指示**: 复用 `weekly_report_example.tsx` 中的 `StatusBadge` 或类似逻辑，直观展示 `healthy` / `warning` / `danger` 状态。

## 5. 预期效果示例

当头部 5% 的创作者贡献了 85% 的内容时，组件顶部会显示红色的“头部固化预警”标签。图表左侧显示一个极短的头部人数条（5%），而右侧对应一个极长的贡献条（85%），形成强烈的视觉反差，直观传达“二八定律”甚至“一九定律”的极端情况。底色。洞察区会提示：“头部创作者贡献占比环比上升 3%，生态固化趋势加剧，建议加大对腰部创作者的流量扶持。”

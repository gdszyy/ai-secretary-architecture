# 漏斗转化组件 (Conversion Funnel) 详细设计文档

## 1. 组件概述

**组件名称**：漏斗转化组件 (Conversion Funnel)
**组件 Key**：`conversion_funnel`
**组件类型**：详情组件 (Detail Component)
**适用模块**：增长与获客 (Growth & Acquisition)、商业化与变现 (Monetization)
**优先级**：P1
**核心目标**：直观展示用户在特定业务流程（如注册、购买、订阅等）中的流失情况，暴露转化瓶颈。

## 2. 视觉与交互设计

### 2.1 布局方案
- **整体结构**：采用卡片式容器，包含标题区、漏斗图表区和图例说明区。
- **图表形态**：采用**阶梯柱状图 (Stepped Bar Chart)** 结合**连接箭头**的形式。相比传统的倒三角漏斗，阶梯柱状图能更清晰地对比各步骤的绝对数值差异，且更易于实现多漏斗对比。
- **数据展示**：
  - **柱状图**：高度代表该步骤的绝对人数/次数。
  - **步骤间转化率**：在相邻两个柱子之间，使用带箭头的标签标注转化率（如 `→ 45%`）。
  - **整体转化率**：在图表右上角或标题旁，醒目展示从第一步到最后一步的整体转化率。

### 2.2 多漏斗对比 (对比模式)
- **场景**：支持本周与上周、A/B 测试不同策略的漏斗对比。
- **视觉区分**：
  - 主漏斗（如本周）使用品牌主色调（如 Indigo/Blue）。
  - 对比漏斗（如上周）使用较弱的颜色（如 Slate/Gray）或带透明度的同色系。
- **瓶颈高亮**：自动计算并高亮显示转化率最低的步骤（或环比下降最严重的步骤），使用警告色（如 Amber/Red）进行视觉强调。

### 2.3 交互说明
- **无三层交互限制**：作为详情组件，核心是“把事情讲清楚”，因此不需要复杂的下钻交互。
- **Hover 提示 (Tooltip)**：鼠标悬停在特定步骤的柱子上时，显示该步骤的详细数据（绝对值、流失人数、相对上一步转化率、整体转化率）。

## 3. 数据结构定义 (TypeScript Interfaces)

```typescript
/** 漏斗单步数据 */
export interface FunnelStep {
  /** 步骤 ID */
  id: string;
  /** 步骤名称，如 "访问落地页" */
  label: string;
  /** 绝对数值（人数/次数） */
  value: number;
  /** 格式化后的数值字符串，如 "12,500" */
  formattedValue?: string;
  /** 相对上一步的转化率 (0-100)，第一步为 null */
  conversionRate?: number;
  /** 是否为转化瓶颈（最低转化率或降幅最大） */
  isBottleneck?: boolean;
}

/** 单个漏斗数据系列 */
export interface FunnelSeries {
  /** 系列名称，如 "本周"、"策略A" */
  name: string;
  /** 步骤数据列表，必须按流程顺序排列 */
  steps: FunnelStep[];
  /** 整体转化率 (最后一步 / 第一步) */
  overallConversionRate: number;
  /** 系列颜色 (Tailwind class，如 "bg-indigo-500") */
  color?: string;
}

/** 漏斗转化组件 Props */
export interface ConversionFunnelProps {
  /** 组件标题 */
  title: string;
  /** 组件描述或分析结论 */
  description?: string;
  /** 漏斗数据系列（支持 1-2 个系列进行对比） */
  series: FunnelSeries[];
  /** 数值单位，如 "人"、"次" */
  unit?: string;
}
```

## 4. 组件实现细节 (React + TailwindCSS)

### 4.1 容器与标题
使用与 `weekly_report_example.tsx` 一致的卡片样式：
```tsx
<div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 p-5">
  {/* 标题和描述 */}
</div>
```

### 4.2 阶梯柱状图渲染逻辑
- 找到所有系列中 `value` 的最大值 `maxValue`，用于计算柱子的高度百分比：`height = (value / maxValue) * 100%`。
- 使用 Flexbox 布局横向排列各个步骤。
- 每个步骤内部，如果有多个系列（对比模式），则并排渲染多个柱子。

### 4.3 转化率箭头渲染
- 在两个步骤容器之间，绝对定位或使用 Flex 插入一个包含箭头和转化率文本的元素。
- 如果某步骤被标记为 `isBottleneck`，则该步骤的转化率标签使用红色/橙色高亮，并可附加警告图标。

### 4.4 响应式处理
- 桌面端：横向排列步骤。
- 移动端：当步骤较多时，允许图表区域横向滚动 (`overflow-x-auto`)，保证柱子和文字不被过度挤压。

## 5. 示例 Mock 数据

```typescript
const mockFunnelData: ConversionFunnelProps = {
  title: "新用户注册转化漏斗",
  description: "本周注册转化率受短信通道延迟影响，『获取验证码』环节转化率环比下降 12%，成为核心瓶颈。",
  unit: "人",
  series: [
    {
      name: "本周",
      color: "bg-indigo-500",
      overallConversionRate: 18.5,
      steps: [
        { id: "s1", label: "访问落地页", value: 10000, conversionRate: null },
        { id: "s2", label: "点击注册", value: 6500, conversionRate: 65.0 },
        { id: "s3", label: "获取验证码", value: 3200, conversionRate: 49.2, isBottleneck: true },
        { id: "s4", label: "注册成功", value: 1850, conversionRate: 57.8 },
      ]
    },
    {
      name: "上周",
      color: "bg-slate-300 dark:bg-slate-600",
      overallConversionRate: 24.2,
      steps: [
        { id: "s1", label: "访问落地页", value: 9500, conversionRate: null },
        { id: "s2", label: "点击注册", value: 6200, conversionRate: 65.2 },
        { id: "s3", label: "获取验证码", value: 3800, conversionRate: 61.2 },
        { id: "s4", label: "注册成功", value: 2300, conversionRate: 60.5 },
      ]
    }
  ]
};
```

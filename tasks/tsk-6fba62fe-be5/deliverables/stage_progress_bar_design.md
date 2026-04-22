# 业务阶段进度组件 (Stage Progress Bar) 详细设计文档

## 1. 组件概述

**组件名称**：业务阶段进度组件 (Stage Progress Bar)
**组件 Key**：`stage_progress_bar`
**所属分类**：首屏模块 (Hero Modules)
**优先级**：P0
**适用模块**：里程碑进度 (Milestone Progress)

该组件旨在通过横向步骤条的形式，直观展示项目当前所处的业务阶段（种子期、启动期、成长期、扩张期、成熟期）。它与 `analysis_framework.md` 中定义的业务阶段矩阵深度联动，帮助阅读者“一眼定调”项目的整体生命周期状态，并提供悬浮概要和下钻详情的三层交互体验。

## 2. 三层交互模型设计

根据 `hero_component_design_principles.md` 和 `component_library.md` 的规范，本组件实现以下三层交互：

### 2.1 一眼定调 (Glance & Tone)
- **视觉形态**：横向步骤条 (Horizontal Stepper)。
- **阶段划分**：固定为 5 个阶段：种子期 (Seed)、启动期 (Launch)、成长期 (Growth)、扩张期 (Scale)、成熟期 (Mature)。
- **状态呈现**：
  - **已完成阶段**：使用对勾图标标记，线条和节点使用主色调（如 Indigo/Blue）。
  - **当前阶段**：节点高亮放大，使用主色调填充，并带有呼吸灯或外发光效果。
  - **未开始阶段**：节点和线条置灰（Slate/Gray）。
- **整体进度**：在组件右侧或上方显著位置显示整体进度百分比（如 "当前进度：成长期 (60%)"）。

### 2.2 悬浮概要 (Hover Summary)
- **触发方式**：鼠标悬停 (Hover) 在任意阶段节点上。
- **浮层内容**：
  - **阶段名称与定义**：如“成长期 (Growth) - 规模化增长”。
  - **核心目标**：该阶段必须达成的核心业务目标（如“用户规模突破 10 万，验证增长引擎”）。
  - **当前完成情况**：该阶段关键指标的当前值与目标值对比。
  - **上下文类型**：支持可配置的上下文类型（如 `success`, `warning`, `danger`），根据该阶段的健康度显示不同颜色的提示信息。

### 2.3 下钻详情 (Drill-down Details)
- **触发方式**：鼠标点击 (Click) 阶段节点。
- **交互逻辑**：触发 `onDrillDown` 回调函数，传入被点击的阶段 ID。
- **跳转目标**：由父组件决定，通常跳转至该阶段的详细规划文档、OKR 看板或对应的业务模块详情（如点击“成长期”跳转至“增长与获客”模块）。

## 3. 数据结构定义 (TypeScript Interfaces)

为了支持上述交互，定义以下数据接口：

```typescript
/** 业务阶段枚举 */
export type BusinessStageId = 'seed' | 'launch' | 'growth' | 'scale' | 'mature';

/** 阶段状态枚举 */
export type StageStatus = 'completed' | 'current' | 'upcoming';

/** 悬浮概要上下文类型 */
export type ContextType = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

/** 单个业务阶段数据结构 */
export interface BusinessStage {
  /** 阶段 ID */
  id: BusinessStageId;
  /** 阶段名称（如：成长期） */
  name: string;
  /** 阶段英文名（如：Growth） */
  nameEn: string;
  /** 阶段状态 */
  status: StageStatus;
  /** 阶段定义/副标题（如：规模化增长） */
  subtitle: string;
  /** 核心目标描述 */
  coreObjective: string;
  /** 当前完成情况描述 */
  currentProgress: string;
  /** 上下文类型（用于悬浮浮层颜色提示） */
  contextType: ContextType;
  /** 关键指标列表（悬浮浮层展示） */
  metrics?: Array<{
    label: string;
    value: string;
    target: string;
  }>;
}

/** 业务阶段进度组件整体数据结构 */
export interface StageProgressData {
  /** 当前所处阶段 ID */
  currentStageId: BusinessStageId;
  /** 整体进度百分比 (0-100) */
  overallProgress: number;
  /** 阶段列表（固定 5 个） */
  stages: BusinessStage[];
}
```

## 4. 组件 Props 接口

```typescript
export interface StageProgressBarProps {
  /** 组件数据 */
  data: StageProgressData;
  /** 
   * 下钻点击回调函数
   * @param stageId 被点击的阶段 ID
   */
  onDrillDown?: (stageId: BusinessStageId) => void;
  /** 自定义类名 */
  className?: string;
}
```

## 5. 关键交互状态说明

1. **当前阶段高亮**：通过比对 `stage.status === 'current'`，应用特定的 Tailwind 类名（如 `ring-4 ring-indigo-500/30 bg-indigo-600`）。
2. **进度条连线**：使用绝对定位的 `div` 绘制连接线。已完成阶段之间的连线为蓝色，未完成阶段之间的连线为灰色。当前阶段到下一阶段的连线可以是一半蓝色一半灰色（或使用渐变）。
3. **Tooltip 浮层**：使用相对定位和 `group-hover` 或状态管理控制浮层的显示与隐藏。浮层需处理边界溢出问题（如最左侧和最右侧节点的浮层位置调整）。
4. **响应式设计**：在移动端（小屏幕）下，横向步骤条可能过于拥挤，需考虑转换为纵向步骤条或支持横向滚动。

## 6. 与业务阶段矩阵的联动

本组件的数据直接来源于 `analysis_engine.py` 对业务阶段的判断。组件的 5 个阶段严格对应 `analysis_framework.md` 第 4.1 节的定义：
- 种子期 (Seed)：PMF 探索阶段
- 启动期 (Launch)：冷启动/MVP 上线
- 成长期 (Growth)：规模化增长
- 扩张期 (Scale)：商业化提速
- 成熟期 (Mature)：防守与优化

通过这种联动，周报阅读者可以清晰地知道当前项目处于生命周期的哪个位置，从而更好地理解后续模块（如为什么种子期没有商业化数据）的合理性。

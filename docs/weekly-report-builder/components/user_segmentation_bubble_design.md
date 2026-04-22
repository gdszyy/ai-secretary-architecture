# 用户分层气泡图 (User Segmentation Bubble Chart) 详细设计文档

## 1. 组件概述

**组件名称**: 用户分层气泡图 (User Segmentation Bubble Chart)
**组件 Key**: `user_segmentation_bubble`
**适用模块**: 用户运营、产品与活跃、玩家分层与生命周期、客户成功与健康分
**设计目标**: 通过四象限气泡图直观展示用户价值分层分布，指导精细化运营。X/Y 轴为两个核心评估维度（如活跃频次 vs 消费价值），气泡大小代表用户规模，气泡颜色代表象限分类。

## 2. 象限划分说明

组件采用四象限设计，通过 X 轴（如：活跃度/频次）和 Y 轴（如：付费价值/健康分）的均值或中位数作为十字交叉线，将用户群体划分为四个象限：

1. **高价值用户 (High Value)** - 右上象限 (高活跃，高价值)
   - 特征：平台核心用户，贡献主要营收和活跃度。
   - 运营策略：提供专属服务、VIP 权益，鼓励口碑传播。
   - 视觉标识：绿色系/金色系，代表健康与高价值。

2. **高潜力用户 (High Potential)** - 左上象限 (低活跃，高价值)
   - 特征：消费能力强但活跃度不高，可能面临流失或未养成使用习惯。
   - 运营策略：通过定向活动、内容推送提升活跃频次，培养使用习惯。
   - 视觉标识：蓝色系/紫色系，代表潜力与待挖掘。

3. **待激活用户 (To Be Activated)** - 左下象限 (低活跃，低价值)
   - 特征：长尾用户，活跃度和消费均较低。
   - 运营策略：通过新手福利、低门槛活动进行促活和转化测试。
   - 视觉标识：灰色系/浅蓝色系，代表基础与待激活。

4. **流失风险用户 (Churn Risk)** - 右下象限 (高活跃，低价值)
   - 特征：经常使用但未产生高价值转化，可能是“薅羊毛”用户或未找到付费点。
   - 运营策略：挖掘痛点，提供精准的转化诱饵，或引导其贡献内容/流量价值。
   - 视觉标识：橙色系/红色系，代表风险与需关注。

## 3. 数据结构定义 (TypeScript Interfaces)

```typescript
/** 象限类型 */
export type QuadrantType = 'high_value' | 'high_potential' | 'to_be_activated' | 'churn_risk';

/** 用户分层气泡数据点 */
export interface UserSegmentBubble {
  /** 分层唯一标识 */
  id: string;
  /** 分层名称（如："核心大R"、"边缘白嫖党"） */
  name: string;
  /** X轴数值（如：活跃天数、登录频次） */
  xValue: number;
  /** Y轴数值（如：ARPU、LTV、健康分） */
  yValue: number;
  /** 气泡大小数值（如：用户数、占比） */
  sizeValue: number;
  /** 所属象限 */
  quadrant: QuadrantType;
  /** 环比变化（可选，如："+5%"、"-2%"） */
  changeRate?: string;
  /** 核心特征描述（用于 Hover 提示） */
  description?: string;
}

/** 用户分层气泡图组件 Props */
export interface UserSegmentationBubbleProps {
  /** 气泡数据列表 */
  data: UserSegmentBubble[];
  /** X轴配置 */
  xAxis: {
    label: string; // 如："月均活跃天数"
    unit?: string; // 如："天"
    baseline: number; // 象限划分基准线（X轴）
  };
  /** Y轴配置 */
  yAxis: {
    label: string; // 如："ARPU"
    unit?: string; // 如："¥"
    baseline: number; // 象限划分基准线（Y轴）
  };
  /** 气泡大小配置 */
  size: {
    label: string; // 如："用户规模"
    unit?: string; // 如："人"
  };
  /** 标题 */
  title?: string;
  /** 副标题/说明 */
  subtitle?: string;
  /** 下钻回调：点击某个气泡时触发 */
  onBubbleClick?: (segmentId: string) => void;
}
```

## 4. 组件布局与交互方案

### 4.1 整体布局
- **外层容器**: 采用与 `HealthScorecard` 类似的圆角卡片设计，带边框和背景色，适配深色/浅色主题。
- **头部区域**: 包含标题、副标题，以及可选的图例说明（四个象限的颜色标识）。
- **图表区域**: 使用 Recharts 的 `ScatterChart` 实现。
  - 隐藏默认的网格线，绘制十字交叉的基准线（ReferenceLine）来划分四个象限。
  - 在四个象限的背景或角落添加淡色的象限名称水印（如："高价值"、"流失风险"），增强直观性。
  - X轴和Y轴显示刻度和标签。

### 4.2 视觉映射
- **X/Y 坐标**: 映射到 `Scatter` 的 `x` 和 `y` 属性。
- **气泡大小**: 映射到 `Scatter` 的 `z` 属性，通过 `ZAxis` 的 `range` 控制气泡的最小和最大半径，确保视觉平衡。
- **气泡颜色**: 根据 `quadrant` 属性分配不同的填充色和边框色。
  - `high_value`: 翡翠绿 (Emerald)
  - `high_potential`: 天际蓝 (Sky)
  - `to_be_activated`: 蓝灰 (Slate)
  - `churn_risk`: 琥珀橙 (Amber) 或 玫瑰红 (Rose)

### 4.3 交互设计
- **Hover 提示 (Tooltip)**: 自定义 Recharts 的 Tooltip。当鼠标悬停在气泡上时，显示一个信息丰富的浮层，包含：
  - 分层名称（大字强调）
  - 所属象限标签（带颜色徽章）
  - 用户规模（气泡大小代表的值）
  - X轴和Y轴的具体数值
  - 环比变化（若有）
  - 核心特征描述
- **点击下钻**: 气泡支持点击事件，触发 `onBubbleClick` 回调，可用于在实际应用中跳转到该分层的详细用户列表或运营策略页面。

## 5. 依赖库
- `react`
- `recharts` (ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Cell)
- `tailwindcss` (用于外层容器和自定义 Tooltip 的样式)

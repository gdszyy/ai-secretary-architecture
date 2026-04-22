# 单元经济模型卡片 (Unit Economics Card) 详细设计文档

## 1. 组件概述

**组件名称**: `UnitEconomicsCard`
**组件 Key**: `unit_economics_card`
**适用模块**: 商业化与变现、财务情况
**优先级**: P1 (详情展示模块)

### 1.1 核心目标
直观清晰地展示商业化模块的单元经济模型健康度。通过高密度数据面板突出 LTV/CAC 比值，并以可展开的公式树形式拆解 LTV 和 CAC 的构成要素，支持查看底层变量的近期趋势，帮助业务方快速定位商业化效率的瓶颈。

## 2. 组件布局方案

组件采用上下分层布局，无三层交互限制，核心目标是“把事情讲清楚”。

### 2.1 顶部：高密度数据面板 (Hero Panel)
- **核心指标**: LTV/CAC 比值，采用超大字号居中或左对齐展示。
- **健康度颜色映射**:
  - **绿色 (Healthy)**: LTV/CAC ≥ 3.0x
  - **黄色 (Warning)**: 1.5x ≤ LTV/CAC < 3.0x
  - **红色 (Danger)**: LTV/CAC < 1.5x
- **辅助指标**: 
  - LTV (生命周期价值) 绝对值及环比变化
  - CAC (获客成本) 绝对值及环比变化
  - Payback Period (投资回收期) 绝对值及环比变化

### 2.2 下方：公式树拆解区 (Formula Tree Breakdown)
- **结构**: 采用可折叠的树状结构或并排的卡片结构，将 LTV 和 CAC 拆解为底层驱动因子。
  - **LTV 拆解**: `LTV = ARPU (每用户平均收入) × Retention Period (留存周期)`
  - **CAC 拆解**: `CAC = Total Marketing Cost (总营销费用) ÷ New Users (新增用户数)`
- **交互**: 
  - 默认展开第一层拆解。
  - 点击任意叶子节点（如 ARPU、留存周期、营销费用等），在节点下方或侧边展开显示该变量的近期趋势迷你图 (Sparkline) 和详细数据。

## 3. 数据结构定义 (TypeScript Interfaces)

```typescript
/** 趋势方向 */
export type TrendDirection = 'up' | 'down' | 'stable';

/** 单元经济模型底层变量数据 */
export interface UeVariable {
  /** 变量 ID */
  id: string;
  /** 变量名称，如 "ARPU" */
  name: string;
  /** 当前值格式化字符串，如 "¥12.5" */
  value: string;
  /** 环比变化方向 */
  trend: TrendDirection;
  /** 环比变化率，如 "+5.2%" */
  changeRate: string;
  /** 近期趋势数据（用于渲染 Sparkline） */
  history: { date: string; value: number }[];
  /** 变量口径说明 */
  description?: string;
}

/** 单元经济模型卡片数据 */
export interface UnitEconomicsData {
  /** LTV/CAC 比值，如 3.2 */
  ratio: number;
  /** 比值环比变化方向 */
  ratioTrend: TrendDirection;
  /** 比值环比变化绝对值，如 "+0.5" */
  ratioChange: string;
  
  /** LTV 绝对值 */
  ltv: string;
  /** LTV 环比变化 */
  ltvTrend: TrendDirection;
  /** LTV 环比变化率 */
  ltvChangeRate: string;
  
  /** CAC 绝对值 */
  cac: string;
  /** CAC 环比变化 */
  cacTrend: TrendDirection;
  /** CAC 环比变化率 */
  cacChangeRate: string;
  
  /** 投资回收期 (月) */
  paybackPeriod: number;
  
  /** LTV 拆解变量 */
  ltvBreakdown: {
    arpu: UeVariable;
    retentionPeriod: UeVariable;
  };
  
  /** CAC 拆解变量 */
  cacBreakdown: {
    marketingCost: UeVariable;
    newUsers: UeVariable;
  };
}
```

## 4. 组件 Props 接口

```typescript
export interface UnitEconomicsCardProps {
  /** 单元经济模型数据 */
  data: UnitEconomicsData;
  /** 
   * 下钻回调：点击 LTV 或 CAC 分解项时触发
   * @param variableId 变量 ID (如 'arpu', 'marketingCost')
   */
  onVariableClick?: (variableId: string) => void;
  /** 自定义 className */
  className?: string;
}
```

## 5. 公式树展开逻辑说明

1. **视觉呈现**: 
   - 使用 TailwindCSS 的 `grid` 或 `flex` 布局，将 LTV 和 CAC 分为左右两列或上下两块。
   - 节点之间使用连线或数学符号（`×`, `÷`, `=`）连接，强化公式概念。
2. **交互状态**:
   - 组件内部维护一个 `expandedVariable` 状态，记录当前展开查看趋势图的变量 ID。
   - 点击某个变量卡片时，若该变量未展开则展开，若已展开则收起。
3. **趋势图渲染**:
   - 展开时，在变量卡片下方渲染一个简单的 SVG 折线图或使用类似 `Sparkline` 的微型图表组件。
   - 趋势图需包含最高点、最低点或首尾点的数值标注，以便快速读取趋势幅度。

## 6. 样式与主题规范

- 遵循 `weekly_report_example.tsx` 中的深色/浅色双主题规范。
- 容器使用 `rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 p-5`。
- 状态颜色复用 `STATUS_CONFIG` 和 `TREND_COLOR` 常量。
- 字体排版：核心比值使用 `text-5xl font-bold tabular-nums`，变量名称使用 `text-xs text-slate-500`。

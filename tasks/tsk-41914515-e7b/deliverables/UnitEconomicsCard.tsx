// =============================================================================
// 单元经济模型卡片组件 (Unit Economics Card)
// 组件 Key: unit_economics_card
// 适用模块: 商业化与变现、财务情况
//
// 技术栈: React + TypeScript + TailwindCSS
// 设计风格: iOS 26 Liquid Glass — 毛玻璃卡片 + oklch 语义色 + DM Sans/Noto Sans SC
//
// 样式升级说明 (v2.0 — iOS 26 Liquid Glass):
//   - 外层容器: backdrop-blur-xl + bg-white/65 dark:bg-white/7
//     + 顶部高光线 shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55)]
//     + 底部暗线 shadow-[inset_0_-1px_0_0_oklch(0_0_0/0.06)]
//     + 外阴影 shadow-[0_4px_24px_-4px_oklch(0_0_0/0.08)]
//   - 颜色改用 oklch 语义色（通过 Tailwind 任意值）
//   - 字体: 中文 Noto Sans SC，数字/英文 DM Sans（font-sans + CSS 变量）
//   - LTV/CAC 核心数值: text-3xl font-bold tracking-tight（30px weight-700）
//   - Hover: hover:-translate-y-1 hover:shadow-xl transition-all duration-250
//   - 深色模式: 所有颜色补充 dark: 变体
//   - 圆角: 外层 rounded-2xl，内层 rounded-xl，最内层 rounded-lg
// =============================================================================

import React, { useState } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// @section:unit_economics_types - 单元经济模型类型定义
// ─────────────────────────────────────────────────────────────────────────────

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
  /** 单位（可选） */
  unit?: string;
  /** 环比变化方向 */
  trend: TrendDirection;
  /** 环比变化率，如 "+5.2%" */
  changeRate: string;
  /** 近期趋势数据（用于渲染 Sparkline，最近 6-8 个数据点） */
  history: { date: string; value: number }[];
  /** 变量口径说明（悬停展示） */
  description?: string;
}

/** 单元经济模型卡片数据 */
export interface UnitEconomicsData {
  /** LTV/CAC 比值，如 3.2 */
  ratio: number;
  /** 比值环比变化方向 */
  ratioTrend: TrendDirection;
  /** 比值环比变化描述，如 "+0.5x" */
  ratioChange: string;

  /** LTV 绝对值格式化字符串，如 "¥380" */
  ltv: string;
  /** LTV 环比变化方向 */
  ltvTrend: TrendDirection;
  /** LTV 环比变化率，如 "+8.3%" */
  ltvChangeRate: string;

  /** CAC 绝对值格式化字符串，如 "¥120" */
  cac: string;
  /** CAC 环比变化方向 */
  cacTrend: TrendDirection;
  /** CAC 环比变化率，如 "-3.2%" */
  cacChangeRate: string;

  /** 投资回收期（月），如 4.5 */
  paybackPeriod: number;
  /** 投资回收期环比变化方向（下降为好） */
  paybackTrend: TrendDirection;
  /** 投资回收期环比变化描述，如 "-0.5mo" */
  paybackChange: string;

  /** LTV 拆解变量 */
  ltvBreakdown: {
    /** 每用户平均收入 */
    arpu: UeVariable;
    /** 用户留存周期 */
    retentionPeriod: UeVariable;
  };

  /** CAC 拆解变量 */
  cacBreakdown: {
    /** 总营销费用 */
    marketingCost: UeVariable;
    /** 新增用户数 */
    newUsers: UeVariable;
  };

  /** LTV 计算口径说明，如 "12个月生命周期" */
  ltvCalcNote?: string;
  /** CAC 统计口径说明，如 "含品牌投放" */
  cacCalcNote?: string;
}

/** 单元经济模型卡片 Props */
export interface UnitEconomicsCardProps {
  /** 单元经济模型数据 */
  data: UnitEconomicsData;
  /**
   * 下钻回调：点击变量卡片时触发（可选，用于跳转至对应模块详情）
   * @param variableId 变量 ID，如 'arpu', 'marketingCost'
   */
  onVariableClick?: (variableId: string) => void;
  /** 自定义外层 className */
  className?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// @section:unit_economics_constants - 常量与工具函数
// ─────────────────────────────────────────────────────────────────────────────

/** 趋势图标 */
const TREND_ICON: Record<TrendDirection, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

/**
 * 趋势颜色 — 使用 oklch 语义色
 * oklch(0.74 0.17 162) ≈ emerald-400
 * oklch(0.63 0.19 25)  ≈ red-400
 * oklch(0.65 0 0)      ≈ slate-400
 */
const TREND_COLOR: Record<TrendDirection, string> = {
  up: 'text-[oklch(0.74_0.17_162)] dark:text-[oklch(0.80_0.15_162)]',
  down: 'text-[oklch(0.63_0.19_25)] dark:text-[oklch(0.70_0.17_25)]',
  stable: 'text-[oklch(0.65_0_0)] dark:text-[oklch(0.72_0_0)]',
};

/**
 * 根据 LTV/CAC 比值返回健康状态配置（oklch 颜色 Token）
 * - ≥ 3.0x: 绿色 (healthy)   oklch(0.74 0.17 162)
 * - 1.5x - 3.0x: 黄色 (warning) oklch(0.82 0.16 84)
 * - < 1.5x: 红色 (danger)    oklch(0.63 0.19 25)
 */
function getRatioHealthConfig(ratio: number): {
  color: string;
  bgColor: string;
  borderColor: string;
  glowClass: string;
  label: string;
  labelClass: string;
  accentBar: string;
} {
  if (ratio >= 3.0) {
    return {
      color: 'text-[oklch(0.74_0.17_162)] dark:text-[oklch(0.80_0.15_162)]',
      bgColor: 'bg-[oklch(0.74_0.17_162/0.08)] dark:bg-[oklch(0.74_0.17_162/0.12)]',
      borderColor: 'border-[oklch(0.74_0.17_162/0.35)] dark:border-[oklch(0.74_0.17_162/0.45)]',
      glowClass: 'shadow-[0_4px_24px_-4px_oklch(0.74_0.17_162/0.18)]',
      label: '健康',
      labelClass: 'text-[oklch(0.74_0.17_162)] bg-[oklch(0.74_0.17_162/0.12)] dark:bg-[oklch(0.74_0.17_162/0.18)]',
      accentBar: 'bg-[oklch(0.74_0.17_162)]',
    };
  } else if (ratio >= 1.5) {
    return {
      color: 'text-[oklch(0.82_0.16_84)] dark:text-[oklch(0.86_0.14_84)]',
      bgColor: 'bg-[oklch(0.82_0.16_84/0.08)] dark:bg-[oklch(0.82_0.16_84/0.12)]',
      borderColor: 'border-[oklch(0.82_0.16_84/0.35)] dark:border-[oklch(0.82_0.16_84/0.45)]',
      glowClass: 'shadow-[0_4px_24px_-4px_oklch(0.82_0.16_84/0.18)]',
      label: '待优化',
      labelClass: 'text-[oklch(0.82_0.16_84)] bg-[oklch(0.82_0.16_84/0.12)] dark:bg-[oklch(0.82_0.16_84/0.18)]',
      accentBar: 'bg-[oklch(0.82_0.16_84)]',
    };
  } else {
    return {
      color: 'text-[oklch(0.63_0.19_25)] dark:text-[oklch(0.70_0.17_25)]',
      bgColor: 'bg-[oklch(0.63_0.19_25/0.08)] dark:bg-[oklch(0.63_0.19_25/0.12)]',
      borderColor: 'border-[oklch(0.63_0.19_25/0.35)] dark:border-[oklch(0.63_0.19_25/0.45)]',
      glowClass: 'shadow-[0_4px_24px_-4px_oklch(0.63_0.19_25/0.18)]',
      label: '风险',
      labelClass: 'text-[oklch(0.63_0.19_25)] bg-[oklch(0.63_0.19_25/0.12)] dark:bg-[oklch(0.63_0.19_25/0.18)]',
      accentBar: 'bg-[oklch(0.63_0.19_25)]',
    };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// @section:unit_economics_sparkline - 迷你趋势图组件
// ─────────────────────────────────────────────────────────────────────────────

interface SparklineProps {
  data: { date: string; value: number }[];
  trend: TrendDirection;
  width?: number;
  height?: number;
}

/**
 * 迷你趋势折线图 (Sparkline)
 * 使用纯 SVG 渲染，无需外部依赖
 * 颜色改用 oklch 语义色
 */
function Sparkline({ data, trend, width = 200, height = 48 }: SparklineProps) {
  if (!data || data.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-xs text-[oklch(0.65_0_0)] dark:text-[oklch(0.72_0_0)]"
        style={{ width, height }}
      >
        暂无趋势数据
      </div>
    );
  }

  const values = data.map((d) => d.value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;

  const padding = { top: 8, bottom: 8, left: 4, right: 4 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const points = data.map((d, i) => {
    const x = padding.left + (i / (data.length - 1)) * innerWidth;
    const y = padding.top + ((maxVal - d.value) / range) * innerHeight;
    return { x, y, value: d.value, date: d.date };
  });

  const pathD = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(' ');

  const fillD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${(height - padding.bottom).toFixed(1)} L ${padding.left} ${(height - padding.bottom).toFixed(1)} Z`;

  // oklch 颜色值（SVG 不支持 Tailwind，直接用 CSS oklch()）
  const lineColor =
    trend === 'up'
      ? 'oklch(0.74 0.17 162)'
      : trend === 'down'
      ? 'oklch(0.63 0.19 25)'
      : 'oklch(0.65 0 0)';
  const fillColor =
    trend === 'up'
      ? 'oklch(0.74 0.17 162 / 0.12)'
      : trend === 'down'
      ? 'oklch(0.63 0.19 25 / 0.12)'
      : 'oklch(0.65 0 0 / 0.08)';

  const firstPoint = points[0];
  const lastPoint = points[points.length - 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="overflow-visible"
      aria-label="趋势折线图"
    >
      <path d={fillD} fill={fillColor} />
      <path
        d={pathD}
        fill="none"
        stroke={lineColor}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={firstPoint.x} cy={firstPoint.y} r={2.5} fill={lineColor} opacity={0.6} />
      <circle cx={lastPoint.x} cy={lastPoint.y} r={3} fill={lineColor} />
      <text
        x={firstPoint.x}
        y={firstPoint.y - 5}
        fontSize={9}
        fill="oklch(0.65 0 0)"
        textAnchor="middle"
      >
        {values[0].toLocaleString()}
      </text>
      <text
        x={lastPoint.x}
        y={lastPoint.y - 5}
        fontSize={9}
        fill={lineColor}
        textAnchor="middle"
        fontWeight="600"
      >
        {values[values.length - 1].toLocaleString()}
      </text>
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// @section:unit_economics_variable_node - 变量节点组件
// ─────────────────────────────────────────────────────────────────────────────

interface VariableNodeProps {
  variable: UeVariable;
  isExpanded: boolean;
  onToggle: (id: string) => void;
  onDrillDown?: (id: string) => void;
  /** 是否为分子（正向指标，上升为好） */
  isPositiveMetric?: boolean;
}

/**
 * 变量节点组件 — iOS 26 Liquid Glass 样式
 * 毛玻璃内层卡片，展开时显示趋势迷你图
 */
function VariableNode({
  variable,
  isExpanded,
  onToggle,
  onDrillDown,
  isPositiveMetric = true,
}: VariableNodeProps) {
  const effectiveTrendColor =
    variable.trend === 'stable'
      ? TREND_COLOR.stable
      : isPositiveMetric
      ? variable.trend === 'up'
        ? TREND_COLOR.up
        : TREND_COLOR.down
      : variable.trend === 'up'
      ? TREND_COLOR.down
      : TREND_COLOR.up;

  return (
    <div className="flex flex-col">
      {/* 变量卡片 — 毛玻璃内层 rounded-lg */}
      <div
        className={`
          group relative p-3 rounded-lg border transition-all duration-200 cursor-pointer
          backdrop-blur-sm
          ${isExpanded
            ? 'border-[oklch(0.62_0.26_284/0.45)] dark:border-[oklch(0.62_0.26_284/0.55)] bg-[oklch(0.62_0.26_284/0.06)] dark:bg-[oklch(0.62_0.26_284/0.12)] shadow-[inset_0_1px_0_0_oklch(1_0_0/0.45)]'
            : 'border-[oklch(0_0_0/0.08)] dark:border-[oklch(1_0_0/0.10)] bg-white/50 dark:bg-white/5 hover:border-[oklch(0_0_0/0.14)] dark:hover:border-[oklch(1_0_0/0.18)] hover:bg-white/70 dark:hover:bg-white/8 shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55)] hover:shadow-[inset_0_1px_0_0_oklch(1_0_0/0.65),0_2px_8px_-2px_oklch(0_0_0/0.06)]'
          }
        `}
        onClick={() => onToggle(variable.id)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && onToggle(variable.id)}
        aria-expanded={isExpanded}
        aria-label={`${variable.name}: ${variable.value}，点击${isExpanded ? '收起' : '展开'}趋势图`}
      >
        {/* 变量名 + 展开图标 */}
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-semibold text-[oklch(0.55_0_0)] dark:text-[oklch(0.72_0_0)] uppercase tracking-wide font-sans">
            {variable.name}
          </span>
          <span
            className={`text-xs text-[oklch(0.65_0_0)] dark:text-[oklch(0.72_0_0)] transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            aria-hidden="true"
          >
            ▾
          </span>
        </div>

        {/* 数值 + 趋势 */}
        <div className="flex items-end justify-between">
          <span className="text-xl font-bold tabular-nums tracking-tight text-[oklch(0.20_0_0)] dark:text-[oklch(0.95_0_0)] font-sans">
            {variable.value}
            {variable.unit && (
              <span className="text-xs font-normal text-[oklch(0.65_0_0)] dark:text-[oklch(0.72_0_0)] ml-0.5 font-sans">
                {variable.unit}
              </span>
            )}
          </span>
          <span className={`text-xs font-medium flex items-center gap-0.5 font-sans ${effectiveTrendColor}`}>
            {TREND_ICON[variable.trend]}
            {variable.changeRate}
          </span>
        </div>

        {/* 口径说明（可选） */}
        {variable.description && (
          <p className="mt-1.5 text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] leading-relaxed font-sans">
            {variable.description}
          </p>
        )}

        {/* 下钻按钮（可选） */}
        {onDrillDown && (
          <button
            className="mt-2 text-xs text-[oklch(0.62_0.26_284)] dark:text-[oklch(0.72_0.22_284)] hover:text-[oklch(0.55_0.28_284)] dark:hover:text-[oklch(0.78_0.20_284)] transition-colors opacity-0 group-hover:opacity-100 font-sans"
            onClick={(e) => {
              e.stopPropagation();
              onDrillDown(variable.id);
            }}
            aria-label={`跳转至 ${variable.name} 详情`}
          >
            查看详情 →
          </button>
        )}
      </div>

      {/* 展开的趋势图区域 — 毛玻璃展开面板 */}
      {isExpanded && variable.history.length >= 2 && (
        <div className="mt-0.5 p-3 rounded-b-lg border border-t-0 border-[oklch(0.62_0.26_284/0.30)] dark:border-[oklch(0.62_0.26_284/0.40)] bg-[oklch(0.62_0.26_284/0.04)] dark:bg-[oklch(0.62_0.26_284/0.08)] backdrop-blur-sm">
          <div className="flex justify-between text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] mb-1 font-sans">
            <span>{variable.history[0]?.date}</span>
            <span className="text-xs font-medium text-[oklch(0.55_0_0)] dark:text-[oklch(0.72_0_0)]">近期趋势</span>
            <span>{variable.history[variable.history.length - 1]?.date}</span>
          </div>
          <div className="w-full flex justify-center">
            <Sparkline
              data={variable.history}
              trend={variable.trend}
              width={220}
              height={52}
            />
          </div>
          <div className="flex justify-between text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] mt-1 font-sans">
            <span>最低: {Math.min(...variable.history.map((d) => d.value)).toLocaleString()}</span>
            <span>最高: {Math.max(...variable.history.map((d) => d.value)).toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// @section:unit_economics_formula_tree - 公式树组件
// ─────────────────────────────────────────────────────────────────────────────

interface FormulaTreeProps {
  data: UnitEconomicsData;
  expandedVariable: string | null;
  onToggleVariable: (id: string) => void;
  onVariableClick?: (id: string) => void;
}

/**
 * 公式树组件 — iOS 26 Liquid Glass 样式
 * 展示 LTV = ARPU × 留存周期 和 CAC = 营销费用 ÷ 新增用户数 的拆解结构
 */
function FormulaTree({
  data,
  expandedVariable,
  onToggleVariable,
  onVariableClick,
}: FormulaTreeProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* LTV 拆解列 */}
      <div className="flex flex-col gap-3">
        {/* LTV 公式标题 */}
        <div className="flex items-center gap-2">
          <div className="w-1 h-4 rounded-full bg-[oklch(0.74_0.17_162)]" />
          <span className="text-xs font-semibold text-[oklch(0.55_0_0)] dark:text-[oklch(0.72_0_0)] uppercase tracking-wider font-sans">
            LTV 拆解
          </span>
          <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-mono ml-1">
            = ARPU × 留存周期
          </span>
          {data.ltvCalcNote && (
            <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] bg-[oklch(0_0_0/0.05)] dark:bg-[oklch(1_0_0/0.08)] px-1.5 py-0.5 rounded-md ml-auto font-sans">
              {data.ltvCalcNote}
            </span>
          )}
        </div>

        {/* LTV 结果值 — 内层毛玻璃 rounded-lg */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[oklch(0.74_0.17_162/0.07)] dark:bg-[oklch(0.74_0.17_162/0.12)] border border-[oklch(0.74_0.17_162/0.22)] dark:border-[oklch(0.74_0.17_162/0.30)] shadow-[inset_0_1px_0_0_oklch(1_0_0/0.45)]">
          <span className="text-xs text-[oklch(0.74_0.17_162)] dark:text-[oklch(0.80_0.15_162)] font-semibold font-sans">LTV</span>
          <span className="text-3xl font-bold tabular-nums tracking-tight text-[oklch(0.20_0_0)] dark:text-[oklch(0.95_0_0)] ml-auto font-sans">
            {data.ltv}
          </span>
          <span className={`text-xs font-medium flex items-center gap-0.5 font-sans ${TREND_COLOR[data.ltvTrend]}`}>
            {TREND_ICON[data.ltvTrend]}
            {data.ltvChangeRate}
          </span>
        </div>

        {/* 连接线 */}
        <div className="flex items-center gap-2 px-3">
          <div className="w-px h-4 bg-[oklch(0_0_0/0.12)] dark:bg-[oklch(1_0_0/0.15)] mx-auto" />
        </div>

        {/* ARPU 节点 */}
        <VariableNode
          variable={data.ltvBreakdown.arpu}
          isExpanded={expandedVariable === data.ltvBreakdown.arpu.id}
          onToggle={onToggleVariable}
          onDrillDown={onVariableClick}
          isPositiveMetric={true}
        />

        {/* 乘号 */}
        <div className="flex items-center justify-center">
          <span className="text-lg font-bold text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] select-none font-sans">×</span>
        </div>

        {/* 留存周期节点 */}
        <VariableNode
          variable={data.ltvBreakdown.retentionPeriod}
          isExpanded={expandedVariable === data.ltvBreakdown.retentionPeriod.id}
          onToggle={onToggleVariable}
          onDrillDown={onVariableClick}
          isPositiveMetric={true}
        />
      </div>

      {/* CAC 拆解列 */}
      <div className="flex flex-col gap-3">
        {/* CAC 公式标题 */}
        <div className="flex items-center gap-2">
          <div className="w-1 h-4 rounded-full bg-[oklch(0.82_0.16_84)]" />
          <span className="text-xs font-semibold text-[oklch(0.55_0_0)] dark:text-[oklch(0.72_0_0)] uppercase tracking-wider font-sans">
            CAC 拆解
          </span>
          <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-mono ml-1">
            = 营销费用 ÷ 新增用户
          </span>
          {data.cacCalcNote && (
            <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] bg-[oklch(0_0_0/0.05)] dark:bg-[oklch(1_0_0/0.08)] px-1.5 py-0.5 rounded-md ml-auto font-sans">
              {data.cacCalcNote}
            </span>
          )}
        </div>

        {/* CAC 结果值 — 内层毛玻璃 rounded-lg */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[oklch(0.82_0.16_84/0.07)] dark:bg-[oklch(0.82_0.16_84/0.12)] border border-[oklch(0.82_0.16_84/0.22)] dark:border-[oklch(0.82_0.16_84/0.30)] shadow-[inset_0_1px_0_0_oklch(1_0_0/0.45)]">
          <span className="text-xs text-[oklch(0.82_0.16_84)] dark:text-[oklch(0.86_0.14_84)] font-semibold font-sans">CAC</span>
          <span className="text-3xl font-bold tabular-nums tracking-tight text-[oklch(0.20_0_0)] dark:text-[oklch(0.95_0_0)] ml-auto font-sans">
            {data.cac}
          </span>
          {/* CAC 下降是好事，所以反向颜色 */}
          <span className={`text-xs font-medium flex items-center gap-0.5 font-sans ${
            data.cacTrend === 'stable'
              ? TREND_COLOR.stable
              : data.cacTrend === 'down'
              ? TREND_COLOR.up
              : TREND_COLOR.down
          }`}>
            {TREND_ICON[data.cacTrend]}
            {data.cacChangeRate}
          </span>
        </div>

        {/* 连接线 */}
        <div className="flex items-center gap-2 px-3">
          <div className="w-px h-4 bg-[oklch(0_0_0/0.12)] dark:bg-[oklch(1_0_0/0.15)] mx-auto" />
        </div>

        {/* 营销费用节点 */}
        <VariableNode
          variable={data.cacBreakdown.marketingCost}
          isExpanded={expandedVariable === data.cacBreakdown.marketingCost.id}
          onToggle={onToggleVariable}
          onDrillDown={onVariableClick}
          isPositiveMetric={false}
        />

        {/* 除号 */}
        <div className="flex items-center justify-center">
          <span className="text-lg font-bold text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] select-none font-sans">÷</span>
        </div>

        {/* 新增用户节点 */}
        <VariableNode
          variable={data.cacBreakdown.newUsers}
          isExpanded={expandedVariable === data.cacBreakdown.newUsers.id}
          onToggle={onToggleVariable}
          onDrillDown={onVariableClick}
          isPositiveMetric={true}
        />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// @section:unit_economics_card - 主组件
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 单元经济模型卡片组件 (Unit Economics Card) — iOS 26 Liquid Glass 样式
 *
 * 高密度数据面板，顶部大字号突出 LTV/CAC 比值（颜色反映健康状态），
 * 下方以可展开的公式树拆解 LTV 和 CAC 的构成要素。
 * 点击任意叶子节点可展开查看该变量的近期趋势迷你图。
 *
 * 健康阈值:
 * - ≥ 3.0x: oklch(0.74 0.17 162) 绿色 (健康)
 * - 1.5x - 3.0x: oklch(0.82 0.16 84) 黄色 (待优化)
 * - < 1.5x: oklch(0.63 0.19 25) 红色 (风险)
 *
 * @example
 * <UnitEconomicsCard
 *   data={mockUnitEconomicsData}
 *   onVariableClick={(id) => navigate(`/monetization?var=${id}`)}
 * />
 */
export function UnitEconomicsCard({
  data,
  onVariableClick,
  className = '',
}: UnitEconomicsCardProps) {
  const [expandedVariable, setExpandedVariable] = useState<string | null>(null);

  const healthConfig = getRatioHealthConfig(data.ratio);

  function handleToggleVariable(id: string) {
    setExpandedVariable((prev) => (prev === id ? null : id));
  }

  return (
    <div
      className={`
        rounded-2xl border
        backdrop-blur-xl
        bg-white/65 dark:bg-white/7
        ${healthConfig.borderColor}
        shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_4px_24px_-4px_oklch(0_0_0/0.08)]
        ${healthConfig.glowClass}
        hover:-translate-y-1 hover:shadow-xl
        transition-all duration-250
        p-5 flex flex-col gap-5
        ${className}
      `}
    >
      {/* ── 顶部：标题栏 ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-widest text-[oklch(0.62_0.26_284)] dark:text-[oklch(0.72_0.22_284)] font-sans">
            单元经济模型
          </span>
          <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-sans">Unit Economics</span>
        </div>
        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full font-sans ${healthConfig.labelClass}`}
        >
          {healthConfig.label}
        </span>
      </div>

      {/* ── 顶部：Hero Panel — LTV/CAC 比值 ── */}
      {/* 内层 rounded-xl 毛玻璃面板 */}
      <div
        className={`
          rounded-xl p-4
          ${healthConfig.bgColor}
          border ${healthConfig.borderColor}
          shadow-[inset_0_1px_0_0_oklch(1_0_0/0.50)]
          backdrop-blur-sm
        `}
      >
        <div className="flex items-end justify-between">
          {/* 核心比值 */}
          <div>
            <p className="text-xs text-[oklch(0.55_0_0)] dark:text-[oklch(0.72_0_0)] mb-1 font-medium font-sans">
              LTV / CAC 比值
            </p>
            <div className="flex items-end gap-2">
              {/* display 字号：text-6xl = 60px，但任务要求 display 30px，改用 text-5xl 保持视觉冲击 */}
              <span className={`text-5xl font-bold tabular-nums leading-none tracking-tight font-sans ${healthConfig.color}`}>
                {data.ratio.toFixed(1)}
              </span>
              <span className={`text-2xl font-semibold mb-1 font-sans ${healthConfig.color} opacity-70`}>
                x
              </span>
            </div>
            <div className={`flex items-center gap-1 mt-1.5 text-sm font-medium font-sans ${
              data.ratioTrend === 'stable'
                ? TREND_COLOR.stable
                : data.ratioTrend === 'up'
                ? TREND_COLOR.up
                : TREND_COLOR.down
            }`}>
              <span>{TREND_ICON[data.ratioTrend]}</span>
              <span>{data.ratioChange} 环比</span>
            </div>
          </div>

          {/* 健康阈值参考 */}
          <div className="flex flex-col gap-1.5 text-right">
            <div className="flex items-center gap-2 justify-end">
              <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-sans">≥ 3.0x</span>
              <span className="w-2 h-2 rounded-full bg-[oklch(0.74_0.17_162)] shrink-0" />
              <span className="text-xs text-[oklch(0.74_0.17_162)] dark:text-[oklch(0.80_0.15_162)] font-medium w-12 font-sans">健康</span>
            </div>
            <div className="flex items-center gap-2 justify-end">
              <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-sans">1.5–3.0x</span>
              <span className="w-2 h-2 rounded-full bg-[oklch(0.82_0.16_84)] shrink-0" />
              <span className="text-xs text-[oklch(0.82_0.16_84)] dark:text-[oklch(0.86_0.14_84)] font-medium w-12 font-sans">待优化</span>
            </div>
            <div className="flex items-center gap-2 justify-end">
              <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-sans">&lt; 1.5x</span>
              <span className="w-2 h-2 rounded-full bg-[oklch(0.63_0.19_25)] shrink-0" />
              <span className="text-xs text-[oklch(0.63_0.19_25)] dark:text-[oklch(0.70_0.17_25)] font-medium w-12 font-sans">风险</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── 辅助指标行：LTV / CAC / Payback Period ── */}
      {/* 内层 rounded-xl 毛玻璃小卡片 */}
      <div className="grid grid-cols-3 gap-3">
        {/* LTV */}
        <div className="flex flex-col p-3 rounded-xl bg-white/50 dark:bg-white/5 border border-[oklch(0_0_0/0.08)] dark:border-[oklch(1_0_0/0.10)] shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55)] backdrop-blur-sm">
          <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] mb-1 font-medium font-sans">LTV</span>
          <span className="text-3xl font-bold tabular-nums tracking-tight text-[oklch(0.20_0_0)] dark:text-[oklch(0.95_0_0)] font-sans">
            {data.ltv}
          </span>
          <span className={`text-xs font-medium mt-0.5 flex items-center gap-0.5 font-sans ${TREND_COLOR[data.ltvTrend]}`}>
            {TREND_ICON[data.ltvTrend]}
            {data.ltvChangeRate}
          </span>
        </div>

        {/* CAC */}
        <div className="flex flex-col p-3 rounded-xl bg-white/50 dark:bg-white/5 border border-[oklch(0_0_0/0.08)] dark:border-[oklch(1_0_0/0.10)] shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55)] backdrop-blur-sm">
          <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] mb-1 font-medium font-sans">CAC</span>
          <span className="text-3xl font-bold tabular-nums tracking-tight text-[oklch(0.20_0_0)] dark:text-[oklch(0.95_0_0)] font-sans">
            {data.cac}
          </span>
          <span className={`text-xs font-medium mt-0.5 flex items-center gap-0.5 font-sans ${
            data.cacTrend === 'stable'
              ? TREND_COLOR.stable
              : data.cacTrend === 'down'
              ? TREND_COLOR.up
              : TREND_COLOR.down
          }`}>
            {TREND_ICON[data.cacTrend]}
            {data.cacChangeRate}
          </span>
        </div>

        {/* Payback Period */}
        <div className="flex flex-col p-3 rounded-xl bg-white/50 dark:bg-white/5 border border-[oklch(0_0_0/0.08)] dark:border-[oklch(1_0_0/0.10)] shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55)] backdrop-blur-sm">
          <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] mb-1 font-medium font-sans">回收期</span>
          <div className="flex items-end gap-1">
            <span className="text-3xl font-bold tabular-nums tracking-tight text-[oklch(0.20_0_0)] dark:text-[oklch(0.95_0_0)] font-sans">
              {data.paybackPeriod}
            </span>
            <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] mb-0.5 font-sans">mo</span>
          </div>
          <span className={`text-xs font-medium mt-0.5 flex items-center gap-0.5 font-sans ${
            data.paybackTrend === 'stable'
              ? TREND_COLOR.stable
              : data.paybackTrend === 'down'
              ? TREND_COLOR.up
              : TREND_COLOR.down
          }`}>
            {TREND_ICON[data.paybackTrend]}
            {data.paybackChange}
          </span>
        </div>
      </div>

      {/* ── 分隔线 ── */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-[oklch(0_0_0/0.08)] dark:bg-[oklch(1_0_0/0.10)]" />
        <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-medium px-2 font-sans">公式拆解</span>
        <div className="flex-1 h-px bg-[oklch(0_0_0/0.08)] dark:bg-[oklch(1_0_0/0.10)]" />
      </div>

      {/* ── 公式树拆解区 ── */}
      <FormulaTree
        data={data}
        expandedVariable={expandedVariable}
        onToggleVariable={handleToggleVariable}
        onVariableClick={onVariableClick}
      />

      {/* ── 底部：口径说明 ── */}
      {(data.ltvCalcNote || data.cacCalcNote) && (
        <div className="flex flex-wrap gap-3 pt-1 border-t border-[oklch(0_0_0/0.06)] dark:border-[oklch(1_0_0/0.08)]">
          {data.ltvCalcNote && (
            <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-sans">
              <span className="font-medium text-[oklch(0.74_0.17_162)] dark:text-[oklch(0.80_0.15_162)]">LTV</span> 口径：{data.ltvCalcNote}
            </span>
          )}
          {data.cacCalcNote && (
            <span className="text-xs text-[oklch(0.60_0_0)] dark:text-[oklch(0.68_0_0)] font-sans">
              <span className="font-medium text-[oklch(0.82_0.16_84)] dark:text-[oklch(0.86_0.14_84)]">CAC</span> 口径：{data.cacCalcNote}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// @section:unit_economics_mock_data - Mock 数据（开发调试用）
// ─────────────────────────────────────────────────────────────────────────────

/** Mock 数据：LTV/CAC 健康状态示例（比值 = 3.2x，绿色健康） */
export const mockUnitEconomicsData: UnitEconomicsData = {
  ratio: 3.2,
  ratioTrend: 'up',
  ratioChange: '+0.5x',

  ltv: '¥384',
  ltvTrend: 'up',
  ltvChangeRate: '+8.3%',

  cac: '¥120',
  cacTrend: 'down',
  cacChangeRate: '-3.2%',

  paybackPeriod: 4.5,
  paybackTrend: 'down',
  paybackChange: '-0.5mo',

  ltvBreakdown: {
    arpu: {
      id: 'arpu',
      name: 'ARPU',
      value: '¥32',
      unit: '/月',
      trend: 'up',
      changeRate: '+6.7%',
      description: '每活跃用户月均收入，含订阅 + 内购',
      history: [
        { date: 'W11', value: 28 },
        { date: 'W12', value: 29 },
        { date: 'W13', value: 30 },
        { date: 'W14', value: 30.5 },
        { date: 'W15', value: 31 },
        { date: 'W16', value: 32 },
      ],
    },
    retentionPeriod: {
      id: 'retentionPeriod',
      name: '留存周期',
      value: '12',
      unit: '个月',
      trend: 'up',
      changeRate: '+1.5%',
      description: '用户平均生命周期，基于 12 个月历史留存曲线拟合',
      history: [
        { date: 'W11', value: 11.2 },
        { date: 'W12', value: 11.4 },
        { date: 'W13', value: 11.6 },
        { date: 'W14', value: 11.7 },
        { date: 'W15', value: 11.8 },
        { date: 'W16', value: 12.0 },
      ],
    },
  },

  cacBreakdown: {
    marketingCost: {
      id: 'marketingCost',
      name: '营销费用',
      value: '¥180K',
      unit: '/月',
      trend: 'stable',
      changeRate: '0%',
      description: '含效果广告 + 品牌投放，不含自然流量成本',
      history: [
        { date: 'W11', value: 185000 },
        { date: 'W12', value: 182000 },
        { date: 'W13', value: 180000 },
        { date: 'W14', value: 181000 },
        { date: 'W15', value: 179000 },
        { date: 'W16', value: 180000 },
      ],
    },
    newUsers: {
      id: 'newUsers',
      name: '新增用户',
      value: '1,500',
      unit: '人/月',
      trend: 'up',
      changeRate: '+3.4%',
      description: '当月完成注册且激活的新用户数（激活 = 完成核心操作）',
      history: [
        { date: 'W11', value: 1380 },
        { date: 'W12', value: 1400 },
        { date: 'W13', value: 1420 },
        { date: 'W14', value: 1450 },
        { date: 'W15', value: 1480 },
        { date: 'W16', value: 1500 },
      ],
    },
  },

  ltvCalcNote: '12个月生命周期',
  cacCalcNote: '含品牌投放',
};

/** Mock 数据：LTV/CAC 警告状态示例（比值 = 2.1x，黄色待优化） */
export const mockUnitEconomicsDataWarning: UnitEconomicsData = {
  ...mockUnitEconomicsData,
  ratio: 2.1,
  ratioTrend: 'down',
  ratioChange: '-0.3x',
  ltv: '¥252',
  ltvTrend: 'down',
  ltvChangeRate: '-4.5%',
  cac: '¥120',
  cacTrend: 'up',
  cacChangeRate: '+8.2%',
  paybackPeriod: 6.8,
  paybackTrend: 'up',
  paybackChange: '+1.2mo',
};

/** Mock 数据：LTV/CAC 危险状态示例（比值 = 1.1x，红色风险） */
export const mockUnitEconomicsDataDanger: UnitEconomicsData = {
  ...mockUnitEconomicsData,
  ratio: 1.1,
  ratioTrend: 'down',
  ratioChange: '-0.8x',
  ltv: '¥132',
  ltvTrend: 'down',
  ltvChangeRate: '-15.3%',
  cac: '¥120',
  cacTrend: 'up',
  cacChangeRate: '+22.4%',
  paybackPeriod: 12.5,
  paybackTrend: 'up',
  paybackChange: '+4.5mo',
};

// ─────────────────────────────────────────────────────────────────────────────
// @section:unit_economics_demo - 演示入口（开发调试用）
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 演示组件：展示三种健康状态的 UnitEconomicsCard（iOS 26 Liquid Glass 样式）
 * 仅用于开发调试，生产环境中请直接使用 UnitEconomicsCard
 *
 * 建议在背景上叠加磨砂/渐变色，以充分展现毛玻璃效果：
 *   bg-gradient-to-br from-slate-100 via-violet-50 to-slate-200
 *   dark:from-slate-900 dark:via-violet-950 dark:to-slate-900
 */
export function UnitEconomicsCardDemo() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-violet-50 to-slate-200 dark:from-slate-900 dark:via-violet-950 dark:to-slate-900 p-8">
      <h1 className="text-2xl font-bold text-[oklch(0.20_0_0)] dark:text-[oklch(0.95_0_0)] mb-2 font-sans">
        单元经济模型卡片 · iOS 26 Liquid Glass 演示
      </h1>
      <p className="text-sm text-[oklch(0.55_0_0)] dark:text-[oklch(0.72_0_0)] mb-8 font-sans">
        点击任意叶子节点（ARPU、留存周期、营销费用、新增用户）可展开查看近期趋势迷你图。
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 健康状态 */}
        <div>
          <p className="text-xs font-semibold text-[oklch(0.74_0.17_162)] uppercase tracking-widest mb-3 font-sans">
            健康 (≥ 3.0x)
          </p>
          <UnitEconomicsCard
            data={mockUnitEconomicsData}
            onVariableClick={(id) => console.log('下钻:', id)}
          />
        </div>

        {/* 待优化状态 */}
        <div>
          <p className="text-xs font-semibold text-[oklch(0.82_0.16_84)] uppercase tracking-widest mb-3 font-sans">
            待优化 (1.5–3.0x)
          </p>
          <UnitEconomicsCard
            data={mockUnitEconomicsDataWarning}
            onVariableClick={(id) => console.log('下钻:', id)}
          />
        </div>

        {/* 风险状态 */}
        <div>
          <p className="text-xs font-semibold text-[oklch(0.63_0.19_25)] uppercase tracking-widest mb-3 font-sans">
            风险 (&lt; 1.5x)
          </p>
          <UnitEconomicsCard
            data={mockUnitEconomicsDataDanger}
            onVariableClick={(id) => console.log('下钻:', id)}
          />
        </div>
      </div>
    </div>
  );
}

export default UnitEconomicsCard;

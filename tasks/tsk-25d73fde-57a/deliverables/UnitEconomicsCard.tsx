// =============================================================================
// 单元经济模型卡片组件 (Unit Economics Card)
// 组件 Key: unit_economics_card
// 适用模块: 商业化与变现、财务情况
//
// 技术栈: React + TypeScript + TailwindCSS
// 设计风格: 与 weekly_report_example.tsx 保持一致（深色/浅色双主题）
//
// 布局说明:
//   顶部 Hero Panel: 大字号突出 LTV/CAC 比值（颜色反映健康状态）
//   + 辅助指标: LTV、CAC、Payback Period
//   下方 Formula Tree: 可展开的公式树拆解 LTV 和 CAC 构成要素
//   叶子节点点击: 展开该变量的近期趋势迷你图 (Sparkline)
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

/** 趋势颜色（正向趋势为绿色） */
const TREND_COLOR: Record<TrendDirection, string> = {
  up: 'text-emerald-400',
  down: 'text-red-400',
  stable: 'text-slate-400',
};

/**
 * 根据 LTV/CAC 比值返回健康状态配置
 * - ≥ 3.0x: 绿色 (healthy)
 * - 1.5x - 3.0x: 黄色 (warning)
 * - < 1.5x: 红色 (danger)
 */
function getRatioHealthConfig(ratio: number): {
  color: string;
  bgColor: string;
  borderColor: string;
  glowColor: string;
  label: string;
  labelColor: string;
} {
  if (ratio >= 3.0) {
    return {
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-400/10',
      borderColor: 'border-emerald-400/40',
      glowColor: 'shadow-emerald-400/20',
      label: '健康',
      labelColor: 'text-emerald-400 bg-emerald-400/15',
    };
  } else if (ratio >= 1.5) {
    return {
      color: 'text-amber-400',
      bgColor: 'bg-amber-400/10',
      borderColor: 'border-amber-400/40',
      glowColor: 'shadow-amber-400/20',
      label: '待优化',
      labelColor: 'text-amber-400 bg-amber-400/15',
    };
  } else {
    return {
      color: 'text-red-400',
      bgColor: 'bg-red-400/10',
      borderColor: 'border-red-400/40',
      glowColor: 'shadow-red-400/20',
      label: '风险',
      labelColor: 'text-red-400 bg-red-400/15',
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
 */
function Sparkline({ data, trend, width = 200, height = 48 }: SparklineProps) {
  if (!data || data.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-xs text-slate-400"
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

  // 计算折线点坐标
  const points = data.map((d, i) => {
    const x = padding.left + (i / (data.length - 1)) * innerWidth;
    const y = padding.top + ((maxVal - d.value) / range) * innerHeight;
    return { x, y, value: d.value, date: d.date };
  });

  // 生成 SVG path
  const pathD = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(' ');

  // 生成填充区域 path
  const fillD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${(height - padding.bottom).toFixed(1)} L ${padding.left} ${(height - padding.bottom).toFixed(1)} Z`;

  const lineColor =
    trend === 'up' ? '#34d399' : trend === 'down' ? '#f87171' : '#94a3b8';
  const fillColor =
    trend === 'up' ? 'rgba(52,211,153,0.12)' : trend === 'down' ? 'rgba(248,113,113,0.12)' : 'rgba(148,163,184,0.08)';

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
      {/* 填充区域 */}
      <path d={fillD} fill={fillColor} />
      {/* 折线 */}
      <path
        d={pathD}
        fill="none"
        stroke={lineColor}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* 起始点标注 */}
      <circle cx={firstPoint.x} cy={firstPoint.y} r={2.5} fill={lineColor} opacity={0.6} />
      {/* 终点标注 */}
      <circle cx={lastPoint.x} cy={lastPoint.y} r={3} fill={lineColor} />
      {/* 首尾数值标注 */}
      <text
        x={firstPoint.x}
        y={firstPoint.y - 5}
        fontSize={9}
        fill="#94a3b8"
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
 * 变量节点组件
 * 展示单个底层变量的当前值、趋势，点击可展开趋势迷你图
 */
function VariableNode({
  variable,
  isExpanded,
  onToggle,
  onDrillDown,
  isPositiveMetric = true,
}: VariableNodeProps) {
  // 对于正向指标（如 ARPU、留存周期），上升是好事
  // 对于成本类指标（如营销费用），上升是坏事
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
      {/* 变量卡片 */}
      <div
        className={`
          group relative p-3 rounded-xl border transition-all duration-200 cursor-pointer
          ${isExpanded
            ? 'border-indigo-400/50 bg-indigo-400/5 dark:bg-indigo-400/10 shadow-sm'
            : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-white dark:hover:bg-slate-800/70'
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
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
            {variable.name}
          </span>
          <span
            className={`text-xs text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            aria-hidden="true"
          >
            ▾
          </span>
        </div>

        {/* 数值 + 趋势 */}
        <div className="flex items-end justify-between">
          <span className="text-xl font-bold tabular-nums text-slate-800 dark:text-slate-100">
            {variable.value}
            {variable.unit && (
              <span className="text-xs font-normal text-slate-400 ml-0.5">{variable.unit}</span>
            )}
          </span>
          <span className={`text-xs font-medium flex items-center gap-0.5 ${effectiveTrendColor}`}>
            {TREND_ICON[variable.trend]}
            {variable.changeRate}
          </span>
        </div>

        {/* 口径说明（可选） */}
        {variable.description && (
          <p className="mt-1.5 text-xs text-slate-400 dark:text-slate-500 leading-relaxed">
            {variable.description}
          </p>
        )}

        {/* 下钻按钮（可选） */}
        {onDrillDown && (
          <button
            className="mt-2 text-xs text-indigo-400 hover:text-indigo-300 transition-colors opacity-0 group-hover:opacity-100"
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

      {/* 展开的趋势图区域 */}
      {isExpanded && variable.history.length >= 2 && (
        <div className="mt-1 p-3 rounded-b-xl border border-t-0 border-indigo-400/30 bg-indigo-400/5 dark:bg-indigo-400/8">
          {/* 日期标签 */}
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>{variable.history[0]?.date}</span>
            <span className="text-xs font-medium text-slate-500">近期趋势</span>
            <span>{variable.history[variable.history.length - 1]?.date}</span>
          </div>
          {/* Sparkline */}
          <div className="w-full flex justify-center">
            <Sparkline
              data={variable.history}
              trend={variable.trend}
              width={220}
              height={52}
            />
          </div>
          {/* 最大最小值 */}
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>
              最低: {Math.min(...variable.history.map((d) => d.value)).toLocaleString()}
            </span>
            <span>
              最高: {Math.max(...variable.history.map((d) => d.value)).toLocaleString()}
            </span>
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
 * 公式树组件
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
          <div className="w-1 h-4 rounded-full bg-emerald-500" />
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            LTV 拆解
          </span>
          <span className="text-xs text-slate-400 font-mono ml-1">
            = ARPU × 留存周期
          </span>
          {data.ltvCalcNote && (
            <span className="text-xs text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded ml-auto">
              {data.ltvCalcNote}
            </span>
          )}
        </div>

        {/* LTV 结果值 */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-400/8 border border-emerald-400/20">
          <span className="text-xs text-emerald-500 font-semibold">LTV</span>
          <span className="text-lg font-bold tabular-nums text-slate-800 dark:text-slate-100 ml-auto">
            {data.ltv}
          </span>
          <span className={`text-xs font-medium flex items-center gap-0.5 ${TREND_COLOR[data.ltvTrend]}`}>
            {TREND_ICON[data.ltvTrend]}
            {data.ltvChangeRate}
          </span>
        </div>

        {/* 连接线 */}
        <div className="flex items-center gap-2 px-3">
          <div className="w-px h-4 bg-slate-300 dark:bg-slate-600 mx-auto" />
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
          <span className="text-lg font-bold text-slate-400 dark:text-slate-500 select-none">×</span>
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
          <div className="w-1 h-4 rounded-full bg-amber-500" />
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            CAC 拆解
          </span>
          <span className="text-xs text-slate-400 font-mono ml-1">
            = 营销费用 ÷ 新增用户
          </span>
          {data.cacCalcNote && (
            <span className="text-xs text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded ml-auto">
              {data.cacCalcNote}
            </span>
          )}
        </div>

        {/* CAC 结果值 */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-400/8 border border-amber-400/20">
          <span className="text-xs text-amber-500 font-semibold">CAC</span>
          <span className="text-lg font-bold tabular-nums text-slate-800 dark:text-slate-100 ml-auto">
            {data.cac}
          </span>
          {/* CAC 下降是好事，所以反向颜色 */}
          <span className={`text-xs font-medium flex items-center gap-0.5 ${
            data.cacTrend === 'stable'
              ? TREND_COLOR.stable
              : data.cacTrend === 'down'
              ? TREND_COLOR.up   // 成本下降 = 好事 = 绿色
              : TREND_COLOR.down // 成本上升 = 坏事 = 红色
          }`}>
            {TREND_ICON[data.cacTrend]}
            {data.cacChangeRate}
          </span>
        </div>

        {/* 连接线 */}
        <div className="flex items-center gap-2 px-3">
          <div className="w-px h-4 bg-slate-300 dark:bg-slate-600 mx-auto" />
        </div>

        {/* 营销费用节点 */}
        <VariableNode
          variable={data.cacBreakdown.marketingCost}
          isExpanded={expandedVariable === data.cacBreakdown.marketingCost.id}
          onToggle={onToggleVariable}
          onDrillDown={onVariableClick}
          isPositiveMetric={false} /* 成本类，上升为坏 */
        />

        {/* 除号 */}
        <div className="flex items-center justify-center">
          <span className="text-lg font-bold text-slate-400 dark:text-slate-500 select-none">÷</span>
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
 * 单元经济模型卡片组件 (Unit Economics Card)
 *
 * 高密度数据面板，顶部大字号突出 LTV/CAC 比值（颜色反映健康状态），
 * 下方以可展开的公式树拆解 LTV 和 CAC 的构成要素。
 * 点击任意叶子节点可展开查看该变量的近期趋势迷你图。
 *
 * 健康阈值:
 * - ≥ 3.0x: 绿色 (健康)
 * - 1.5x - 3.0x: 黄色 (待优化)
 * - < 1.5x: 红色 (风险)
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
        rounded-2xl border bg-white dark:bg-slate-800/60
        ${healthConfig.borderColor}
        shadow-lg ${healthConfig.glowColor}
        p-5 flex flex-col gap-5
        ${className}
      `}
    >
      {/* ── 顶部：标题栏 ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-widest text-violet-500">
            单元经济模型
          </span>
          <span className="text-xs text-slate-400">Unit Economics</span>
        </div>
        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full ${healthConfig.labelColor}`}
        >
          {healthConfig.label}
        </span>
      </div>

      {/* ── 顶部：Hero Panel — LTV/CAC 比值 ── */}
      <div className={`rounded-xl p-4 ${healthConfig.bgColor} border ${healthConfig.borderColor}`}>
        <div className="flex items-end justify-between">
          {/* 核心比值 */}
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1 font-medium">
              LTV / CAC 比值
            </p>
            <div className="flex items-end gap-2">
              <span className={`text-6xl font-bold tabular-nums leading-none ${healthConfig.color}`}>
                {data.ratio.toFixed(1)}
              </span>
              <span className={`text-2xl font-semibold mb-1 ${healthConfig.color} opacity-70`}>
                x
              </span>
            </div>
            <div className={`flex items-center gap-1 mt-1.5 text-sm font-medium ${
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
              <span className="text-xs text-slate-400">≥ 3.0x</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
              <span className="text-xs text-emerald-400 font-medium w-12">健康</span>
            </div>
            <div className="flex items-center gap-2 justify-end">
              <span className="text-xs text-slate-400">1.5–3.0x</span>
              <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
              <span className="text-xs text-amber-400 font-medium w-12">待优化</span>
            </div>
            <div className="flex items-center gap-2 justify-end">
              <span className="text-xs text-slate-400">&lt; 1.5x</span>
              <span className="w-2 h-2 rounded-full bg-red-400 shrink-0" />
              <span className="text-xs text-red-400 font-medium w-12">风险</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── 辅助指标行：LTV / CAC / Payback Period ── */}
      <div className="grid grid-cols-3 gap-3">
        {/* LTV */}
        <div className="flex flex-col p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
          <span className="text-xs text-slate-400 mb-1 font-medium">LTV</span>
          <span className="text-xl font-bold tabular-nums text-slate-800 dark:text-slate-100">
            {data.ltv}
          </span>
          <span className={`text-xs font-medium mt-0.5 flex items-center gap-0.5 ${TREND_COLOR[data.ltvTrend]}`}>
            {TREND_ICON[data.ltvTrend]}
            {data.ltvChangeRate}
          </span>
        </div>

        {/* CAC */}
        <div className="flex flex-col p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
          <span className="text-xs text-slate-400 mb-1 font-medium">CAC</span>
          <span className="text-xl font-bold tabular-nums text-slate-800 dark:text-slate-100">
            {data.cac}
          </span>
          <span className={`text-xs font-medium mt-0.5 flex items-center gap-0.5 ${
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
        <div className="flex flex-col p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
          <span className="text-xs text-slate-400 mb-1 font-medium">回收期</span>
          <div className="flex items-end gap-1">
            <span className="text-xl font-bold tabular-nums text-slate-800 dark:text-slate-100">
              {data.paybackPeriod}
            </span>
            <span className="text-xs text-slate-400 mb-0.5">mo</span>
          </div>
          <span className={`text-xs font-medium mt-0.5 flex items-center gap-0.5 ${
            data.paybackTrend === 'stable'
              ? TREND_COLOR.stable
              : data.paybackTrend === 'down'
              ? TREND_COLOR.up   // 回收期缩短 = 好事 = 绿色
              : TREND_COLOR.down
          }`}>
            {TREND_ICON[data.paybackTrend]}
            {data.paybackChange}
          </span>
        </div>
      </div>

      {/* ── 分隔线 ── */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
        <span className="text-xs text-slate-400 font-medium px-2">公式拆解</span>
        <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
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
        <div className="flex flex-wrap gap-3 pt-1 border-t border-slate-100 dark:border-slate-700/50">
          {data.ltvCalcNote && (
            <span className="text-xs text-slate-400">
              <span className="font-medium text-emerald-500">LTV</span> 口径：{data.ltvCalcNote}
            </span>
          )}
          {data.cacCalcNote && (
            <span className="text-xs text-slate-400">
              <span className="font-medium text-amber-500">CAC</span> 口径：{data.cacCalcNote}
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
 * 演示组件：展示三种健康状态的 UnitEconomicsCard
 * 仅用于开发调试，生产环境中请直接使用 UnitEconomicsCard
 */
export function UnitEconomicsCardDemo() {
  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-8">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-2">
        单元经济模型卡片 · 演示
      </h1>
      <p className="text-sm text-slate-500 mb-8">
        点击任意叶子节点（ARPU、留存周期、营销费用、新增用户）可展开查看近期趋势迷你图。
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 健康状态 */}
        <div>
          <p className="text-xs font-semibold text-emerald-500 uppercase tracking-widest mb-3">
            健康 (≥ 3.0x)
          </p>
          <UnitEconomicsCard
            data={mockUnitEconomicsData}
            onVariableClick={(id) => console.log('下钻:', id)}
          />
        </div>

        {/* 待优化状态 */}
        <div>
          <p className="text-xs font-semibold text-amber-500 uppercase tracking-widest mb-3">
            待优化 (1.5–3.0x)
          </p>
          <UnitEconomicsCard
            data={mockUnitEconomicsDataWarning}
            onVariableClick={(id) => console.log('下钻:', id)}
          />
        </div>

        {/* 风险状态 */}
        <div>
          <p className="text-xs font-semibold text-red-500 uppercase tracking-widest mb-3">
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

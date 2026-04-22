import React, { useState, useCallback, useMemo } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';

// =============================================================================
// 组件数据绑定说明
// 组件 Key: trend_matrix_grid
// 组件类型: 详情组件 (Detail Component)
// 适用模块: 多指标监控、业务模块详情
//
// 使用示例:
//   <TrendMatrixGrid
//     dataset={trendMatrixData}
//     columns={2}
//     chartHeight={200}
//   />
//
// 数据接口 (TrendMatrixData):
//   data: TrendDataPoint[]    — 时间序列数据，每个点包含 date 和各指标值
//   metrics: MetricConfig[]   — 指标配置列表，定义名称、颜色、单位等
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// Section 1: TypeScript 接口定义
// ─────────────────────────────────────────────────────────────────────────────

/** 趋势数据点 */
export interface TrendDataPoint {
  /** 时间标签，如 "2023-10-01" 或 "W16" */
  date: string;
  /** 动态键值对，键为指标 ID，值为该时间点的数值 */
  [metricId: string]: number | string;
}

/** 单个指标的元数据配置 */
export interface MetricConfig {
  /** 指标唯一标识 */
  id: string;
  /** 指标显示名称 */
  name: string;
  /** 数值单位，如 "%", "万", "人" */
  unit?: string;
  /** 趋势线颜色 (Hex 值) */
  color?: string;
  /**
   * 涨跌颜色反转
   * 默认: 涨绿跌红
   * 设为 true: 涨红跌绿（适用于"跳出率"、"错误率"等负向指标）
   */
  invertColors?: boolean;
  /**
   * 当前最新值（可由组件自动计算，也可外部传入覆盖）
   * 若不传，组件取 data 数组最后一项的对应值
   */
  currentValue?: number;
  /**
   * 环比变化率（可由组件自动计算，也可外部传入覆盖）
   * 若不传，组件自动计算最后两项的变化率
   */
  changeRate?: number;
}

/** 组件整体数据接口 */
export interface TrendMatrixData {
  /** 时间序列数据数组（按时间升序排列） */
  data: TrendDataPoint[];
  /** 需要展示的指标配置列表 */
  metrics: MetricConfig[];
}

/** 组件 Props 接口 */
export interface TrendMatrixGridProps {
  /** 矩阵数据源 */
  dataset: TrendMatrixData;
  /** 网格列数，默认 2 */
  columns?: 1 | 2 | 3 | 4;
  /** 每个子图的图表区高度（px），默认 160 */
  chartHeight?: number;
  /** 是否显示面积图阴影，默认 true */
  showArea?: boolean;
  /** 是否显示网格线，默认 false */
  showGrid?: boolean;
  /** 自定义容器 className */
  className?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 2: 工具函数与常量
// ─────────────────────────────────────────────────────────────────────────────

/** 默认指标颜色序列（与模板主题一致） */
const DEFAULT_COLORS = [
  '#6366f1', // indigo-500
  '#10b981', // emerald-500
  '#f59e0b', // amber-500
  '#3b82f6', // blue-500
  '#ec4899', // pink-500
  '#8b5cf6', // violet-500
  '#14b8a6', // teal-500
  '#f97316', // orange-500
];

/**
 * 格式化数值显示
 * 超过 10000 的数值使用 "万" 单位
 */
function formatValue(value: number, unit?: string): string {
  if (unit === '%') {
    return `${value.toFixed(1)}%`;
  }
  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(1)}万${unit ?? ''}`;
  }
  if (Math.abs(value) >= 1000) {
    return `${value.toLocaleString()}${unit ?? ''}`;
  }
  return `${value}${unit ?? ''}`;
}

/**
 * 计算环比变化率
 * @returns 变化率（百分比数值，如 5.2 代表 +5.2%）
 */
function calcChangeRate(current: number, previous: number): number {
  if (previous === 0) return 0;
  return ((current - previous) / Math.abs(previous)) * 100;
}

/**
 * 根据变化率和是否反向，返回颜色 class
 */
function getChangeColor(changeRate: number, invertColors: boolean = false): string {
  if (changeRate === 0) return 'text-slate-400';
  const isPositive = changeRate > 0;
  const isGood = invertColors ? !isPositive : isPositive;
  return isGood ? 'text-emerald-400' : 'text-red-400';
}

/**
 * 根据变化率和是否反向，返回变化率文字
 */
function formatChangeRate(changeRate: number): string {
  if (changeRate === 0) return '持平';
  const sign = changeRate > 0 ? '+' : '';
  return `${sign}${changeRate.toFixed(1)}%`;
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 3: 子组件 — 单个指标趋势图卡片
// ─────────────────────────────────────────────────────────────────────────────

interface MetricChartCardProps {
  /** 指标配置 */
  metric: MetricConfig;
  /** 时间序列数据 */
  data: TrendDataPoint[];
  /** 指标颜色 */
  color: string;
  /** 图表区高度 */
  chartHeight: number;
  /** 是否显示面积阴影 */
  showArea: boolean;
  /** 是否显示网格线 */
  showGrid: boolean;
  /** 当前联动悬浮的数据点索引（-1 表示无悬浮） */
  activeIndex: number;
  /** 鼠标进入某个数据点时的回调 */
  onHover: (index: number) => void;
  /** 鼠标离开图表时的回调 */
  onLeave: () => void;
}

/**
 * 单个指标趋势图卡片
 *
 * 展示一个 KPI 的历史趋势折线/面积图，包含：
 * - 顶部信息区：指标名称、当前值、环比变化
 * - 图表区：Recharts AreaChart，支持联动十字准星
 */
function MetricChartCard({
  metric,
  data,
  color,
  chartHeight,
  showArea,
  showGrid,
  activeIndex,
  onHover,
  onLeave,
}: MetricChartCardProps) {
  // 计算当前值和环比变化率
  const currentValue = useMemo(() => {
    if (metric.currentValue !== undefined) return metric.currentValue;
    const last = data[data.length - 1];
    return last ? (last[metric.id] as number) : 0;
  }, [metric, data]);

  const changeRate = useMemo(() => {
    if (metric.changeRate !== undefined) return metric.changeRate;
    if (data.length < 2) return 0;
    const last = data[data.length - 1][metric.id] as number;
    const prev = data[data.length - 2][metric.id] as number;
    return calcChangeRate(last, prev);
  }, [metric, data]);

  // 悬浮时显示的值（联动时显示悬浮点的值，否则显示当前值）
  const displayValue = useMemo(() => {
    if (activeIndex >= 0 && activeIndex < data.length) {
      const hoverVal = data[activeIndex][metric.id];
      return hoverVal !== undefined ? (hoverVal as number) : currentValue;
    }
    return currentValue;
  }, [activeIndex, data, metric.id, currentValue]);

  // 悬浮时显示的日期标签
  const displayDate = useMemo(() => {
    if (activeIndex >= 0 && activeIndex < data.length) {
      return data[activeIndex].date;
    }
    return null;
  }, [activeIndex, data]);

  const changeColorClass = getChangeColor(changeRate, metric.invertColors);
  const changeText = formatChangeRate(changeRate);

  // 处理 Recharts 的 onMouseMove 事件
  const handleMouseMove = useCallback(
    (chartState: { activeTooltipIndex?: number }) => {
      if (chartState && chartState.activeTooltipIndex !== undefined) {
        onHover(chartState.activeTooltipIndex);
      }
    },
    [onHover]
  );

  // Y 轴自适应范围（留 10% 上下边距）
  const yDomain = useMemo(() => {
    const values = data
      .map((d) => d[metric.id] as number)
      .filter((v) => v !== undefined && !isNaN(v));
    if (values.length === 0) return ['auto', 'auto'] as const;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.15 || Math.abs(max) * 0.1 || 1;
    return [min - padding, max + padding] as const;
  }, [data, metric.id]);

  // 悬浮时显示的参考线日期（用于 ReferenceLine dataKey）
  const referenceDate = activeIndex >= 0 && activeIndex < data.length
    ? data[activeIndex].date
    : null;

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 p-4 flex flex-col transition-shadow hover:shadow-md">
      {/* ── 顶部信息区 ── */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          {/* 指标名称 */}
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide truncate">
            {metric.name}
          </p>
          {/* 当前值（联动时动态更新） */}
          <div className="flex items-baseline gap-1.5 mt-1">
            <span
              className="text-2xl font-bold tabular-nums text-slate-800 dark:text-slate-100 transition-all duration-150"
              style={{ color: activeIndex >= 0 ? color : undefined }}
            >
              {formatValue(displayValue, metric.unit)}
            </span>
            {/* 联动时显示悬浮日期 */}
            {displayDate && (
              <span className="text-xs text-slate-400 dark:text-slate-500 ml-1">
                {displayDate}
              </span>
            )}
          </div>
        </div>

        {/* 环比变化率徽章 */}
        <div className="shrink-0 ml-3">
          <span
            className={`
              inline-flex items-center gap-0.5 text-xs font-semibold px-2 py-1 rounded-lg
              ${changeColorClass}
              ${changeRate > 0
                ? 'bg-emerald-400/10'
                : changeRate < 0
                ? 'bg-red-400/10'
                : 'bg-slate-100 dark:bg-slate-700'
              }
            `}
          >
            {changeRate > 0 ? '↑' : changeRate < 0 ? '↓' : '→'}
            {changeText}
          </span>
          <p className="text-xs text-slate-400 dark:text-slate-500 text-right mt-0.5">
            环比
          </p>
        </div>
      </div>

      {/* ── 图表区 ── */}
      <div
        style={{ height: chartHeight }}
        onMouseLeave={onLeave}
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
            onMouseMove={handleMouseMove}
            onMouseLeave={onLeave}
          >
            {/* 渐变填充定义 */}
            <defs>
              <linearGradient id={`gradient-${metric.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.25} />
                <stop offset="95%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>

            {/* 网格线（可选） */}
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.15)"
                vertical={false}
              />
            )}

            {/* X 轴 */}
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />

            {/* Y 轴（自适应范围） */}
            <YAxis
              domain={yDomain}
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => {
                if (metric.unit === '%') return `${v.toFixed(0)}%`;
                if (Math.abs(v) >= 10000) return `${(v / 10000).toFixed(0)}w`;
                if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(0)}k`;
                return String(v);
              }}
              width={40}
            />

            {/* 联动十字准星：垂直参考线 */}
            {referenceDate && (
              <ReferenceLine
                x={referenceDate}
                stroke={color}
                strokeWidth={1.5}
                strokeDasharray="4 3"
                strokeOpacity={0.8}
              />
            )}

            {/* 悬浮 Tooltip（单图内显示，辅助联动参考线） */}
            <Tooltip
              content={() => null}
              cursor={false}
            />

            {/* 面积/折线 */}
            <Area
              type="monotone"
              dataKey={metric.id}
              stroke={color}
              strokeWidth={2}
              fill={showArea ? `url(#gradient-${metric.id})` : 'none'}
              dot={false}
              activeDot={{
                r: 5,
                fill: color,
                stroke: '#fff',
                strokeWidth: 2,
              }}
              isAnimationActive={true}
              animationDuration={600}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 4: 全局悬浮 Tooltip（所有子图共享）
// ─────────────────────────────────────────────────────────────────────────────

interface GlobalTooltipProps {
  /** 当前悬浮的数据点 */
  dataPoint: TrendDataPoint | null;
  /** 指标配置列表 */
  metrics: MetricConfig[];
  /** 指标颜色映射 */
  colorMap: Record<string, string>;
}

/**
 * 全局联动 Tooltip
 *
 * 当鼠标悬浮在任意子图时，在组件顶部显示当前时间点所有指标的数值摘要。
 */
function GlobalTooltip({ dataPoint, metrics, colorMap }: GlobalTooltipProps) {
  if (!dataPoint) return null;

  return (
    <div className="flex items-center gap-4 flex-wrap px-1 py-2 mb-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 transition-all duration-150">
      {/* 时间标签 */}
      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 shrink-0">
        📅 {dataPoint.date}
      </span>
      {/* 各指标值 */}
      {metrics.map((metric) => {
        const value = dataPoint[metric.id] as number | undefined;
        if (value === undefined) return null;
        return (
          <div key={metric.id} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: colorMap[metric.id] }}
            />
            <span className="text-xs text-slate-500 dark:text-slate-400">{metric.name}</span>
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-200 tabular-nums">
              {formatValue(value, metric.unit)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 5: 主组件 — TrendMatrixGrid
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 指标趋势矩阵组件 (Trend Matrix Grid)
 *
 * 以小倍数图 (Small Multiples) 形式展示多个 KPI 的历史趋势，
 * 支持鼠标悬浮时的联动十字准星 (Synchronized Crosshair)，
 * 便于横向比对同一时间点下多个指标的数值。
 *
 * 核心特性：
 * - 小倍数图网格排列（2列×N行，可配置）
 * - 共享 X 轴时间范围
 * - 联动十字准星：悬浮任意子图，所有子图同步高亮同一时间点
 * - 全局 Tooltip：顶部摘要栏展示当前时间点所有指标值
 * - 每个子图顶部显示指标名称、当前值、环比变化（颜色区分涨跌）
 * - 深色/浅色双主题支持
 *
 * @example
 * ```tsx
 * <TrendMatrixGrid
 *   dataset={{
 *     data: [
 *       { date: 'W13', dau: 10500, retention: 21, revenue: 8200 },
 *       { date: 'W14', dau: 11200, retention: 20.5, revenue: 8800 },
 *       { date: 'W15', dau: 11650, retention: 20, revenue: 9100 },
 *       { date: 'W16', dau: 12500, retention: 18.2, revenue: 9600 },
 *     ],
 *     metrics: [
 *       { id: 'dau', name: 'DAU', unit: '人', color: '#6366f1' },
 *       { id: 'retention', name: 'D7 留存率', unit: '%', invertColors: true },
 *       { id: 'revenue', name: '营收', unit: '元' },
 *     ],
 *   }}
 *   columns={2}
 *   chartHeight={160}
 * />
 * ```
 */
export function TrendMatrixGrid({
  dataset,
  columns = 2,
  chartHeight = 160,
  showArea = true,
  showGrid = false,
  className = '',
}: TrendMatrixGridProps) {
  // ── 联动状态：当前悬浮的数据点索引 ──
  const [activeIndex, setActiveIndex] = useState<number>(-1);

  // ── 指标颜色映射 ──
  const colorMap = useMemo<Record<string, string>>(() => {
    const map: Record<string, string> = {};
    dataset.metrics.forEach((metric, i) => {
      map[metric.id] = metric.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length];
    });
    return map;
  }, [dataset.metrics]);

  // ── 当前悬浮的数据点 ──
  const activeDataPoint = useMemo<TrendDataPoint | null>(() => {
    if (activeIndex < 0 || activeIndex >= dataset.data.length) return null;
    return dataset.data[activeIndex];
  }, [activeIndex, dataset.data]);

  // ── 事件处理 ──
  const handleHover = useCallback((index: number) => {
    setActiveIndex(index);
  }, []);

  const handleLeave = useCallback(() => {
    setActiveIndex(-1);
  }, []);

  // ── 网格列数 class ──
  const gridColsClass: Record<number, string> = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  };

  if (!dataset.data.length || !dataset.metrics.length) {
    return (
      <div className={`rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 p-8 text-center ${className}`}>
        <p className="text-sm text-slate-400">暂无趋势数据</p>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      {/* ── 全局联动 Tooltip（顶部摘要栏） ── */}
      <div
        className="transition-all duration-200"
        style={{
          opacity: activeDataPoint ? 1 : 0,
          transform: activeDataPoint ? 'translateY(0)' : 'translateY(-4px)',
          pointerEvents: 'none',
          minHeight: activeDataPoint ? undefined : 0,
        }}
      >
        {activeDataPoint && (
          <GlobalTooltip
            dataPoint={activeDataPoint}
            metrics={dataset.metrics}
            colorMap={colorMap}
          />
        )}
      </div>

      {/* ── 小倍数图网格 ── */}
      <div className={`grid ${gridColsClass[columns]} gap-4`}>
        {dataset.metrics.map((metric) => (
          <MetricChartCard
            key={metric.id}
            metric={metric}
            data={dataset.data}
            color={colorMap[metric.id]}
            chartHeight={chartHeight}
            showArea={showArea}
            showGrid={showGrid}
            activeIndex={activeIndex}
            onHover={handleHover}
            onLeave={handleLeave}
          />
        ))}
      </div>

      {/* ── 底部图例（所有指标颜色说明） ── */}
      <div className="flex items-center gap-4 flex-wrap mt-4 px-1">
        {dataset.metrics.map((metric) => (
          <div key={metric.id} className="flex items-center gap-1.5">
            <span
              className="w-3 h-0.5 rounded-full"
              style={{ backgroundColor: colorMap[metric.id] }}
            />
            <span className="text-xs text-slate-400 dark:text-slate-500">{metric.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 6: 演示数据与 Demo 组件
// ─────────────────────────────────────────────────────────────────────────────

/** 演示数据：模拟 8 周的多指标趋势 */
export const DEMO_TREND_MATRIX_DATA: TrendMatrixData = {
  data: [
    { date: 'W09', dau: 9200,  d7_retention: 22.1, pay_rate: 4.5, arpu: 7.2,  new_users: 980,  session_duration: 10.2 },
    { date: 'W10', dau: 9800,  d7_retention: 21.8, pay_rate: 4.3, arpu: 7.5,  new_users: 1050, session_duration: 10.8 },
    { date: 'W11', dau: 10200, d7_retention: 21.5, pay_rate: 4.4, arpu: 7.8,  new_users: 1100, session_duration: 11.1 },
    { date: 'W12', dau: 10500, d7_retention: 21.2, pay_rate: 4.2, arpu: 7.6,  new_users: 1080, session_duration: 11.5 },
    { date: 'W13', dau: 10500, d7_retention: 21.0, pay_rate: 4.1, arpu: 7.9,  new_users: 1120, session_duration: 11.8 },
    { date: 'W14', dau: 11200, d7_retention: 20.5, pay_rate: 4.2, arpu: 8.1,  new_users: 1200, session_duration: 12.0 },
    { date: 'W15', dau: 11650, d7_retention: 20.0, pay_rate: 4.0, arpu: 8.3,  new_users: 1180, session_duration: 12.3 },
    { date: 'W16', dau: 12500, d7_retention: 18.2, pay_rate: 3.8, arpu: 8.5,  new_users: 1350, session_duration: 12.0 },
  ],
  metrics: [
    {
      id: 'dau',
      name: 'DAU',
      unit: '人',
      color: '#6366f1',
    },
    {
      id: 'd7_retention',
      name: 'D7 留存率',
      unit: '%',
      color: '#10b981',
      invertColors: true, // 下降是坏事，红色提示
    },
    {
      id: 'pay_rate',
      name: '付费渗透率',
      unit: '%',
      color: '#f59e0b',
      invertColors: true,
    },
    {
      id: 'arpu',
      name: 'ARPU',
      unit: '元',
      color: '#3b82f6',
    },
    {
      id: 'new_users',
      name: '新增用户',
      unit: '人',
      color: '#8b5cf6',
    },
    {
      id: 'session_duration',
      name: '人均使用时长',
      unit: 'min',
      color: '#14b8a6',
    },
  ],
};

/**
 * TrendMatrixGrid 演示页面
 *
 * 用于独立预览和调试组件效果。
 * 在实际周报中，请将 DEMO_TREND_MATRIX_DATA 替换为真实数据。
 */
export function TrendMatrixGridDemo() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 sm:p-10">
      {/* 页面标题 */}
      <div className="max-w-[1200px] mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-1 h-6 rounded-full bg-indigo-500" />
          <h1 className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400 dark:text-slate-500">
            指标趋势矩阵
          </h1>
          <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
          <span className="text-xs text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
            trend_matrix_grid
          </span>
        </div>

        {/* 使用说明 */}
        <div className="mb-6 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800/50">
          <p className="text-xs text-indigo-600 dark:text-indigo-400 font-medium mb-1">
            💡 交互提示
          </p>
          <p className="text-xs text-indigo-500 dark:text-indigo-500">
            将鼠标悬浮在任意子图上，所有图表将同步显示该时间点的数据（联动十字准星），顶部摘要栏也会同步更新。
          </p>
        </div>

        {/* 2 列布局演示 */}
        <div className="mb-8">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-4">
            2 列布局（默认）
          </p>
          <TrendMatrixGrid
            dataset={DEMO_TREND_MATRIX_DATA}
            columns={2}
            chartHeight={160}
            showArea={true}
          />
        </div>

        {/* 3 列布局演示 */}
        <div className="mb-8">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-4">
            3 列布局
          </p>
          <TrendMatrixGrid
            dataset={DEMO_TREND_MATRIX_DATA}
            columns={3}
            chartHeight={140}
            showArea={true}
            showGrid={true}
          />
        </div>
      </div>
    </div>
  );
}

// 默认导出演示页面（方便独立预览）
export default TrendMatrixGridDemo;

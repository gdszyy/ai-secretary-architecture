// @section:health_radar_chart - 多维健康度雷达图首屏组件
//
// 组件 Key: health_radar_chart
// 适用模块: 项目健康度诊断 (Health Score)
// 类型: 首屏模块 (Hero Component) - P0
//
// 三层交互模型:
//   1. 一眼定调: 多边形雷达图，叠加当前/目标双层，危险维度红色预警
//   2. 悬浮概要: Hover 维度顶点弹出浮层，显示得分/指标简报/扣分项
//   3. 下钻详情: Click 维度顶点触发 onDrillDown 回调，由父组件决定跳转
//
// 依赖: React, TypeScript, TailwindCSS, Recharts
// 使用示例:
//   <HealthRadarChart
//     data={healthRadarData}
//     onDrillDown={(dimId) => scrollToSection(`section-${dimId}`)}
//   />

import React, { useState, useCallback } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

// =============================================================================
// TypeScript 接口定义
// =============================================================================

/** 趋势方向 */
export type TrendDirection = 'up' | 'down' | 'stable';

/** 核心支撑指标简报条目 */
export interface RadarKeyMetric {
  /** 指标名称，如"DAU" */
  label: string;
  /** 指标当前值，如"1.2w" */
  value: string;
  /** 趋势方向 */
  trend?: TrendDirection;
}

/** 雷达图单个维度数据 */
export interface RadarDimension {
  /** 维度唯一标识，如"growth" */
  id: string;
  /** 维度显示名称，如"增长势能" */
  name: string;
  /** 当前得分 (0-100) */
  score: number;
  /** 目标得分 (0-100) */
  targetScore: number;
  /** 警戒线分数，低于此分数将触发红色预警，默认 60 */
  warningThreshold?: number;
  /** 核心支撑指标简报（用于 Hover 浮层） */
  keyMetrics?: RadarKeyMetric[];
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

/** 组件 Props 接口 */
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
   */
  onDrillDown?: (dimensionId: string) => void;
  /** 自定义类名 */
  className?: string;
}

// =============================================================================
// Mock 数据（用于开发调试）
// =============================================================================

export const mockHealthRadarData: HealthRadarData = {
  overallScore: 72,
  overallTrend: 'up',
  phase: '蓄力期',
  summary: '核心指标稳健，增长势能持续积累，商业化转化仍有提升空间。',
  dimensions: [
    {
      id: 'growth',
      name: '增长势能',
      score: 82,
      targetScore: 90,
      warningThreshold: 60,
      keyMetrics: [
        { label: 'DAU', value: '1.25w', trend: 'up' },
        { label: '新用户/日', value: '1,200', trend: 'up' },
      ],
      riskPoints: ['D1 留存率 38%，未达 45% 目标'],
    },
    {
      id: 'product',
      name: '产品完成度',
      score: 60,
      targetScore: 80,
      warningThreshold: 60,
      keyMetrics: [
        { label: 'D7 留存率', value: '18.2%', trend: 'down' },
        { label: '人均时长', value: '12min', trend: 'stable' },
      ],
      riskPoints: ['D7 留存率 18.2%，低于 20% 预警线', '核心功能渗透率仍待提升'],
    },
    {
      id: 'monetization',
      name: '商业化健康',
      score: 45,
      targetScore: 70,
      warningThreshold: 60,
      keyMetrics: [
        { label: '付费渗透率', value: '3.8%', trend: 'down' },
        { label: 'ARPU', value: '¥8.5', trend: 'stable' },
      ],
      riskPoints: ['付费渗透率低于 5% 目标', 'ARPU 较目标 ¥12 仍有差距'],
    },
    {
      id: 'risk',
      name: '风险控制',
      score: 65,
      targetScore: 85,
      warningThreshold: 60,
      keyMetrics: [
        { label: 'SLA', value: '99.8%', trend: 'stable' },
        { label: '客诉率', value: '0.3%', trend: 'up' },
      ],
      riskPoints: ['客诉率轻微上升，需关注'],
    },
    {
      id: 'milestone',
      name: '里程碑进度',
      score: 75,
      targetScore: 85,
      warningThreshold: 60,
      keyMetrics: [
        { label: '当前版本', value: 'v2.0', trend: 'stable' },
        { label: '整体进度', value: '65%', trend: 'up' },
      ],
      riskPoints: [],
    },
  ],
};

// =============================================================================
// 工具函数与常量
// =============================================================================

/** 趋势图标映射 */
const TREND_ICON: Record<TrendDirection, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

/** 趋势颜色映射（Tailwind 类名） */
const TREND_COLOR: Record<TrendDirection, string> = {
  up: 'text-emerald-400',
  down: 'text-red-400',
  stable: 'text-slate-400',
};

/** 获取综合评分的颜色类名 */
function getScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-400';
  if (score >= 60) return 'text-amber-400';
  return 'text-red-400';
}

/** 判断维度是否处于危险状态 */
function isDangerous(dim: RadarDimension): boolean {
  const threshold = dim.warningThreshold ?? 60;
  return dim.score < threshold;
}

// =============================================================================
// 子组件：自定义 Tooltip（悬浮概要层）
// =============================================================================

interface DimensionTooltipProps {
  dimension: RadarDimension;
}

/**
 * 维度悬浮概要浮层
 * 展示维度得分、核心支撑指标简报、主要扣分项
 */
function DimensionTooltip({ dimension }: DimensionTooltipProps) {
  const dangerous = isDangerous(dimension);
  const threshold = dimension.warningThreshold ?? 60;

  return (
    <div
      className="
        bg-slate-900/95 backdrop-blur-sm
        border border-slate-700
        rounded-xl shadow-2xl
        p-4 min-w-[220px] max-w-[280px]
        pointer-events-none
      "
    >
      {/* 维度名称与得分 */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-slate-100">{dimension.name}</span>
        <div className="flex items-center gap-1.5">
          <span
            className={`text-lg font-bold tabular-nums ${
              dangerous ? 'text-red-400' : 'text-emerald-400'
            }`}
          >
            {dimension.score}
          </span>
          <span className="text-xs text-slate-500">/ 100</span>
        </div>
      </div>

      {/* 得分进度条 */}
      <div className="relative h-1.5 bg-slate-700 rounded-full overflow-hidden mb-1">
        {/* 警戒线标记 */}
        <div
          className="absolute top-0 bottom-0 w-px bg-red-400/60 z-10"
          style={{ left: `${threshold}%` }}
        />
        {/* 当前得分 */}
        <div
          className={`h-full rounded-full transition-all duration-700 ${
            dangerous ? 'bg-red-500' : 'bg-indigo-500'
          }`}
          style={{ width: `${dimension.score}%` }}
        />
        {/* 目标得分 */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-slate-400/60"
          style={{ left: `${dimension.targetScore}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-slate-500 mb-3">
        <span>当前 {dimension.score}</span>
        <span>目标 {dimension.targetScore}</span>
      </div>

      {/* 核心支撑指标简报 */}
      {dimension.keyMetrics && dimension.keyMetrics.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            核心指标
          </p>
          <div className="space-y-1">
            {dimension.keyMetrics.map((metric, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <span className="text-xs text-slate-400">{metric.label}</span>
                <div className="flex items-center gap-1">
                  <span className="text-xs font-medium text-slate-200">{metric.value}</span>
                  {metric.trend && (
                    <span className={`text-xs ${TREND_COLOR[metric.trend]}`}>
                      {TREND_ICON[metric.trend]}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 主要扣分项 */}
      {dimension.riskPoints && dimension.riskPoints.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-red-400/80 uppercase tracking-wider mb-1.5">
            主要扣分项
          </p>
          <ul className="space-y-1">
            {dimension.riskPoints.map((point, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <span className="text-red-400 mt-0.5 shrink-0">•</span>
                <span className="text-xs text-slate-400 leading-relaxed">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 点击提示 */}
      <div className="mt-3 pt-2.5 border-t border-slate-700">
        <p className="text-xs text-slate-500 text-center">点击查看详情 →</p>
      </div>
    </div>
  );
}

// =============================================================================
// 子组件：自定义 Recharts Tooltip
// =============================================================================

interface CustomRechartsTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: { fullData: RadarDimension } }>;
}

function CustomRechartsTooltip({ active, payload }: CustomRechartsTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const dimension = payload[0]?.payload?.fullData;
  if (!dimension) return null;
  return <DimensionTooltip dimension={dimension} />;
}

// =============================================================================
// 子组件：自定义 PolarAngleAxis Tick（维度标签）
// =============================================================================

interface CustomAngleTickProps {
  x?: number;
  y?: number;
  payload?: { value: string };
  dimensions: RadarDimension[];
  activeDimId: string | null;
  onDrillDown?: (dimensionId: string) => void;
}

function CustomAngleTick({
  x = 0,
  y = 0,
  payload,
  dimensions,
  activeDimId,
  onDrillDown,
}: CustomAngleTickProps) {
  if (!payload) return null;
  const dim = dimensions.find((d) => d.name === payload.value);
  if (!dim) return null;

  const dangerous = isDangerous(dim);
  const isActive = activeDimId === dim.id;
  const fillColor = dangerous ? '#f87171' : isActive ? '#818cf8' : '#94a3b8';
  const fontWeight = dangerous || isActive ? 'bold' : 'normal';

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDrillDown?.(dim.id);
  };

  return (
    <g
      onClick={handleClick}
      style={{ cursor: onDrillDown ? 'pointer' : 'default' }}
    >
      {/* 危险状态警告图标 */}
      {dangerous && (
        <text
          x={x}
          y={y - 14}
          textAnchor="middle"
          fontSize={12}
          fill="#f87171"
        >
          ⚠
        </text>
      )}
      {/* 维度名称标签 */}
      <text
        x={x}
        y={y}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={11}
        fontWeight={fontWeight}
        fill={fillColor}
      >
        {payload.value}
      </text>
      {/* 得分标签 */}
      <text
        x={x}
        y={y + 14}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={10}
        fill={dangerous ? '#fca5a5' : '#64748b'}
      >
        {dim.score}
      </text>
    </g>
  );
}

// =============================================================================
// 主组件：多维健康度雷达图 (HealthRadarChart)
// =============================================================================

/**
 * 多维健康度雷达图组件 (Health Radar Chart)
 *
 * 展示项目各维度健康度的多边形雷达图，支持三层交互：
 * - 一眼定调：双层多边形（当前/目标），危险维度红色预警
 * - 悬浮概要：Hover 维度顶点弹出指标简报和扣分项浮层
 * - 下钻详情：Click 维度顶点触发 onDrillDown 回调
 *
 * @example
 * <HealthRadarChart
 *   data={healthRadarData}
 *   onDrillDown={(dimId) => scrollToSection(`section-${dimId}`)}
 * />
 */
export function HealthRadarChart({
  data,
  onClick,
  onDrillDown,
  className = '',
}: HealthRadarChartProps) {
  const [activeDimId, setActiveDimId] = useState<string | null>(null);

  // 将 dimensions 数据转换为 Recharts 所需的格式
  const chartData = data.dimensions.map((dim) => ({
    name: dim.name,
    current: dim.score,
    target: dim.targetScore,
    fullData: dim, // 携带完整数据供 Tooltip 使用
  }));

  // 统计危险维度数量
  const dangerousCount = data.dimensions.filter(isDangerous).length;

  const handleChartClick = useCallback(
    (chartEvent: { activePayload?: Array<{ payload: { fullData: RadarDimension } }> } | null) => {
      if (!chartEvent?.activePayload || chartEvent.activePayload.length === 0) return;
      const dim = chartEvent.activePayload[0]?.payload?.fullData;
      if (dim && onDrillDown) {
        onDrillDown(dim.id);
      }
    },
    [onDrillDown]
  );

  const handleMouseMove = useCallback(
    (chartEvent: { activePayload?: Array<{ payload: { fullData: RadarDimension } }> } | null) => {
      if (!chartEvent?.activePayload || chartEvent.activePayload.length === 0) {
        setActiveDimId(null);
        return;
      }
      const dim = chartEvent.activePayload[0]?.payload?.fullData;
      setActiveDimId(dim?.id ?? null);
    },
    []
  );

  const handleMouseLeave = useCallback(() => {
    setActiveDimId(null);
  }, []);

  return (
    <div
      className={`
        rounded-2xl border border-slate-200 dark:border-slate-700
        bg-white dark:bg-slate-800/60
        p-5 h-full flex flex-col
        ${onClick ? 'cursor-pointer hover:border-indigo-400/50 hover:shadow-lg transition-all duration-200' : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
      aria-label={onClick ? `查看健康度详情，综合评分 ${data.overallScore}` : undefined}
    >
      {/* ── 标题区 ── */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold uppercase tracking-widest text-indigo-500">
          项目健康度
        </span>
        <div className="flex items-center gap-2">
          {dangerousCount > 0 && (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-red-400 bg-red-400/10 px-2 py-0.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
              {dangerousCount} 项预警
            </span>
          )}
          <span
            className={`text-xs font-medium ${TREND_COLOR[data.overallTrend]}`}
          >
            {TREND_ICON[data.overallTrend]}
          </span>
        </div>
      </div>

      {/* ── 综合评分与阶段描述 ── */}
      <div className="flex items-end gap-3 mb-1">
        <span
          className={`text-5xl font-bold tabular-nums ${getScoreColor(data.overallScore)}`}
        >
          {data.overallScore}
        </span>
        <span className="text-slate-400 text-sm mb-2">/ 100</span>
        <div className="ml-auto text-right">
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            {data.phase}
          </p>
        </div>
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
        {data.summary}
      </p>

      {/* ── 雷达图 ── */}
      <div className="flex-1 min-h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart
            data={chartData}
            margin={{ top: 20, right: 30, bottom: 20, left: 30 }}
            onClick={handleChartClick as (event: unknown) => void}
            onMouseMove={handleMouseMove as (event: unknown) => void}
            onMouseLeave={handleMouseLeave}
          >
            {/* 网格 */}
            <PolarGrid
              gridType="polygon"
              stroke="#334155"
              strokeOpacity={0.5}
            />

            {/* 维度轴标签（自定义 Tick，支持危险状态标红和点击下钻） */}
            <PolarAngleAxis
              dataKey="name"
              tick={(props) => (
                <CustomAngleTick
                  {...props}
                  dimensions={data.dimensions}
                  activeDimId={activeDimId}
                  onDrillDown={onDrillDown}
                />
              )}
              tickLine={false}
            />

            {/* 刻度轴（隐藏数值，保持简洁） */}
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={false}
              axisLine={false}
            />

            {/* 目标状态多边形（虚线，无填充） */}
            <Radar
              name="目标"
              dataKey="target"
              stroke="#64748b"
              strokeWidth={1.5}
              strokeDasharray="4 3"
              fill="transparent"
              dot={false}
            />

            {/* 当前状态多边形（实线，半透明填充） */}
            <Radar
              name="当前"
              dataKey="current"
              stroke="#6366f1"
              strokeWidth={2}
              fill="#6366f1"
              fillOpacity={0.2}
              dot={(props) => {
                const { cx, cy, payload } = props as {
                  cx: number;
                  cy: number;
                  payload: { fullData: RadarDimension };
                };
                const dim = payload?.fullData;
                if (!dim) return <circle key={`dot-${cx}-${cy}`} cx={cx} cy={cy} r={0} />;
                const dangerous = isDangerous(dim);
                const isActive = activeDimId === dim.id;
                return (
                  <circle
                    key={`dot-${dim.id}`}
                    cx={cx}
                    cy={cy}
                    r={isActive ? 6 : 4}
                    fill={dangerous ? '#ef4444' : '#6366f1'}
                    stroke={dangerous ? '#fca5a5' : '#818cf8'}
                    strokeWidth={isActive ? 2 : 1}
                    style={{ cursor: onDrillDown ? 'pointer' : 'default' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onDrillDown?.(dim.id);
                    }}
                  />
                );
              }}
              activeDot={(props) => {
                const { cx, cy, payload } = props as {
                  cx: number;
                  cy: number;
                  payload: { fullData: RadarDimension };
                };
                const dim = payload?.fullData;
                if (!dim) return <circle key={`adot-${cx}-${cy}`} cx={cx} cy={cy} r={0} />;
                const dangerous = isDangerous(dim);
                return (
                  <circle
                    key={`adot-${dim.id}`}
                    cx={cx}
                    cy={cy}
                    r={7}
                    fill={dangerous ? '#ef4444' : '#6366f1'}
                    stroke={dangerous ? '#fca5a5' : '#a5b4fc'}
                    strokeWidth={2}
                    style={{ cursor: onDrillDown ? 'pointer' : 'default' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onDrillDown?.(dim.id);
                    }}
                  />
                );
              }}
            />

            {/* 自定义 Tooltip（悬浮概要层） */}
            <Tooltip
              content={<CustomRechartsTooltip />}
              cursor={false}
              wrapperStyle={{ zIndex: 50 }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* ── 图例说明 ── */}
      <div className="flex items-center justify-center gap-5 mt-3 pt-3 border-t border-slate-100 dark:border-slate-700">
        <div className="flex items-center gap-1.5">
          <div className="w-4 h-0.5 bg-indigo-500 rounded" />
          <span className="text-xs text-slate-500">当前状态</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div
            className="w-4 h-0.5 rounded"
            style={{
              background: 'repeating-linear-gradient(90deg, #64748b 0, #64748b 4px, transparent 4px, transparent 7px)',
            }}
          />
          <span className="text-xs text-slate-500">目标状态</span>
        </div>
        {dangerousCount > 0 && (
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-xs text-red-400">低于警戒线</span>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// 默认导出
// =============================================================================

export default HealthRadarChart;

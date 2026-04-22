import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';


// =============================================================================
// 组件数据绑定说明
// 组件 Key: ecosystem_health_map
// 组件类型: 详情组件 (Detail Component)
// 适用模块: 内容与社区、平台生态
//
// 数据来源: 来自创作者/供给方分层统计数据
// 展示字段: 各层级人数规模占比、价值贡献占比、环比变化趋势
// 核心目标: 直观反映生态集中度，预警固化风险（头部过度集中）
// 支持功能: 本周 vs 上周时间维度对比
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// Section 1: TypeScript 接口定义
// ─────────────────────────────────────────────────────────────────────────────

/** 生态层级标识 */
export type EcosystemTier = 'top' | 'middle' | 'tail';

/** 生态健康度状态 */
export type EcosystemStatus = 'healthy' | 'warning' | 'danger';

/** 单个层级的数据结构 */
export interface TierData {
  /** 层级标识 */
  id: EcosystemTier;
  /** 层级名称，如 "头部 Top 5%" */
  name: string;
  /** 人数规模绝对值 */
  population: number;
  /** 人数规模占比 (0-100) */
  populationRatio: number;
  /** 价值贡献绝对值（如发文量、GMV 等） */
  contribution: number;
  /** 价值贡献占比 (0-100) */
  contributionRatio: number;
  /** 环比变化：人数占比变化（百分点，正值=增加） */
  populationRatioChange?: number;
  /** 环比变化：贡献占比变化（百分点，正值=增加） */
  contributionRatioChange?: number;
}

/** 组件整体数据结构 */
export interface EcosystemHealthData {
  /** 价值贡献的指标名称，如 "内容产出量"、"GMV 贡献" */
  contributionMetricName: string;
  /** 当前周期数据 */
  currentPeriod: {
    label: string;
    tiers: TierData[];
  };
  /** 对比周期数据（可选） */
  previousPeriod?: {
    label: string;
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

// ─────────────────────────────────────────────────────────────────────────────
// Section 2: Mock 数据（供开发预览使用，生产环境替换为真实数据）
// ─────────────────────────────────────────────────────────────────────────────

export const mockEcosystemData: EcosystemHealthData = {
  contributionMetricName: '内容产出量',
  status: 'warning',
  concentrationWarningThreshold: 80,
  insights: [
    '头部 5% 的创作者贡献了 82% 的内容，存在较高的单点依赖风险。',
    '腰部创作者贡献占比环比下降 2%，生态固化趋势加剧，建议加大腰部流量扶持。',
    '尾部创作者人数占比增加 3%，但贡献度持续偏低，新手激励机制有待优化。',
  ],
  currentPeriod: {
    label: '本周',
    tiers: [
      {
        id: 'top',
        name: '头部',
        population: 500,
        populationRatio: 5,
        contribution: 8200,
        contributionRatio: 82,
        populationRatioChange: 0,
        contributionRatioChange: 3,
      },
      {
        id: 'middle',
        name: '腰部',
        population: 2000,
        populationRatio: 20,
        contribution: 1500,
        contributionRatio: 15,
        populationRatioChange: -3,
        contributionRatioChange: -2,
      },
      {
        id: 'tail',
        name: '尾部',
        population: 7500,
        populationRatio: 75,
        contribution: 300,
        contributionRatio: 3,
        populationRatioChange: 3,
        contributionRatioChange: -1,
      },
    ],
  },
  previousPeriod: {
    label: '上周',
    tiers: [
      {
        id: 'top',
        name: '头部',
        population: 500,
        populationRatio: 5,
        contribution: 7900,
        contributionRatio: 79,
      },
      {
        id: 'middle',
        name: '腰部',
        population: 2300,
        populationRatio: 23,
        contribution: 1700,
        contributionRatio: 17,
      },
      {
        id: 'tail',
        name: '尾部',
        population: 7200,
        populationRatio: 72,
        contribution: 400,
        contributionRatio: 4,
      },
    ],
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Section 3: 常量与工具函数
// ─────────────────────────────────────────────────────────────────────────────

/** 层级颜色配置 */
const TIER_CONFIG: Record<EcosystemTier, {
  label: string;
  color: string;         // Tailwind 文字颜色
  barColor: string;      // Recharts 图表颜色（hex）
  bgColor: string;       // Tailwind 背景颜色
  borderColor: string;   // Tailwind 边框颜色
}> = {
  top: {
    label: '头部',
    color: 'text-indigo-400',
    barColor: '#818cf8',
    bgColor: 'bg-indigo-400/10',
    borderColor: 'border-indigo-400/30',
  },
  middle: {
    label: '腰部',
    color: 'text-sky-400',
    barColor: '#38bdf8',
    bgColor: 'bg-sky-400/10',
    borderColor: 'border-sky-400/30',
  },
  tail: {
    label: '尾部',
    color: 'text-slate-400',
    barColor: '#94a3b8',
    bgColor: 'bg-slate-400/10',
    borderColor: 'border-slate-400/30',
  },
};

/** 生态状态配置 */
const STATUS_CONFIG: Record<EcosystemStatus, {
  label: string;
  color: string;
  bg: string;
  border: string;
  dot: string;
  icon: string;
}> = {
  healthy: {
    label: '生态健康',
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
    border: 'border-emerald-400/30',
    dot: 'bg-emerald-400',
    icon: '✓',
  },
  warning: {
    label: '头部固化预警',
    color: 'text-amber-400',
    bg: 'bg-amber-400/10',
    border: 'border-amber-400/30',
    dot: 'bg-amber-400',
    icon: '⚠',
  },
  danger: {
    label: '生态失衡危险',
    color: 'text-red-400',
    bg: 'bg-red-400/10',
    border: 'border-red-400/30',
    dot: 'bg-red-400',
    icon: '✕',
  },
};

/** 格式化数字：超过 10000 显示为万 */
function formatNumber(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  return n.toLocaleString();
}

/** 格式化变化量（带符号） */
function formatChange(v?: number): string {
  if (v === undefined) return '-';
  if (v === 0) return '持平';
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}pp`;
}

/** 变化量颜色（对于贡献占比，增加是负面的；对于人数，视具体语境） */
function getChangeColor(v?: number, inverse = false): string {
  if (v === undefined || v === 0) return 'text-slate-400';
  const isPositive = inverse ? v < 0 : v > 0;
  return isPositive ? 'text-emerald-400' : 'text-red-400';
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 4: 子组件
// ─────────────────────────────────────────────────────────────────────────────

// ── 4.1 自定义 Tooltip ────────────────────────────────────────────────────────

interface ChartTooltipData {
  tier: TierData;
  metricName: string;
  side: 'population' | 'contribution';
}

function EcosystemTooltip({ tier, metricName, side }: ChartTooltipData) {
  const cfg = TIER_CONFIG[tier.id];
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3 shadow-xl text-xs min-w-[160px]">
      <div className={`font-semibold mb-2 ${cfg.color}`}>{tier.name}层创作者</div>
      {side === 'population' ? (
        <>
          <div className="flex justify-between gap-4 mb-1">
            <span className="text-slate-400">人数规模</span>
            <span className="font-medium text-slate-700 dark:text-slate-200">{formatNumber(tier.population)} 人</span>
          </div>
          <div className="flex justify-between gap-4 mb-1">
            <span className="text-slate-400">人数占比</span>
            <span className="font-medium text-slate-700 dark:text-slate-200">{tier.populationRatio}%</span>
          </div>
          {tier.populationRatioChange !== undefined && (
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">环比变化</span>
              <span className={`font-medium ${getChangeColor(tier.populationRatioChange)}`}>
                {formatChange(tier.populationRatioChange)}
              </span>
            </div>
          )}
        </>
      ) : (
        <>
          <div className="flex justify-between gap-4 mb-1">
            <span className="text-slate-400">{metricName}</span>
            <span className="font-medium text-slate-700 dark:text-slate-200">{formatNumber(tier.contribution)}</span>
          </div>
          <div className="flex justify-between gap-4 mb-1">
            <span className="text-slate-400">贡献占比</span>
            <span className="font-medium text-slate-700 dark:text-slate-200">{tier.contributionRatio}%</span>
          </div>
          {tier.contributionRatioChange !== undefined && (
            <div className="flex justify-between gap-4">
              <span className="text-slate-400">环比变化</span>
              <span className={`font-medium ${getChangeColor(tier.contributionRatioChange, true)}`}>
                {formatChange(tier.contributionRatioChange)}
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── 4.2 双向条形图（核心可视化）────────────────────────────────────────────────

interface BiDirectionalChartProps {
  tiers: TierData[];
  metricName: string;
  label: string;
  showWarning: boolean;
  warningThreshold: number;
}

/** 为 Recharts 构建双向图数据 */
function buildChartData(tiers: TierData[]) {
  return tiers.map((tier) => ({
    name: tier.name,
    id: tier.id,
    // 人数占比：向左延伸，使用负值
    populationRatio: -tier.populationRatio,
    // 贡献占比：向右延伸，正值
    contributionRatio: tier.contributionRatio,
    // 原始数据引用（用于 Tooltip）
    _raw: tier,
  }));
}

interface CustomBarLabelProps {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  value?: number;
  side?: 'left' | 'right';
}

function CustomBarLabel({ x = 0, y = 0, width = 0, height = 0, value = 0, side = 'right' }: CustomBarLabelProps) {
  const absValue = Math.abs(value);
  if (absValue === 0) return null;

  const labelX = side === 'left' ? x - 4 : x + width + 4;
  const labelY = y + height / 2;
  const anchor = side === 'left' ? 'end' : 'start';

  return (
    <text
      x={labelX}
      y={labelY}
      dy={4}
      textAnchor={anchor}
      fontSize={11}
      fill="#94a3b8"
    >
      {absValue}%
    </text>
  );
}

function BiDirectionalChart({ tiers, metricName, label, showWarning, warningThreshold }: BiDirectionalChartProps) {
  const [activeBar, setActiveBar] = useState<{ tierId: EcosystemTier; side: 'population' | 'contribution' } | null>(null);
  const chartData = buildChartData(tiers);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const CustomTooltipRenderer = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
    if (!active || !payload || payload.length === 0) return null;
    const entry = payload[0];
    if (!entry || !entry.payload) return null;
    const raw = (entry.payload as ReturnType<typeof buildChartData>[0])._raw;
    const side: 'population' | 'contribution' = entry.dataKey === 'populationRatio' ? 'population' : 'contribution';
    return <EcosystemTooltip tier={raw} metricName={metricName} side={side} />;
  };

  return (
    <div className="w-full">
      {/* 图表标题行 */}
      <div className="flex items-center justify-between mb-3 px-1">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">← 人数规模占比</span>
        <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 px-3 py-1 rounded-full">
          {label}
        </span>
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{metricName}贡献占比 →</span>
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 48, left: 48, bottom: 4 }}
          barSize={28}
          barGap={4}
        >
          <CartesianGrid horizontal={false} stroke="#334155" strokeOpacity={0.3} />
          <XAxis
            type="number"
            domain={[-100, 100]}
            tickFormatter={(v) => `${Math.abs(v)}%`}
            tick={{ fontSize: 10, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 12, fill: '#94a3b8', fontWeight: 600 }}
            axisLine={false}
            tickLine={false}
            width={32}
          />
          <ReferenceLine x={0} stroke="#475569" strokeWidth={1.5} />
          <Tooltip content={<CustomTooltipRenderer />} cursor={{ fill: 'rgba(148,163,184,0.05)' }} />

          {/* 人数占比（向左，负值） */}
          <Bar
            dataKey="populationRatio"
            name="人数规模占比"
            radius={[4, 0, 0, 4]}
            label={<CustomBarLabel side="left" />}
            onMouseEnter={(data) => {
              const tierId = (data as unknown as { id: string }).id as EcosystemTier;
              setActiveBar({ tierId, side: 'population' });
            }}
            onMouseLeave={() => setActiveBar(null)}
          >
            {chartData.map((entry) => (
              <Cell
                key={entry.id}
                fill={TIER_CONFIG[entry.id as EcosystemTier].barColor}
                fillOpacity={activeBar && activeBar.tierId !== entry.id ? 0.4 : 0.85}
              />
            ))}
          </Bar>

          {/* 贡献占比（向右，正值） */}
          <Bar
            dataKey="contributionRatio"
            name={`${metricName}贡献占比`}
            radius={[0, 4, 4, 0]}
            label={<CustomBarLabel side="right" />}
            onMouseEnter={(data) => {
              const tierId = (data as unknown as { id: string }).id as EcosystemTier;
              setActiveBar({ tierId, side: 'contribution' });
            }}
            onMouseLeave={() => setActiveBar(null)}
          >
            {chartData.map((entry) => {
              const isTopTier = entry.id === 'top';
              const isOverThreshold = isTopTier && entry.contributionRatio >= warningThreshold;
              return (
                <Cell
                  key={entry.id}
                  fill={isOverThreshold && showWarning ? '#f87171' : TIER_CONFIG[entry.id as EcosystemTier].barColor}
                  fillOpacity={activeBar && activeBar.tierId !== entry.id ? 0.4 : 0.85}
                />
              );
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── 4.3 层级数据卡片（详细数字展示）────────────────────────────────────────────

interface TierCardProps {
  tier: TierData;
  metricName: string;
  showChange: boolean;
}

function TierCard({ tier, metricName, showChange }: TierCardProps) {
  const cfg = TIER_CONFIG[tier.id];
  return (
    <div className={`rounded-xl border ${cfg.borderColor} ${cfg.bgColor} p-3 flex flex-col gap-1.5`}>
      <div className={`text-xs font-semibold ${cfg.color} mb-0.5`}>{tier.name}</div>

      {/* 人数规模 */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500 dark:text-slate-400">人数占比</span>
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-bold text-slate-700 dark:text-slate-200 tabular-nums">
            {tier.populationRatio}%
          </span>
          {showChange && tier.populationRatioChange !== undefined && (
            <span className={`text-xs ${getChangeColor(tier.populationRatioChange)}`}>
              {formatChange(tier.populationRatioChange)}
            </span>
          )}
        </div>
      </div>

      {/* 人数进度条 */}
      <div className="h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${tier.populationRatio}%`, backgroundColor: cfg.barColor }}
        />
      </div>

      {/* 贡献占比 */}
      <div className="flex items-center justify-between mt-1">
        <span className="text-xs text-slate-500 dark:text-slate-400">{metricName}贡献</span>
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-bold text-slate-700 dark:text-slate-200 tabular-nums">
            {tier.contributionRatio}%
          </span>
          {showChange && tier.contributionRatioChange !== undefined && (
            <span className={`text-xs ${getChangeColor(tier.contributionRatioChange, true)}`}>
              {formatChange(tier.contributionRatioChange)}
            </span>
          )}
        </div>
      </div>

      {/* 贡献进度条 */}
      <div className="h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${tier.contributionRatio}%`, backgroundColor: cfg.barColor }}
        />
      </div>

      {/* 绝对值 */}
      <div className="flex items-center justify-between mt-0.5 text-xs text-slate-400">
        <span>{formatNumber(tier.population)} 人</span>
        <span>{formatNumber(tier.contribution)}</span>
      </div>
    </div>
  );
}

// ── 4.4 集中度指示器（可视化头部贡献 vs 人数的反差）────────────────────────────

interface ConcentrationIndicatorProps {
  topTier: TierData;
  threshold: number;
  metricName: string;
}

function ConcentrationIndicator({ topTier, threshold, metricName }: ConcentrationIndicatorProps) {
  const ratio = topTier.contributionRatio / topTier.populationRatio;
  const isWarning = topTier.contributionRatio >= threshold;

  return (
    <div className={`rounded-xl border p-3 ${isWarning ? 'border-amber-400/40 bg-amber-400/5' : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">生态集中度指数</span>
        {isWarning && (
          <span className="text-xs text-amber-400 font-medium bg-amber-400/10 px-2 py-0.5 rounded-full">
            ⚠ 集中度过高
          </span>
        )}
      </div>
      <div className="flex items-end gap-2 mb-2">
        <span className={`text-3xl font-bold tabular-nums ${isWarning ? 'text-amber-400' : 'text-slate-700 dark:text-slate-200'}`}>
          {ratio.toFixed(1)}x
        </span>
        <span className="text-xs text-slate-400 mb-1">
          头部人均{metricName}是整体均值的 {ratio.toFixed(1)} 倍
        </span>
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
        头部 <span className={`font-semibold ${isWarning ? 'text-amber-400' : 'text-indigo-400'}`}>{topTier.populationRatio}%</span> 的创作者
        贡献了 <span className={`font-semibold ${isWarning ? 'text-amber-400' : 'text-indigo-400'}`}>{topTier.contributionRatio}%</span> 的{metricName}
        {isWarning && (
          <span className="text-amber-400">，超过预警阈值 {threshold}%</span>
        )}
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 5: 主组件
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 创作者/供给方生态图组件 (Ecosystem Health Map)
 *
 * 通过双向堆叠柱状图对比头、腰、尾部创作者的人数规模占比与价值贡献占比，
 * 直观反映生态集中度，并在头部贡献超过预警阈值时高亮警示。
 * 支持本周 vs 上周时间维度对比。
 *
 * @example
 * <EcosystemHealthMap data={mockEcosystemData} />
 */
export function EcosystemHealthMap({ data, className = '' }: EcosystemHealthMapProps) {
  const [activePeriod, setActivePeriod] = useState<'current' | 'previous'>('current');
  const hasPreviousPeriod = !!data.previousPeriod;
  const threshold = data.concentrationWarningThreshold ?? 80;
  const statusCfg = STATUS_CONFIG[data.status];

  const displayData = activePeriod === 'current'
    ? data.currentPeriod
    : (data.previousPeriod ?? data.currentPeriod);

  const topTier = displayData.tiers.find((t) => t.id === 'top')!;
  const showChange = activePeriod === 'current' && hasPreviousPeriod;

  return (
    <div
      className={`
        rounded-2xl border border-slate-200 dark:border-slate-700
        bg-white dark:bg-slate-800/60
        p-5 flex flex-col gap-5
        ${className}
      `}
    >
      {/* ── 头部信息区 ── */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-semibold uppercase tracking-widest text-violet-500">
            创作者生态图
          </span>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
            供给方生态健康度
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            各层级创作者人数规模 vs {data.contributionMetricName}贡献分布
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          {/* 状态标签 */}
          <span className={`inline-flex items-center gap-1.5 rounded-full text-xs font-medium px-2.5 py-1 border ${statusCfg.bg} ${statusCfg.color} ${statusCfg.border}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${statusCfg.dot}`} />
            {statusCfg.icon} {statusCfg.label}
          </span>

          {/* 时间维度切换 */}
          {hasPreviousPeriod && (
            <div className="flex rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700 text-xs">
              <button
                className={`px-3 py-1.5 transition-colors ${activePeriod === 'current'
                  ? 'bg-violet-500 text-white font-medium'
                  : 'bg-transparent text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
                  }`}
                onClick={() => setActivePeriod('current')}
              >
                {data.currentPeriod.label}
              </button>
              <button
                className={`px-3 py-1.5 transition-colors ${activePeriod === 'previous'
                  ? 'bg-violet-500 text-white font-medium'
                  : 'bg-transparent text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
                  }`}
                onClick={() => setActivePeriod('previous')}
              >
                {data.previousPeriod!.label}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── 集中度指示器 ── */}
      <ConcentrationIndicator
        topTier={topTier}
        threshold={threshold}
        metricName={data.contributionMetricName}
      />

      {/* ── 双向条形图（核心可视化） ── */}
      <BiDirectionalChart
        tiers={displayData.tiers}
        metricName={data.contributionMetricName}
        label={displayData.label}
        showWarning={data.status !== 'healthy'}
        warningThreshold={threshold}
      />

      {/* ── 层级数据卡片（三列） ── */}
      <div className="grid grid-cols-3 gap-3">
        {displayData.tiers.map((tier) => (
          <TierCard
            key={tier.id}
            tier={tier}
            metricName={data.contributionMetricName}
            showChange={showChange}
          />
        ))}
      </div>

      {/* ── 本周 vs 上周对比说明（仅在查看当前周期且有对比数据时显示） ── */}
      {showChange && data.previousPeriod && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 p-3">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
            环比变化摘要（{data.currentPeriod.label} vs {data.previousPeriod.label}）
          </div>
          <div className="grid grid-cols-3 gap-2">
            {data.currentPeriod.tiers.map((tier) => {
              const prevTier = data.previousPeriod!.tiers.find((t) => t.id === tier.id);
              if (!prevTier) return null;
              const contribDiff = tier.contributionRatio - prevTier.contributionRatio;
              const popDiff = tier.populationRatio - prevTier.populationRatio;
              const cfg = TIER_CONFIG[tier.id];
              return (
                <div key={tier.id} className="text-xs">
                  <div className={`font-semibold mb-1 ${cfg.color}`}>{tier.name}</div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>人数</span>
                    <span className={getChangeColor(popDiff)}>{formatChange(popDiff)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>贡献</span>
                    <span className={getChangeColor(contribDiff, true)}>{formatChange(contribDiff)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 洞察与预警区 ── */}
      {data.insights.length > 0 && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 p-3">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
            ✦ 生态洞察
          </div>
          <ul className="space-y-1.5">
            {data.insights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                <span className="text-violet-400 mt-0.5 shrink-0">•</span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 6: 默认导出（用于懒加载场景）
// ─────────────────────────────────────────────────────────────────────────────

export default EcosystemHealthMap;

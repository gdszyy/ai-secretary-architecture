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
//
// 样式版本: v2.0 — iOS 26 Liquid Glass Design System
// 升级日期: 2026-04-22
// 升级内容: 毛玻璃卡片容器、顶部高光线 inset shadow、oklch 语义色、
//           DM Sans + Noto Sans SC 字体、Hover 动效、深色模式双主题
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

/**
 * 层级颜色配置 — iOS 26 Liquid Glass oklch 语义色
 *
 * 颜色体系说明：
 *   头部 (top)   — 紫罗兰 violet，oklch(0.60 0.22 290)
 *   腰部 (middle) — 天蓝 sky，     oklch(0.65 0.18 220)
 *   尾部 (tail)   — 石板 slate，   oklch(0.60 0.04 250)
 *
 * barColor 使用 oklch() 字面量，直接传给 Recharts Cell fill。
 * Tailwind 任意值语法：text-[oklch(...)] / bg-[oklch(...)/0.12]
 */
const TIER_CONFIG: Record<EcosystemTier, {
  label: string;
  /** Tailwind 文字颜色（oklch 任意值） */
  color: string;
  /** Recharts Cell fill — oklch 字面量 */
  barColor: string;
  /** Tailwind 背景（含透明度） */
  bgColor: string;
  /** Tailwind 边框（含透明度） */
  borderColor: string;
}> = {
  top: {
    label: '头部',
    color: 'text-[oklch(0.60_0.22_290)]  dark:text-[oklch(0.72_0.20_290)]',
    barColor: 'oklch(0.60 0.22 290)',
    bgColor: 'bg-[oklch(0.60_0.22_290/0.10)] dark:bg-[oklch(0.72_0.20_290/0.12)]',
    borderColor: 'border-[oklch(0.60_0.22_290/0.30)] dark:border-[oklch(0.72_0.20_290/0.25)]',
  },
  middle: {
    label: '腰部',
    color: 'text-[oklch(0.65_0.18_220)] dark:text-[oklch(0.75_0.16_220)]',
    barColor: 'oklch(0.65 0.18 220)',
    bgColor: 'bg-[oklch(0.65_0.18_220/0.10)] dark:bg-[oklch(0.75_0.16_220/0.12)]',
    borderColor: 'border-[oklch(0.65_0.18_220/0.30)] dark:border-[oklch(0.75_0.16_220/0.25)]',
  },
  tail: {
    label: '尾部',
    color: 'text-[oklch(0.60_0.04_250)] dark:text-[oklch(0.70_0.04_250)]',
    barColor: 'oklch(0.60 0.04 250)',
    bgColor: 'bg-[oklch(0.60_0.04_250/0.08)] dark:bg-[oklch(0.70_0.04_250/0.10)]',
    borderColor: 'border-[oklch(0.60_0.04_250/0.25)] dark:border-[oklch(0.70_0.04_250/0.20)]',
  },
};

/**
 * 生态状态配置 — oklch 语义色
 *
 *   healthy — 翠绿 emerald，oklch(0.65 0.18 160)
 *   warning — 琥珀 amber，  oklch(0.72 0.18  80)
 *   danger  — 红色 red，    oklch(0.60 0.22  25)
 */
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
    color: 'text-[oklch(0.65_0.18_160)] dark:text-[oklch(0.75_0.16_160)]',
    bg: 'bg-[oklch(0.65_0.18_160/0.10)] dark:bg-[oklch(0.75_0.16_160/0.12)]',
    border: 'border-[oklch(0.65_0.18_160/0.30)] dark:border-[oklch(0.75_0.16_160/0.25)]',
    dot: 'bg-[oklch(0.65_0.18_160)] dark:bg-[oklch(0.75_0.16_160)]',
    icon: '✓',
  },
  warning: {
    label: '头部固化预警',
    color: 'text-[oklch(0.72_0.18_80)] dark:text-[oklch(0.82_0.16_80)]',
    bg: 'bg-[oklch(0.72_0.18_80/0.10)] dark:bg-[oklch(0.82_0.16_80/0.12)]',
    border: 'border-[oklch(0.72_0.18_80/0.35)] dark:border-[oklch(0.82_0.16_80/0.28)]',
    dot: 'bg-[oklch(0.72_0.18_80)] dark:bg-[oklch(0.82_0.16_80)]',
    icon: '⚠',
  },
  danger: {
    label: '生态失衡危险',
    color: 'text-[oklch(0.60_0.22_25)] dark:text-[oklch(0.72_0.20_25)]',
    bg: 'bg-[oklch(0.60_0.22_25/0.10)] dark:bg-[oklch(0.72_0.20_25/0.12)]',
    border: 'border-[oklch(0.60_0.22_25/0.35)] dark:border-[oklch(0.72_0.20_25/0.28)]',
    dot: 'bg-[oklch(0.60_0.22_25)] dark:bg-[oklch(0.72_0.20_25)]',
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
  if (v === undefined || v === 0) return 'text-[oklch(0.60_0.04_250)] dark:text-[oklch(0.70_0.04_250)]';
  const isPositive = inverse ? v < 0 : v > 0;
  return isPositive
    ? 'text-[oklch(0.65_0.18_160)] dark:text-[oklch(0.75_0.16_160)]'
    : 'text-[oklch(0.60_0.22_25)] dark:text-[oklch(0.72_0.20_25)]';
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 4: 子组件
// ─────────────────────────────────────────────────────────────────────────────

// ── 4.1 自定义 Tooltip（Liquid Glass 毛玻璃浮层）────────────────────────────────

interface ChartTooltipData {
  tier: TierData;
  metricName: string;
  side: 'population' | 'contribution';
}

/**
 * 毛玻璃 Tooltip
 * 样式：backdrop-blur-xl + bg-white/75 dark:bg-white/8 + 顶部高光线 + 圆角 rounded-xl
 */
function EcosystemTooltip({ tier, metricName, side }: ChartTooltipData) {
  const cfg = TIER_CONFIG[tier.id];
  return (
    <div
      className={`
        rounded-xl
        border border-[oklch(1_0_0/0.18)] dark:border-[oklch(1_0_0/0.12)]
        bg-white/75 dark:bg-white/8
        backdrop-blur-xl
        shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_8px_32px_-4px_oklch(0_0_0/0.12)]
        p-3 text-xs min-w-[160px]
        font-sans
      `}
    >
      <div className={`font-semibold mb-2 ${cfg.color}`}>{tier.name}层创作者</div>
      {side === 'population' ? (
        <>
          <div className="flex justify-between gap-4 mb-1">
            <span className="text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">人数规模</span>
            <span className="font-medium text-[oklch(0.25_0.02_250)] dark:text-[oklch(0.92_0.01_250)] tabular-nums">
              {formatNumber(tier.population)} 人
            </span>
          </div>
          <div className="flex justify-between gap-4 mb-1">
            <span className="text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">人数占比</span>
            <span className="font-medium text-[oklch(0.25_0.02_250)] dark:text-[oklch(0.92_0.01_250)] tabular-nums">
              {tier.populationRatio}%
            </span>
          </div>
          {tier.populationRatioChange !== undefined && (
            <div className="flex justify-between gap-4">
              <span className="text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">环比变化</span>
              <span className={`font-medium ${getChangeColor(tier.populationRatioChange)}`}>
                {formatChange(tier.populationRatioChange)}
              </span>
            </div>
          )}
        </>
      ) : (
        <>
          <div className="flex justify-between gap-4 mb-1">
            <span className="text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">{metricName}</span>
            <span className="font-medium text-[oklch(0.25_0.02_250)] dark:text-[oklch(0.92_0.01_250)] tabular-nums">
              {formatNumber(tier.contribution)}
            </span>
          </div>
          <div className="flex justify-between gap-4 mb-1">
            <span className="text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">贡献占比</span>
            <span className="font-medium text-[oklch(0.25_0.02_250)] dark:text-[oklch(0.92_0.01_250)] tabular-nums">
              {tier.contributionRatio}%
            </span>
          </div>
          {tier.contributionRatioChange !== undefined && (
            <div className="flex justify-between gap-4">
              <span className="text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">环比变化</span>
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
      // oklch(0.60 0.04 250) ≈ slate-500
      fill="oklch(0.60 0.04 250)"
      fontFamily="'DM Sans', 'Noto Sans SC', sans-serif"
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
        <span className="text-xs font-medium text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">
          ← 人数规模占比
        </span>
        <span
          className={`
            text-xs font-semibold
            text-[oklch(0.30_0.02_250)] dark:text-[oklch(0.88_0.01_250)]
            bg-[oklch(0.96_0.01_250/0.80)] dark:bg-[oklch(1_0_0/0.08)]
            backdrop-blur-sm
            border border-[oklch(0_0_0/0.06)] dark:border-[oklch(1_0_0/0.10)]
            px-3 py-1 rounded-full
            shadow-[inset_0_1px_0_0_oklch(1_0_0/0.40)]
          `}
        >
          {label}
        </span>
        <span className="text-xs font-medium text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">
          {metricName}贡献占比 →
        </span>
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 48, left: 48, bottom: 4 }}
          barSize={28}
          barGap={4}
        >
          {/* oklch(0.30 0.02 250 / 0.15) ≈ 深色网格线 */}
          <CartesianGrid horizontal={false} stroke="oklch(0.30 0.02 250)" strokeOpacity={0.15} />
          <XAxis
            type="number"
            domain={[-100, 100]}
            tickFormatter={(v) => `${Math.abs(v)}%`}
            tick={{ fontSize: 10, fill: 'oklch(0.55 0.04 250)', fontFamily: "'DM Sans', sans-serif" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 12, fill: 'oklch(0.60 0.04 250)', fontWeight: 600, fontFamily: "'Noto Sans SC', sans-serif" }}
            axisLine={false}
            tickLine={false}
            width={32}
          />
          {/* 中轴线 oklch(0.45 0.04 250) ≈ slate-600 */}
          <ReferenceLine x={0} stroke="oklch(0.45 0.04 250)" strokeWidth={1.5} />
          <Tooltip
            content={<CustomTooltipRenderer />}
            cursor={{ fill: 'oklch(0.60 0.04 250 / 0.05)' }}
          />

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
                fillOpacity={activeBar && activeBar.tierId !== entry.id ? 0.35 : 0.88}
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
              // 预警色：oklch(0.60 0.22 25) ≈ red-500
              return (
                <Cell
                  key={entry.id}
                  fill={isOverThreshold && showWarning ? 'oklch(0.60 0.22 25)' : TIER_CONFIG[entry.id as EcosystemTier].barColor}
                  fillOpacity={activeBar && activeBar.tierId !== entry.id ? 0.35 : 0.88}
                />
              );
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── 4.3 层级数据卡片（Liquid Glass 内层卡片）────────────────────────────────────

interface TierCardProps {
  tier: TierData;
  metricName: string;
  showChange: boolean;
}

/**
 * 层级数据卡片
 * 样式：内层 rounded-xl + 毛玻璃背景 + 顶部高光线 + Hover 上浮动效
 */
function TierCard({ tier, metricName, showChange }: TierCardProps) {
  const cfg = TIER_CONFIG[tier.id];
  return (
    <div
      className={`
        rounded-xl
        border ${cfg.borderColor}
        ${cfg.bgColor}
        backdrop-blur-sm
        shadow-[inset_0_1px_0_0_oklch(1_0_0/0.45),inset_0_-1px_0_0_oklch(0_0_0/0.04),0_2px_12px_-2px_oklch(0_0_0/0.06)]
        p-3 flex flex-col gap-1.5
        hover:-translate-y-1 hover:shadow-xl
        transition-all duration-[250ms] ease-out
        cursor-default
        font-sans
      `}
    >
      <div className={`text-xs font-semibold mb-0.5 ${cfg.color}`}>{tier.name}</div>

      {/* 人数规模 */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">人数占比</span>
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-bold text-[oklch(0.20_0.02_250)] dark:text-[oklch(0.92_0.01_250)] tabular-nums tracking-tight">
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
      <div className="h-1 bg-[oklch(0.88_0.01_250/0.60)] dark:bg-[oklch(1_0_0/0.08)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${tier.populationRatio}%`, backgroundColor: cfg.barColor }}
        />
      </div>

      {/* 贡献占比 */}
      <div className="flex items-center justify-between mt-1">
        <span className="text-xs text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">{metricName}贡献</span>
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-bold text-[oklch(0.20_0.02_250)] dark:text-[oklch(0.92_0.01_250)] tabular-nums tracking-tight">
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
      <div className="h-1 bg-[oklch(0.88_0.01_250/0.60)] dark:bg-[oklch(1_0_0/0.08)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${tier.contributionRatio}%`, backgroundColor: cfg.barColor }}
        />
      </div>

      {/* 绝对值 */}
      <div className="flex items-center justify-between mt-0.5 text-xs text-[oklch(0.60_0.04_250)] dark:text-[oklch(0.68_0.04_250)] tabular-nums">
        <span>{formatNumber(tier.population)} 人</span>
        <span>{formatNumber(tier.contribution)}</span>
      </div>
    </div>
  );
}

// ── 4.4 集中度指示器（Liquid Glass 内层卡片 + KPI 核心数值规范）────────────────

interface ConcentrationIndicatorProps {
  topTier: TierData;
  threshold: number;
  metricName: string;
}

/**
 * 集中度指示器
 * KPI 核心数值：text-3xl font-bold tracking-tight（iOS 26 规范）
 * 样式：内层 rounded-xl + 毛玻璃 + Hover 上浮
 */
function ConcentrationIndicator({ topTier, threshold, metricName }: ConcentrationIndicatorProps) {
  const ratio = topTier.contributionRatio / topTier.populationRatio;
  const isWarning = topTier.contributionRatio >= threshold;

  return (
    <div
      className={`
        rounded-xl
        border
        ${isWarning
          ? 'border-[oklch(0.72_0.18_80/0.40)] dark:border-[oklch(0.82_0.16_80/0.30)] bg-[oklch(0.72_0.18_80/0.06)] dark:bg-[oklch(0.82_0.16_80/0.08)]'
          : 'border-[oklch(0_0_0/0.08)] dark:border-[oklch(1_0_0/0.10)] bg-[oklch(0.97_0.01_250/0.70)] dark:bg-[oklch(1_0_0/0.05)]'
        }
        backdrop-blur-sm
        shadow-[inset_0_1px_0_0_oklch(1_0_0/0.45),inset_0_-1px_0_0_oklch(0_0_0/0.04),0_2px_12px_-2px_oklch(0_0_0/0.06)]
        p-3
        hover:-translate-y-1 hover:shadow-xl
        transition-all duration-[250ms] ease-out
        font-sans
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">
          生态集中度指数
        </span>
        {isWarning && (
          <span
            className={`
              text-xs font-medium
              text-[oklch(0.72_0.18_80)] dark:text-[oklch(0.82_0.16_80)]
              bg-[oklch(0.72_0.18_80/0.12)] dark:bg-[oklch(0.82_0.16_80/0.15)]
              border border-[oklch(0.72_0.18_80/0.30)] dark:border-[oklch(0.82_0.16_80/0.25)]
              px-2 py-0.5 rounded-full
            `}
          >
            ⚠ 集中度过高
          </span>
        )}
      </div>
      {/* KPI 核心数值：text-3xl font-bold tracking-tight */}
      <div className="flex items-end gap-2 mb-2">
        <span
          className={`
            text-3xl font-bold tracking-tight tabular-nums
            ${isWarning
              ? 'text-[oklch(0.72_0.18_80)] dark:text-[oklch(0.82_0.16_80)]'
              : 'text-[oklch(0.20_0.02_250)] dark:text-[oklch(0.92_0.01_250)]'
            }
          `}
        >
          {ratio.toFixed(1)}x
        </span>
        <span className="text-xs text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)] mb-1">
          头部人均{metricName}是整体均值的 {ratio.toFixed(1)} 倍
        </span>
      </div>
      <p className="text-xs text-[oklch(0.50_0.04_250)] dark:text-[oklch(0.65_0.04_250)] leading-relaxed">
        头部{' '}
        <span
          className={`font-semibold ${isWarning
            ? 'text-[oklch(0.72_0.18_80)] dark:text-[oklch(0.82_0.16_80)]'
            : 'text-[oklch(0.60_0.22_290)] dark:text-[oklch(0.72_0.20_290)]'
          }`}
        >
          {topTier.populationRatio}%
        </span>{' '}
        的创作者贡献了{' '}
        <span
          className={`font-semibold ${isWarning
            ? 'text-[oklch(0.72_0.18_80)] dark:text-[oklch(0.82_0.16_80)]'
            : 'text-[oklch(0.60_0.22_290)] dark:text-[oklch(0.72_0.20_290)]'
          }`}
        >
          {topTier.contributionRatio}%
        </span>{' '}
        的{metricName}
        {isWarning && (
          <span className="text-[oklch(0.72_0.18_80)] dark:text-[oklch(0.82_0.16_80)]">
            ，超过预警阈值 {threshold}%
          </span>
        )}
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 5: 主组件
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 创作者/供给方生态图组件 (Ecosystem Health Map) — iOS 26 Liquid Glass 样式
 *
 * 通过双向堆叠柱状图对比头、腰、尾部创作者的人数规模占比与价值贡献占比，
 * 直观反映生态集中度，并在头部贡献超过预警阈值时高亮警示。
 * 支持本周 vs 上周时间维度对比。
 *
 * 样式特性（v2.0 Liquid Glass）：
 * - 外层容器：backdrop-blur-xl + bg-white/65 dark:bg-white/7 + 顶部高光线 inset shadow
 * - 内层卡片：rounded-xl + 毛玻璃背景 + Hover 上浮 -translate-y-1
 * - 颜色：全面改用 oklch() 语义色，支持 light/dark 双主题
 * - 字体：中文 Noto Sans SC，数字/英文 DM Sans
 * - KPI 数值：text-3xl font-bold tracking-tight
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
        rounded-2xl
        border border-[oklch(1_0_0/0.18)] dark:border-[oklch(1_0_0/0.10)]
        bg-white/65 dark:bg-white/[0.07]
        backdrop-blur-xl
        shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_4px_24px_-4px_oklch(0_0_0/0.08)]
        p-5 flex flex-col gap-5
        hover:-translate-y-1 hover:shadow-xl
        transition-all duration-[250ms] ease-out
        font-sans
        ${className}
      `}
    >
      {/* ── 头部信息区 ── */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1.5">
          {/* 眉标：uppercase + tracking-widest，oklch violet */}
          <span className="text-xs font-semibold uppercase tracking-widest text-[oklch(0.60_0.22_290)] dark:text-[oklch(0.72_0.20_290)]">
            创作者生态图
          </span>
          <h3 className="text-base font-bold text-[oklch(0.15_0.02_250)] dark:text-[oklch(0.95_0.01_250)] tracking-tight">
            供给方生态健康度
          </h3>
          <p className="text-xs text-[oklch(0.50_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">
            各层级创作者人数规模 vs {data.contributionMetricName}贡献分布
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          {/* 状态标签 — Liquid Glass pill */}
          <span
            className={`
              inline-flex items-center gap-1.5 rounded-full text-xs font-medium px-2.5 py-1
              border
              backdrop-blur-sm
              shadow-[inset_0_1px_0_0_oklch(1_0_0/0.35)]
              ${statusCfg.bg} ${statusCfg.color} ${statusCfg.border}
            `}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${statusCfg.dot}`} />
            {statusCfg.icon} {statusCfg.label}
          </span>

          {/* 时间维度切换 — Liquid Glass segmented control */}
          {hasPreviousPeriod && (
            <div
              className={`
                flex rounded-lg overflow-hidden text-xs
                border border-[oklch(0_0_0/0.08)] dark:border-[oklch(1_0_0/0.10)]
                bg-[oklch(0.96_0.01_250/0.60)] dark:bg-[oklch(1_0_0/0.06)]
                backdrop-blur-sm
                shadow-[inset_0_1px_0_0_oklch(1_0_0/0.40)]
              `}
            >
              <button
                className={`
                  px-3 py-1.5 transition-all duration-[250ms]
                  ${activePeriod === 'current'
                    ? 'bg-[oklch(0.60_0.22_290)] dark:bg-[oklch(0.60_0.22_290)] text-white font-semibold shadow-[inset_0_1px_0_0_oklch(1_0_0/0.25)]'
                    : 'bg-transparent text-[oklch(0.50_0.04_250)] dark:text-[oklch(0.65_0.04_250)] hover:bg-[oklch(0_0_0/0.04)] dark:hover:bg-[oklch(1_0_0/0.06)]'
                  }
                `}
                onClick={() => setActivePeriod('current')}
              >
                {data.currentPeriod.label}
              </button>
              <button
                className={`
                  px-3 py-1.5 transition-all duration-[250ms]
                  ${activePeriod === 'previous'
                    ? 'bg-[oklch(0.60_0.22_290)] dark:bg-[oklch(0.60_0.22_290)] text-white font-semibold shadow-[inset_0_1px_0_0_oklch(1_0_0/0.25)]'
                    : 'bg-transparent text-[oklch(0.50_0.04_250)] dark:text-[oklch(0.65_0.04_250)] hover:bg-[oklch(0_0_0/0.04)] dark:hover:bg-[oklch(1_0_0/0.06)]'
                  }
                `}
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
        <div
          className={`
            rounded-xl
            border border-[oklch(0_0_0/0.07)] dark:border-[oklch(1_0_0/0.08)]
            bg-[oklch(0.97_0.01_250/0.65)] dark:bg-[oklch(1_0_0/0.04)]
            backdrop-blur-sm
            shadow-[inset_0_1px_0_0_oklch(1_0_0/0.40)]
            p-3
          `}
        >
          <div className="text-xs font-semibold text-[oklch(0.50_0.04_250)] dark:text-[oklch(0.65_0.04_250)] mb-2">
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
                <div key={tier.id} className="text-xs font-sans">
                  <div className={`font-semibold mb-1 ${cfg.color}`}>{tier.name}</div>
                  <div className="flex items-center justify-between text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">
                    <span>人数</span>
                    <span className={getChangeColor(popDiff)}>{formatChange(popDiff)}</span>
                  </div>
                  <div className="flex items-center justify-between text-[oklch(0.55_0.04_250)] dark:text-[oklch(0.65_0.04_250)]">
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
        <div
          className={`
            rounded-xl
            border border-[oklch(0_0_0/0.07)] dark:border-[oklch(1_0_0/0.08)]
            bg-[oklch(0.97_0.01_250/0.65)] dark:bg-[oklch(1_0_0/0.04)]
            backdrop-blur-sm
            shadow-[inset_0_1px_0_0_oklch(1_0_0/0.40)]
            p-3
          `}
        >
          <div className="text-xs font-semibold text-[oklch(0.50_0.04_250)] dark:text-[oklch(0.65_0.04_250)] mb-2">
            ✦ 生态洞察
          </div>
          <ul className="space-y-1.5">
            {data.insights.map((insight, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs text-[oklch(0.35_0.03_250)] dark:text-[oklch(0.80_0.02_250)] leading-relaxed"
              >
                {/* 洞察圆点：oklch violet */}
                <span className="text-[oklch(0.60_0.22_290)] dark:text-[oklch(0.72_0.20_290)] mt-0.5 shrink-0">•</span>
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

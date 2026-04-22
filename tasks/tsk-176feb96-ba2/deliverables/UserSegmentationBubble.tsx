// @section:user_segmentation_bubble - 用户分层气泡图 (User Segmentation Bubble Chart)
// ─────────────────────────────────────────────────────────────────────────────
// 组件 Key: user_segmentation_bubble
// 适用模块: 用户运营、产品与活跃、玩家分层与生命周期、客户成功与健康分
// 技术栈: React + TypeScript + TailwindCSS + Recharts (ScatterChart)
// 样式版本: iOS 26 Liquid Glass (v2.0)
//   - 外层容器: backdrop-blur-xl + bg-white/65 dark:bg-white/7 + 顶部高光线 + 底部暗线 + 外阴影
//   - 颜色: oklch 语义色 Token
//   - 字体: 中文 Noto Sans SC / 数字英文 DM Sans
//   - 深色模式: 完整 dark: 变体
//   - 圆角: 外层 rounded-2xl / 内层 rounded-xl / 最内层 rounded-lg
//   - Hover: -translate-y-1 + shadow-xl + transition-all duration-250
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
  Label,
} from 'recharts';

// ─────────────────────────────────────────────────────────────────────────────
// CSS 变量注入（Noto Sans SC + DM Sans 字体）
// ─────────────────────────────────────────────────────────────────────────────
// 在宿主页面的 <head> 中添加以下 Google Fonts 引入：
// <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
// 并在 tailwind.config.js 中配置：
// fontFamily: { sans: ['Noto Sans SC', 'DM Sans', 'system-ui', 'sans-serif'] }

// ─────────────────────────────────────────────────────────────────────────────
// TypeScript 接口定义
// ─────────────────────────────────────────────────────────────────────────────

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
  /** 所属象限（由数据提供方预先分类，或由组件根据 baseline 自动推断） */
  quadrant?: QuadrantType;
  /** 环比变化（可选，如："+5%"、"-2%"） */
  changeRate?: string;
  /** 核心特征描述（用于 Hover 提示） */
  description?: string;
  /** 运营建议（用于 Hover 提示） */
  recommendation?: string;
}

/** 用户分层气泡图组件 Props */
export interface UserSegmentationBubbleProps {
  /** 气泡数据列表 */
  data: UserSegmentBubble[];
  /** X轴配置 */
  xAxis: {
    /** X轴标签，如："月均活跃天数" */
    label: string;
    /** X轴单位，如："天" */
    unit?: string;
    /** 象限划分基准线（X轴中线） */
    baseline: number;
  };
  /** Y轴配置 */
  yAxis: {
    /** Y轴标签，如："ARPU" */
    label: string;
    /** Y轴单位，如："¥" */
    unit?: string;
    /** 象限划分基准线（Y轴中线） */
    baseline: number;
  };
  /** 气泡大小配置 */
  size: {
    /** 大小字段标签，如："用户规模" */
    label: string;
    /** 大小字段单位，如："人" */
    unit?: string;
  };
  /** 组件标题 */
  title?: string;
  /** 副标题/说明 */
  subtitle?: string;
  /** 下钻回调：点击某个气泡时触发，传入分层 ID */
  onBubbleClick?: (segmentId: string) => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// 象限配置常量（使用 oklch 语义色 Token）
// ─────────────────────────────────────────────────────────────────────────────

const QUADRANT_CONFIG: Record<QuadrantType, {
  label: string;
  labelEn: string;
  /** oklch 颜色值，用于 SVG 气泡描边和光晕 */
  color: string;
  /** oklch 气泡填充色（带透明度） */
  fillColor: string;
  /** Tailwind 背景色（用于卡片底部摘要） */
  bgColor: string;
  /** Tailwind 文字色 */
  textColor: string;
  /** Tailwind 边框色 */
  borderColor: string;
  /** 象限描述 */
  description: string;
}> = {
  high_value: {
    label: '高价值',
    labelEn: 'High Value',
    // oklch(0.72 0.18 160) ≈ emerald-500 系列
    color: 'oklch(0.72 0.18 160)',
    fillColor: 'oklch(0.72 0.18 160 / 0.72)',
    bgColor: 'bg-[oklch(0.72_0.18_160/0.12)] dark:bg-[oklch(0.72_0.18_160/0.18)]',
    textColor: 'text-[oklch(0.72_0.18_160)] dark:text-[oklch(0.82_0.16_160)]',
    borderColor: 'border-[oklch(0.72_0.18_160/0.35)] dark:border-[oklch(0.72_0.18_160/0.45)]',
    description: '高活跃 · 高价值 · 核心用户',
  },
  high_potential: {
    label: '高潜力',
    labelEn: 'High Potential',
    // oklch(0.72 0.18 255) ≈ sky-400 系列
    color: 'oklch(0.72 0.18 255)',
    fillColor: 'oklch(0.72 0.18 255 / 0.72)',
    bgColor: 'bg-[oklch(0.72_0.18_255/0.12)] dark:bg-[oklch(0.72_0.18_255/0.18)]',
    textColor: 'text-[oklch(0.72_0.18_255)] dark:text-[oklch(0.82_0.16_255)]',
    borderColor: 'border-[oklch(0.72_0.18_255/0.35)] dark:border-[oklch(0.72_0.18_255/0.45)]',
    description: '低活跃 · 高价值 · 待激活',
  },
  to_be_activated: {
    label: '待激活',
    labelEn: 'To Be Activated',
    // oklch(0.62 0.04 255) ≈ slate-400 系列
    color: 'oklch(0.62 0.04 255)',
    fillColor: 'oklch(0.62 0.04 255 / 0.60)',
    bgColor: 'bg-[oklch(0.62_0.04_255/0.10)] dark:bg-[oklch(0.62_0.04_255/0.15)]',
    textColor: 'text-[oklch(0.62_0.04_255)] dark:text-[oklch(0.72_0.04_255)]',
    borderColor: 'border-[oklch(0.62_0.04_255/0.30)] dark:border-[oklch(0.62_0.04_255/0.40)]',
    description: '低活跃 · 低价值 · 长尾用户',
  },
  churn_risk: {
    label: '流失风险',
    labelEn: 'Churn Risk',
    // oklch(0.78 0.18 55) ≈ amber-400 系列
    color: 'oklch(0.78 0.18 55)',
    fillColor: 'oklch(0.78 0.18 55 / 0.72)',
    bgColor: 'bg-[oklch(0.78_0.18_55/0.12)] dark:bg-[oklch(0.78_0.18_55/0.18)]',
    textColor: 'text-[oklch(0.78_0.18_55)] dark:text-[oklch(0.88_0.16_55)]',
    borderColor: 'border-[oklch(0.78_0.18_55/0.35)] dark:border-[oklch(0.78_0.18_55/0.45)]',
    description: '高活跃 · 低价值 · 需转化',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// 辅助函数：根据基准线自动推断象限
// ─────────────────────────────────────────────────────────────────────────────

function inferQuadrant(
  xValue: number,
  yValue: number,
  xBaseline: number,
  yBaseline: number
): QuadrantType {
  const isHighX = xValue >= xBaseline;
  const isHighY = yValue >= yBaseline;
  if (isHighX && isHighY) return 'high_value';
  if (!isHighX && isHighY) return 'high_potential';
  if (!isHighX && !isHighY) return 'to_be_activated';
  return 'churn_risk'; // isHighX && !isHighY
}

// ─────────────────────────────────────────────────────────────────────────────
// 自定义 Tooltip 组件（Liquid Glass 毛玻璃风格）
// ─────────────────────────────────────────────────────────────────────────────

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: UserSegmentBubble & { quadrantResolved: QuadrantType };
  }>;
  sizeLabel: string;
  sizeUnit?: string;
  xAxisLabel: string;
  xAxisUnit?: string;
  yAxisLabel: string;
  yAxisUnit?: string;
}

function CustomTooltip({
  active,
  payload,
  sizeLabel,
  sizeUnit,
  xAxisLabel,
  xAxisUnit,
  yAxisLabel,
  yAxisUnit,
}: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const d = payload[0].payload;
  const quadrant = d.quadrantResolved;
  const cfg = QUADRANT_CONFIG[quadrant];

  return (
    <div
      className={`
        rounded-xl border
        backdrop-blur-xl
        bg-white/75 dark:bg-white/8
        shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_4px_24px_-4px_oklch(0_0_0/0.12)]
        dark:shadow-[inset_0_1px_0_0_oklch(1_0_0/0.12),inset_0_-1px_0_0_oklch(0_0_0/0.18),0_4px_24px_-4px_oklch(0_0_0/0.32)]
        border-white/60 dark:border-white/10
        p-4 min-w-[200px] max-w-[260px]
        font-sans
      `}
      style={{ pointerEvents: 'none' }}
    >
      {/* 分层名称 */}
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-3 h-3 rounded-full shrink-0"
          style={{ backgroundColor: cfg.color }}
        />
        <span className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-tight tracking-tight">
          {d.name}
        </span>
      </div>

      {/* 象限标签 */}
      <div
        className={`
          inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-lg mb-3
          ${cfg.bgColor} ${cfg.textColor} border ${cfg.borderColor}
        `}
      >
        {cfg.label} · {cfg.description}
      </div>

      {/* 核心指标 */}
      <div className="space-y-1.5 text-xs">
        <div className="flex justify-between items-center">
          <span className="text-slate-500 dark:text-slate-400">{sizeLabel}</span>
          <span className="font-semibold text-slate-700 dark:text-slate-200 tabular-nums font-[DM_Sans,system-ui]">
            {d.sizeValue.toLocaleString()}{sizeUnit ? ` ${sizeUnit}` : ''}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 dark:text-slate-400">{xAxisLabel}</span>
          <span className="font-semibold text-slate-700 dark:text-slate-200 tabular-nums font-[DM_Sans,system-ui]">
            {xAxisUnit ? `${xAxisUnit} ` : ''}{d.xValue.toLocaleString()}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 dark:text-slate-400">{yAxisLabel}</span>
          <span className="font-semibold text-slate-700 dark:text-slate-200 tabular-nums font-[DM_Sans,system-ui]">
            {yAxisUnit ? `${yAxisUnit} ` : ''}{d.yValue.toLocaleString()}
          </span>
        </div>
        {d.changeRate && (
          <div className="flex justify-between items-center">
            <span className="text-slate-500 dark:text-slate-400">环比变化</span>
            <span
              className={`font-semibold tabular-nums font-[DM_Sans,system-ui] ${
                d.changeRate.startsWith('+')
                  ? 'text-[oklch(0.72_0.18_160)] dark:text-[oklch(0.82_0.16_160)]'
                  : 'text-[oklch(0.65_0.22_25)] dark:text-[oklch(0.75_0.20_25)]'
              }`}
            >
              {d.changeRate}
            </span>
          </div>
        )}
      </div>

      {/* 特征描述 */}
      {d.description && (
        <p className="mt-2.5 pt-2.5 border-t border-slate-200/60 dark:border-white/10 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          {d.description}
        </p>
      )}

      {/* 运营建议 */}
      {d.recommendation && (
        <div className="mt-2 pt-2 border-t border-slate-200/60 dark:border-white/10">
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">运营建议</p>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {d.recommendation}
          </p>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 自定义气泡渲染（带描边和光晕，oklch 颜色）
// ─────────────────────────────────────────────────────────────────────────────

interface CustomDotProps {
  cx?: number;
  cy?: number;
  r?: number;
  fill?: string;
  payload?: UserSegmentBubble & { quadrantResolved: QuadrantType };
  onClick?: (id: string) => void;
}

function CustomDot({ cx = 0, cy = 0, r = 10, fill, payload, onClick }: CustomDotProps) {
  if (!payload) return null;
  const cfg = QUADRANT_CONFIG[payload.quadrantResolved];

  return (
    <g>
      {/* 外圈光晕（使用 oklch 颜色） */}
      <circle
        cx={cx}
        cy={cy}
        r={r + 5}
        fill={cfg.color}
        fillOpacity={0.10}
      />
      {/* 中间光晕 */}
      <circle
        cx={cx}
        cy={cy}
        r={r + 2}
        fill={cfg.color}
        fillOpacity={0.06}
      />
      {/* 主气泡 */}
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill={fill || cfg.fillColor}
        stroke={cfg.color}
        strokeWidth={1.5}
        style={{ cursor: onClick ? 'pointer' : 'default', transition: 'r 0.2s ease' }}
        onClick={() => onClick && payload.id && onClick(payload.id)}
      />
      {/* 顶部高光（模拟 Liquid Glass 反光效果） */}
      <circle
        cx={cx - r * 0.22}
        cy={cy - r * 0.28}
        r={r * 0.22}
        fill="white"
        fillOpacity={0.55}
      />
      {/* 底部微暗边 */}
      <circle
        cx={cx}
        cy={cy + r * 0.3}
        r={r * 0.15}
        fill="black"
        fillOpacity={0.06}
      />
    </g>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 主组件：UserSegmentationBubble（iOS 26 Liquid Glass 样式升级版）
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 用户分层气泡图组件 (User Segmentation Bubble Chart)
 *
 * 通过四象限气泡图直观展示用户价值分层分布，指导精细化运营。
 * - X轴：活跃度/频次维度
 * - Y轴：付费价值/健康分维度
 * - 气泡大小：用户规模
 * - 气泡颜色：象限分类（高价值/高潜力/待激活/流失风险）
 *
 * 样式规范（iOS 26 Liquid Glass v2.0）：
 * - 外层容器：backdrop-blur-xl + bg-white/65 dark:bg-white/7 + 顶部高光线 + 底部暗线 + 外阴影
 * - 颜色：oklch 语义色 Token
 * - 字体：中文 Noto Sans SC，数字/英文 DM Sans
 * - 深色模式：完整 dark: 变体
 *
 * @example
 * <UserSegmentationBubble
 *   data={mockSegmentData}
 *   xAxis={{ label: '月均活跃天数', unit: '天', baseline: 15 }}
 *   yAxis={{ label: 'ARPU', unit: '¥', baseline: 50 }}
 *   size={{ label: '用户规模', unit: '人' }}
 *   title="用户分层分布"
 *   onBubbleClick={(id) => console.log('点击分层:', id)}
 * />
 */
export function UserSegmentationBubble({
  data,
  xAxis,
  yAxis,
  size,
  title = '用户分层气泡图',
  subtitle,
  onBubbleClick,
}: UserSegmentationBubbleProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  // 为每个数据点推断象限（若未提供则自动计算）
  const enrichedData = data.map((d) => ({
    ...d,
    quadrantResolved: d.quadrant ?? inferQuadrant(d.xValue, d.yValue, xAxis.baseline, yAxis.baseline),
    // Recharts ScatterChart 使用 x, y, z 字段
    x: d.xValue,
    y: d.yValue,
    z: d.sizeValue,
  }));

  // 按象限分组，每个象限单独一个 Scatter 以便独立控制颜色
  const quadrantGroups = (['high_value', 'high_potential', 'to_be_activated', 'churn_risk'] as QuadrantType[]).map(
    (q) => ({
      quadrant: q,
      points: enrichedData.filter((d) => d.quadrantResolved === q),
    })
  );

  // 计算坐标轴范围（留 20% 边距）
  const allX = enrichedData.map((d) => d.xValue);
  const allY = enrichedData.map((d) => d.yValue);
  const xMin = Math.max(0, Math.min(...allX) * 0.7);
  const xMax = Math.max(...allX) * 1.25;
  const yMin = Math.max(0, Math.min(...allY) * 0.7);
  const yMax = Math.max(...allY) * 1.25;

  // 气泡大小范围
  const allZ = enrichedData.map((d) => d.sizeValue);
  const zMin = Math.min(...allZ);
  const zMax = Math.max(...allZ);
  const bubbleMin = 400;
  const bubbleMax = 3000;

  return (
    <div
      className={`
        rounded-2xl border
        backdrop-blur-xl
        bg-white/65 dark:bg-white/7
        shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_4px_24px_-4px_oklch(0_0_0/0.08)]
        dark:shadow-[inset_0_1px_0_0_oklch(1_0_0/0.10),inset_0_-1px_0_0_oklch(0_0_0/0.20),0_4px_24px_-4px_oklch(0_0_0/0.28)]
        border-white/60 dark:border-white/10
        hover:-translate-y-1 hover:shadow-xl
        transition-all duration-[250ms]
        p-5 flex flex-col
        w-full
        font-sans
      `}
    >
      {/* ── 头部区域 ── */}
      <div className="flex items-start justify-between mb-4">
        <div>
          {/* 分类标签 */}
          <span className="text-xs font-semibold uppercase tracking-widest text-[oklch(0.62_0.22_295)] dark:text-[oklch(0.72_0.20_295)]">
            用户分层
          </span>
          {/* 标题：中文 Noto Sans SC，字号 base，weight-700 */}
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-100 mt-0.5 tracking-tight">
            {title}
          </h3>
          {subtitle && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
              {subtitle}
            </p>
          )}
        </div>

        {/* 图例 */}
        <div className="flex flex-wrap gap-x-3 gap-y-1.5 justify-end max-w-[280px]">
          {(Object.keys(QUADRANT_CONFIG) as QuadrantType[]).map((q) => {
            const cfg = QUADRANT_CONFIG[q];
            return (
              <div key={q} className="flex items-center gap-1.5">
                <div
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: cfg.color }}
                />
                <span className="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                  {cfg.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── 气泡大小说明 ── */}
      <div className="flex items-center gap-2 mb-3 text-xs text-slate-400 dark:text-slate-500">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-slate-300/70 dark:bg-slate-600/70" />
          <div className="w-3.5 h-3.5 rounded-full bg-slate-300/70 dark:bg-slate-600/70" />
          <div className="w-5 h-5 rounded-full bg-slate-300/70 dark:bg-slate-600/70" />
        </div>
        <span>气泡大小 = {size.label}{size.unit ? `（${size.unit}）` : ''}</span>
      </div>

      {/* ── 图表区域 ── */}
      <div className="relative flex-1" style={{ minHeight: 380 }}>
        {/* 象限背景标签（使用 oklch 颜色，透明度降低以保持 Liquid Glass 通透感） */}
        <div
          className="absolute inset-0 pointer-events-none z-10"
          style={{ paddingLeft: 48, paddingBottom: 40, paddingRight: 16, paddingTop: 8 }}
        >
          <div className="relative w-full h-full">
            {/* 左上：高潜力 */}
            <div
              className="absolute top-2 left-2 text-xs font-semibold select-none"
              style={{ color: 'oklch(0.72 0.18 255 / 0.35)' }}
            >
              ← 低活跃 · 高价值
            </div>
            {/* 右上：高价值 */}
            <div
              className="absolute top-2 right-2 text-xs font-semibold select-none text-right"
              style={{ color: 'oklch(0.72 0.18 160 / 0.35)' }}
            >
              高活跃 · 高价值 →
            </div>
            {/* 左下：待激活 */}
            <div
              className="absolute bottom-2 left-2 text-xs font-semibold select-none"
              style={{ color: 'oklch(0.62 0.04 255 / 0.30)' }}
            >
              ← 低活跃 · 低价值
            </div>
            {/* 右下：流失风险 */}
            <div
              className="absolute bottom-2 right-2 text-xs font-semibold select-none text-right"
              style={{ color: 'oklch(0.78 0.18 55 / 0.35)' }}
            >
              高活跃 · 低价值 →
            </div>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={380}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 20 }}>
            {/* 网格线（使用 oklch 颜色，更通透） */}
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="oklch(0.62 0.04 255 / 0.12)"
            />

            <XAxis
              type="number"
              dataKey="x"
              domain={[xMin, xMax]}
              tickLine={false}
              axisLine={{ stroke: 'oklch(0.62 0.04 255 / 0.25)' }}
              tick={{ fontSize: 11, fill: 'oklch(0.62 0.04 255)' }}
              tickFormatter={(v) => `${v}${xAxis.unit ? xAxis.unit : ''}`}
            >
              <Label
                value={xAxis.label}
                offset={-10}
                position="insideBottom"
                style={{ fontSize: 11, fill: 'oklch(0.62 0.04 255)', fontWeight: 500 }}
              />
            </XAxis>

            <YAxis
              type="number"
              dataKey="y"
              domain={[yMin, yMax]}
              tickLine={false}
              axisLine={{ stroke: 'oklch(0.62 0.04 255 / 0.25)' }}
              tick={{ fontSize: 11, fill: 'oklch(0.62 0.04 255)' }}
              tickFormatter={(v) => `${yAxis.unit ? yAxis.unit : ''}${v}`}
              width={48}
            >
              <Label
                value={yAxis.label}
                angle={-90}
                position="insideLeft"
                offset={10}
                style={{ fontSize: 11, fill: 'oklch(0.62 0.04 255)', fontWeight: 500 }}
              />
            </YAxis>

            <ZAxis
              type="number"
              dataKey="z"
              range={[bubbleMin, bubbleMax]}
              domain={[zMin, zMax]}
            />

            {/* 象限分割线（使用 oklch 颜色） */}
            <ReferenceLine
              x={xAxis.baseline}
              stroke="oklch(0.62 0.04 255 / 0.35)"
              strokeDasharray="6 3"
              strokeWidth={1.5}
            />
            <ReferenceLine
              y={yAxis.baseline}
              stroke="oklch(0.62 0.04 255 / 0.35)"
              strokeDasharray="6 3"
              strokeWidth={1.5}
            />

            {/* 自定义 Tooltip */}
            <Tooltip
              content={
                <CustomTooltip
                  sizeLabel={size.label}
                  sizeUnit={size.unit}
                  xAxisLabel={xAxis.label}
                  xAxisUnit={xAxis.unit}
                  yAxisLabel={yAxis.label}
                  yAxisUnit={yAxis.unit}
                />
              }
              cursor={{ strokeDasharray: '3 3', stroke: 'oklch(0.62 0.04 255 / 0.25)' }}
            />

            {/* 按象限分组渲染气泡 */}
            {quadrantGroups.map(({ quadrant, points }) => {
              if (points.length === 0) return null;
              const cfg = QUADRANT_CONFIG[quadrant];
              return (
                <Scatter
                  key={quadrant}
                  name={cfg.label}
                  data={points}
                  fill={cfg.fillColor}
                  shape={(props: any) => (
                    <CustomDot
                      {...props}
                      onClick={onBubbleClick}
                    />
                  )}
                  onClick={(d: any) => {
                    if (onBubbleClick && d.id) {
                      onBubbleClick(d.id);
                    }
                  }}
                >
                  {points.map((entry) => (
                    <Cell
                      key={entry.id}
                      fill={cfg.fillColor}
                      stroke={cfg.color}
                      strokeWidth={activeId === entry.id ? 2.5 : 1.5}
                    />
                  ))}
                </Scatter>
              );
            })}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* ── 底部：象限运营策略摘要（Liquid Glass 内层卡片） ── */}
      <div className="mt-4 grid grid-cols-2 gap-2">
        {(Object.keys(QUADRANT_CONFIG) as QuadrantType[]).map((q) => {
          const cfg = QUADRANT_CONFIG[q];
          const count = enrichedData.filter((d) => d.quadrantResolved === q).length;
          const totalUsers = enrichedData
            .filter((d) => d.quadrantResolved === q)
            .reduce((sum, d) => sum + d.sizeValue, 0);
          return (
            <div
              key={q}
              className={`
                flex items-start gap-2 p-2.5 rounded-xl border
                backdrop-blur-sm
                ${cfg.bgColor} ${cfg.borderColor}
                transition-all duration-[250ms]
                hover:-translate-y-0.5 hover:shadow-md
              `}
            >
              <div
                className="w-2.5 h-2.5 rounded-full mt-0.5 shrink-0"
                style={{ backgroundColor: cfg.color }}
              />
              <div className="min-w-0">
                <div className={`text-xs font-semibold ${cfg.textColor}`}>
                  {cfg.label}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 font-[DM_Sans,system-ui] tabular-nums">
                  {count} 个分层 · {totalUsers.toLocaleString()}{size.unit ? ` ${size.unit}` : ''}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Mock 数据（供开发调试和文档示例使用）
// ─────────────────────────────────────────────────────────────────────────────

export const mockUserSegmentData: UserSegmentBubble[] = [
  // 高价值象限（右上：高活跃 + 高价值）
  {
    id: 'seg-vip',
    name: '核心大R',
    xValue: 25,
    yValue: 320,
    sizeValue: 1200,
    quadrant: 'high_value',
    changeRate: '+8%',
    description: '月均活跃 25 天，ARPU ¥320，贡献平台 45% 营收。',
    recommendation: '提供专属 VIP 服务和优先客服通道，鼓励口碑传播。',
  },
  {
    id: 'seg-active-payer',
    name: '活跃付费用户',
    xValue: 20,
    yValue: 120,
    sizeValue: 5800,
    quadrant: 'high_value',
    changeRate: '+3%',
    description: '月均活跃 20 天，ARPU ¥120，是平台的稳定收入来源。',
    recommendation: '通过订阅制或会员体系提升 LTV，防止流失。',
  },
  // 高潜力象限（左上：低活跃 + 高价值）
  {
    id: 'seg-whale-sleeper',
    name: '沉睡高价值',
    xValue: 6,
    yValue: 180,
    sizeValue: 2100,
    quadrant: 'high_potential',
    changeRate: '-5%',
    description: '月均活跃仅 6 天，但 ARPU 达 ¥180，具备高消费能力。',
    recommendation: '定向推送高质量内容和专属活动，提升活跃频次。',
  },
  {
    id: 'seg-occasional-spender',
    name: '偶发消费用户',
    xValue: 9,
    yValue: 85,
    sizeValue: 4200,
    quadrant: 'high_potential',
    changeRate: '+1%',
    description: '偶尔登录但消费意愿强，需要培养使用习惯。',
    recommendation: '设置签到奖励和每日任务，引导形成使用习惯。',
  },
  // 待激活象限（左下：低活跃 + 低价值）
  {
    id: 'seg-new-user',
    name: '新注册用户',
    xValue: 4,
    yValue: 12,
    sizeValue: 18000,
    quadrant: 'to_be_activated',
    changeRate: '+22%',
    description: '新用户，尚未完成激活，大量流失发生在此阶段。',
    recommendation: '优化新手引导流程，提供注册即送福利，降低首次使用门槛。',
  },
  {
    id: 'seg-dormant',
    name: '沉默用户',
    xValue: 2,
    yValue: 5,
    sizeValue: 12000,
    quadrant: 'to_be_activated',
    changeRate: '-8%',
    description: '长期低活跃，几乎不产生价值，需要召回或清洗。',
    recommendation: '发送召回推送，提供限时优惠，无响应则归入流失池。',
  },
  // 流失风险象限（右下：高活跃 + 低价值）
  {
    id: 'seg-freeloader',
    name: '高频免费用户',
    xValue: 22,
    yValue: 8,
    sizeValue: 9500,
    quadrant: 'churn_risk',
    changeRate: '+12%',
    description: '活跃度极高但几乎不付费，消耗大量服务器资源。',
    recommendation: '设计付费转化诱饵，如高级功能解锁或去广告特权。',
  },
  {
    id: 'seg-content-consumer',
    name: '内容消费者',
    xValue: 17,
    yValue: 22,
    sizeValue: 7200,
    quadrant: 'churn_risk',
    changeRate: '-2%',
    description: '活跃度较高，主要消费内容，付费转化率低。',
    recommendation: '引导参与内容创作或社区互动，提升平台贡献价值。',
  },
];

export const mockUserSegmentConfig = {
  xAxis: { label: '月均活跃天数', unit: '天', baseline: 15 },
  yAxis: { label: 'ARPU', unit: '¥', baseline: 50 },
  size: { label: '用户规模', unit: '人' },
  title: '用户分层分布图',
  subtitle: '基于活跃频次 × 消费价值的四象限用户分层，指导精细化运营策略制定',
};

// ─────────────────────────────────────────────────────────────────────────────
// 演示页面（独立运行时展示）
// ─────────────────────────────────────────────────────────────────────────────

export default function UserSegmentationBubbleDemo() {
  const handleBubbleClick = (segmentId: string) => {
    const seg = mockUserSegmentData.find((d) => d.id === segmentId);
    if (seg) {
      console.log('[用户分层气泡图] 点击分层:', seg.name, seg);
    }
  };

  return (
    <div
      className="min-h-screen p-6 sm:p-10 font-sans"
      style={{
        background: 'linear-gradient(135deg, oklch(0.96 0.02 255) 0%, oklch(0.94 0.03 295) 50%, oklch(0.96 0.02 160) 100%)',
      }}
    >
      {/* 深色模式背景 */}
      <style>{`
        @media (prefers-color-scheme: dark) {
          .demo-bg {
            background: linear-gradient(135deg, oklch(0.18 0.02 255) 0%, oklch(0.16 0.03 295) 50%, oklch(0.18 0.02 160) 100%) !important;
          }
        }
      `}</style>
      <div className="max-w-4xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">
            用户分层气泡图 · 组件演示
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            组件 Key:{' '}
            <code
              className="px-1.5 py-0.5 rounded-lg text-xs font-mono"
              style={{
                background: 'oklch(0.62 0.22 295 / 0.10)',
                color: 'oklch(0.62 0.22 295)',
              }}
            >
              user_segmentation_bubble
            </code>
            &nbsp;·&nbsp; 样式版本: iOS 26 Liquid Glass v2.0
          </p>
        </div>

        {/* 组件展示 */}
        <UserSegmentationBubble
          data={mockUserSegmentData}
          xAxis={mockUserSegmentConfig.xAxis}
          yAxis={mockUserSegmentConfig.yAxis}
          size={mockUserSegmentConfig.size}
          title={mockUserSegmentConfig.title}
          subtitle={mockUserSegmentConfig.subtitle}
          onBubbleClick={handleBubbleClick}
        />

        {/* 使用说明（Liquid Glass 内层卡片） */}
        <div
          className={`
            mt-6 p-4 rounded-2xl border
            backdrop-blur-xl
            bg-white/65 dark:bg-white/7
            shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_4px_24px_-4px_oklch(0_0_0/0.08)]
            dark:shadow-[inset_0_1px_0_0_oklch(1_0_0/0.10),inset_0_-1px_0_0_oklch(0_0_0/0.20),0_4px_24px_-4px_oklch(0_0_0/0.28)]
            border-white/60 dark:border-white/10
          `}
        >
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3 tracking-tight">
            使用说明
          </h2>
          <div className="space-y-2 text-xs text-slate-500 dark:text-slate-400">
            <p>• 将鼠标悬停在气泡上，查看该用户分层的详细信息（规模、指标、运营建议）。</p>
            <p>
              • 点击气泡可触发{' '}
              <code
                className="px-1 rounded-md font-mono"
                style={{ background: 'oklch(0.62 0.04 255 / 0.12)' }}
              >
                onBubbleClick
              </code>{' '}
              回调，用于跳转到该分层的详细运营页面。
            </p>
            <p>
              • 四条象限分割线基于{' '}
              <code
                className="px-1 rounded-md font-mono"
                style={{ background: 'oklch(0.62 0.04 255 / 0.12)' }}
              >
                xAxis.baseline
              </code>{' '}
              和{' '}
              <code
                className="px-1 rounded-md font-mono"
                style={{ background: 'oklch(0.62 0.04 255 / 0.12)' }}
              >
                yAxis.baseline
              </code>{' '}
              绘制，可根据业务实际调整。
            </p>
            <p>
              • 若数据点未提供{' '}
              <code
                className="px-1 rounded-md font-mono"
                style={{ background: 'oklch(0.62 0.04 255 / 0.12)' }}
              >
                quadrant
              </code>{' '}
              字段，组件将根据基准线自动推断所属象限。
            </p>
          </div>
        </div>

        {/* 样式规范说明 */}
        <div
          className={`
            mt-4 p-4 rounded-2xl border
            backdrop-blur-xl
            bg-white/65 dark:bg-white/7
            shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_4px_24px_-4px_oklch(0_0_0/0.08)]
            dark:shadow-[inset_0_1px_0_0_oklch(1_0_0/0.10),inset_0_-1px_0_0_oklch(0_0_0/0.20),0_4px_24px_-4px_oklch(0_0_0/0.28)]
            border-white/60 dark:border-white/10
          `}
        >
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3 tracking-tight">
            iOS 26 Liquid Glass 样式规范
          </h2>
          <div className="grid grid-cols-2 gap-3 text-xs text-slate-500 dark:text-slate-400">
            <div>
              <p className="font-semibold text-slate-600 dark:text-slate-300 mb-1">毛玻璃效果</p>
              <p>backdrop-blur-xl + bg-white/65</p>
              <p>顶部高光线 inset shadow</p>
              <p>底部暗线 + 外阴影</p>
            </div>
            <div>
              <p className="font-semibold text-slate-600 dark:text-slate-300 mb-1">颜色系统</p>
              <p>oklch 语义色 Token</p>
              <p>四象限独立颜色身份</p>
              <p>完整深色模式 dark: 变体</p>
            </div>
            <div>
              <p className="font-semibold text-slate-600 dark:text-slate-300 mb-1">字体规范</p>
              <p>中文: Noto Sans SC</p>
              <p>数字/英文: DM Sans</p>
              <p>数值: tabular-nums tracking-tight</p>
            </div>
            <div>
              <p className="font-semibold text-slate-600 dark:text-slate-300 mb-1">交互规范</p>
              <p>hover:-translate-y-1</p>
              <p>hover:shadow-xl</p>
              <p>transition-all duration-250</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

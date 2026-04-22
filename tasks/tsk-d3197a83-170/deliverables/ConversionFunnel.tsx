// @section:conversion_funnel - 漏斗转化组件 (Conversion Funnel)
// =============================================================================
// 组件数据绑定说明
// 组件 Key: conversion_funnel
// 组件类型: 详情组件 (Detail Component)
// 适用模块: 增长与获客 (Growth & Acquisition)、商业化与变现 (Monetization)
//
// 设计规范: iOS 26 Liquid Glass Design System
// 版本: v2.0 (2026-04-22) — 毛玻璃卡片 + oklch 品牌蓝渐变 + DM Sans / Noto Sans SC 字体
//
// 数据来源: 来自增长与获客模块，追踪从曝光到激活的各环节用户数
// 展示字段: 各步骤绝对人数、步骤间转化率、整体转化率、转化瓶颈高亮
// 下钻逻辑: 作为详情组件，核心目标是直观清晰地把事情讲清楚，无强制下钻
//
// 使用示例:
//   <ConversionFunnel
//     title="新用户注册转化漏斗"
//     description="本周注册转化率受短信通道延迟影响，『获取验证码』环节成为核心瓶颈。"
//     series={[primarySeries, comparisonSeries]}
//     unit="人"
//   />
//
// 数据接口 (ConversionFunnelProps):
//   title: string                  — 组件标题
//   description?: string           — 分析结论描述
//   series: FunnelSeries[]         — 漏斗数据系列（支持 1-2 个系列对比）
//   unit?: string                  — 数值单位，如 "人"、"次"
// =============================================================================

import React, { useState } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// TypeScript 接口定义
// ─────────────────────────────────────────────────────────────────────────────

/** 漏斗单步数据 */
export interface FunnelStep {
  /** 步骤 ID */
  id: string;
  /** 步骤名称，如 "访问落地页" */
  label: string;
  /** 绝对数值（人数/次数） */
  value: number;
  /** 相对上一步的转化率 (0-100)，第一步为 undefined */
  conversionRate?: number;
  /** 是否为转化瓶颈（最低转化率或降幅最大的步骤） */
  isBottleneck?: boolean;
}

/** 单个漏斗数据系列 */
export interface FunnelSeries {
  /** 系列名称，如 "本周"、"策略A" */
  name: string;
  /** 步骤数据列表，必须按流程顺序排列 */
  steps: FunnelStep[];
  /** 整体转化率 (最后一步 / 第一步 * 100) */
  overallConversionRate: number;
  /** 系列主色调（Tailwind 颜色类名，如 "indigo"） */
  colorKey?: string;
}

/** 漏斗转化组件 Props */
export interface ConversionFunnelProps {
  /** 组件标题 */
  title: string;
  /** 组件描述或分析结论 */
  description?: string;
  /** 漏斗数据系列（支持 1-2 个系列进行对比） */
  series: FunnelSeries[];
  /** 数值单位，如 "人"、"次" */
  unit?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// 工具函数
// ─────────────────────────────────────────────────────────────────────────────

/** 格式化数字，添加千分位分隔符 */
function formatNumber(n: number): string {
  return n.toLocaleString('zh-CN');
}

/** 格式化转化率，保留一位小数 */
function formatRate(rate: number): string {
  return `${rate.toFixed(1)}%`;
}

// ─────────────────────────────────────────────────────────────────────────────
// iOS 26 Liquid Glass 颜色配置
// 使用 oklch 品牌蓝渐变 + 语义色
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 系列颜色配置 — oklch 品牌蓝渐变
 *
 * 主系列: oklch(0.55 0.22 264) — 品牌蓝
 * 对比系列: oklch(0.60 0.04 264) — 中性蓝灰
 */
const SERIES_COLORS = [
  {
    // 主系列：品牌蓝渐变
    barGradient: 'from-[oklch(0.55_0.22_264)] to-[oklch(0.65_0.18_264)]',
    bar: 'bg-[oklch(0.55_0.22_264)]',
    barLight: 'bg-[oklch(0.65_0.18_264)]',
    text: 'text-[oklch(0.55_0.22_264)] dark:text-[oklch(0.72_0.18_264)]',
    border: 'border-[oklch(0.55_0.22_264/0.4)]',
    badge:
      'bg-[oklch(0.55_0.22_264/0.10)] dark:bg-[oklch(0.55_0.22_264/0.18)] text-[oklch(0.45_0.22_264)] dark:text-[oklch(0.78_0.18_264)]',
    dot: 'bg-[oklch(0.55_0.22_264)]',
    bottleneckRing: 'ring-[oklch(0.75_0.18_60)] ring-offset-1',
  },
  {
    // 对比系列：中性蓝灰
    barGradient: 'from-[oklch(0.60_0.04_264)] to-[oklch(0.72_0.03_264)]',
    bar: 'bg-[oklch(0.60_0.04_264)] dark:bg-[oklch(0.45_0.04_264)]',
    barLight: 'bg-[oklch(0.72_0.03_264)] dark:bg-[oklch(0.38_0.03_264)]',
    text: 'text-[oklch(0.55_0.04_264)] dark:text-[oklch(0.70_0.03_264)]',
    border: 'border-[oklch(0.60_0.04_264/0.4)]',
    badge:
      'bg-[oklch(0.60_0.04_264/0.10)] dark:bg-[oklch(0.60_0.04_264/0.15)] text-[oklch(0.45_0.04_264)] dark:text-[oklch(0.72_0.03_264)]',
    dot: 'bg-[oklch(0.60_0.04_264)] dark:bg-[oklch(0.55_0.04_264)]',
    bottleneckRing: 'ring-[oklch(0.75_0.18_60)] ring-offset-1',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：Tooltip（悬浮提示）— Liquid Glass 毛玻璃风格
// ─────────────────────────────────────────────────────────────────────────────

interface TooltipData {
  stepLabel: string;
  seriesName: string;
  value: number;
  unit: string;
  conversionRate?: number;
  overallRate: number;
  lostCount?: number;
  isBottleneck?: boolean;
}

interface TooltipProps {
  data: TooltipData;
  visible: boolean;
}

function FunnelTooltip({ data, visible }: TooltipProps) {
  if (!visible) return null;
  return (
    <div
      className={[
        // Liquid Glass 毛玻璃效果
        'absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-52',
        'rounded-xl',
        'backdrop-blur-xl',
        'bg-white/80 dark:bg-[oklch(0.18_0.01_264/0.85)]',
        // 顶部高光线 + 底部暗线
        'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_8px_32px_-4px_oklch(0_0_0/0.18)]',
        'border border-[oklch(0.85_0.02_264/0.35)] dark:border-[oklch(0.55_0.04_264/0.25)]',
        'p-3 pointer-events-none',
      ].join(' ')}
    >
      {/* 步骤名称 */}
      <p className="text-xs font-semibold text-[oklch(0.25_0.02_264)] dark:text-[oklch(0.92_0.01_264)] mb-2 truncate font-sans">
        {data.stepLabel}
        {data.isBottleneck && (
          <span className="ml-1 text-[oklch(0.72_0.18_60)]">⚠</span>
        )}
      </p>
      {/* 系列名称 */}
      <p className="text-xs text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)] mb-1.5 font-sans">
        {data.seriesName}
      </p>
      {/* 绝对值 */}
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)]">数量</span>
        <span className="text-xs font-semibold text-[oklch(0.25_0.02_264)] dark:text-[oklch(0.92_0.01_264)] tabular-nums font-sans">
          {formatNumber(data.value)} {data.unit}
        </span>
      </div>
      {/* 步骤间转化率 */}
      {data.conversionRate !== undefined && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)]">步骤转化</span>
          <span
            className={`text-xs font-semibold tabular-nums font-sans ${
              data.isBottleneck
                ? 'text-[oklch(0.65_0.18_60)] dark:text-[oklch(0.75_0.18_60)]'
                : 'text-[oklch(0.52_0.16_152)] dark:text-[oklch(0.68_0.16_152)]'
            }`}
          >
            {formatRate(data.conversionRate)}
          </span>
        </div>
      )}
      {/* 流失数量 */}
      {data.lostCount !== undefined && data.lostCount > 0 && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)]">流失</span>
          <span className="text-xs font-semibold text-[oklch(0.55_0.20_25)] dark:text-[oklch(0.68_0.18_25)] tabular-nums font-sans">
            -{formatNumber(data.lostCount)} {data.unit}
          </span>
        </div>
      )}
      {/* 整体转化率 */}
      <div className="flex justify-between items-center pt-1.5 border-t border-[oklch(0.85_0.02_264/0.3)] dark:border-[oklch(0.45_0.04_264/0.3)] mt-1">
        <span className="text-xs text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)]">整体转化</span>
        <span className="text-xs font-bold text-[oklch(0.55_0.22_264)] dark:text-[oklch(0.72_0.18_264)] tabular-nums font-sans">
          {formatRate(data.overallRate)}
        </span>
      </div>
      {/* 箭头 */}
      <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-white/80 dark:border-t-[oklch(0.18_0.01_264/0.85)]" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：单步骤列（包含柱子组和步骤标签）
// ─────────────────────────────────────────────────────────────────────────────

interface StepColumnProps {
  stepIndex: number;
  stepLabel: string;
  series: FunnelSeries[];
  maxValue: number;
  unit: string;
  isBottleneck: boolean;
}

function StepColumn({ stepIndex, stepLabel, series, maxValue, unit, isBottleneck }: StepColumnProps) {
  const [hoveredSeriesIdx, setHoveredSeriesIdx] = useState<number | null>(null);

  return (
    <div className="flex flex-col items-center flex-1 min-w-[80px]">
      {/* 柱子区域 */}
      <div className="w-full flex items-end justify-center gap-1.5 h-40 relative">
        {series.map((s, sIdx) => {
          const step = s.steps[stepIndex];
          if (!step) return null;
          const heightPct = maxValue > 0 ? (step.value / maxValue) * 100 : 0;
          const colors = SERIES_COLORS[sIdx] ?? SERIES_COLORS[0];
          const isHovered = hoveredSeriesIdx === sIdx;
          const prevStep = stepIndex > 0 ? s.steps[stepIndex - 1] : null;
          const lostCount = prevStep ? prevStep.value - step.value : undefined;

          const tooltipData: TooltipData = {
            stepLabel,
            seriesName: s.name,
            value: step.value,
            unit,
            conversionRate: step.conversionRate,
            overallRate: s.overallConversionRate,
            lostCount,
            isBottleneck: step.isBottleneck,
          };

          return (
            <div
              key={s.name}
              className="relative flex-1 max-w-[56px] flex flex-col items-center justify-end group"
              onMouseEnter={() => setHoveredSeriesIdx(sIdx)}
              onMouseLeave={() => setHoveredSeriesIdx(null)}
            >
              {/* Tooltip */}
              <FunnelTooltip data={tooltipData} visible={isHovered} />

              {/* 数值标签（柱子顶部）— DM Sans 数字字体 */}
              <span
                className={`text-xs font-semibold tabular-nums mb-1 transition-opacity duration-200 font-sans ${
                  isHovered ? 'opacity-100' : 'opacity-60'
                } ${colors.text}`}
              >
                {formatNumber(step.value)}
              </span>

              {/* 柱子主体 — oklch 渐变 + Liquid Glass 圆角 */}
              <div
                className={[
                  'w-full rounded-t-lg transition-all duration-300 cursor-pointer',
                  // 渐变色柱子
                  `bg-gradient-to-t ${colors.barGradient}`,
                  // 瓶颈高亮环
                  isBottleneck && step.isBottleneck
                    ? `ring-2 ${colors.bottleneckRing}`
                    : '',
                  // Hover 效果
                  isHovered ? 'brightness-110 scale-x-105 shadow-lg' : '',
                ].join(' ')}
                style={{ height: `${heightPct}%`, minHeight: '8px' }}
              />
            </div>
          );
        })}
      </div>

      {/* 步骤标签 */}
      <div
        className={`mt-2 text-center px-1 ${
          isBottleneck
            ? 'text-[oklch(0.65_0.18_60)] dark:text-[oklch(0.75_0.18_60)]'
            : 'text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)]'
        }`}
      >
        {isBottleneck && (
          <span className="block text-xs font-bold mb-0.5">⚠ 瓶颈</span>
        )}
        <span className="text-xs leading-tight line-clamp-2 font-sans">{stepLabel}</span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：步骤间转化率箭头
// ─────────────────────────────────────────────────────────────────────────────

interface ConversionArrowProps {
  series: FunnelSeries[];
  stepIndex: number; // 当前步骤（箭头指向该步骤）
}

function ConversionArrow({ series, stepIndex }: ConversionArrowProps) {
  return (
    <div className="flex flex-col items-center justify-end pb-10 shrink-0 w-10">
      {series.map((s, sIdx) => {
        const step = s.steps[stepIndex];
        if (!step || step.conversionRate === undefined) return null;
        const colors = SERIES_COLORS[sIdx] ?? SERIES_COLORS[0];
        const isBottleneck = step.isBottleneck ?? false;
        return (
          <div key={s.name} className="flex flex-col items-center mb-1">
            <span
              className={`text-xs font-bold tabular-nums font-sans ${
                isBottleneck
                  ? 'text-[oklch(0.65_0.18_60)] dark:text-[oklch(0.75_0.18_60)]'
                  : colors.text
              }`}
            >
              {formatRate(step.conversionRate)}
            </span>
            <span
              className={`text-base leading-none ${
                isBottleneck
                  ? 'text-[oklch(0.72_0.18_60)] dark:text-[oklch(0.75_0.18_60)]'
                  : 'text-[oklch(0.75_0.03_264)] dark:text-[oklch(0.45_0.03_264)]'
              }`}
            >
              →
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 主组件：ConversionFunnel
// iOS 26 Liquid Glass 设计规范升级版
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 漏斗转化组件 (Conversion Funnel) — iOS 26 Liquid Glass 版
 *
 * 以阶梯柱状图形式展示用户在特定业务流程中的流失情况，
 * 支持多漏斗对比，自动高亮转化瓶颈步骤。
 * 采用 iOS 26 Liquid Glass 毛玻璃设计规范：
 * - 外层容器：backdrop-blur-xl + bg-white/65 + inset shadow 高光线
 * - 漏斗柱子：oklch 品牌蓝渐变
 * - 字体：DM Sans（数字/英文）+ Noto Sans SC（中文）
 * - 深色模式：完整 dark: 变体支持
 *
 * @example
 * <ConversionFunnel
 *   title="新用户注册转化漏斗"
 *   description="本周注册转化率受短信通道延迟影响，『获取验证码』环节成为核心瓶颈。"
 *   series={[thisWeekSeries, lastWeekSeries]}
 *   unit="人"
 * />
 */
export function ConversionFunnel({ title, description, series, unit = '人' }: ConversionFunnelProps) {
  // 确保最多展示 2 个系列
  const displaySeries = series.slice(0, 2);

  // 计算所有系列中的最大值（用于归一化柱子高度）
  const maxValue = Math.max(
    ...displaySeries.flatMap((s) => s.steps.map((step) => step.value))
  );

  // 获取步骤数量（以第一个系列为准）
  const stepCount = displaySeries[0]?.steps.length ?? 0;
  const stepLabels = displaySeries[0]?.steps.map((s) => s.label) ?? [];

  // 检查是否存在瓶颈步骤
  const hasBottleneck = displaySeries.some((s) => s.steps.some((step) => step.isBottleneck));

  return (
    <div
      className={[
        // ── iOS 26 Liquid Glass 外层容器 ──
        'rounded-2xl',
        // 毛玻璃背景
        'backdrop-blur-xl',
        'bg-white/65 dark:bg-[oklch(0.18_0.01_264/0.70)]',
        // 边框
        'border border-[oklch(0.85_0.02_264/0.45)] dark:border-[oklch(0.55_0.04_264/0.22)]',
        // 顶部高光线 + 底部暗线 + 外阴影
        'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_4px_24px_-4px_oklch(0_0_0/0.08)]',
        // Hover 效果
        'hover:-translate-y-1 hover:shadow-xl transition-all duration-250',
        'p-5 flex flex-col',
      ].join(' ')}
    >

      {/* ── 标题区 ── */}
      <div className="flex items-start justify-between mb-3 gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {/* 组件类型标签 — oklch 品牌蓝 */}
            <span className="text-xs font-semibold uppercase tracking-widest text-[oklch(0.55_0.22_264)] dark:text-[oklch(0.72_0.18_264)] font-sans">
              转化漏斗
            </span>
            {hasBottleneck && (
              <span
                className={[
                  'text-xs px-2 py-0.5 rounded-full font-medium font-sans',
                  'bg-[oklch(0.75_0.18_60/0.15)] dark:bg-[oklch(0.65_0.18_60/0.20)]',
                  'text-[oklch(0.55_0.18_60)] dark:text-[oklch(0.78_0.18_60)]',
                  'border border-[oklch(0.75_0.18_60/0.3)] dark:border-[oklch(0.65_0.18_60/0.3)]',
                ].join(' ')}
              >
                ⚠ 存在转化瓶颈
              </span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-[oklch(0.20_0.02_264)] dark:text-[oklch(0.94_0.01_264)] truncate font-sans">
            {title}
          </h3>
        </div>

        {/* 整体转化率徽章 — Liquid Glass 风格 */}
        <div className="shrink-0 flex flex-col items-end gap-1">
          {displaySeries.map((s, idx) => {
            const colors = SERIES_COLORS[idx] ?? SERIES_COLORS[0];
            return (
              <div
                key={s.name}
                className={[
                  'flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg font-sans',
                  'backdrop-blur-sm',
                  colors.badge,
                  'border border-[oklch(0.85_0.02_264/0.25)] dark:border-[oklch(0.55_0.04_264/0.20)]',
                ].join(' ')}
              >
                <span className={`w-2 h-2 rounded-full shrink-0 ${colors.dot}`} />
                <span className="font-medium">{s.name}</span>
                <span className="font-bold tabular-nums">{formatRate(s.overallConversionRate)}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── 描述文字 ── */}
      {description && (
        <p
          className={[
            'text-xs leading-relaxed mb-4 font-sans',
            'text-[oklch(0.45_0.03_264)] dark:text-[oklch(0.68_0.03_264)]',
            // 内层毛玻璃卡片
            'rounded-xl px-3 py-2',
            'bg-[oklch(0.55_0.22_264/0.06)] dark:bg-[oklch(0.55_0.22_264/0.10)]',
            'border-l-2 border-[oklch(0.55_0.22_264/0.5)] dark:border-[oklch(0.65_0.18_264/0.5)]',
          ].join(' ')}
        >
          {description}
        </p>
      )}

      {/* ── 图例 ── */}
      {displaySeries.length > 1 && (
        <div className="flex items-center gap-4 mb-4">
          {displaySeries.map((s, idx) => {
            const colors = SERIES_COLORS[idx] ?? SERIES_COLORS[0];
            return (
              <div key={s.name} className="flex items-center gap-1.5">
                <span className={`w-3 h-3 rounded-sm ${colors.bar}`} />
                <span className="text-xs text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)] font-sans">
                  {s.name}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* ── 漏斗图表区 ── */}
      <div className="overflow-x-auto">
        <div className="flex items-stretch min-w-max gap-0">
          {Array.from({ length: stepCount }).map((_, stepIdx) => (
            <React.Fragment key={stepIdx}>
              {/* 步骤柱 */}
              <StepColumn
                stepIndex={stepIdx}
                stepLabel={stepLabels[stepIdx] ?? `步骤 ${stepIdx + 1}`}
                series={displaySeries}
                maxValue={maxValue}
                unit={unit}
                isBottleneck={displaySeries.some((s) => s.steps[stepIdx]?.isBottleneck)}
              />
              {/* 步骤间转化率箭头（最后一步后不显示） */}
              {stepIdx < stepCount - 1 && (
                <ConversionArrow series={displaySeries} stepIndex={stepIdx + 1} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* ── 底部摘要：整体流失分析 ── */}
      <div className="mt-4 pt-4 border-t border-[oklch(0.85_0.02_264/0.3)] dark:border-[oklch(0.45_0.04_264/0.25)]">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {displaySeries.map((s, sIdx) => {
            const firstStep = s.steps[0];
            const lastStep = s.steps[s.steps.length - 1];
            const totalLost = firstStep && lastStep ? firstStep.value - lastStep.value : 0;
            const colors = SERIES_COLORS[sIdx] ?? SERIES_COLORS[0];

            return (
              <React.Fragment key={s.name}>
                {/* 整体转化数 — 内层 Liquid Glass 卡片 */}
                <div
                  className={[
                    'rounded-xl p-3',
                    'backdrop-blur-sm',
                    'bg-[oklch(0.97_0.01_264/0.60)] dark:bg-[oklch(0.22_0.02_264/0.50)]',
                    'border border-[oklch(0.85_0.02_264/0.35)] dark:border-[oklch(0.45_0.04_264/0.25)]',
                    'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.40)]',
                    'hover:-translate-y-0.5 hover:shadow-md transition-all duration-200',
                  ].join(' ')}
                >
                  <p className="text-xs text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)] mb-1 font-sans">
                    {s.name} · 转化人数
                  </p>
                  {/* KPI 核心数值：text-3xl font-bold tracking-tight */}
                  <p className={`text-3xl font-bold tracking-tight tabular-nums font-sans ${colors.text}`}>
                    {lastStep ? formatNumber(lastStep.value) : '—'}
                  </p>
                  <p className="text-xs text-[oklch(0.60_0.03_264)] dark:text-[oklch(0.60_0.03_264)] mt-0.5 font-sans">
                    {unit}
                  </p>
                </div>
                {/* 整体流失数 — 内层 Liquid Glass 卡片 */}
                <div
                  className={[
                    'rounded-xl p-3',
                    'backdrop-blur-sm',
                    'bg-[oklch(0.97_0.01_264/0.60)] dark:bg-[oklch(0.22_0.02_264/0.50)]',
                    'border border-[oklch(0.85_0.02_264/0.35)] dark:border-[oklch(0.45_0.04_264/0.25)]',
                    'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.40)]',
                    'hover:-translate-y-0.5 hover:shadow-md transition-all duration-200',
                  ].join(' ')}
                >
                  <p className="text-xs text-[oklch(0.55_0.03_264)] dark:text-[oklch(0.65_0.03_264)] mb-1 font-sans">
                    {s.name} · 总流失
                  </p>
                  {/* KPI 核心数值：text-3xl font-bold tracking-tight */}
                  <p className="text-3xl font-bold tracking-tight tabular-nums text-[oklch(0.55_0.20_25)] dark:text-[oklch(0.68_0.18_25)] font-sans">
                    -{formatNumber(totalLost)}
                  </p>
                  <p className="text-xs text-[oklch(0.60_0.03_264)] dark:text-[oklch(0.60_0.03_264)] mt-0.5 font-sans">
                    {unit}
                  </p>
                </div>
              </React.Fragment>
            );
          })}
        </div>

        {/* 瓶颈说明 — Liquid Glass 警告卡片 */}
        {hasBottleneck && (
          <div
            className={[
              'mt-3 flex items-start gap-2 rounded-xl px-3 py-2.5',
              'backdrop-blur-sm',
              'bg-[oklch(0.75_0.18_60/0.08)] dark:bg-[oklch(0.65_0.18_60/0.12)]',
              'border border-[oklch(0.75_0.18_60/0.3)] dark:border-[oklch(0.65_0.18_60/0.25)]',
              'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.30)]',
            ].join(' ')}
          >
            <span className="text-[oklch(0.65_0.18_60)] dark:text-[oklch(0.75_0.18_60)] text-sm shrink-0 mt-0.5">⚠</span>
            <div>
              <p className="text-xs font-semibold text-[oklch(0.50_0.18_60)] dark:text-[oklch(0.78_0.18_60)] mb-0.5 font-sans">
                转化瓶颈识别
              </p>
              {displaySeries.map((s) => {
                const bottleneckStep = s.steps.find((step) => step.isBottleneck);
                if (!bottleneckStep) return null;
                return (
                  <p
                    key={s.name}
                    className="text-xs text-[oklch(0.55_0.15_60)] dark:text-[oklch(0.72_0.15_60)] font-sans"
                  >
                    <span className="font-medium">{s.name}</span>：「{bottleneckStep.label}」转化率最低，仅{' '}
                    {bottleneckStep.conversionRate !== undefined
                      ? formatRate(bottleneckStep.conversionRate)
                      : '—'}
                    ，需重点优化。
                  </p>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Mock 数据（供开发预览和测试使用）
// ─────────────────────────────────────────────────────────────────────────────

export const mockConversionFunnelData: ConversionFunnelProps = {
  title: '新用户注册转化漏斗',
  description:
    '本周注册转化率受短信通道延迟影响，「获取验证码」环节转化率环比下降 12pp，成为核心瓶颈，建议优先排查短信服务商稳定性。',
  unit: '人',
  series: [
    {
      name: '本周',
      colorKey: 'indigo',
      overallConversionRate: 18.5,
      steps: [
        { id: 's1', label: '访问落地页', value: 10000 },
        { id: 's2', label: '点击注册', value: 6500, conversionRate: 65.0 },
        {
          id: 's3',
          label: '获取验证码',
          value: 3200,
          conversionRate: 49.2,
          isBottleneck: true,
        },
        { id: 's4', label: '注册成功', value: 1850, conversionRate: 57.8 },
      ],
    },
    {
      name: '上周',
      colorKey: 'slate',
      overallConversionRate: 24.2,
      steps: [
        { id: 's1', label: '访问落地页', value: 9500 },
        { id: 's2', label: '点击注册', value: 6200, conversionRate: 65.2 },
        { id: 's3', label: '获取验证码', value: 3800, conversionRate: 61.2 },
        { id: 's4', label: '注册成功', value: 2300, conversionRate: 60.5 },
      ],
    },
  ],
};

// ─────────────────────────────────────────────────────────────────────────────
// 预览入口（独立运行时展示 Mock 数据）
// ─────────────────────────────────────────────────────────────────────────────

export default function ConversionFunnelPreview() {
  return (
    <div
      className="min-h-screen p-8"
      style={{
        // iOS 26 风格背景：浅色模式用磨砂白，深色模式用深蓝灰
        background:
          'linear-gradient(135deg, oklch(0.94 0.02 264) 0%, oklch(0.90 0.03 280) 100%)',
      }}
    >
      {/* 字体注入 CSS 变量 */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
        :root {
          --font-sans: 'DM Sans', 'Noto Sans SC', system-ui, sans-serif;
        }
        .font-sans {
          font-family: var(--font-sans);
        }
        @media (prefers-color-scheme: dark) {
          body { background: oklch(0.12 0.02 264); }
        }
      `}</style>

      <div className="max-w-3xl mx-auto">
        <h1 className="text-xl font-bold text-[oklch(0.20_0.02_264)] dark:text-[oklch(0.94_0.01_264)] mb-2 font-sans">
          漏斗转化组件预览 — iOS 26 Liquid Glass
        </h1>
        <p className="text-sm text-[oklch(0.50_0.03_264)] dark:text-[oklch(0.65_0.03_264)] mb-6 font-sans">
          毛玻璃卡片 · oklch 品牌蓝渐变 · DM Sans / Noto Sans SC 字体 · 深色模式双主题
        </p>

        {/* 双漏斗对比示例 */}
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-[oklch(0.50_0.03_264)] dark:text-[oklch(0.65_0.03_264)] mb-3 font-sans">
            双漏斗对比（本周 vs 上周）
          </h2>
          <ConversionFunnel {...mockConversionFunnelData} />
        </div>

        {/* 单漏斗示例 */}
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-[oklch(0.50_0.03_264)] dark:text-[oklch(0.65_0.03_264)] mb-3 font-sans">
            单漏斗示例（付费转化）
          </h2>
          <ConversionFunnel
            title="付费转化漏斗"
            description="付费渗透率本周提升 0.4pp，「加入购物车」→「发起支付」环节转化率达到历史最高，商业化策略初见成效。"
            unit="人"
            series={[
              {
                name: '本周',
                colorKey: 'indigo',
                overallConversionRate: 3.8,
                steps: [
                  { id: 'p1', label: '进入商城', value: 8500 },
                  { id: 'p2', label: '查看商品', value: 5200, conversionRate: 61.2 },
                  { id: 'p3', label: '加入购物车', value: 1800, conversionRate: 34.6, isBottleneck: true },
                  { id: 'p4', label: '发起支付', value: 650, conversionRate: 36.1 },
                  { id: 'p5', label: '支付成功', value: 323, conversionRate: 49.7 },
                ],
              },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

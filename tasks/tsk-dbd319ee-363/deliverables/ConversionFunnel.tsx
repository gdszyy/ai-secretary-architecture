// @section:conversion_funnel - 漏斗转化组件 (Conversion Funnel)
// =============================================================================
// 组件数据绑定说明
// 组件 Key: conversion_funnel
// 组件类型: 详情组件 (Detail Component)
// 适用模块: 增长与获客 (Growth & Acquisition)、商业化与变现 (Monetization)
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
// 颜色配置
// ─────────────────────────────────────────────────────────────────────────────

/** 系列颜色配置 */
const SERIES_COLORS = [
  {
    bar: 'bg-indigo-500',
    barLight: 'bg-indigo-400',
    text: 'text-indigo-600 dark:text-indigo-400',
    border: 'border-indigo-400',
    badge: 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300',
    dot: 'bg-indigo-500',
  },
  {
    bar: 'bg-slate-300 dark:bg-slate-600',
    barLight: 'bg-slate-200 dark:bg-slate-700',
    text: 'text-slate-500 dark:text-slate-400',
    border: 'border-slate-400',
    badge: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400',
    dot: 'bg-slate-400',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：Tooltip（悬浮提示）
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
    <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 shadow-xl p-3 pointer-events-none">
      {/* 步骤名称 */}
      <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-2 truncate">
        {data.stepLabel}
        {data.isBottleneck && (
          <span className="ml-1 text-amber-500">⚠</span>
        )}
      </p>
      {/* 系列名称 */}
      <p className="text-xs text-slate-400 mb-1">{data.seriesName}</p>
      {/* 绝对值 */}
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-slate-500">数量</span>
        <span className="text-xs font-medium text-slate-700 dark:text-slate-200 tabular-nums">
          {formatNumber(data.value)} {data.unit}
        </span>
      </div>
      {/* 步骤间转化率 */}
      {data.conversionRate !== undefined && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-slate-500">步骤转化</span>
          <span className={`text-xs font-medium tabular-nums ${data.isBottleneck ? 'text-amber-500' : 'text-emerald-500'}`}>
            {formatRate(data.conversionRate)}
          </span>
        </div>
      )}
      {/* 流失数量 */}
      {data.lostCount !== undefined && data.lostCount > 0 && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-slate-500">流失</span>
          <span className="text-xs font-medium text-red-400 tabular-nums">
            -{formatNumber(data.lostCount)} {data.unit}
          </span>
        </div>
      )}
      {/* 整体转化率 */}
      <div className="flex justify-between items-center pt-1 border-t border-slate-100 dark:border-slate-700 mt-1">
        <span className="text-xs text-slate-500">整体转化</span>
        <span className="text-xs font-semibold text-indigo-500 tabular-nums">
          {formatRate(data.overallRate)}
        </span>
      </div>
      {/* 箭头 */}
      <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-white dark:border-t-slate-800" />
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

              {/* 数值标签（柱子顶部） */}
              <span className={`text-xs font-semibold tabular-nums mb-1 transition-opacity ${isHovered ? 'opacity-100' : 'opacity-70'} ${colors.text}`}>
                {formatNumber(step.value)}
              </span>

              {/* 柱子主体 */}
              <div
                className={`
                  w-full rounded-t-lg transition-all duration-300 cursor-pointer
                  ${isBottleneck && step.isBottleneck ? 'ring-2 ring-amber-400 ring-offset-1' : ''}
                  ${isHovered ? 'brightness-110 scale-x-105' : ''}
                  ${colors.bar}
                `}
                style={{ height: `${heightPct}%`, minHeight: '8px' }}
              />
            </div>
          );
        })}
      </div>

      {/* 步骤标签 */}
      <div className={`mt-2 text-center px-1 ${isBottleneck ? 'text-amber-500 dark:text-amber-400' : 'text-slate-500 dark:text-slate-400'}`}>
        {isBottleneck && (
          <span className="block text-xs font-bold mb-0.5">⚠ 瓶颈</span>
        )}
        <span className="text-xs leading-tight line-clamp-2">{stepLabel}</span>
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
              className={`text-xs font-bold tabular-nums ${
                isBottleneck
                  ? 'text-amber-500 dark:text-amber-400'
                  : colors.text
              }`}
            >
              {formatRate(step.conversionRate)}
            </span>
            <span className={`text-base leading-none ${isBottleneck ? 'text-amber-400' : 'text-slate-300 dark:text-slate-600'}`}>
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
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 漏斗转化组件 (Conversion Funnel)
 *
 * 以阶梯柱状图形式展示用户在特定业务流程中的流失情况，
 * 支持多漏斗对比，自动高亮转化瓶颈步骤。
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
    <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 p-5 flex flex-col">

      {/* ── 标题区 ── */}
      <div className="flex items-start justify-between mb-3 gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-widest text-indigo-500">
              转化漏斗
            </span>
            {hasBottleneck && (
              <span className="text-xs bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded-full font-medium">
                ⚠ 存在转化瓶颈
              </span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">
            {title}
          </h3>
        </div>

        {/* 整体转化率徽章 */}
        <div className="shrink-0 flex flex-col items-end gap-1">
          {displaySeries.map((s, idx) => {
            const colors = SERIES_COLORS[idx] ?? SERIES_COLORS[0];
            return (
              <div key={s.name} className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg ${colors.badge}`}>
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
        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4 bg-slate-50 dark:bg-slate-700/40 rounded-lg px-3 py-2 border-l-2 border-indigo-300 dark:border-indigo-600">
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
                <span className="text-xs text-slate-500 dark:text-slate-400">{s.name}</span>
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
      <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {displaySeries.map((s, sIdx) => {
            const firstStep = s.steps[0];
            const lastStep = s.steps[s.steps.length - 1];
            const totalLost = firstStep && lastStep ? firstStep.value - lastStep.value : 0;
            const colors = SERIES_COLORS[sIdx] ?? SERIES_COLORS[0];
            const bottleneckStep = s.steps.find((step) => step.isBottleneck);

            return (
              <React.Fragment key={s.name}>
                {/* 整体转化数 */}
                <div className="rounded-xl bg-slate-50 dark:bg-slate-700/40 p-3">
                  <p className="text-xs text-slate-400 mb-1">{s.name} · 转化人数</p>
                  <p className={`text-lg font-bold tabular-nums ${colors.text}`}>
                    {lastStep ? formatNumber(lastStep.value) : '—'}
                  </p>
                  <p className="text-xs text-slate-400">{unit}</p>
                </div>
                {/* 整体流失数 */}
                <div className="rounded-xl bg-slate-50 dark:bg-slate-700/40 p-3">
                  <p className="text-xs text-slate-400 mb-1">{s.name} · 总流失</p>
                  <p className="text-lg font-bold tabular-nums text-red-400">
                    -{formatNumber(totalLost)}
                  </p>
                  <p className="text-xs text-slate-400">{unit}</p>
                </div>
              </React.Fragment>
            );
          })}
        </div>

        {/* 瓶颈说明 */}
        {hasBottleneck && (
          <div className="mt-3 flex items-start gap-2 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/50 px-3 py-2.5">
            <span className="text-amber-500 text-sm shrink-0 mt-0.5">⚠</span>
            <div>
              <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 mb-0.5">转化瓶颈识别</p>
              {displaySeries.map((s) => {
                const bottleneckStep = s.steps.find((step) => step.isBottleneck);
                if (!bottleneckStep) return null;
                return (
                  <p key={s.name} className="text-xs text-amber-600 dark:text-amber-500">
                    <span className="font-medium">{s.name}</span>：「{bottleneckStep.label}」转化率最低，仅 {bottleneckStep.conversionRate !== undefined ? formatRate(bottleneckStep.conversionRate) : '—'}，需重点优化。
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
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-6">
          漏斗转化组件预览
        </h1>

        {/* 双漏斗对比示例 */}
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-slate-500 mb-3">双漏斗对比（本周 vs 上周）</h2>
          <ConversionFunnel {...mockConversionFunnelData} />
        </div>

        {/* 单漏斗示例 */}
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-slate-500 mb-3">单漏斗示例（付费转化）</h2>
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

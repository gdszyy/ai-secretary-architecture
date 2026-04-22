// @section:user_segmentation_bubble - 用户分层气泡图 (User Segmentation Bubble Chart)
// ─────────────────────────────────────────────────────────────────────────────
// 组件 Key: user_segmentation_bubble
// 适用模块: 用户运营、产品与活跃、玩家分层与生命周期、客户成功与健康分
// 技术栈: React + TypeScript + TailwindCSS + Recharts (ScatterChart)
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
// 象限配置常量
// ─────────────────────────────────────────────────────────────────────────────

const QUADRANT_CONFIG: Record<QuadrantType, {
  label: string;
  labelEn: string;
  color: string;
  fillColor: string;
  bgColor: string;
  textColor: string;
  borderColor: string;
  description: string;
}> = {
  high_value: {
    label: '高价值',
    labelEn: 'High Value',
    color: '#10b981',
    fillColor: 'rgba(16, 185, 129, 0.75)',
    bgColor: 'bg-emerald-400/15',
    textColor: 'text-emerald-400',
    borderColor: 'border-emerald-400/40',
    description: '高活跃 · 高价值 · 核心用户',
  },
  high_potential: {
    label: '高潜力',
    labelEn: 'High Potential',
    color: '#38bdf8',
    fillColor: 'rgba(56, 189, 248, 0.75)',
    bgColor: 'bg-sky-400/15',
    textColor: 'text-sky-400',
    borderColor: 'border-sky-400/40',
    description: '低活跃 · 高价值 · 待激活',
  },
  to_be_activated: {
    label: '待激活',
    labelEn: 'To Be Activated',
    color: '#94a3b8',
    fillColor: 'rgba(148, 163, 184, 0.65)',
    bgColor: 'bg-slate-400/15',
    textColor: 'text-slate-400',
    borderColor: 'border-slate-400/40',
    description: '低活跃 · 低价值 · 长尾用户',
  },
  churn_risk: {
    label: '流失风险',
    labelEn: 'Churn Risk',
    color: '#f59e0b',
    fillColor: 'rgba(245, 158, 11, 0.75)',
    bgColor: 'bg-amber-400/15',
    textColor: 'text-amber-400',
    borderColor: 'border-amber-400/40',
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
// 自定义 Tooltip 组件
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
        rounded-xl border shadow-xl backdrop-blur-sm
        bg-white dark:bg-slate-800
        border-slate-200 dark:border-slate-600
        p-4 min-w-[200px] max-w-[260px]
      `}
      style={{ pointerEvents: 'none' }}
    >
      {/* 分层名称 */}
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-3 h-3 rounded-full shrink-0"
          style={{ backgroundColor: cfg.color }}
        />
        <span className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-tight">
          {d.name}
        </span>
      </div>

      {/* 象限标签 */}
      <div className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full mb-3 ${cfg.bgColor} ${cfg.textColor}`}>
        {cfg.label} · {cfg.description}
      </div>

      {/* 核心指标 */}
      <div className="space-y-1.5 text-xs">
        <div className="flex justify-between items-center">
          <span className="text-slate-500 dark:text-slate-400">{sizeLabel}</span>
          <span className="font-semibold text-slate-700 dark:text-slate-200 tabular-nums">
            {d.sizeValue.toLocaleString()}{sizeUnit ? ` ${sizeUnit}` : ''}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 dark:text-slate-400">{xAxisLabel}</span>
          <span className="font-semibold text-slate-700 dark:text-slate-200 tabular-nums">
            {xAxisUnit ? `${xAxisUnit} ` : ''}{d.xValue.toLocaleString()}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500 dark:text-slate-400">{yAxisLabel}</span>
          <span className="font-semibold text-slate-700 dark:text-slate-200 tabular-nums">
            {yAxisUnit ? `${yAxisUnit} ` : ''}{d.yValue.toLocaleString()}
          </span>
        </div>
        {d.changeRate && (
          <div className="flex justify-between items-center">
            <span className="text-slate-500 dark:text-slate-400">环比变化</span>
            <span
              className={`font-semibold tabular-nums ${
                d.changeRate.startsWith('+') ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {d.changeRate}
            </span>
          </div>
        )}
      </div>

      {/* 特征描述 */}
      {d.description && (
        <p className="mt-2.5 pt-2.5 border-t border-slate-200 dark:border-slate-600 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          {d.description}
        </p>
      )}

      {/* 运营建议 */}
      {d.recommendation && (
        <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-600">
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
// 自定义气泡渲染（带描边和阴影）
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
      {/* 外圈光晕 */}
      <circle
        cx={cx}
        cy={cy}
        r={r + 4}
        fill={cfg.color}
        fillOpacity={0.12}
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
      {/* 高亮点 */}
      <circle
        cx={cx - r * 0.25}
        cy={cy - r * 0.25}
        r={r * 0.2}
        fill="white"
        fillOpacity={0.5}
      />
    </g>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 主组件：UserSegmentationBubble
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
      className="
        rounded-2xl border border-slate-200 dark:border-slate-700
        bg-white dark:bg-slate-800/60
        p-5 flex flex-col
        w-full
      "
    >
      {/* ── 头部区域 ── */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-widest text-violet-500">
            用户分层
          </span>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-100 mt-0.5">
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
          <div className="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-600" />
          <div className="w-3.5 h-3.5 rounded-full bg-slate-300 dark:bg-slate-600" />
          <div className="w-5 h-5 rounded-full bg-slate-300 dark:bg-slate-600" />
        </div>
        <span>气泡大小 = {size.label}{size.unit ? `（${size.unit}）` : ''}</span>
      </div>

      {/* ── 图表区域 ── */}
      <div className="relative flex-1" style={{ minHeight: 380 }}>
        {/* 象限背景标签 */}
        <div className="absolute inset-0 pointer-events-none z-10" style={{ paddingLeft: 48, paddingBottom: 40, paddingRight: 16, paddingTop: 8 }}>
          <div className="relative w-full h-full">
            {/* 左上：高潜力 */}
            <div className="absolute top-2 left-2 text-xs font-semibold text-sky-400/40 dark:text-sky-400/30 select-none">
              ← 低活跃 · 高价值
            </div>
            {/* 右上：高价值 */}
            <div className="absolute top-2 right-2 text-xs font-semibold text-emerald-400/40 dark:text-emerald-400/30 select-none text-right">
              高活跃 · 高价值 →
            </div>
            {/* 左下：待激活 */}
            <div className="absolute bottom-2 left-2 text-xs font-semibold text-slate-400/40 dark:text-slate-400/30 select-none">
              ← 低活跃 · 低价值
            </div>
            {/* 右下：流失风险 */}
            <div className="absolute bottom-2 right-2 text-xs font-semibold text-amber-400/40 dark:text-amber-400/30 select-none text-right">
              高活跃 · 低价值 →
            </div>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={380}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 20 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(148, 163, 184, 0.15)"
            />

            <XAxis
              type="number"
              dataKey="x"
              domain={[xMin, xMax]}
              tickLine={false}
              axisLine={{ stroke: 'rgba(148, 163, 184, 0.3)' }}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              tickFormatter={(v) => `${v}${xAxis.unit ? xAxis.unit : ''}`}
            >
              <Label
                value={xAxis.label}
                offset={-10}
                position="insideBottom"
                style={{ fontSize: 11, fill: '#94a3b8', fontWeight: 500 }}
              />
            </XAxis>

            <YAxis
              type="number"
              dataKey="y"
              domain={[yMin, yMax]}
              tickLine={false}
              axisLine={{ stroke: 'rgba(148, 163, 184, 0.3)' }}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              tickFormatter={(v) => `${yAxis.unit ? yAxis.unit : ''}${v}`}
              width={48}
            >
              <Label
                value={yAxis.label}
                angle={-90}
                position="insideLeft"
                offset={10}
                style={{ fontSize: 11, fill: '#94a3b8', fontWeight: 500 }}
              />
            </YAxis>

            <ZAxis
              type="number"
              dataKey="z"
              range={[bubbleMin, bubbleMax]}
              domain={[zMin, zMax]}
            />

            {/* 象限分割线 */}
            <ReferenceLine
              x={xAxis.baseline}
              stroke="rgba(148, 163, 184, 0.4)"
              strokeDasharray="6 3"
              strokeWidth={1.5}
            />
            <ReferenceLine
              y={yAxis.baseline}
              stroke="rgba(148, 163, 184, 0.4)"
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
              cursor={{ strokeDasharray: '3 3', stroke: 'rgba(148,163,184,0.3)' }}
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

      {/* ── 底部：象限运营策略摘要 ── */}
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
              className={`flex items-start gap-2 p-2.5 rounded-xl border ${cfg.bgColor} ${cfg.borderColor}`}
            >
              <div
                className="w-2.5 h-2.5 rounded-full mt-0.5 shrink-0"
                style={{ backgroundColor: cfg.color }}
              />
              <div className="min-w-0">
                <div className={`text-xs font-semibold ${cfg.textColor}`}>
                  {cfg.label}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-6 sm:p-10">
      <div className="max-w-4xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            用户分层气泡图 · 组件演示
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            组件 Key: <code className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-violet-500 font-mono text-xs">user_segmentation_bubble</code>
            &nbsp;·&nbsp; 技术栈: React + TypeScript + TailwindCSS + Recharts
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

        {/* 使用说明 */}
        <div className="mt-6 p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">
            使用说明
          </h2>
          <div className="space-y-2 text-xs text-slate-500 dark:text-slate-400">
            <p>• 将鼠标悬停在气泡上，查看该用户分层的详细信息（规模、指标、运营建议）。</p>
            <p>• 点击气泡可触发 <code className="bg-slate-100 dark:bg-slate-800 px-1 rounded font-mono">onBubbleClick</code> 回调，用于跳转到该分层的详细运营页面。</p>
            <p>• 四条象限分割线基于 <code className="bg-slate-100 dark:bg-slate-800 px-1 rounded font-mono">xAxis.baseline</code> 和 <code className="bg-slate-100 dark:bg-slate-800 px-1 rounded font-mono">yAxis.baseline</code> 绘制，可根据业务实际调整。</p>
            <p>• 若数据点未提供 <code className="bg-slate-100 dark:bg-slate-800 px-1 rounded font-mono">quadrant</code> 字段，组件将根据基准线自动推断所属象限。</p>
          </div>
        </div>
      </div>
    </div>
  );
}

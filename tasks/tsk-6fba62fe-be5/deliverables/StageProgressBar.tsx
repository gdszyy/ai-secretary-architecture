// @section:stage_progress_bar - 业务阶段进度组件 (Hero Component)
//
// 组件 Key: stage_progress_bar
// 类型: 首屏组件 (Hero Component)
// 适用模块: 里程碑进度 (Milestone Progress)
//
// 三层交互模型:
//   1. 一眼定调: 横向步骤条，当前阶段高亮，已完成阶段对勾标记，整体进度百分比
//   2. 悬浮概要: Hover 阶段节点弹出浮层，显示核心目标及当前完成情况
//   3. 下钻详情: Click 阶段节点触发 onDrillDown 回调，传入阶段 ID
//
// 数据接口: StageProgressData
// 与 analysis_framework.md 第 4.1 节业务阶段矩阵深度联动
//
// 使用示例:
//   <StageProgressBar
//     data={data.stageProgress}
//     onDrillDown={(stageId) => scrollToSection(`stage-detail-${stageId}`)}
//   />
//
// 数据接口 (StageProgressData):
//   currentStageId: BusinessStageId    — 当前阶段 ID
//   overallProgress: number            — 整体进度百分比 (0-100)
//   stages: BusinessStage[]            — 5 个阶段的详细数据

import React, { useState, useRef, useEffect } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// TypeScript 接口定义
// ─────────────────────────────────────────────────────────────────────────────

/** 业务阶段 ID（与 analysis_framework.md 第 4.1 节对应） */
export type BusinessStageId = 'seed' | 'launch' | 'growth' | 'scale' | 'mature';

/** 阶段状态 */
export type StageStatus = 'completed' | 'current' | 'upcoming';

/** 悬浮浮层上下文类型（影响颜色主题） */
export type ContextType = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

/** 阶段指标项 */
export interface StageMetric {
  /** 指标名称 */
  label: string;
  /** 当前值 */
  value: string;
  /** 目标值 */
  target: string;
}

/** 单个业务阶段数据 */
export interface BusinessStage {
  /** 阶段 ID */
  id: BusinessStageId;
  /** 阶段中文名（如：成长期） */
  name: string;
  /** 阶段英文名（如：Growth） */
  nameEn: string;
  /** 阶段状态 */
  status: StageStatus;
  /** 阶段副标题/定义（如：规模化增长） */
  subtitle: string;
  /** 核心目标描述 */
  coreObjective: string;
  /** 当前完成情况描述 */
  currentProgress: string;
  /** 浮层上下文类型（决定颜色主题） */
  contextType: ContextType;
  /** 关键指标列表（悬浮浮层展示，可选） */
  metrics?: StageMetric[];
}

/** 业务阶段进度组件整体数据 */
export interface StageProgressData {
  /** 当前所处阶段 ID */
  currentStageId: BusinessStageId;
  /** 整体进度百分比 (0-100) */
  overallProgress: number;
  /** 阶段列表（固定 5 个，按顺序） */
  stages: BusinessStage[];
}

/** 组件 Props */
export interface StageProgressBarProps {
  /** 组件数据 */
  data: StageProgressData;
  /**
   * 下钻点击回调
   * @param stageId 被点击的阶段 ID
   */
  onDrillDown?: (stageId: BusinessStageId) => void;
  /** 自定义外层容器类名 */
  className?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// 常量与工具函数
// ─────────────────────────────────────────────────────────────────────────────

/** 上下文类型颜色配置 */
const CONTEXT_CONFIG: Record<ContextType, {
  badge: string;
  badgeBg: string;
  border: string;
  dot: string;
  text: string;
}> = {
  success: {
    badge: 'text-emerald-400',
    badgeBg: 'bg-emerald-400/15',
    border: 'border-emerald-400/30',
    dot: 'bg-emerald-400',
    text: 'text-emerald-300',
  },
  warning: {
    badge: 'text-amber-400',
    badgeBg: 'bg-amber-400/15',
    border: 'border-amber-400/30',
    dot: 'bg-amber-400',
    text: 'text-amber-300',
  },
  danger: {
    badge: 'text-red-400',
    badgeBg: 'bg-red-400/15',
    border: 'border-red-400/30',
    dot: 'bg-red-400',
    text: 'text-red-300',
  },
  info: {
    badge: 'text-sky-400',
    badgeBg: 'bg-sky-400/15',
    border: 'border-sky-400/30',
    dot: 'bg-sky-400',
    text: 'text-sky-300',
  },
  neutral: {
    badge: 'text-slate-400',
    badgeBg: 'bg-slate-400/15',
    border: 'border-slate-400/30',
    dot: 'bg-slate-400',
    text: 'text-slate-300',
  },
};

/** 上下文类型标签 */
const CONTEXT_LABEL: Record<ContextType, string> = {
  success: '进展顺利',
  warning: '需要关注',
  danger: '存在风险',
  info: '进行中',
  neutral: '正常',
};

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：阶段节点 Tooltip 浮层
// ─────────────────────────────────────────────────────────────────────────────

interface StageTooltipProps {
  stage: BusinessStage;
  /** 浮层位置调整：'left' | 'center' | 'right' */
  position: 'left' | 'center' | 'right';
  visible: boolean;
}

function StageTooltip({ stage, position, visible }: StageTooltipProps) {
  const ctx = CONTEXT_CONFIG[stage.contextType];

  const positionClass =
    position === 'left'
      ? 'left-0 -translate-x-0'
      : position === 'right'
      ? 'right-0 translate-x-0'
      : 'left-1/2 -translate-x-1/2';

  return (
    <div
      className={`
        absolute bottom-full mb-3 z-50 w-64
        ${positionClass}
        transition-all duration-200
        ${visible ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 translate-y-1 pointer-events-none'}
      `}
      role="tooltip"
      aria-hidden={!visible}
    >
      {/* 浮层主体 */}
      <div className={`
        rounded-xl border bg-slate-900/95 backdrop-blur-sm shadow-2xl
        ${ctx.border}
        p-4
      `}>
        {/* 标题行 */}
        <div className="flex items-center justify-between mb-3">
          <div>
            <span className="text-sm font-semibold text-white">{stage.name}</span>
            <span className="text-xs text-slate-400 ml-1.5">({stage.nameEn})</span>
          </div>
          <span className={`
            text-xs font-medium px-2 py-0.5 rounded-full
            ${ctx.badge} ${ctx.badgeBg}
          `}>
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${ctx.dot} mr-1 align-middle`} />
            {CONTEXT_LABEL[stage.contextType]}
          </span>
        </div>

        {/* 阶段副标题 */}
        <p className="text-xs text-slate-400 mb-3">{stage.subtitle}</p>

        {/* 核心目标 */}
        <div className="mb-3">
          <div className="text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <svg className="w-3 h-3 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            核心目标
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">{stage.coreObjective}</p>
        </div>

        {/* 当前完成情况 */}
        <div className={`rounded-lg p-2.5 ${ctx.badgeBg} border ${ctx.border}`}>
          <div className="text-xs font-semibold text-slate-300 mb-1">当前完成情况</div>
          <p className={`text-xs leading-relaxed ${ctx.text}`}>{stage.currentProgress}</p>
        </div>

        {/* 关键指标（可选） */}
        {stage.metrics && stage.metrics.length > 0 && (
          <div className="mt-3 space-y-1.5">
            <div className="text-xs font-semibold text-slate-400">关键指标</div>
            {stage.metrics.map((m, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <span className="text-slate-400">{m.label}</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-white font-medium">{m.value}</span>
                  <span className="text-slate-500">/ {m.target}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 箭头指示器 */}
      <div className={`
        absolute top-full
        ${position === 'left' ? 'left-6' : position === 'right' ? 'right-6' : 'left-1/2 -translate-x-1/2'}
        w-0 h-0
        border-l-[6px] border-l-transparent
        border-r-[6px] border-r-transparent
        border-t-[6px] border-t-slate-700
      `} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：单个阶段节点
// ─────────────────────────────────────────────────────────────────────────────

interface StageNodeProps {
  stage: BusinessStage;
  index: number;
  total: number;
  onDrillDown?: (stageId: BusinessStageId) => void;
}

function StageNode({ stage, index, total, onDrillDown }: StageNodeProps) {
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const nodeRef = useRef<HTMLDivElement>(null);

  // 决定 Tooltip 的水平对齐方向（避免溢出）
  const tooltipPosition: 'left' | 'center' | 'right' =
    index === 0 ? 'left' : index === total - 1 ? 'right' : 'center';

  const isCompleted = stage.status === 'completed';
  const isCurrent = stage.status === 'current';
  const isUpcoming = stage.status === 'upcoming';

  const handleClick = () => {
    if (onDrillDown) {
      onDrillDown(stage.id);
    }
  };

  return (
    <div
      ref={nodeRef}
      className="relative flex flex-col items-center"
      style={{ flex: '1 1 0' }}
      onMouseEnter={() => setTooltipVisible(true)}
      onMouseLeave={() => setTooltipVisible(false)}
      onFocus={() => setTooltipVisible(true)}
      onBlur={() => setTooltipVisible(false)}
    >
      {/* Tooltip 浮层 */}
      <StageTooltip
        stage={stage}
        position={tooltipPosition}
        visible={tooltipVisible}
      />

      {/* 节点圆圈 */}
      <button
        type="button"
        onClick={handleClick}
        className={`
          relative z-10 flex items-center justify-center rounded-full
          transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900
          ${isCompleted
            ? 'w-9 h-9 bg-indigo-600 border-2 border-indigo-500 hover:bg-indigo-500 hover:scale-110 cursor-pointer shadow-lg shadow-indigo-500/20'
            : isCurrent
            ? 'w-11 h-11 bg-indigo-600 border-4 border-indigo-400 hover:bg-indigo-500 cursor-pointer shadow-xl shadow-indigo-500/40 ring-4 ring-indigo-500/20'
            : 'w-9 h-9 bg-slate-700 border-2 border-slate-600 hover:border-slate-500 cursor-pointer hover:scale-105'
          }
        `}
        aria-label={`${stage.name} - ${stage.status === 'completed' ? '已完成' : stage.status === 'current' ? '进行中' : '未开始'}`}
        aria-describedby={`stage-tooltip-${stage.id}`}
      >
        {isCompleted ? (
          /* 对勾图标 */
          <svg
            className="w-4 h-4 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={3}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        ) : isCurrent ? (
          /* 当前阶段：脉冲动画点 */
          <span className="relative flex items-center justify-center">
            <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-indigo-300 opacity-60" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-white" />
          </span>
        ) : (
          /* 未开始阶段：序号 */
          <span className="text-xs font-semibold text-slate-400">{index + 1}</span>
        )}
      </button>

      {/* 阶段名称标签 */}
      <div className="mt-3 text-center">
        <div className={`
          text-xs font-semibold leading-tight
          ${isCompleted ? 'text-indigo-400' : isCurrent ? 'text-white' : 'text-slate-500'}
        `}>
          {stage.name}
        </div>
        <div className={`
          text-xs mt-0.5 leading-tight
          ${isCompleted ? 'text-slate-500' : isCurrent ? 'text-slate-400' : 'text-slate-600'}
        `}>
          {stage.nameEn}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 主组件：StageProgressBar
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 业务阶段进度组件 (Stage Progress Bar)
 *
 * 首屏 Hero 组件，通过横向步骤条展示项目当前所处的业务阶段。
 * 与 analysis_framework.md 的业务阶段矩阵（种子期/启动期/成长期/扩张期/成熟期）深度联动。
 *
 * @example
 * <StageProgressBar
 *   data={data.stageProgress}
 *   onDrillDown={(stageId) => scrollToSection(`stage-detail-${stageId}`)}
 * />
 */
export function StageProgressBar({ data, onDrillDown, className = '' }: StageProgressBarProps) {
  const { stages, overallProgress, currentStageId } = data;
  const currentStage = stages.find(s => s.id === currentStageId);
  const currentIndex = stages.findIndex(s => s.id === currentStageId);

  return (
    <div className={`
      relative rounded-2xl border border-slate-700/50
      bg-gradient-to-br from-slate-800/80 to-slate-900/80
      backdrop-blur-sm shadow-xl
      p-6 sm:p-8
      ${className}
    `}>
      {/* 顶部标题行 */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {/* 阶段图标 */}
            <div className="w-5 h-5 rounded-md bg-indigo-500/20 flex items-center justify-center">
              <svg className="w-3 h-3 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">业务阶段进度</h3>
          </div>
          {currentStage && (
            <p className="text-xs text-slate-500">
              当前处于 <span className="text-indigo-400 font-medium">{currentStage.name}</span>
              <span className="mx-1">·</span>
              <span>{currentStage.subtitle}</span>
            </p>
          )}
        </div>

        {/* 整体进度百分比 */}
        <div className="text-right">
          <div className="text-2xl font-bold text-white tabular-nums">
            {overallProgress}
            <span className="text-base font-normal text-slate-400">%</span>
          </div>
          <div className="text-xs text-slate-500 mt-0.5">整体进度</div>
        </div>
      </div>

      {/* 步骤条主体 */}
      <div className="relative">
        {/* 连接线层（绝对定位，在节点层之下） */}
        <div
          className="absolute top-[18px] left-0 right-0 flex items-center"
          aria-hidden="true"
          style={{ zIndex: 0 }}
        >
          {stages.map((stage, idx) => {
            if (idx === stages.length - 1) return null;
            const nextStage = stages[idx + 1];
            const isLineCompleted = stage.status === 'completed' && nextStage.status !== 'upcoming';
            const isLineHalf = stage.status === 'completed' && nextStage.status === 'current';
            const isLineCurrent = stage.status === 'current';

            return (
              <div
                key={`line-${idx}`}
                className="flex-1 h-0.5 mx-1 overflow-hidden rounded-full"
                style={{ background: isLineCompleted ? '#6366f1' : '#334155' }}
              >
                {isLineCurrent && (
                  <div className="h-full w-1/2 bg-gradient-to-r from-indigo-500 to-slate-700 rounded-full" />
                )}
              </div>
            );
          })}
        </div>

        {/* 节点层 */}
        <div className="relative flex items-start" style={{ zIndex: 1 }}>
          {stages.map((stage, idx) => (
            <StageNode
              key={stage.id}
              stage={stage}
              index={idx}
              total={stages.length}
              onDrillDown={onDrillDown}
            />
          ))}
        </div>
      </div>

      {/* 底部进度条 */}
      <div className="mt-8">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
          <span>种子期</span>
          <span>成熟期</span>
        </div>
        <div className="relative h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-600 to-indigo-400 rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${overallProgress}%` }}
          />
          {/* 当前阶段指示器 */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-indigo-500 shadow-md shadow-indigo-500/50 transition-all duration-1000"
            style={{ left: `calc(${overallProgress}% - 6px)` }}
          />
        </div>
      </div>

      {/* 下钻提示文字 */}
      <p className="mt-4 text-center text-xs text-slate-600">
        点击阶段节点可查看详细规划 · 悬停可预览阶段概要
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Mock 数据示例（供开发调试使用）
// ─────────────────────────────────────────────────────────────────────────────

export const mockStageProgressData: StageProgressData = {
  currentStageId: 'growth',
  overallProgress: 52,
  stages: [
    {
      id: 'seed',
      name: '种子期',
      nameEn: 'Seed',
      status: 'completed',
      subtitle: 'PMF 探索阶段',
      coreObjective: '验证核心需求，完成 PMF 验证，获取首批种子用户（目标 1,000 人）。',
      currentProgress: '已完成 PMF 验证，种子用户 1,200 人，NPS 评分 62，核心功能留存曲线趋于平稳。',
      contextType: 'success',
      metrics: [
        { label: '种子用户数', value: '1,200', target: '1,000' },
        { label: 'NPS 评分', value: '62', target: '≥ 50' },
      ],
    },
    {
      id: 'launch',
      name: '启动期',
      nameEn: 'Launch',
      status: 'completed',
      subtitle: '冷启动 / MVP 上线',
      coreObjective: '完成 MVP 上线，跑通核心路径，用户规模达到 1 万~10 万。',
      currentProgress: '已完成 MVP 上线，注册用户 4.8 万，核心路径转化率 32%，D1 留存 41%。',
      contextType: 'success',
      metrics: [
        { label: '注册用户', value: '4.8万', target: '1万' },
        { label: 'D1 留存率', value: '41%', target: '≥ 35%' },
      ],
    },
    {
      id: 'growth',
      name: '成长期',
      nameEn: 'Growth',
      status: 'current',
      subtitle: '规模化增长',
      coreObjective: '用户规模突破 10 万，建立增长引擎，D7 留存率稳定在 20% 以上，验证渠道效率矩阵。',
      currentProgress: 'DAU 1.25 万，D7 留存率 18.2%（低于目标 20%），增长引擎搭建中，推荐算法 v1 已上线。',
      contextType: 'warning',
      metrics: [
        { label: 'DAU', value: '12,500', target: '15,000' },
        { label: 'D7 留存率', value: '18.2%', target: '≥ 20%' },
        { label: '付费渗透率', value: '3.8%', target: '5%' },
      ],
    },
    {
      id: 'scale',
      name: '扩张期',
      nameEn: 'Scale',
      status: 'upcoming',
      subtitle: '商业化提速',
      coreObjective: '用户规模稳定后，重点转向变现效率和多元化，验证单元经济模型（LTV/CAC > 3）。',
      currentProgress: '尚未进入该阶段，待成长期核心指标达标后启动。',
      contextType: 'neutral',
    },
    {
      id: 'mature',
      name: '成熟期',
      nameEn: 'Mature',
      status: 'upcoming',
      subtitle: '防守与优化',
      coreObjective: '增长放缓后，重点转向留存、效率和新增长曲线，精细化用户分层运营。',
      currentProgress: '尚未进入该阶段。',
      contextType: 'neutral',
    },
  ],
};

// ─────────────────────────────────────────────────────────────────────────────
// 独立演示组件（用于在 weekly_report_example.tsx 中集成）
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 演示用包装组件，展示 StageProgressBar 的完整功能
 */
export function StageProgressBarDemo() {
  const [drillDownTarget, setDrillDownTarget] = useState<BusinessStageId | null>(null);

  const handleDrillDown = (stageId: BusinessStageId) => {
    setDrillDownTarget(stageId);
    // 实际使用时，此处应调用父组件的导航逻辑，如：
    // scrollToSection(`stage-detail-${stageId}`)
    console.log('[StageProgressBar] 下钻至阶段:', stageId);
  };

  return (
    <div className="space-y-4">
      <StageProgressBar
        data={mockStageProgressData}
        onDrillDown={handleDrillDown}
      />
      {drillDownTarget && (
        <div className="text-xs text-center text-slate-500 animate-fade-in">
          已触发下钻：阶段 ID = <code className="text-indigo-400 bg-slate-800 px-1.5 py-0.5 rounded">{drillDownTarget}</code>
          <button
            type="button"
            className="ml-2 text-slate-600 hover:text-slate-400 underline"
            onClick={() => setDrillDownTarget(null)}
          >
            清除
          </button>
        </div>
      )}
    </div>
  );
}

export default StageProgressBar;

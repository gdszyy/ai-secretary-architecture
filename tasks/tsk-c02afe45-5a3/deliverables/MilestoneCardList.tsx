import React, { useState } from 'react';

// =============================================================================
// 组件数据绑定说明
// 组件 Key: milestone_card_list
// 适用模块: 里程碑进度 (Milestone Progress)
// 组件类型: 详情组件 (Detail Component)
//
// 使用示例:
//   <MilestoneCardList
//     milestones={data.milestones}
//     title="里程碑详情"
//   />
//
// 数据接口 (MilestoneCardData[]):
//   id: string              — 里程碑唯一标识
//   title: string           — 里程碑名称
//   status: MilestoneCardStatus — 状态 ('done' | 'active' | 'delayed' | 'upcoming')
//   plannedDate: string     — 计划完成时间 (YYYY-MM-DD)
//   actualDate?: string     — 实际/预计完成时间 (YYYY-MM-DD)
//   delayDays?: number      — 延期天数（仅 delayed 状态时有效）
//   ownerName: string       — 负责人姓名
//   ownerAvatar?: string    — 负责人头像 URL（可选）
//   description: string     — 简短描述或关键交付物
//   progress: number        — 进度百分比 (0-100)
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// Section 1: TypeScript 接口定义
// ─────────────────────────────────────────────────────────────────────────────

/** 里程碑卡片状态枚举 */
export type MilestoneCardStatus = 'done' | 'active' | 'delayed' | 'upcoming';

/** 状态筛选选项 */
type FilterOption = 'all' | MilestoneCardStatus;

/** 里程碑卡片数据接口 */
export interface MilestoneCardData {
  /** 里程碑唯一标识 */
  id: string;
  /** 里程碑名称 */
  title: string;
  /** 当前状态 */
  status: MilestoneCardStatus;
  /** 计划完成时间 (YYYY-MM-DD) */
  plannedDate: string;
  /** 实际完成时间或预计完成时间 (YYYY-MM-DD) */
  actualDate?: string;
  /** 延期天数（仅在 status 为 'delayed' 时有效） */
  delayDays?: number;
  /** 负责人姓名 */
  ownerName: string;
  /** 负责人头像 URL（可选） */
  ownerAvatar?: string;
  /** 简短描述或关键交付物 */
  description: string;
  /** 当前进度百分比 (0-100) */
  progress: number;
}

/** 组件 Props 接口 */
export interface MilestoneCardListProps {
  /** 里程碑数据列表 */
  milestones: MilestoneCardData[];
  /** 组件标题，默认为 "里程碑详情" */
  title?: string;
  /** 自定义外层容器类名 */
  className?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 2: 常量与配置
// ─────────────────────────────────────────────────────────────────────────────

/** 状态配置映射（颜色、标签、进度条颜色） */
const STATUS_CONFIG: Record<MilestoneCardStatus, {
  label: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
  dotColor: string;
  progressColor: string;
  cardBg: string;
}> = {
  done: {
    label: '已完成',
    textColor: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
    borderColor: 'border-emerald-200 dark:border-emerald-700/50',
    dotColor: 'bg-emerald-500',
    progressColor: 'bg-emerald-500',
    cardBg: 'bg-white dark:bg-slate-800/60',
  },
  active: {
    label: '进行中',
    textColor: 'text-sky-600 dark:text-sky-400',
    bgColor: 'bg-sky-50 dark:bg-sky-900/20',
    borderColor: 'border-sky-200 dark:border-sky-700/50',
    dotColor: 'bg-sky-500',
    progressColor: 'bg-sky-500',
    cardBg: 'bg-white dark:bg-slate-800/60',
  },
  delayed: {
    label: '延期',
    textColor: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    borderColor: 'border-red-200 dark:border-red-700/50',
    dotColor: 'bg-red-500',
    progressColor: 'bg-red-500',
    // 延期卡片背景使用淡红色，视觉上优先吸引注意
    cardBg: 'bg-red-50 dark:bg-red-900/10',
  },
  upcoming: {
    label: '待启动',
    textColor: 'text-slate-500 dark:text-slate-400',
    bgColor: 'bg-slate-100 dark:bg-slate-700/30',
    borderColor: 'border-slate-200 dark:border-slate-600/50',
    dotColor: 'bg-slate-400',
    progressColor: 'bg-slate-400',
    cardBg: 'bg-white dark:bg-slate-800/60',
  },
};

/** 筛选 Tab 配置 */
const FILTER_TABS: { key: FilterOption; label: string; count?: number }[] = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '进行中' },
  { key: 'done', label: '已完成' },
  { key: 'delayed', label: '延期' },
  { key: 'upcoming', label: '待启动' },
];

/** 状态排序优先级（延期最优先，已完成最后） */
const STATUS_SORT_ORDER: Record<MilestoneCardStatus, number> = {
  delayed: 0,
  active: 1,
  upcoming: 2,
  done: 3,
};

// ─────────────────────────────────────────────────────────────────────────────
// Section 3: 工具函数
// ─────────────────────────────────────────────────────────────────────────────

/** 格式化日期显示（YYYY-MM-DD → MM/DD） */
function formatDate(dateStr: string): string {
  if (!dateStr) return '-';
  const parts = dateStr.split('-');
  if (parts.length < 3) return dateStr;
  return `${parts[1]}/${parts[2]}`;
}

/** 获取负责人头像首字母（当无头像 URL 时使用） */
function getInitials(name: string): string {
  if (!name) return '?';
  // 中文姓名取最后一个字，英文取首字母
  const trimmed = name.trim();
  if (/[\u4e00-\u9fa5]/.test(trimmed)) {
    return trimmed.charAt(trimmed.length - 1);
  }
  return trimmed.charAt(0).toUpperCase();
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 4: 子组件
// ─────────────────────────────────────────────────────────────────────────────

// ── 4.1 状态标签 ─────────────────────────────────────────────────────────────

interface StatusBadgeProps {
  status: MilestoneCardStatus;
}

function StatusBadge({ status }: StatusBadgeProps) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full
        text-xs font-semibold px-2.5 py-0.5
        ${cfg.bgColor} ${cfg.textColor}
      `}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dotColor}`} />
      {cfg.label}
    </span>
  );
}

// ── 4.2 负责人头像 ───────────────────────────────────────────────────────────

interface OwnerAvatarProps {
  name: string;
  avatarUrl?: string;
  size?: 'sm' | 'md';
}

function OwnerAvatar({ name, avatarUrl, size = 'sm' }: OwnerAvatarProps) {
  const sizeClass = size === 'sm' ? 'w-6 h-6 text-xs' : 'w-8 h-8 text-sm';
  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={name}
        className={`${sizeClass} rounded-full object-cover ring-1 ring-slate-200 dark:ring-slate-600`}
      />
    );
  }
  return (
    <div
      className={`
        ${sizeClass} rounded-full
        bg-indigo-100 dark:bg-indigo-900/40
        text-indigo-600 dark:text-indigo-400
        font-semibold flex items-center justify-center
        ring-1 ring-indigo-200 dark:ring-indigo-700/50
        shrink-0
      `}
    >
      {getInitials(name)}
    </div>
  );
}

// ── 4.3 进度条 ───────────────────────────────────────────────────────────────

interface MilestoneProgressBarProps {
  value: number;
  status: MilestoneCardStatus;
}

function MilestoneProgressBar({ value, status }: MilestoneProgressBarProps) {
  const cfg = STATUS_CONFIG[status];
  const clampedValue = Math.min(100, Math.max(0, value));
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${cfg.progressColor}`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
      <span className="text-xs font-medium text-slate-500 dark:text-slate-400 tabular-nums w-8 text-right shrink-0">
        {clampedValue}%
      </span>
    </div>
  );
}

// ── 4.4 单个里程碑卡片 ───────────────────────────────────────────────────────

interface MilestoneCardItemProps {
  milestone: MilestoneCardData;
}

function MilestoneCardItem({ milestone }: MilestoneCardItemProps) {
  const [expanded, setExpanded] = useState(false);
  const cfg = STATUS_CONFIG[milestone.status];
  const isDelayed = milestone.status === 'delayed';

  return (
    <div
      className={`
        rounded-xl border p-4
        transition-shadow duration-200 hover:shadow-md
        ${cfg.cardBg}
        ${isDelayed
          ? 'border-red-200 dark:border-red-700/50'
          : 'border-slate-200 dark:border-slate-700'
        }
      `}
    >
      {/* 头部：名称 + 状态标签 */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-snug flex-1 min-w-0">
          {milestone.title}
        </h3>
        <StatusBadge status={milestone.status} />
      </div>

      {/* 信息区：时间对比 + 负责人 */}
      <div className="flex items-center justify-between gap-4 mb-3">
        {/* 时间对比 */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1">
            <span className="text-xs text-slate-400 dark:text-slate-500">计划</span>
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300 tabular-nums">
              {formatDate(milestone.plannedDate)}
            </span>
          </div>
          {milestone.actualDate && (
            <>
              <span className="text-xs text-slate-300 dark:text-slate-600">→</span>
              <div className="flex items-center gap-1">
                <span className="text-xs text-slate-400 dark:text-slate-500">
                  {milestone.status === 'done' ? '完成' : '预计'}
                </span>
                <span
                  className={`text-xs font-medium tabular-nums ${
                    isDelayed
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-slate-600 dark:text-slate-300'
                  }`}
                >
                  {formatDate(milestone.actualDate)}
                </span>
              </div>
            </>
          )}
          {/* 延期天数标签 */}
          {isDelayed && milestone.delayDays !== undefined && milestone.delayDays > 0 && (
            <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 px-2 py-0.5 rounded-full">
              延期 {milestone.delayDays} 天
            </span>
          )}
        </div>

        {/* 负责人 */}
        <div className="flex items-center gap-1.5 shrink-0">
          <OwnerAvatar name={milestone.ownerName} avatarUrl={milestone.ownerAvatar} />
          <span className="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
            {milestone.ownerName}
          </span>
        </div>
      </div>

      {/* 描述/关键交付物（可折叠） */}
      <div className="mb-3">
        <p
          className={`
            text-xs text-slate-600 dark:text-slate-400 leading-relaxed
            ${!expanded ? 'line-clamp-2' : ''}
          `}
        >
          {milestone.description}
        </p>
        {milestone.description.length > 80 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-1 text-xs text-indigo-500 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors"
          >
            {expanded ? '收起 ↑' : '展开 ↓'}
          </button>
        )}
      </div>

      {/* 进度条 */}
      <MilestoneProgressBar value={milestone.progress} status={milestone.status} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 5: 主组件
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 里程碑卡片列表组件 (Milestone Card List)
 *
 * 竖直滚动面板，每一行是一个里程碑卡片，支持按状态筛选。
 * 延期里程碑卡片背景使用淡红色，视觉上优先吸引注意。
 *
 * @example
 * <MilestoneCardList
 *   milestones={data.milestones}
 *   title="里程碑详情"
 * />
 */
export function MilestoneCardList({
  milestones,
  title = '里程碑详情',
  className = '',
}: MilestoneCardListProps) {
  const [filterStatus, setFilterStatus] = useState<FilterOption>('all');

  // 统计各状态数量（用于 Tab 徽章）
  const countByStatus = milestones.reduce<Record<MilestoneCardStatus, number>>(
    (acc, m) => {
      acc[m.status] = (acc[m.status] ?? 0) + 1;
      return acc;
    },
    { done: 0, active: 0, delayed: 0, upcoming: 0 }
  );

  // 筛选
  const filtered = filterStatus === 'all'
    ? milestones
    : milestones.filter((m) => m.status === filterStatus);

  // 排序：按状态优先级（延期 > 进行中 > 待启动 > 已完成），同状态按计划时间升序
  const sorted = [...filtered].sort((a, b) => {
    const statusDiff = STATUS_SORT_ORDER[a.status] - STATUS_SORT_ORDER[b.status];
    if (statusDiff !== 0) return statusDiff;
    return a.plannedDate.localeCompare(b.plannedDate);
  });

  return (
    <div
      className={`
        rounded-2xl border border-slate-200 dark:border-slate-700
        bg-white dark:bg-slate-800/60
        flex flex-col
        ${className}
      `}
    >
      {/* 面板头部 */}
      <div className="px-5 pt-5 pb-3 border-b border-slate-100 dark:border-slate-700/50">
        {/* 标题行 */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-1 h-5 rounded-full bg-indigo-500" />
            <h2 className="text-sm font-bold text-slate-700 dark:text-slate-200">
              {title}
            </h2>
          </div>
          <span className="text-xs text-slate-400 dark:text-slate-500">
            共 {milestones.length} 个里程碑
          </span>
        </div>

        {/* 状态筛选 Tab */}
        <div className="flex items-center gap-1 flex-wrap">
          {FILTER_TABS.map((tab) => {
            const count = tab.key === 'all'
              ? milestones.length
              : countByStatus[tab.key as MilestoneCardStatus] ?? 0;
            const isActive = filterStatus === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setFilterStatus(tab.key)}
                className={`
                  inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium
                  transition-all duration-150
                  ${isActive
                    ? 'bg-indigo-500 text-white shadow-sm'
                    : 'bg-slate-100 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                  }
                `}
              >
                {tab.label}
                {count > 0 && (
                  <span
                    className={`
                      text-xs rounded-full px-1.5 py-0 leading-5 font-semibold
                      ${isActive
                        ? 'bg-white/20 text-white'
                        : tab.key === 'delayed' && count > 0
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-500 dark:text-red-400'
                          : 'bg-slate-200 dark:bg-slate-600 text-slate-500 dark:text-slate-400'
                      }
                    `}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 卡片列表（固定高度，超出滚动） */}
      <div className="flex-1 overflow-y-auto max-h-96 px-4 py-3 space-y-3 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-700">
        {sorted.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <p className="text-sm text-slate-400 dark:text-slate-500">
              暂无{filterStatus === 'all' ? '' : `「${FILTER_TABS.find(t => t.key === filterStatus)?.label}」`}里程碑
            </p>
          </div>
        ) : (
          sorted.map((milestone) => (
            <MilestoneCardItem key={milestone.id} milestone={milestone} />
          ))
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Section 6: Mock 数据（开发预览用）
// ─────────────────────────────────────────────────────────────────────────────

export const mockMilestones: MilestoneCardData[] = [
  {
    id: 'ms-001',
    title: '核心功能上线',
    status: 'done',
    plannedDate: '2026-02-28',
    actualDate: '2026-02-28',
    ownerName: '张三',
    description: '完成用户注册/登录流程、核心业务功能开发及基础数据埋点，通过内测后正式上线。',
    progress: 100,
  },
  {
    id: 'ms-002',
    title: '增长引擎搭建',
    status: 'active',
    plannedDate: '2026-04-30',
    actualDate: '2026-04-30',
    ownerName: '李四',
    description: '搭建用户增长体系，完成新手引导优化和推荐算法 v1 上线，目标将 D7 留存提升至 20%+。',
    progress: 65,
  },
  {
    id: 'ms-003',
    title: 'D7 留存专项优化',
    status: 'delayed',
    plannedDate: '2026-04-15',
    actualDate: '2026-05-10',
    delayDays: 25,
    ownerName: '王五',
    description: '针对 D7 留存下滑问题启动专项排查，定位根因后实施优化方案，包括核心路径体验改造和个性化内容推荐能力升级。',
    progress: 40,
  },
  {
    id: 'ms-004',
    title: '商业化突破',
    status: 'upcoming',
    plannedDate: '2026-06-30',
    ownerName: '赵六',
    description: '实现商业化规模化，月 GMV 突破目标值，ARPU 提升 30%，付费渗透率达到 5%。',
    progress: 0,
  },
  {
    id: 'ms-005',
    title: '国际化扩张 - 东南亚市场',
    status: 'delayed',
    plannedDate: '2026-03-31',
    actualDate: '2026-05-15',
    delayDays: 45,
    ownerName: '钱七',
    description: '完成东南亚三个核心市场（泰国、越南、印尼）的本地化适配，包括多语言支持、本地支付接入和合规审查。',
    progress: 30,
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Section 7: 默认导出（预览页面）
// ─────────────────────────────────────────────────────────────────────────────

export default function MilestoneCardListPreview() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-lg font-bold text-slate-700 dark:text-slate-200 mb-6">
          里程碑卡片组件预览
        </h1>
        <MilestoneCardList
          milestones={mockMilestones}
          title="里程碑详情"
        />
      </div>
    </div>
  );
}

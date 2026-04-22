import React, { useState } from 'react';

// =============================================================================
// 组件数据绑定说明
// 组件 Key: milestone_card_list
// 适用模块: 里程碑进度 (Milestone Progress)
// 组件类型: 详情组件 (Detail Component)
// 样式版本: iOS 26 Liquid Glass v1.0（2026-04-22）
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
//
// iOS 26 Liquid Glass 设计规范说明:
//   - 外层容器: backdrop-blur-xl + bg-white/65 dark:bg-white/7 + inset 高光/暗线 shadow + 外阴影
//   - 每行卡片: Level 2 玻璃层，rounded-xl，bg-white/50 dark:bg-white/5
//   - 状态色: oklch 语义色（通过 Tailwind 任意值）
//   - 字体: 中文 Noto Sans SC，数字/英文 DM Sans（font-sans + CSS 变量）
//   - 延期项: oklch(0.65 0.22 25) 暖红高亮
//   - 深色模式: 所有颜色补充 dark: 变体
//   - 圆角层级: 外层 rounded-2xl → 内层 rounded-xl → 最内层 rounded-lg
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
// Section 2: 常量与配置（iOS 26 Liquid Glass oklch 语义色）
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 状态配置映射
 * 颜色全部改用 oklch 语义色（通过 Tailwind 任意值 [oklch(...)]）
 * 深色模式使用 dark: 变体
 *
 * oklch 语义色参考:
 *   成功绿: oklch(0.72 0.17 155)  dark: oklch(0.78 0.15 155)
 *   进行蓝: oklch(0.68 0.19 240)  dark: oklch(0.75 0.17 240)
 *   延期红: oklch(0.65 0.22 25)   dark: oklch(0.72 0.20 25)
 *   待启动灰: oklch(0.60 0.00 0)  dark: oklch(0.65 0.00 0)
 */
const STATUS_CONFIG: Record<MilestoneCardStatus, {
  label: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
  dotColor: string;
  progressColor: string;
  cardBg: string;
  cardBorder: string;
  cardShadow: string;
}> = {
  done: {
    label: '已完成',
    // oklch 成功绿 语义色
    textColor: 'text-[oklch(0.55_0.17_155)] dark:text-[oklch(0.78_0.15_155)]',
    bgColor: 'bg-[oklch(0.96_0.04_155)] dark:bg-[oklch(0.25_0.05_155/0.25)]',
    borderColor: 'border-[oklch(0.85_0.08_155)] dark:border-[oklch(0.45_0.10_155/0.40)]',
    dotColor: 'bg-[oklch(0.65_0.17_155)]',
    progressColor: 'bg-[oklch(0.65_0.17_155)] dark:bg-[oklch(0.72_0.15_155)]',
    // Level 2 玻璃层卡片背景
    cardBg: 'bg-white/50 dark:bg-white/5 backdrop-blur-sm',
    cardBorder: 'border-[oklch(0.85_0.08_155/0.35)] dark:border-[oklch(0.45_0.10_155/0.25)]',
    cardShadow: 'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.45)] shadow-[0_2px_12px_-2px_oklch(0.65_0.17_155/0.10)]',
  },
  active: {
    label: '进行中',
    // oklch 进行蓝 语义色
    textColor: 'text-[oklch(0.50_0.19_240)] dark:text-[oklch(0.75_0.17_240)]',
    bgColor: 'bg-[oklch(0.95_0.05_240)] dark:bg-[oklch(0.22_0.06_240/0.25)]',
    borderColor: 'border-[oklch(0.82_0.10_240)] dark:border-[oklch(0.45_0.12_240/0.40)]',
    dotColor: 'bg-[oklch(0.60_0.19_240)]',
    progressColor: 'bg-[oklch(0.60_0.19_240)] dark:bg-[oklch(0.68_0.17_240)]',
    // Level 2 玻璃层卡片背景
    cardBg: 'bg-white/50 dark:bg-white/5 backdrop-blur-sm',
    cardBorder: 'border-[oklch(0.82_0.10_240/0.35)] dark:border-[oklch(0.45_0.12_240/0.25)]',
    cardShadow: 'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.45)] shadow-[0_2px_12px_-2px_oklch(0.60_0.19_240/0.12)]',
  },
  delayed: {
    label: '延期',
    // oklch 延期暖红 语义色（高亮）
    textColor: 'text-[oklch(0.50_0.22_25)] dark:text-[oklch(0.72_0.20_25)]',
    bgColor: 'bg-[oklch(0.96_0.06_25)] dark:bg-[oklch(0.22_0.07_25/0.30)]',
    borderColor: 'border-[oklch(0.82_0.12_25)] dark:border-[oklch(0.50_0.15_25/0.45)]',
    dotColor: 'bg-[oklch(0.60_0.22_25)]',
    progressColor: 'bg-[oklch(0.60_0.22_25)] dark:bg-[oklch(0.65_0.20_25)]',
    // 延期卡片：使用淡暖红玻璃层，视觉上优先吸引注意
    cardBg: 'bg-[oklch(0.97_0.04_25/0.60)] dark:bg-[oklch(0.22_0.07_25/0.20)] backdrop-blur-sm',
    cardBorder: 'border-[oklch(0.82_0.12_25/0.50)] dark:border-[oklch(0.50_0.15_25/0.40)]',
    cardShadow: 'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.45)] shadow-[0_2px_16px_-2px_oklch(0.60_0.22_25/0.18)]',
  },
  upcoming: {
    label: '待启动',
    // oklch 中性灰 语义色
    textColor: 'text-[oklch(0.52_0.00_0)] dark:text-[oklch(0.65_0.00_0)]',
    bgColor: 'bg-[oklch(0.94_0.00_0)] dark:bg-[oklch(0.25_0.00_0/0.20)]',
    borderColor: 'border-[oklch(0.85_0.00_0)] dark:border-[oklch(0.45_0.00_0/0.35)]',
    dotColor: 'bg-[oklch(0.65_0.00_0)]',
    progressColor: 'bg-[oklch(0.65_0.00_0)] dark:bg-[oklch(0.60_0.00_0)]',
    // Level 2 玻璃层卡片背景
    cardBg: 'bg-white/40 dark:bg-white/4 backdrop-blur-sm',
    cardBorder: 'border-[oklch(0.85_0.00_0/0.30)] dark:border-[oklch(0.45_0.00_0/0.20)]',
    cardShadow: 'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.40)] shadow-[0_2px_8px_-2px_oklch(0_0_0/0.06)]',
  },
};

/** 筛选 Tab 配置 */
const FILTER_TABS: { key: FilterOption; label: string }[] = [
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
        inline-flex items-center gap-1.5
        rounded-lg
        text-xs font-semibold px-2.5 py-0.5
        border
        ${cfg.bgColor} ${cfg.textColor} ${cfg.borderColor}
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
        className={`
          ${sizeClass} rounded-full object-cover
          ring-1 ring-[oklch(0.85_0.00_0/0.40)] dark:ring-[oklch(0.45_0.00_0/0.40)]
        `}
      />
    );
  }
  return (
    <div
      className={`
        ${sizeClass} rounded-full
        bg-[oklch(0.93_0.06_270)] dark:bg-[oklch(0.28_0.08_270/0.50)]
        text-[oklch(0.45_0.18_270)] dark:text-[oklch(0.75_0.15_270)]
        font-semibold flex items-center justify-center
        ring-1 ring-[oklch(0.80_0.10_270/0.40)] dark:ring-[oklch(0.50_0.12_270/0.35)]
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
      {/* 进度条轨道：最内层 rounded-lg */}
      <div className="flex-1 h-1.5 bg-[oklch(0.92_0.00_0/0.60)] dark:bg-[oklch(0.30_0.00_0/0.50)] rounded-lg overflow-hidden">
        <div
          className={`h-full rounded-lg transition-all duration-700 ${cfg.progressColor}`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
      {/* 进度数值：DM Sans 数字字体 */}
      <span className="text-xs font-medium text-[oklch(0.52_0.00_0)] dark:text-[oklch(0.65_0.00_0)] tabular-nums w-8 text-right shrink-0 font-sans">
        {clampedValue}%
      </span>
    </div>
  );
}

// ── 4.4 单个里程碑卡片（Level 2 玻璃层） ─────────────────────────────────────

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
        ${cfg.cardBg}
        ${cfg.cardBorder}
        ${cfg.cardShadow}
        hover:-translate-y-1 hover:shadow-xl
        transition-all duration-250
        cursor-default
      `}
    >
      {/* 头部：名称 + 状态标签 */}
      <div className="flex items-start justify-between gap-3 mb-3">
        {/* 里程碑名称：中文 Noto Sans SC，font-sans */}
        <h3 className="text-sm font-bold text-[oklch(0.20_0.00_0)] dark:text-[oklch(0.95_0.00_0)] leading-snug flex-1 min-w-0 font-sans">
          {milestone.title}
        </h3>
        <StatusBadge status={milestone.status} />
      </div>

      {/* 信息区：时间对比 + 负责人 */}
      <div className="flex items-center justify-between gap-4 mb-3">
        {/* 时间对比 */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1">
            <span className="text-xs text-[oklch(0.60_0.00_0)] dark:text-[oklch(0.55_0.00_0)]">计划</span>
            {/* 日期数值：DM Sans 等宽数字 */}
            <span className="text-xs font-medium text-[oklch(0.35_0.00_0)] dark:text-[oklch(0.80_0.00_0)] tabular-nums font-sans">
              {formatDate(milestone.plannedDate)}
            </span>
          </div>
          {milestone.actualDate && (
            <>
              <span className="text-xs text-[oklch(0.75_0.00_0)] dark:text-[oklch(0.40_0.00_0)]">→</span>
              <div className="flex items-center gap-1">
                <span className="text-xs text-[oklch(0.60_0.00_0)] dark:text-[oklch(0.55_0.00_0)]">
                  {milestone.status === 'done' ? '完成' : '预计'}
                </span>
                <span
                  className={`text-xs font-medium tabular-nums font-sans ${
                    isDelayed
                      ? 'text-[oklch(0.50_0.22_25)] dark:text-[oklch(0.72_0.20_25)]'
                      : 'text-[oklch(0.35_0.00_0)] dark:text-[oklch(0.80_0.00_0)]'
                  }`}
                >
                  {formatDate(milestone.actualDate)}
                </span>
              </div>
            </>
          )}
          {/* 延期天数标签：oklch 暖红高亮 */}
          {isDelayed && milestone.delayDays !== undefined && milestone.delayDays > 0 && (
            <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-[oklch(0.50_0.22_25)] dark:text-[oklch(0.72_0.20_25)] bg-[oklch(0.96_0.06_25)] dark:bg-[oklch(0.22_0.07_25/0.30)] border border-[oklch(0.82_0.12_25/0.40)] dark:border-[oklch(0.50_0.15_25/0.35)] px-2 py-0.5 rounded-lg font-sans">
              延期 {milestone.delayDays} 天
            </span>
          )}
        </div>

        {/* 负责人 */}
        <div className="flex items-center gap-1.5 shrink-0">
          <OwnerAvatar name={milestone.ownerName} avatarUrl={milestone.ownerAvatar} />
          <span className="text-xs text-[oklch(0.45_0.00_0)] dark:text-[oklch(0.65_0.00_0)] font-sans">
            {milestone.ownerName}
          </span>
        </div>
      </div>

      {/* 描述/关键交付物（可折叠） */}
      <div className="mb-3">
        <p
          className={`
            text-xs text-[oklch(0.42_0.00_0)] dark:text-[oklch(0.62_0.00_0)] leading-relaxed font-sans
            ${!expanded ? 'line-clamp-2' : ''}
          `}
        >
          {milestone.description}
        </p>
        {milestone.description.length > 80 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-1 text-xs text-[oklch(0.50_0.18_270)] dark:text-[oklch(0.68_0.15_270)] hover:text-[oklch(0.38_0.20_270)] dark:hover:text-[oklch(0.80_0.17_270)] transition-colors font-sans"
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
// Section 5: 主组件（iOS 26 Liquid Glass 外层容器）
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 里程碑卡片列表组件 (Milestone Card List)
 *
 * iOS 26 Liquid Glass 样式升级版本：
 * - 外层容器：毛玻璃效果（backdrop-blur-xl + bg-white/65 dark:bg-white/7）
 * - 顶部高光线：shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55)]
 * - 底部暗线：shadow-[inset_0_-1px_0_0_oklch(0_0_0/0.06)]
 * - 外阴影：shadow-[0_4px_24px_-4px_oklch(0_0_0/0.08)]
 * - 每行卡片：Level 2 玻璃层（rounded-xl + bg-white/50 dark:bg-white/5）
 * - 状态色：oklch 语义色
 * - 字体：中文 Noto Sans SC，数字/英文 DM Sans（font-sans）
 * - 深色模式：所有颜色补充 dark: 变体
 * - 圆角层级：外层 rounded-2xl → 内层 rounded-xl → 最内层 rounded-lg
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
        rounded-2xl border
        border-[oklch(0.88_0.00_0/0.50)] dark:border-[oklch(0.35_0.00_0/0.50)]
        bg-white/65 dark:bg-white/[0.07]
        backdrop-blur-xl
        shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55)]
        shadow-[inset_0_-1px_0_0_oklch(0_0_0/0.06)]
        shadow-[0_4px_24px_-4px_oklch(0_0_0/0.08)]
        flex flex-col
        ${className}
      `}
    >
      {/* 面板头部 */}
      <div className="px-5 pt-5 pb-3 border-b border-[oklch(0.88_0.00_0/0.30)] dark:border-[oklch(0.35_0.00_0/0.30)]">
        {/* 标题行 */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {/* 标题左侧装饰线：oklch 蓝紫色 */}
            <div className="w-1 h-5 rounded-full bg-[oklch(0.58_0.20_270)] dark:bg-[oklch(0.68_0.18_270)]" />
            {/* 标题：中文 Noto Sans SC */}
            <h2 className="text-sm font-bold text-[oklch(0.25_0.00_0)] dark:text-[oklch(0.90_0.00_0)] font-sans">
              {title}
            </h2>
          </div>
          <span className="text-xs text-[oklch(0.58_0.00_0)] dark:text-[oklch(0.52_0.00_0)] font-sans">
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
            const isDelayedTab = tab.key === 'delayed';
            return (
              <button
                key={tab.key}
                onClick={() => setFilterStatus(tab.key)}
                className={`
                  inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium
                  transition-all duration-150 font-sans
                  ${isActive
                    ? isDelayedTab
                      // 延期 Tab 激活：暖红玻璃
                      ? 'bg-[oklch(0.60_0.22_25)] dark:bg-[oklch(0.55_0.20_25)] text-white shadow-sm shadow-[0_2px_8px_-2px_oklch(0.60_0.22_25/0.40)]'
                      // 其他 Tab 激活：蓝紫玻璃
                      : 'bg-[oklch(0.58_0.20_270)] dark:bg-[oklch(0.55_0.18_270)] text-white shadow-sm shadow-[0_2px_8px_-2px_oklch(0.58_0.20_270/0.35)]'
                    : 'bg-[oklch(0.94_0.00_0/0.60)] dark:bg-[oklch(0.28_0.00_0/0.40)] text-[oklch(0.45_0.00_0)] dark:text-[oklch(0.65_0.00_0)] hover:bg-[oklch(0.90_0.00_0/0.80)] dark:hover:bg-[oklch(0.32_0.00_0/0.50)] border border-[oklch(0.85_0.00_0/0.40)] dark:border-[oklch(0.40_0.00_0/0.30)]'
                  }
                `}
              >
                {tab.label}
                {count > 0 && (
                  <span
                    className={`
                      text-xs rounded-lg px-1.5 py-0 leading-5 font-semibold font-sans
                      ${isActive
                        ? 'bg-white/20 text-white'
                        : isDelayedTab && count > 0
                          // 延期计数徽章：暖红色
                          ? 'bg-[oklch(0.96_0.06_25)] dark:bg-[oklch(0.22_0.07_25/0.30)] text-[oklch(0.50_0.22_25)] dark:text-[oklch(0.72_0.20_25)]'
                          : 'bg-[oklch(0.88_0.00_0/0.60)] dark:bg-[oklch(0.35_0.00_0/0.50)] text-[oklch(0.45_0.00_0)] dark:text-[oklch(0.65_0.00_0)]'
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
      <div className="flex-1 overflow-y-auto max-h-96 px-4 py-3 space-y-3 scrollbar-thin scrollbar-thumb-[oklch(0.85_0.00_0/0.40)] dark:scrollbar-thumb-[oklch(0.35_0.00_0/0.50)]">
        {sorted.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <p className="text-sm text-[oklch(0.58_0.00_0)] dark:text-[oklch(0.52_0.00_0)] font-sans">
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

/**
 * 预览页面背景使用渐变色，模拟 iOS 26 Liquid Glass 的毛玻璃叠加效果。
 * 实际使用时，外层背景由父组件提供。
 */
export default function MilestoneCardListPreview() {
  return (
    <div
      className="min-h-screen p-8"
      style={{
        // 模拟 iOS 26 风格渐变背景，用于预览毛玻璃效果
        background: 'linear-gradient(135deg, oklch(0.92 0.06 270) 0%, oklch(0.95 0.04 200) 50%, oklch(0.90 0.08 30) 100%)',
      }}
    >
      <div className="max-w-2xl mx-auto">
        <h1 className="text-lg font-bold text-[oklch(0.20_0.00_0)] dark:text-[oklch(0.90_0.00_0)] mb-6 font-sans">
          里程碑卡片组件预览（iOS 26 Liquid Glass）
        </h1>
        <MilestoneCardList
          milestones={mockMilestones}
          title="里程碑详情"
        />
      </div>
    </div>
  );
}

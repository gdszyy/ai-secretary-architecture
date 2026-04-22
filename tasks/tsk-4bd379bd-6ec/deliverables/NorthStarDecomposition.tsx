// @section:north_star_decomposition - 北极星因子分解图组件
//
// 组件 Key: north_star_decomposition
// 适用模块: 北极星指标归因 (North Star Attribution)
// 优先级: P0 (首屏核心组件)
//
// 三层交互模型:
//   一眼定调: SVG 树状结构图，节点颜色(绿/黄/红)反映健康状态，连线粗细反映权重，警戒节点加警告图标
//   悬浮概要: Hover 节点弹出浮层，显示当前值/目标差距/负责团队/洞察分析
//   下钻详情: Click 节点触发 onDrillDown 回调，传入节点ID，由父组件决定跳转目标
//
// 样式版本: iOS 26 Liquid Glass (v2.0)
//   - 毛玻璃卡片容器: backdrop-blur-xl + bg-white/65 dark:bg-white/7
//   - 顶部高光线: shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55)]
//   - 底部暗线: shadow-[inset_0_-1px_0_0_oklch(0_0_0/0.06)]
//   - 外阴影: shadow-[0_4px_24px_-4px_oklch(0_0_0/0.08)]
//   - 颜色: oklch 语义色
//   - 字体: Noto Sans SC (中文) + DM Sans (数字/英文)
//   - Hover: -translate-y-1 + shadow-xl + transition-all duration-[250ms]
//   - 深色模式: 所有颜色补充 dark: 变体
//   - 圆角: 外层 rounded-2xl，内层 rounded-xl，最内层 rounded-lg
//
// 使用示例:
//   <NorthStarDecomposition
//     data={northStarDecompositionData}
//     onDrillDown={(nodeId, moduleId) => scrollToSection(`module-${moduleId}`)}
//   />
//
// 数据接口 (NorthStarDecompositionData):
//   metric: string                  — 北极星指标名称（如 "DAU"）
//   value: number                   — 当前总值
//   unit?: string                   — 单位（如 "万"）
//   change: number                  — 总环比变化量
//   changeRate: string              — 总环比变化率（如 "+7.3%"）
//   trend: TrendDirection           — 总体趋势
//   target?: number                 — 目标值
//   rootNode: DecompositionNode     — 因子分解树根节点

import React, { useState, useCallback, useRef, useEffect } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// 类型定义 (Type Definitions)
// ─────────────────────────────────────────────────────────────────────────────

/** 趋势方向 */
export type TrendDirection = 'up' | 'down' | 'stable';

/** 节点健康度状态 */
export type NodeStatus = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

/** 因子节点上下文信息（用于 Hover 浮层） */
export interface FactorContext {
  /** 当前值（格式化字符串） */
  currentValue?: string;
  /** 目标值（格式化字符串） */
  targetValue?: string;
  /** 环比变化率（如 "+5.2%"） */
  changeRate?: string;
  /** 负责团队/人 */
  owner?: string;
  /** 风险描述或原因分析 */
  insight?: string;
  /** 解决方案 */
  solution?: string;
  /** 数据洞察 */
  dataInsight?: string;
}

/** 因子分解树节点 */
export interface DecompositionNode {
  /** 节点唯一 ID */
  id: string;
  /** 因子名称（如 "新用户增长"、"转化率"） */
  name: string;
  /** 对父节点的贡献量（正值为正向，负值为负向） */
  contribution: number;
  /** 节点健康度状态（决定节点颜色） */
  status: NodeStatus;
  /** 关联的业务模块 ID（用于下钻跳转） */
  moduleId?: string;
  /** 悬浮上下文信息 */
  context?: FactorContext;
  /** 子节点列表 */
  children?: DecompositionNode[];
}

/** 北极星因子分解图组件数据 */
export interface NorthStarDecompositionData {
  /** 北极星指标名称（如 "DAU"） */
  metric: string;
  /** 当前总值 */
  value: number;
  /** 单位（如 "万"） */
  unit?: string;
  /** 总环比变化量 */
  change: number;
  /** 总环比变化率 */
  changeRate: string;
  /** 总体趋势 */
  trend: TrendDirection;
  /** 目标值 */
  target?: number;
  /** 因子分解树根节点 */
  rootNode: DecompositionNode;
}

/** 组件 Props */
export interface NorthStarDecompositionProps {
  /** 组件数据 */
  data: NorthStarDecompositionData;
  /**
   * 下钻回调函数
   * @param nodeId 被点击的节点 ID
   * @param moduleId 关联的业务模块 ID（如果有）
   */
  onDrillDown?: (nodeId: string, moduleId?: string) => void;
  /** 自定义类名 */
  className?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// 常量与工具函数 (Constants & Utilities)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 节点状态颜色配置 — iOS 26 Liquid Glass oklch 语义色
 *
 * 颜色规范：
 *   success: oklch(0.72 0.18 160) — 翠绿 (Emerald Green)
 *   warning: oklch(0.78 0.18 75)  — 琥珀 (Amber)
 *   danger:  oklch(0.62 0.25 25)  — 赤红 (Red)
 *   info:    oklch(0.68 0.18 240) — 天蓝 (Sky Blue)
 *   neutral: oklch(0.72 0.02 240) — 石板灰 (Slate)
 */
const NODE_STATUS_CONFIG: Record<NodeStatus, {
  /** SVG fill — 节点背景色（亮色模式） */
  fill: string;
  /** SVG fill — 节点背景色（暗色模式） */
  fillDark: string;
  /** SVG stroke — 节点边框色 */
  stroke: string;
  /** SVG stroke — 节点边框色（暗色模式） */
  strokeDark: string;
  /** 文字颜色 */
  text: string;
  /** 文字颜色（暗色模式） */
  textDark: string;
  /** 徽章颜色 */
  badge: string;
  /** 危险节点发光效果 */
  glow?: string;
  /** Tailwind 类名 — 图例色块背景 */
  legendBg: string;
  /** Tailwind 类名 — 图例色块边框 */
  legendBorder: string;
}> = {
  success: {
    fill: 'oklch(0.95 0.06 160 / 0.85)',
    fillDark: 'oklch(0.28 0.08 160 / 0.75)',
    stroke: 'oklch(0.62 0.18 160)',
    strokeDark: 'oklch(0.72 0.18 160)',
    text: 'oklch(0.32 0.12 160)',
    textDark: 'oklch(0.88 0.10 160)',
    badge: 'oklch(0.62 0.18 160)',
    legendBg: 'bg-[oklch(0.95_0.06_160/0.85)]',
    legendBorder: 'border-[oklch(0.62_0.18_160)]',
  },
  warning: {
    fill: 'oklch(0.96 0.08 75 / 0.85)',
    fillDark: 'oklch(0.28 0.08 75 / 0.75)',
    stroke: 'oklch(0.72 0.18 75)',
    strokeDark: 'oklch(0.82 0.18 75)',
    text: 'oklch(0.38 0.14 75)',
    textDark: 'oklch(0.88 0.12 75)',
    badge: 'oklch(0.72 0.18 75)',
    legendBg: 'bg-[oklch(0.96_0.08_75/0.85)]',
    legendBorder: 'border-[oklch(0.72_0.18_75)]',
  },
  danger: {
    fill: 'oklch(0.95 0.08 25 / 0.85)',
    fillDark: 'oklch(0.28 0.10 25 / 0.75)',
    stroke: 'oklch(0.62 0.25 25)',
    strokeDark: 'oklch(0.72 0.25 25)',
    text: 'oklch(0.32 0.18 25)',
    textDark: 'oklch(0.88 0.14 25)',
    badge: 'oklch(0.62 0.25 25)',
    glow: '0 0 14px oklch(0.62 0.25 25 / 0.45)',
    legendBg: 'bg-[oklch(0.95_0.08_25/0.85)]',
    legendBorder: 'border-[oklch(0.62_0.25_25)]',
  },
  info: {
    fill: 'oklch(0.95 0.06 240 / 0.85)',
    fillDark: 'oklch(0.28 0.08 240 / 0.75)',
    stroke: 'oklch(0.62 0.18 240)',
    strokeDark: 'oklch(0.72 0.18 240)',
    text: 'oklch(0.32 0.14 240)',
    textDark: 'oklch(0.88 0.10 240)',
    badge: 'oklch(0.62 0.18 240)',
    legendBg: 'bg-[oklch(0.95_0.06_240/0.85)]',
    legendBorder: 'border-[oklch(0.62_0.18_240)]',
  },
  neutral: {
    fill: 'oklch(0.96 0.01 240 / 0.85)',
    fillDark: 'oklch(0.28 0.02 240 / 0.75)',
    stroke: 'oklch(0.68 0.02 240)',
    strokeDark: 'oklch(0.78 0.02 240)',
    text: 'oklch(0.38 0.02 240)',
    textDark: 'oklch(0.85 0.02 240)',
    badge: 'oklch(0.68 0.02 240)',
    legendBg: 'bg-[oklch(0.96_0.01_240/0.85)]',
    legendBorder: 'border-[oklch(0.68_0.02_240)]',
  },
};

/** 趋势图标 */
const TREND_ICON: Record<TrendDirection, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

/** 趋势颜色（Tailwind 类名，使用 oklch 语义色） */
const TREND_COLOR: Record<TrendDirection, string> = {
  up: 'text-[oklch(0.62_0.18_160)]',
  down: 'text-[oklch(0.62_0.25_25)]',
  stable: 'text-[oklch(0.68_0.02_240)]',
};

// ─────────────────────────────────────────────────────────────────────────────
// 树状图布局计算 (Tree Layout Calculation)
// ─────────────────────────────────────────────────────────────────────────────

/** 带坐标的节点 */
interface LayoutNode extends DecompositionNode {
  x: number;
  y: number;
  width: number;
  height: number;
  children?: LayoutNode[];
}

const NODE_WIDTH = 140;
const NODE_HEIGHT = 56;
const LEVEL_GAP = 180;  // 水平层级间距
const SIBLING_GAP = 16; // 同级节点垂直间距

/**
 * 递归计算树状图布局坐标
 * 采用从左到右水平布局，返回每个节点的 (x, y) 坐标
 */
function calculateLayout(node: DecompositionNode, level: number = 0): LayoutNode {
  const layoutNode: LayoutNode = {
    ...node,
    x: level * LEVEL_GAP,
    y: 0,
    width: NODE_WIDTH,
    height: NODE_HEIGHT,
    children: node.children?.map((child) => calculateLayout(child, level + 1)),
  };
  return layoutNode;
}

/**
 * 计算子树高度（用于垂直居中对齐）
 * 返回该子树所需的总高度
 */
function getSubtreeHeight(node: LayoutNode): number {
  if (!node.children || node.children.length === 0) {
    return NODE_HEIGHT;
  }
  const childrenTotalHeight = node.children.reduce((sum, child) => {
    return sum + getSubtreeHeight(child);
  }, 0) + (node.children.length - 1) * SIBLING_GAP;
  return Math.max(NODE_HEIGHT, childrenTotalHeight);
}

/**
 * 为所有节点分配 y 坐标（垂直居中对齐）
 */
function assignYCoordinates(node: LayoutNode, startY: number): void {
  const subtreeHeight = getSubtreeHeight(node);
  node.y = startY + (subtreeHeight - NODE_HEIGHT) / 2;

  if (node.children && node.children.length > 0) {
    let currentY = startY;
    for (const child of node.children) {
      const childSubtreeHeight = getSubtreeHeight(child);
      assignYCoordinates(child, currentY);
      currentY += childSubtreeHeight + SIBLING_GAP;
    }
  }
}

/**
 * 收集所有节点（展平树结构）
 */
function collectNodes(node: LayoutNode): LayoutNode[] {
  const nodes: LayoutNode[] = [node];
  if (node.children) {
    for (const child of node.children) {
      nodes.push(...collectNodes(child));
    }
  }
  return nodes;
}

/**
 * 收集所有连线（父子节点对）
 */
function collectEdges(node: LayoutNode): Array<{ parent: LayoutNode; child: LayoutNode }> {
  const edges: Array<{ parent: LayoutNode; child: LayoutNode }> = [];
  if (node.children) {
    for (const child of node.children) {
      edges.push({ parent: node, child });
      edges.push(...collectEdges(child));
    }
  }
  return edges;
}

/**
 * 计算连线粗细（基于贡献量占父节点总绝对贡献的比例）
 */
function getEdgeWidth(child: LayoutNode, parent: LayoutNode): number {
  if (!parent.children || parent.children.length === 0) return 2;
  const totalAbs = parent.children.reduce((sum, c) => sum + Math.abs(c.contribution), 0);
  if (totalAbs === 0) return 2;
  const ratio = Math.abs(child.contribution) / totalAbs;
  return Math.max(2, Math.min(10, Math.round(ratio * 12)));
}

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：Hover 浮层 (Tooltip) — iOS 26 Liquid Glass 样式
// ─────────────────────────────────────────────────────────────────────────────

interface TooltipProps {
  node: LayoutNode;
  visible: boolean;
  x: number;
  y: number;
  containerRef: React.RefObject<HTMLDivElement>;
}

function NodeTooltip({ node, visible, x, y, containerRef }: TooltipProps) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [adjustedPos, setAdjustedPos] = useState({ x, y });

  useEffect(() => {
    if (!visible || !tooltipRef.current || !containerRef.current) return;
    const tooltip = tooltipRef.current.getBoundingClientRect();
    const container = containerRef.current.getBoundingClientRect();
    let newX = x;
    let newY = y;
    // 防止超出右边界
    if (x + tooltip.width > container.width) {
      newX = x - tooltip.width - 16;
    }
    // 防止超出下边界
    if (y + tooltip.height > container.height) {
      newY = container.height - tooltip.height - 8;
    }
    setAdjustedPos({ x: newX, y: newY });
  }, [visible, x, y, containerRef]);

  if (!visible) return null;

  const { context, status } = node;
  const cfg = NODE_STATUS_CONFIG[status];
  const isPositive = node.contribution >= 0;

  return (
    <div
      ref={tooltipRef}
      className="absolute z-50 pointer-events-none"
      style={{
        left: adjustedPos.x,
        top: adjustedPos.y,
        minWidth: '220px',
        maxWidth: '280px',
      }}
    >
      {/* Liquid Glass 浮层容器 */}
      <div
        className={[
          'rounded-xl p-4',
          // 毛玻璃背景
          'backdrop-blur-xl',
          'bg-white/80 dark:bg-white/8',
          // 顶部高光线 + 底部暗线 + 外阴影
          'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_8px_32px_-4px_oklch(0_0_0/0.18)]',
          // 边框
          'border border-white/40 dark:border-white/10',
        ].join(' ')}
      >
        {/* 标题 */}
        <div className="flex items-center gap-2 mb-3">
          <span
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ backgroundColor: cfg.stroke }}
          />
          <span
            className="text-sm font-semibold leading-tight"
            style={{
              fontFamily: "'Noto Sans SC', 'DM Sans', sans-serif",
              color: 'oklch(0.18 0.02 240)',
            }}
          >
            {node.name}
          </span>
          {status === 'danger' && (
            <span
              className="ml-auto text-base shrink-0"
              style={{ color: 'oklch(0.62 0.25 25)' }}
              title="警告：该因子存在风险"
            >
              ⚠️
            </span>
          )}
        </div>

        {/* 贡献量 */}
        <div
          className="flex items-center justify-between mb-2 pb-2"
          style={{ borderBottom: '1px solid oklch(0.88 0.01 240 / 0.5)' }}
        >
          <span
            className="text-xs"
            style={{ color: 'oklch(0.55 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
          >
            贡献量
          </span>
          <span
            className="text-sm font-bold tabular-nums"
            style={{
              fontFamily: "'DM Sans', 'Noto Sans SC', sans-serif",
              color: isPositive ? 'oklch(0.52 0.18 160)' : 'oklch(0.52 0.25 25)',
            }}
          >
            {isPositive ? '+' : ''}{node.contribution.toLocaleString()}
          </span>
        </div>

        {/* 上下文信息 */}
        {context && (
          <div className="space-y-1.5">
            {context.currentValue && (
              <div className="flex justify-between text-xs">
                <span style={{ color: 'oklch(0.55 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}>
                  当前值
                </span>
                <span
                  className="font-medium tabular-nums"
                  style={{ color: 'oklch(0.25 0.02 240)', fontFamily: "'DM Sans', sans-serif" }}
                >
                  {context.currentValue}
                </span>
              </div>
            )}
            {context.targetValue && (
              <div className="flex justify-between text-xs">
                <span style={{ color: 'oklch(0.55 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}>
                  目标值
                </span>
                <span
                  className="font-medium tabular-nums"
                  style={{ color: 'oklch(0.25 0.02 240)', fontFamily: "'DM Sans', sans-serif" }}
                >
                  {context.targetValue}
                </span>
              </div>
            )}
            {context.changeRate && (
              <div className="flex justify-between text-xs">
                <span style={{ color: 'oklch(0.55 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}>
                  环比变化
                </span>
                <span
                  className="font-medium tabular-nums"
                  style={{
                    fontFamily: "'DM Sans', sans-serif",
                    color: context.changeRate.startsWith('+')
                      ? 'oklch(0.52 0.18 160)'
                      : 'oklch(0.52 0.25 25)',
                  }}
                >
                  {context.changeRate}
                </span>
              </div>
            )}
            {context.owner && (
              <div className="flex justify-between text-xs">
                <span style={{ color: 'oklch(0.55 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}>
                  负责团队
                </span>
                <span
                  className="font-medium"
                  style={{ color: 'oklch(0.25 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
                >
                  {context.owner}
                </span>
              </div>
            )}
            {context.insight && (
              <div
                className="mt-2 pt-2"
                style={{ borderTop: '1px solid oklch(0.88 0.01 240 / 0.5)' }}
              >
                <p
                  className="text-xs mb-1"
                  style={{ color: 'oklch(0.55 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
                >
                  洞察分析
                </p>
                <p
                  className="text-xs leading-relaxed"
                  style={{ color: 'oklch(0.32 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
                >
                  {context.insight}
                </p>
              </div>
            )}
            {context.solution && (
              <div className="mt-1.5">
                <p
                  className="text-xs mb-1"
                  style={{ color: 'oklch(0.55 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
                >
                  解决方案
                </p>
                <p
                  className="text-xs leading-relaxed"
                  style={{ color: 'oklch(0.42 0.18 160)', fontFamily: "'Noto Sans SC', sans-serif" }}
                >
                  {context.solution}
                </p>
              </div>
            )}
          </div>
        )}

        {/* 下钻提示 */}
        {node.moduleId && (
          <div
            className="mt-3 pt-2"
            style={{ borderTop: '1px solid oklch(0.88 0.01 240 / 0.5)' }}
          >
            <p
              className="text-xs"
              style={{ color: 'oklch(0.52 0.18 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
            >
              点击查看详情 →
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：单个节点 (Node) — iOS 26 Liquid Glass 样式
// ─────────────────────────────────────────────────────────────────────────────

interface TreeNodeProps {
  node: LayoutNode;
  onHover: (node: LayoutNode | null, x: number, y: number) => void;
  onDrillDown?: (nodeId: string, moduleId?: string) => void;
  isDarkMode?: boolean;
}

function TreeNode({ node, onHover, onDrillDown, isDarkMode = false }: TreeNodeProps) {
  const cfg = NODE_STATUS_CONFIG[node.status];
  const isPositive = node.contribution >= 0;
  const isDanger = node.status === 'danger';
  const isClickable = !!onDrillDown;

  const fillColor = isDarkMode ? cfg.fillDark : cfg.fill;
  const strokeColor = isDarkMode ? cfg.strokeDark : cfg.stroke;
  const textColor = isDarkMode ? cfg.textDark : cfg.text;

  const handleMouseEnter = useCallback((e: React.MouseEvent) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const containerRect = (e.currentTarget as HTMLElement).closest('[data-tree-container]')?.getBoundingClientRect();
    if (containerRect) {
      onHover(node, rect.right - containerRect.left + 8, rect.top - containerRect.top);
    }
  }, [node, onHover]);

  const handleMouseLeave = useCallback(() => {
    onHover(null, 0, 0);
  }, [onHover]);

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDrillDown) {
      onDrillDown(node.id, node.moduleId);
    }
  }, [node.id, node.moduleId, onDrillDown]);

  return (
    <g
      transform={`translate(${node.x}, ${node.y})`}
      style={{ cursor: isClickable ? 'pointer' : 'default' }}
      role={isClickable ? 'button' : undefined}
      aria-label={`${node.name}: 贡献量 ${isPositive ? '+' : ''}${node.contribution}`}
    >
      {/* 节点背景矩形 */}
      <foreignObject
        x={0}
        y={0}
        width={NODE_WIDTH}
        height={NODE_HEIGHT}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      >
        {/* Liquid Glass 节点容器 */}
        <div
          className={[
            'w-full h-full rounded-xl border-2 flex flex-col justify-center px-3 py-2',
            // 毛玻璃效果
            'backdrop-blur-xl',
            // Hover 动效：-translate-y-1 + shadow-xl (250ms)
            'transition-all duration-[250ms]',
            isClickable
              ? 'hover:-translate-y-1 hover:shadow-xl hover:opacity-100'
              : '',
            // 危险节点呼吸动效（P0 级）
            isDanger ? 'animate-pulse' : '',
          ].join(' ')}
          style={{
            backgroundColor: fillColor,
            borderColor: strokeColor,
            // 顶部高光线 + 底部暗线 + 危险发光
            boxShadow: isDanger
              ? `inset 0 1px 0 0 oklch(1 0 0 / 0.55), inset 0 -1px 0 0 oklch(0 0 0 / 0.06), ${cfg.glow}`
              : 'inset 0 1px 0 0 oklch(1 0 0 / 0.55), inset 0 -1px 0 0 oklch(0 0 0 / 0.06)',
            opacity: 0.9,
          }}
        >
          {/* 因子名称 */}
          <div className="flex items-center gap-1 mb-0.5">
            <span
              className="text-xs font-semibold truncate leading-tight"
              style={{
                color: textColor,
                maxWidth: isDanger ? '90px' : '120px',
                fontFamily: "'Noto Sans SC', sans-serif",
              }}
              title={node.name}
            >
              {node.name}
            </span>
            {isDanger && (
              <span
                className="text-xs shrink-0"
                style={{ color: 'oklch(0.62 0.25 25)' }}
                title="风险节点"
              >
                ⚠
              </span>
            )}
          </div>
          {/* 贡献量 */}
          <span
            className="text-sm font-bold tabular-nums leading-tight"
            style={{
              color: isPositive ? 'oklch(0.52 0.18 160)' : 'oklch(0.52 0.25 25)',
              fontFamily: "'DM Sans', 'Noto Sans SC', sans-serif",
            }}
          >
            {isPositive ? '+' : ''}{node.contribution.toLocaleString()}
          </span>
        </div>
      </foreignObject>
    </g>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：连线 (Edge) — oklch 语义色
// ─────────────────────────────────────────────────────────────────────────────

interface TreeEdgeProps {
  parent: LayoutNode;
  child: LayoutNode;
}

function TreeEdge({ parent, child }: TreeEdgeProps) {
  const strokeWidth = getEdgeWidth(child, parent);
  const isPositive = child.contribution >= 0;
  // 使用 oklch 语义色：正向贡献翠绿，负向贡献赤红
  const strokeColor = isPositive
    ? 'oklch(0.62 0.18 160)'
    : 'oklch(0.62 0.25 25)';

  // 连线起点：父节点右侧中心
  const x1 = parent.x + NODE_WIDTH;
  const y1 = parent.y + NODE_HEIGHT / 2;
  // 连线终点：子节点左侧中心
  const x2 = child.x;
  const y2 = child.y + NODE_HEIGHT / 2;
  // 贝塞尔曲线控制点
  const cx1 = x1 + (x2 - x1) * 0.5;
  const cy1 = y1;
  const cx2 = x1 + (x2 - x1) * 0.5;
  const cy2 = y2;

  return (
    <path
      d={`M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`}
      fill="none"
      stroke={strokeColor}
      strokeWidth={strokeWidth}
      strokeOpacity={0.55}
      strokeLinecap="round"
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 主组件：北极星因子分解图 (NorthStarDecomposition) — iOS 26 Liquid Glass
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 北极星因子分解图组件 (North Star Decomposition)
 *
 * 以 SVG 树状结构图展示北极星指标的因子分解，支持三层交互：
 * - 一眼定调：节点颜色/连线粗细反映健康状态与权重，警戒节点加警告图标
 * - 悬浮概要：Hover 节点弹出 Liquid Glass 浮层，显示当前值/目标差距/负责团队/洞察分析
 * - 下钻详情：Click 节点触发 onDrillDown 回调，由父组件决定跳转目标
 *
 * 样式规范：iOS 26 Liquid Glass
 *
 * @example
 * <NorthStarDecomposition
 *   data={northStarDecompositionData}
 *   onDrillDown={(nodeId, moduleId) => scrollToSection(`module-${moduleId}`)}
 * />
 */
export function NorthStarDecomposition({ data, onDrillDown, className = '' }: NorthStarDecompositionProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{
    node: LayoutNode | null;
    x: number;
    y: number;
  }>({ node: null, x: 0, y: 0 });

  // 计算布局
  const layoutRoot = calculateLayout(data.rootNode);
  assignYCoordinates(layoutRoot, 0);
  const allNodes = collectNodes(layoutRoot);
  const allEdges = collectEdges(layoutRoot);

  // 计算 SVG 视口大小
  const maxX = Math.max(...allNodes.map((n) => n.x)) + NODE_WIDTH + 24;
  const maxY = Math.max(...allNodes.map((n) => n.y)) + NODE_HEIGHT + 24;
  const svgWidth = maxX;
  const svgHeight = maxY;

  const handleHover = useCallback((node: LayoutNode | null, x: number, y: number) => {
    setTooltip({ node, x, y });
  }, []);

  const targetAchievement = data.target
    ? Math.round((data.value / data.target) * 100)
    : null;

  // 目标达成率颜色（oklch 语义色）
  const achievementColor = targetAchievement !== null
    ? targetAchievement >= 80
      ? 'oklch(0.52 0.18 160)'
      : targetAchievement >= 60
        ? 'oklch(0.62 0.18 75)'
        : 'oklch(0.52 0.25 25)'
    : undefined;

  // 进度条颜色（oklch 语义色）
  const progressBarColor = targetAchievement !== null
    ? targetAchievement >= 80
      ? 'oklch(0.62 0.18 160)'
      : targetAchievement >= 60
        ? 'oklch(0.72 0.18 75)'
        : 'oklch(0.62 0.25 25)'
    : undefined;

  return (
    <div
      className={[
        // 外层容器：Liquid Glass 毛玻璃卡片
        'rounded-2xl p-5 flex flex-col',
        // 毛玻璃背景
        'backdrop-blur-xl',
        'bg-white/65 dark:bg-white/7',
        // 顶部高光线 + 底部暗线 + 外阴影
        'shadow-[inset_0_1px_0_0_oklch(1_0_0/0.55),inset_0_-1px_0_0_oklch(0_0_0/0.06),0_4px_24px_-4px_oklch(0_0_0/0.08)]',
        // 边框
        'border border-white/40 dark:border-white/10',
        // Hover 整体卡片上浮
        'transition-all duration-[250ms] hover:-translate-y-1 hover:shadow-xl',
        className,
      ].join(' ')}
    >
      {/* ── 标题区 ── */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-semibold uppercase tracking-widest"
            style={{
              color: 'oklch(0.52 0.18 240)',
              fontFamily: "'DM Sans', 'Noto Sans SC', sans-serif",
            }}
          >
            北极星因子分解
          </span>
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{
              color: 'oklch(0.45 0.02 240)',
              backgroundColor: 'oklch(0.92 0.01 240 / 0.6)',
              fontFamily: "'DM Sans', 'Noto Sans SC', sans-serif",
              backdropFilter: 'blur(8px)',
            }}
          >
            {data.metric}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={`text-sm font-bold ${TREND_COLOR[data.trend]}`}
            style={{ fontFamily: "'DM Sans', sans-serif" }}
          >
            {TREND_ICON[data.trend]} {data.changeRate}
          </span>
        </div>
      </div>

      {/* ── 核心指标摘要 ── */}
      <div
        className="flex items-end gap-4 mb-4 pb-4"
        style={{ borderBottom: '1px solid oklch(0.88 0.01 240 / 0.4)' }}
      >
        <div>
          {/* KPI 核心数值：text-3xl font-bold tracking-tight */}
          <span
            className="text-3xl font-bold tracking-tight tabular-nums"
            style={{
              color: 'oklch(0.18 0.02 240)',
              fontFamily: "'DM Sans', 'Noto Sans SC', sans-serif",
            }}
          >
            {data.value.toLocaleString()}
          </span>
          {data.unit && (
            <span
              className="text-sm ml-1"
              style={{
                color: 'oklch(0.62 0.02 240)',
                fontFamily: "'Noto Sans SC', sans-serif",
              }}
            >
              {data.unit}
            </span>
          )}
        </div>
        <div className="flex flex-col text-xs pb-0.5" style={{ color: 'oklch(0.62 0.02 240)' }}>
          <span style={{ fontFamily: "'Noto Sans SC', sans-serif" }}>
            环比{' '}
            <span
              className="font-medium tabular-nums"
              style={{
                color: data.change >= 0 ? 'oklch(0.52 0.18 160)' : 'oklch(0.52 0.25 25)',
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              {data.change >= 0 ? '+' : ''}{data.change.toLocaleString()}
            </span>
          </span>
          {targetAchievement !== null && (
            <span style={{ fontFamily: "'Noto Sans SC', sans-serif" }}>
              目标达成率{' '}
              <span
                className="font-medium tabular-nums"
                style={{
                  color: achievementColor,
                  fontFamily: "'DM Sans', sans-serif",
                }}
              >
                {targetAchievement}%
              </span>
            </span>
          )}
        </div>
        {/* 目标进度条 */}
        {targetAchievement !== null && (
          <div className="flex-1 ml-2">
            <div
              className="flex justify-between text-xs mb-1"
              style={{ color: 'oklch(0.62 0.02 240)', fontFamily: "'Noto Sans SC', 'DM Sans', sans-serif" }}
            >
              <span>目标 {data.target?.toLocaleString()}{data.unit}</span>
              <span style={{ fontFamily: "'DM Sans', sans-serif" }}>{targetAchievement}%</span>
            </div>
            <div
              className="h-1.5 rounded-full overflow-hidden"
              style={{ backgroundColor: 'oklch(0.92 0.01 240 / 0.5)' }}
            >
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${Math.min(100, targetAchievement)}%`,
                  backgroundColor: progressBarColor,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* ── 图例说明 ── */}
      <div className="flex items-center gap-4 mb-3 flex-wrap">
        <span
          className="text-xs font-medium"
          style={{ color: 'oklch(0.62 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
        >
          图例：
        </span>
        {(['success', 'warning', 'danger'] as NodeStatus[]).map((s) => (
          <div key={s} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-lg border-2"
              style={{
                backgroundColor: NODE_STATUS_CONFIG[s].fill,
                borderColor: NODE_STATUS_CONFIG[s].stroke,
                backdropFilter: 'blur(4px)',
              }}
            />
            <span
              className="text-xs"
              style={{ color: 'oklch(0.52 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
            >
              {s === 'success' ? '健康' : s === 'warning' ? '待优化' : '风险'}
            </span>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <span
            className="text-xs"
            style={{ color: 'oklch(0.52 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
          >
            连线粗细 = 权重
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className="text-xs"
            style={{ color: 'oklch(0.52 0.25 25)', fontFamily: "'Noto Sans SC', sans-serif" }}
          >
            ⚠ = 警戒节点
          </span>
        </div>
      </div>

      {/* ── 树状图区域 ── */}
      <div
        ref={containerRef}
        data-tree-container
        className="relative overflow-auto flex-1"
        style={{ minHeight: '200px' }}
      >
        <svg
          width={svgWidth}
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ overflow: 'visible', display: 'block' }}
        >
          {/* 连线层（先渲染，在节点下方） */}
          <g>
            {allEdges.map(({ parent, child }, idx) => (
              <TreeEdge key={`edge-${idx}`} parent={parent} child={child} />
            ))}
          </g>
          {/* 节点层 */}
          <g>
            {allNodes.map((node) => (
              <TreeNode
                key={node.id}
                node={node}
                onHover={handleHover}
                onDrillDown={onDrillDown}
              />
            ))}
          </g>
        </svg>

        {/* Hover 浮层 */}
        {tooltip.node && (
          <NodeTooltip
            node={tooltip.node}
            visible={!!tooltip.node}
            x={tooltip.x}
            y={tooltip.y}
            containerRef={containerRef}
          />
        )}
      </div>

      {/* ── 底部提示 ── */}
      {onDrillDown && (
        <p
          className="text-xs mt-3 text-center"
          style={{ color: 'oklch(0.62 0.02 240)', fontFamily: "'Noto Sans SC', sans-serif" }}
        >
          点击节点可下钻查看详情
        </p>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Mock 数据示例 (Mock Data for Development & Testing)
// ─────────────────────────────────────────────────────────────────────────────

export const mockNorthStarDecompositionData: NorthStarDecompositionData = {
  metric: 'DAU',
  value: 12500,
  unit: '人',
  change: 850,
  changeRate: '+7.3%',
  trend: 'up',
  target: 15000,
  rootNode: {
    id: 'root',
    name: 'DAU 总变化',
    contribution: 850,
    status: 'warning',
    context: {
      currentValue: '12,500 人',
      targetValue: '15,000 人',
      changeRate: '+7.3%',
      insight: '整体 DAU 增长，但距目标仍有差距，主要受流失增加拖累。',
    },
    children: [
      {
        id: 'new_user',
        name: '新用户增长',
        contribution: 1200,
        status: 'success',
        moduleId: 'growth',
        context: {
          currentValue: '1,200 人/日',
          targetValue: '1,500 人/日',
          changeRate: '+15.4%',
          owner: '增长团队 · 张三',
          insight: '新用户获取渠道优化效果显著，ASO 带来 40% 自然增长。',
        },
        children: [
          {
            id: 'aso',
            name: 'ASO 自然增长',
            contribution: 480,
            status: 'success',
            moduleId: 'growth',
            context: {
              currentValue: '480 人/日',
              changeRate: '+22%',
              owner: '增长团队',
              insight: '关键词优化带动自然搜索流量提升。',
            },
          },
          {
            id: 'paid_ads',
            name: '付费投放',
            contribution: 720,
            status: 'warning',
            moduleId: 'growth',
            context: {
              currentValue: '720 人/日',
              targetValue: '900 人/日',
              changeRate: '+8%',
              owner: '增长团队',
              insight: 'ROI 偏低，部分渠道 CPA 超出预算上限。',
              solution: '调整投放策略，暂停低效渠道，集中预算至高转化渠道。',
            },
          },
        ],
      },
      {
        id: 'retention',
        name: '留存提升',
        contribution: 350,
        status: 'warning',
        moduleId: 'product',
        context: {
          currentValue: '18.2%',
          targetValue: '20%',
          changeRate: '-1.8pp',
          owner: '产品团队 · 李四',
          insight: 'D7 留存低于预警线，新版本上线后核心路径流失增加。',
          solution: '已启动专项排查，预计本周定位根因。',
        },
      },
      {
        id: 'churn',
        name: '流失增加',
        contribution: -450,
        status: 'danger',
        moduleId: 'product',
        context: {
          currentValue: '-450 人/日',
          changeRate: '-12%',
          owner: '产品团队 · 李四',
          insight: '流失率上升，主要集中在 D3-D7 阶段，与新版本 UI 改版相关。',
          solution: '回滚部分 UI 变更，同时启动用户访谈收集反馈。',
        },
      },
      {
        id: 'reactivation',
        name: '召回用户',
        contribution: -250,
        status: 'warning',
        moduleId: 'growth',
        context: {
          currentValue: '-250 人/日',
          changeRate: '-5%',
          owner: '增长团队',
          insight: '召回活动 ROI 下降，Push 通知打开率降至 3.2%。',
          solution: '优化 Push 文案，测试个性化召回策略。',
        },
      },
    ],
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// 默认导出（用于快速预览）
// ─────────────────────────────────────────────────────────────────────────────

export default function NorthStarDecompositionDemo() {
  const handleDrillDown = (nodeId: string, moduleId?: string) => {
    console.log('[下钻跳转] nodeId:', nodeId, 'moduleId:', moduleId);
    // 父组件可在此实现具体跳转逻辑，例如：
    // scrollToSection(`module-${moduleId}`);
    // navigate(`/modules/${moduleId}?factor=${nodeId}`);
  };

  return (
    <div
      className="min-h-screen p-8"
      style={{ background: 'oklch(0.96 0.01 240)' }}
    >
      {/* 深色模式预览 */}
      <div className="dark" style={{ background: 'oklch(0.12 0.02 240)', padding: '2rem', borderRadius: '1rem', marginBottom: '2rem' }}>
        <h2
          className="text-xl font-bold mb-6"
          style={{
            color: 'oklch(0.92 0.01 240)',
            fontFamily: "'DM Sans', 'Noto Sans SC', sans-serif",
          }}
        >
          北极星因子分解图 — 深色模式预览
        </h2>
        <NorthStarDecomposition
          data={mockNorthStarDecompositionData}
          onDrillDown={handleDrillDown}
        />
      </div>

      {/* 亮色模式预览 */}
      <div className="max-w-4xl mx-auto">
        <h1
          className="text-2xl font-bold mb-6"
          style={{
            color: 'oklch(0.18 0.02 240)',
            fontFamily: "'DM Sans', 'Noto Sans SC', sans-serif",
          }}
        >
          北极星因子分解图 — 亮色模式预览
        </h1>
        <NorthStarDecomposition
          data={mockNorthStarDecompositionData}
          onDrillDown={handleDrillDown}
        />
      </div>
    </div>
  );
}

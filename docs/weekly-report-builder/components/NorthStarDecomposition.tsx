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

/** 节点状态颜色配置 */
const NODE_STATUS_CONFIG: Record<NodeStatus, {
  fill: string;
  stroke: string;
  text: string;
  badge: string;
  badgeBg: string;
  glow?: string;
}> = {
  success: {
    fill: '#d1fae5',
    stroke: '#10b981',
    text: '#065f46',
    badge: '#10b981',
    badgeBg: '#d1fae5',
  },
  warning: {
    fill: '#fef3c7',
    stroke: '#f59e0b',
    text: '#78350f',
    badge: '#f59e0b',
    badgeBg: '#fef3c7',
  },
  danger: {
    fill: '#fee2e2',
    stroke: '#ef4444',
    text: '#7f1d1d',
    badge: '#ef4444',
    badgeBg: '#fee2e2',
    glow: '0 0 12px rgba(239,68,68,0.4)',
  },
  info: {
    fill: '#e0f2fe',
    stroke: '#0ea5e9',
    text: '#0c4a6e',
    badge: '#0ea5e9',
    badgeBg: '#e0f2fe',
  },
  neutral: {
    fill: '#f1f5f9',
    stroke: '#94a3b8',
    text: '#334155',
    badge: '#94a3b8',
    badgeBg: '#f1f5f9',
  },
};

/** 趋势图标 */
const TREND_ICON: Record<TrendDirection, string> = {
  up: '↑',
  down: '↓',
  stable: '→',
};

/** 趋势颜色（Tailwind 类名） */
const TREND_COLOR: Record<TrendDirection, string> = {
  up: 'text-emerald-500',
  down: 'text-red-500',
  stable: 'text-slate-400',
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
// 子组件：Hover 浮层 (Tooltip)
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
      <div
        className="rounded-xl shadow-2xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 p-4"
        style={{ boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}
      >
        {/* 标题 */}
        <div className="flex items-center gap-2 mb-3">
          <span
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ backgroundColor: cfg.stroke }}
          />
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            {node.name}
          </span>
          {status === 'danger' && (
            <span className="ml-auto text-red-500 text-base" title="警告：该因子存在风险">⚠️</span>
          )}
        </div>

        {/* 贡献量 */}
        <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-100 dark:border-slate-700">
          <span className="text-xs text-slate-500 dark:text-slate-400">贡献量</span>
          <span className={`text-sm font-bold tabular-nums ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
            {isPositive ? '+' : ''}{node.contribution.toLocaleString()}
          </span>
        </div>

        {/* 上下文信息 */}
        {context && (
          <div className="space-y-1.5">
            {context.currentValue && (
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 dark:text-slate-400">当前值</span>
                <span className="font-medium text-slate-700 dark:text-slate-200">{context.currentValue}</span>
              </div>
            )}
            {context.targetValue && (
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 dark:text-slate-400">目标值</span>
                <span className="font-medium text-slate-700 dark:text-slate-200">{context.targetValue}</span>
              </div>
            )}
            {context.changeRate && (
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 dark:text-slate-400">环比变化</span>
                <span className={`font-medium tabular-nums ${context.changeRate.startsWith('+') ? 'text-emerald-500' : 'text-red-500'}`}>
                  {context.changeRate}
                </span>
              </div>
            )}
            {context.owner && (
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 dark:text-slate-400">负责团队</span>
                <span className="font-medium text-slate-700 dark:text-slate-200">{context.owner}</span>
              </div>
            )}
            {context.insight && (
              <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-700">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">洞察分析</p>
                <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">{context.insight}</p>
              </div>
            )}
            {context.solution && (
              <div className="mt-1.5">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">解决方案</p>
                <p className="text-xs text-emerald-600 dark:text-emerald-400 leading-relaxed">{context.solution}</p>
              </div>
            )}
          </div>
        )}

        {/* 下钻提示 */}
        {node.moduleId && (
          <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-700">
            <p className="text-xs text-sky-500 dark:text-sky-400">点击查看详情 →</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：单个节点 (Node)
// ─────────────────────────────────────────────────────────────────────────────

interface TreeNodeProps {
  node: LayoutNode;
  onHover: (node: LayoutNode | null, x: number, y: number) => void;
  onDrillDown?: (nodeId: string, moduleId?: string) => void;
}

function TreeNode({ node, onHover, onDrillDown }: TreeNodeProps) {
  const cfg = NODE_STATUS_CONFIG[node.status];
  const isPositive = node.contribution >= 0;
  const isDanger = node.status === 'danger';
  const isClickable = !!onDrillDown;

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
        <div
          className={`
            w-full h-full rounded-xl border-2 flex flex-col justify-center px-3 py-2
            transition-all duration-200
            ${isClickable ? 'hover:scale-105 hover:shadow-lg' : ''}
            ${isDanger ? 'animate-pulse-subtle' : ''}
          `}
          style={{
            backgroundColor: cfg.fill,
            borderColor: cfg.stroke,
            boxShadow: isDanger ? cfg.glow : undefined,
          }}
        >
          {/* 因子名称 */}
          <div className="flex items-center gap-1 mb-0.5">
            <span
              className="text-xs font-semibold truncate leading-tight"
              style={{ color: cfg.text, maxWidth: isDanger ? '90px' : '120px' }}
              title={node.name}
            >
              {node.name}
            </span>
            {isDanger && (
              <span className="text-red-500 text-xs shrink-0" title="风险节点">⚠</span>
            )}
          </div>
          {/* 贡献量 */}
          <span
            className="text-sm font-bold tabular-nums leading-tight"
            style={{ color: isPositive ? '#10b981' : '#ef4444' }}
          >
            {isPositive ? '+' : ''}{node.contribution.toLocaleString()}
          </span>
        </div>
      </foreignObject>
    </g>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 子组件：连线 (Edge)
// ─────────────────────────────────────────────────────────────────────────────

interface TreeEdgeProps {
  parent: LayoutNode;
  child: LayoutNode;
}

function TreeEdge({ parent, child }: TreeEdgeProps) {
  const strokeWidth = getEdgeWidth(child, parent);
  const isPositive = child.contribution >= 0;
  const strokeColor = isPositive ? '#10b981' : '#ef4444';

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
      strokeOpacity={0.5}
      strokeLinecap="round"
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 主组件：北极星因子分解图 (NorthStarDecomposition)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 北极星因子分解图组件 (North Star Decomposition)
 *
 * 以 SVG 树状结构图展示北极星指标的因子分解，支持三层交互：
 * - 一眼定调：节点颜色/连线粗细反映健康状态与权重，警戒节点加警告图标
 * - 悬浮概要：Hover 节点弹出浮层，显示当前值/目标差距/负责团队/洞察分析
 * - 下钻详情：Click 节点触发 onDrillDown 回调，由父组件决定跳转目标
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

  return (
    <div
      className={`rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 p-5 flex flex-col ${className}`}
    >
      {/* ── 标题区 ── */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-widest text-sky-500">
            北极星因子分解
          </span>
          <span className="text-xs text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-full">
            {data.metric}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`text-sm font-bold ${TREND_COLOR[data.trend]}`}>
            {TREND_ICON[data.trend]} {data.changeRate}
          </span>
        </div>
      </div>

      {/* ── 核心指标摘要 ── */}
      <div className="flex items-end gap-4 mb-4 pb-4 border-b border-slate-100 dark:border-slate-700">
        <div>
          <span className="text-3xl font-bold text-slate-800 dark:text-slate-100 tabular-nums">
            {data.value.toLocaleString()}
          </span>
          {data.unit && (
            <span className="text-slate-400 text-sm ml-1">{data.unit}</span>
          )}
        </div>
        <div className="flex flex-col text-xs text-slate-400 pb-0.5">
          <span>
            环比 <span className={`font-medium ${data.change >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
              {data.change >= 0 ? '+' : ''}{data.change.toLocaleString()}
            </span>
          </span>
          {targetAchievement !== null && (
            <span>
              目标达成率 <span className={`font-medium ${targetAchievement >= 80 ? 'text-emerald-500' : targetAchievement >= 60 ? 'text-amber-500' : 'text-red-500'}`}>
                {targetAchievement}%
              </span>
            </span>
          )}
        </div>
        {/* 目标进度条 */}
        {targetAchievement !== null && (
          <div className="flex-1 ml-2">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>目标 {data.target?.toLocaleString()}{data.unit}</span>
              <span>{targetAchievement}%</span>
            </div>
            <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  targetAchievement >= 80 ? 'bg-emerald-500' :
                  targetAchievement >= 60 ? 'bg-amber-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, targetAchievement)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* ── 图例说明 ── */}
      <div className="flex items-center gap-4 mb-3 flex-wrap">
        <span className="text-xs text-slate-400 font-medium">图例：</span>
        {(['success', 'warning', 'danger'] as NodeStatus[]).map((s) => (
          <div key={s} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-sm border"
              style={{
                backgroundColor: NODE_STATUS_CONFIG[s].fill,
                borderColor: NODE_STATUS_CONFIG[s].stroke,
              }}
            />
            <span className="text-xs text-slate-500">
              {s === 'success' ? '健康' : s === 'warning' ? '待优化' : '风险'}
            </span>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-slate-500">连线粗细 = 权重</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-red-500">⚠ = 警戒节点</span>
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
        <p className="text-xs text-slate-400 mt-3 text-center">
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-6">
          北极星因子分解图 — 组件预览
        </h1>
        <NorthStarDecomposition
          data={mockNorthStarDecompositionData}
          onDrillDown={handleDrillDown}
        />
      </div>
    </div>
  );
}

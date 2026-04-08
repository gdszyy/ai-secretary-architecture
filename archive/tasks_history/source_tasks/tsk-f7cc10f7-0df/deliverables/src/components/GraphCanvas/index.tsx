/**
 * GraphCanvas - G6 画布主组件
 * XPBET 全球站功能地图管理系统
 *
 * 负责初始化和管理 G6 TreeGraph 实例，处理画布级别的交互事件。
 */

import React, { useEffect, useRef, useCallback, useState } from 'react';
import G6, { type TreeGraph, type GraphData, type IG6GraphEvent } from '@antv/g6';
import { Spin, message } from 'antd';
import { registerXPBETNode } from './customNodes';
import { NodeTooltip } from '../NodeTooltip';
import type { MindMapNode } from '../../services/transformer';

// 注册自定义节点（在模块加载时执行一次）
registerXPBETNode();

// ==================== 类型定义 ====================

interface GraphCanvasProps {
  /** 树形数据（来自 DataContext） */
  data: MindMapNode | null;
  /** 加载状态 */
  loading?: boolean;
  /** 视图方向：H=水平，V=垂直 */
  direction?: 'H' | 'V';
  /** 节点点击回调 */
  onNodeClick?: (node: MindMapNode) => void;
  /** 节点双击回调（跳转文档） */
  onNodeDoubleClick?: (node: MindMapNode) => void;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  nodeData: MindMapNode | null;
}

// ==================== G6 配置 ====================

const GRAPH_CONFIG = {
  /** 最小缩放比例 */
  minZoom: 0.1,
  /** 最大缩放比例 */
  maxZoom: 4,
  /** 动画持续时间（ms） */
  animateDuration: 300,
  /** 初始缩放比例 */
  defaultZoom: 0.8,
} as const;

// ==================== 组件 ====================

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  data,
  loading = false,
  direction = 'H',
  onNodeClick,
  onNodeDoubleClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<TreeGraph | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    nodeData: null,
  });

  // ── 初始化 G6 图实例 ────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || 1200;
    const height = container.clientHeight || 800;

    const graph = new G6.TreeGraph({
      container,
      width,
      height,

      // ── 布局配置 ──────────────────────────────────────────────────
      layout: {
        type: 'mindmap',
        direction,
        getHeight: (node: MindMapNode) => {
          const typeConfig = { root: 48, category: 40, module: 36, feature: 28 };
          return typeConfig[node.type as keyof typeof typeConfig] ?? 28;
        },
        getWidth: (node: MindMapNode) => {
          const label = node.label ?? '';
          const fontSizes = { root: 16, category: 14, module: 13, feature: 12 };
          const fontSize = fontSizes[node.type as keyof typeof fontSizes] ?? 12;
          return Math.max(label.length * (fontSize * 0.65) + 32, 80);
        },
        getVGap: () => 8,
        getHGap: () => 50,
      },

      // ── 默认节点配置 ──────────────────────────────────────────────
      defaultNode: {
        type: 'xpbet-node',
      },

      // ── 默认边配置 ────────────────────────────────────────────────
      defaultEdge: {
        type: 'cubic-horizontal',
        style: {
          stroke: '#C2C8D5',
          lineWidth: 1.5,
          endArrow: false,
        },
      },

      // ── 交互行为 ──────────────────────────────────────────────────
      modes: {
        default: [
          'collapse-expand',
          {
            type: 'drag-canvas',
            enableOptimize: true,
          },
          {
            type: 'zoom-canvas',
            minZoom: GRAPH_CONFIG.minZoom,
            maxZoom: GRAPH_CONFIG.maxZoom,
            enableOptimize: true,
          },
        ],
      },

      // ── 渲染配置 ──────────────────────────────────────────────────
      renderer: 'canvas',
      fitView: true,
      fitViewPadding: [40, 60, 40, 60],
      animate: true,
      animateCfg: {
        duration: GRAPH_CONFIG.animateDuration,
        easing: 'easeCubic',
      },
    });

    graphRef.current = graph;

    // ── 注册事件监听 ──────────────────────────────────────────────
    // 节点悬浮：显示 Tooltip
    graph.on('node:mouseenter', (evt: IG6GraphEvent) => {
      const { item, clientX, clientY } = evt;
      if (!item) return;
      const model = item.getModel() as MindMapNode;
      if (model.type === 'feature' || model.type === 'module') {
        setTooltip({
          visible: true,
          x: clientX + 12,
          y: clientY - 8,
          nodeData: model,
        });
      }
      graph.setItemState(item, 'hover', true);
    });

    graph.on('node:mouseleave', (evt: IG6GraphEvent) => {
      const { item } = evt;
      if (item) graph.setItemState(item, 'hover', false);
      setTooltip((prev) => ({ ...prev, visible: false }));
    });

    // 节点单击：触发回调（用于右侧详情面板）
    graph.on('node:click', (evt: IG6GraphEvent) => {
      const { item } = evt;
      if (!item) return;
      const model = item.getModel() as MindMapNode;
      graph.setItemState(item, 'selected', true);
      onNodeClick?.(model);
    });

    // 节点双击：跳转飞书文档
    graph.on('node:dblclick', (evt: IG6GraphEvent) => {
      const { item } = evt;
      if (!item) return;
      const model = item.getModel() as MindMapNode;
      if (model.data?.docLink) {
        onNodeDoubleClick?.(model);
        openFeishuDocument(model.data.docLink);
      }
    });

    // 画布点击：取消所有节点选中状态
    graph.on('canvas:click', () => {
      graph.getNodes().forEach((node) => {
        graph.clearItemStates(node, ['selected']);
      });
    });

    // ── 窗口大小变化时自适应 ──────────────────────────────────────
    const handleResize = () => {
      if (!container || !graph || graph.get('destroyed')) return;
      graph.changeSize(container.clientWidth, container.clientHeight);
      graph.fitView();
    };
    window.addEventListener('resize', handleResize);

    // ── 清理函数 ──────────────────────────────────────────────────
    return () => {
      window.removeEventListener('resize', handleResize);
      if (graph && !graph.get('destroyed')) {
        graph.destroy();
      }
      graphRef.current = null;
    };
  }, []); // 仅初始化一次

  // ── 数据变化时更新画布 ──────────────────────────────────────────────
  useEffect(() => {
    const graph = graphRef.current;
    if (!graph || graph.get('destroyed') || !data) return;

    graph.changeData(data as unknown as GraphData);
    graph.fitView();
  }, [data]);

  // ── 布局方向变化时更新 ──────────────────────────────────────────────
  useEffect(() => {
    const graph = graphRef.current;
    if (!graph || graph.get('destroyed')) return;

    graph.updateLayout({ direction });
    graph.fitView();
  }, [direction]);

  // ── 工具栏操作 ──────────────────────────────────────────────────────
  const handleFitView = useCallback(() => {
    graphRef.current?.fitView();
  }, []);

  const handleZoomIn = useCallback(() => {
    const graph = graphRef.current;
    if (!graph) return;
    const currentZoom = graph.getZoom();
    const newZoom = Math.min(currentZoom * 1.2, GRAPH_CONFIG.maxZoom);
    graph.zoomTo(newZoom, graph.getGraphCenterPoint());
  }, []);

  const handleZoomOut = useCallback(() => {
    const graph = graphRef.current;
    if (!graph) return;
    const currentZoom = graph.getZoom();
    const newZoom = Math.max(currentZoom / 1.2, GRAPH_CONFIG.minZoom);
    graph.zoomTo(newZoom, graph.getGraphCenterPoint());
  }, []);

  const handleExpandAll = useCallback(() => {
    const graph = graphRef.current;
    if (!graph) return;
    graph.getNodes().forEach((node) => {
      if (node.getModel().collapsed) {
        graph.setItemState(node, 'collapsed', false);
      }
    });
    graph.fitView();
    message.success('已展开所有节点');
  }, []);

  // ── 渲染 ────────────────────────────────────────────────────────────
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* G6 画布容器 */}
      <div
        ref={containerRef}
        style={{ width: '100%', height: '100%', background: '#F7F8FA' }}
      />

      {/* 加载状态遮罩 */}
      {loading && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(247, 248, 250, 0.8)',
            zIndex: 10,
          }}
        >
          <Spin size="large" tip="正在加载功能地图..." />
        </div>
      )}

      {/* 工具栏 */}
      <div
        style={{
          position: 'absolute',
          top: 16,
          right: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          zIndex: 5,
        }}
      >
        <ToolButton onClick={handleZoomIn} title="放大">+</ToolButton>
        <ToolButton onClick={handleZoomOut} title="缩小">−</ToolButton>
        <ToolButton onClick={handleFitView} title="适应屏幕">⊡</ToolButton>
        <ToolButton onClick={handleExpandAll} title="展开全部">⊞</ToolButton>
      </div>

      {/* 节点悬浮提示 */}
      {tooltip.visible && tooltip.nodeData && (
        <NodeTooltip
          node={tooltip.nodeData}
          x={tooltip.x}
          y={tooltip.y}
        />
      )}
    </div>
  );
};

// ==================== 工具栏按钮子组件 ====================

const ToolButton: React.FC<{
  onClick: () => void;
  title: string;
  children: React.ReactNode;
}> = ({ onClick, title, children }) => (
  <button
    onClick={onClick}
    title={title}
    style={{
      width: 32,
      height: 32,
      border: '1px solid #D9D9D9',
      borderRadius: 4,
      background: '#FFFFFF',
      cursor: 'pointer',
      fontSize: 16,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    }}
  >
    {children}
  </button>
);

// ==================== 工具函数 ====================

/**
 * 打开飞书文档
 * 自动检测运行环境（飞书 Gadget vs 普通浏览器）
 */
function openFeishuDocument(url: string): void {
  const isLarkEnvironment = navigator.userAgent.toLowerCase().includes('lark');

  if (isLarkEnvironment && typeof (window as any).tt !== 'undefined') {
    // 飞书 Gadget 环境：使用 JSSDK 在飞书内打开
    (window as any).tt.openDocument({ url });
  } else {
    // 普通浏览器：新标签页打开
    window.open(url, '_blank', 'noopener,noreferrer');
  }
}

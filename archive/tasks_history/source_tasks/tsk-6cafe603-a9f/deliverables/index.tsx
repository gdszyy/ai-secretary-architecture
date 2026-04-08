/**
 * GraphCanvas - G6 v5 画布核心组件
 * 设计风格：清爽专业风 - 浅色主题，状态颜色突出
 * 
 * 关键设计：
 * - G6 v5 使用 nodes + edges 格式，NodeData.children 存储子节点ID
 * - mindmap 布局通过 type: 'mindmap' 配置
 * - graph.layout() 只能在 render() 完成后调用
 * - 节点 size 属性为 [width, height] 数组
 * - collapse-expand 行为默认是单击触发，改为双击
 * - Tooltip 通过 POINTER_ENTER/LEAVE 事件触发
 */

import React, { useEffect, useRef, useCallback, useState } from 'react';
import { Graph, NodeEvent } from '@antv/g6';
import type { NodeData, IPointerEvent } from '@antv/g6';
import type { MindMapRoot } from '../../types/mindmap';
import { transformToG6Data } from '../../lib/dataTransformer';
import { NodeTooltip } from '../NodeTooltip';

interface GraphCanvasProps {
  data: MindMapRoot | null;
  loading?: boolean;
  direction?: 'H' | 'V';
  onNodeClick?: (nodeData: NodeData) => void;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  nodeData: NodeData | null;
}

// 获取节点宽度
// @antv/hierarchy 传入的是 { id, data: {...}, children: [...] } 格式
function getNodeWidth(d: any): number {
  const data = d.data || d;
  const label = (data.label as string) || '';
  const nodeType = (data.nodeType as string) || 'feature';
  const baseWidths: Record<string, number> = { root: 180, category: 160, module: 140, feature: 120 };
  const base = baseWidths[nodeType] ?? 120;
  return Math.max(base, label.length * 14 + 40);
}

// 获取节点高度
function getNodeHeight(d: any): number {
  const data = d.data || d;
  const nodeType = (data.nodeType as string) || 'feature';
  const heights: Record<string, number> = { root: 52, category: 44, module: 40, feature: 36 };
  return heights[nodeType] ?? 36;
}

// 创建 G6 Graph 配置
function createGraphOptions(container: HTMLDivElement, direction: 'H' | 'V') {
  return {
    container,
    width: container.clientWidth,
    height: container.clientHeight,
    autoResize: true,
    layout: {
      type: 'mindmap',
      direction,
      getWidth: getNodeWidth,
      getHeight: getNodeHeight,
      getHGap: () => 50,
      getVGap: () => 10,
      getSide: () => 'right',
    } as any,
    node: {
      type: 'rect',
      style: (d: NodeData) => {
        const nodeType = (d.data?.nodeType as string) || 'feature';
        const rawFill = (d.data?.fill as string) || '#F5F5F5';
        const fill = nodeType === 'root' ? '#001529' : rawFill;
        const stroke = (d.data?.stroke as string) || '#D9D9D9';
        const lineWidth = nodeType === 'root' ? 0 : (d.data?.lineWidth as number) || 1;
        const label = (d.data?.label as string) || '';
        return {
          fill,
          stroke: nodeType === 'root' ? fill : stroke,
          lineWidth,
          radius: nodeType === 'root' ? 10 : nodeType === 'category' ? 6 : 4,
          labelText: label,
          labelFill: nodeType === 'root' ? '#FFFFFF' : '#1A1A2E',
          labelFontSize: nodeType === 'root' ? 15 : nodeType === 'category' ? 13 : nodeType === 'module' ? 12 : 11,
          labelMaxWidth: getNodeWidth(d) - 16,
          labelFontWeight: (nodeType === 'root' || nodeType === 'category') ? 600 : 400,
          labelPlacement: 'center',
          size: [getNodeWidth(d), getNodeHeight(d)] as [number, number],
          cursor: 'pointer',
        };
      },
      state: {
        selected: { stroke: '#1677FF', lineWidth: 2, shadowColor: 'rgba(22,119,255,0.3)', shadowBlur: 8 },
        hover: { stroke: '#1677FF', lineWidth: 1.5 },
      },
    },
    edge: {
      type: 'cubic-horizontal',
      style: { stroke: '#C8C8C8', lineWidth: 1.5, endArrow: false },
    },
    behaviors: [
      'drag-canvas',
      'zoom-canvas',
      // collapse-expand 改为双击触发，避免与单击查看详情冲突
      { type: 'collapse-expand', trigger: 'dblclick' },
      'hover-activate',
    ],
    animation: false,
    zoomRange: [0.1, 4],
    background: '#F7F8FA',
  };
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  data,
  loading = false,
  direction = 'H',
  onNodeClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const onNodeClickRef = useRef(onNodeClick);
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false, x: 0, y: 0, nodeData: null,
  });

  // 保持回调引用最新
  useEffect(() => {
    onNodeClickRef.current = onNodeClick;
  }, [onNodeClick]);

  // 当数据或方向变化时，重建图实例
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !data) return;

    // 销毁旧实例
    if (graphRef.current && !graphRef.current.destroyed) {
      graphRef.current.destroy();
      graphRef.current = null;
    }

    // 创建新实例
    const graph = new Graph(createGraphOptions(container, direction) as any);
    graphRef.current = graph;

    // 设置数据并渲染
    const g6Data = transformToG6Data(data);
    graph.setData(g6Data);

    graph.render().then(() => {
      if (graph.destroyed) return;
      graph.fitView();
      setTimeout(() => {
        if (graph.destroyed) return;
        const zoom = graph.getZoom();
        if (zoom > 0.75) {
          graph.zoomTo(0.65);
          graph.fitView();
        }
      }, 200);
    }).catch(() => {});

    // 单击节点：显示 Tooltip 详情（如果有文档链接则打开）
    graph.on(NodeEvent.CLICK, (evt: IPointerEvent) => {
      const nodeId = (evt.target as any)?.id;
      if (!nodeId) return;
      try {
        const nodeData = graph.getNodeData(nodeId);
        if (nodeData) {
          onNodeClickRef.current?.(nodeData);
          // 功能节点单击时打开文档链接
          const nodeType = nodeData.data?.nodeType as string;
          if (nodeType === 'feature' && nodeData.data?.docLink) {
            window.open(nodeData.data.docLink as string, '_blank', 'noopener,noreferrer');
          }
        }
      } catch (e) { /* ignore */ }
    });

    // 节点悬浮 Tooltip（使用 POINTER_OVER 而非 POINTER_ENTER，更可靠）
    graph.on(NodeEvent.POINTER_OVER, (evt: IPointerEvent) => {
      const nodeId = (evt.target as any)?.id;
      if (!nodeId) return;
      try {
        const nodeData = graph.getNodeData(nodeId);
        const nodeType = nodeData?.data?.nodeType as string;
        if (nodeData && (nodeType === 'feature' || nodeType === 'module')) {
          const clientX = (evt as any).client?.x ?? (evt as any).clientX ?? 0;
          const clientY = (evt as any).client?.y ?? (evt as any).clientY ?? 0;
          const rect = container.getBoundingClientRect();
          setTooltip({ 
            visible: true, 
            x: clientX - rect.left + 12, 
            y: clientY - rect.top - 10, 
            nodeData 
          });
        }
      } catch (e) { /* ignore */ }
    });

    graph.on(NodeEvent.POINTER_MOVE, (evt: IPointerEvent) => {
      const clientX = (evt as any).client?.x ?? (evt as any).clientX ?? 0;
      const clientY = (evt as any).client?.y ?? (evt as any).clientY ?? 0;
      const rect = container.getBoundingClientRect();
      setTooltip(prev => prev.visible ? { 
        ...prev, 
        x: clientX - rect.left + 12, 
        y: clientY - rect.top - 10 
      } : prev);
    });

    graph.on(NodeEvent.POINTER_OUT, () => {
      setTooltip(prev => ({ ...prev, visible: false }));
    });

    // 窗口大小变化
    const handleResize = () => {
      if (!container || !graph || graph.destroyed) return;
      graph.setSize(container.clientWidth, container.clientHeight);
      graph.fitView();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (graph && !graph.destroyed) graph.destroy();
      graphRef.current = null;
    };
  }, [data, direction]);

  const handleFitView = useCallback(() => graphRef.current?.fitView(), []);
  const handleZoomIn = useCallback(() => {
    const g = graphRef.current;
    if (g) g.zoomTo(Math.min(g.getZoom() * 1.2, 4));
  }, []);
  const handleZoomOut = useCallback(() => {
    const g = graphRef.current;
    if (g) g.zoomTo(Math.max(g.getZoom() / 1.2, 0.1));
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%', background: '#F7F8FA' }} />

      {loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
          justifyContent: 'center', background: 'rgba(247,248,250,0.85)', zIndex: 10,
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              width: 40, height: 40, border: '3px solid #E8E8E8', borderTopColor: '#1677FF',
              borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px',
            }} />
            <div style={{ fontSize: 14, color: '#595959' }}>正在加载功能地图...</div>
          </div>
        </div>
      )}

      {/* 工具栏 */}
      <div style={{ position: 'absolute', top: 16, right: 16, display: 'flex', flexDirection: 'column', gap: 6, zIndex: 5 }}>
        <ToolButton onClick={handleZoomIn} title="放大">＋</ToolButton>
        <ToolButton onClick={handleZoomOut} title="缩小">－</ToolButton>
        <ToolButton onClick={handleFitView} title="适应屏幕">⊡</ToolButton>
      </div>

      {tooltip.visible && tooltip.nodeData && (
        <NodeTooltip nodeData={tooltip.nodeData} x={tooltip.x} y={tooltip.y} />
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};

const ToolButton: React.FC<{ onClick: () => void; title: string; children: React.ReactNode }> = ({ onClick, title, children }) => (
  <button
    onClick={onClick} title={title}
    style={{
      width: 32, height: 32, border: '1px solid #E8E8E8', borderRadius: 6,
      background: '#FFFFFF', cursor: 'pointer', display: 'flex', alignItems: 'center',
      justifyContent: 'center', color: '#595959', fontSize: 16,
      boxShadow: '0 2px 6px rgba(0,0,0,0.08)', transition: 'all 0.2s',
    }}
    onMouseEnter={e => { e.currentTarget.style.borderColor = '#1677FF'; e.currentTarget.style.color = '#1677FF'; }}
    onMouseLeave={e => { e.currentTarget.style.borderColor = '#E8E8E8'; e.currentTarget.style.color = '#595959'; }}
  >
    {children}
  </button>
);

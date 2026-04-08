/**
 * NodeTooltip - 节点悬浮提示组件
 * 设计风格：清爽专业风 - 白色卡片，阴影突出
 */

import React from 'react';
import type { NodeData } from '@antv/g6';
import { STATUS_COLORS, STATUS_TEXT_COLORS, PRIORITY_COLORS } from '../../types/mindmap';

interface NodeTooltipProps {
  nodeData: NodeData;
  x: number;
  y: number;
}

export const NodeTooltip: React.FC<NodeTooltipProps> = ({ nodeData, x, y }) => {
  const data = nodeData.data || {};
  const label = data.label as string || '';
  const status = data.status as string || '';
  const priority = data.priority as string || '';
  const owner = data.owner as string || '';
  const description = data.description as string || '';
  const iteration = data.iteration as string || '';
  const stage = data.stage as string || '';
  const docLink = data.docLink as string || '';
  const docText = data.docText as string || '';

  const statusColor = STATUS_COLORS[status] || '#D9D9D9';
  const statusTextColor = STATUS_TEXT_COLORS[status] || '#595959';
  const priorityColor = PRIORITY_COLORS[priority] || '#8C8C8C';

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        zIndex: 100,
        background: '#FFFFFF',
        border: '1px solid #E8E8E8',
        borderRadius: 8,
        boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
        padding: '12px 14px',
        minWidth: 200,
        maxWidth: 280,
        pointerEvents: 'none',
        fontSize: 13,
        lineHeight: '1.5',
      }}
    >
      {/* 标题 */}
      <div style={{ fontWeight: 600, fontSize: 14, color: '#1A1A2E', marginBottom: 8 }}>
        {label}
      </div>

      {/* 状态 + 优先级 */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
        {status && (
          <span style={{
            padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 500,
            background: statusColor, color: statusTextColor,
          }}>
            {status}
          </span>
        )}
        {priority && (
          <span style={{
            padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 500,
            background: priorityColor + '20', color: priorityColor,
            border: `1px solid ${priorityColor}40`,
          }}>
            {priority}
          </span>
        )}
      </div>

      {/* 描述 */}
      {description && (
        <div style={{ color: '#595959', fontSize: 12, marginBottom: 6, lineHeight: '1.6' }}>
          {description.length > 80 ? description.slice(0, 80) + '...' : description}
        </div>
      )}

      {/* 详细信息 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {owner && (
          <div style={{ display: 'flex', gap: 6 }}>
            <span style={{ color: '#8C8C8C', minWidth: 48, fontSize: 12 }}>负责人</span>
            <span style={{ color: '#1A1A2E', fontSize: 12 }}>{owner}</span>
          </div>
        )}
        {iteration && (
          <div style={{ display: 'flex', gap: 6 }}>
            <span style={{ color: '#8C8C8C', minWidth: 48, fontSize: 12 }}>迭代版本</span>
            <span style={{ color: '#1A1A2E', fontSize: 12 }}>{iteration}</span>
          </div>
        )}
        {stage && (
          <div style={{ display: 'flex', gap: 6 }}>
            <span style={{ color: '#8C8C8C', minWidth: 48, fontSize: 12 }}>阶段</span>
            <span style={{ color: '#1A1A2E', fontSize: 12 }}>{stage}</span>
          </div>
        )}
        {docLink && (
          <div style={{ marginTop: 4 }}>
            <span style={{
              fontSize: 11, color: '#1677FF',
              display: 'flex', alignItems: 'center', gap: 4,
            }}>
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M1 9L9 1M9 1H4M9 1v5" stroke="#1677FF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              {docText || '点击查看文档'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

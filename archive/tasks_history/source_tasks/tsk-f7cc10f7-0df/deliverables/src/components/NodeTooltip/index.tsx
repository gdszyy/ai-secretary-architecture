/**
 * NodeTooltip - 节点悬浮提示组件
 * XPBET 全球站功能地图管理系统
 *
 * 鼠标悬浮在功能节点或模块节点时，展示详细信息卡片。
 */

import React from 'react';
import { Tag } from 'antd';
import type { MindMapNode } from '../../services/transformer';
import { STATUS_COLOR_MAP, PRIORITY_COLOR_MAP } from '../../services/transformer';

interface NodeTooltipProps {
  node: MindMapNode;
  x: number;
  y: number;
}

/** 优先级标签颜色映射（Ant Design Tag 颜色） */
const PRIORITY_TAG_COLOR: Record<string, string> = {
  P0: 'red',
  P1: 'orange',
  P2: 'blue',
  P3: 'default',
};

export const NodeTooltip: React.FC<NodeTooltipProps> = ({ node, x, y }) => {
  const { data, label, type } = node;
  if (!data) return null;

  const priorityPrefix = data.priority?.slice(0, 2) ?? '';
  const statusColor = data.status ? (STATUS_COLOR_MAP[data.status] ?? '#D9D9D9') : '#D9D9D9';
  const priorityTagColor = PRIORITY_TAG_COLOR[priorityPrefix] ?? 'default';

  return (
    <div
      style={{
        position: 'fixed',
        left: x,
        top: y,
        zIndex: 1000,
        background: '#FFFFFF',
        border: '1px solid #E8E8E8',
        borderRadius: 8,
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.12)',
        padding: '12px 16px',
        maxWidth: 320,
        minWidth: 200,
        pointerEvents: 'none', // 不拦截鼠标事件
      }}
    >
      {/* 节点标题 */}
      <div
        style={{
          fontWeight: 600,
          fontSize: 14,
          color: '#262626',
          marginBottom: 8,
          borderBottom: `2px solid ${statusColor}`,
          paddingBottom: 6,
        }}
      >
        {label}
      </div>

      {/* 状态和优先级标签 */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
        {data.status && (
          <Tag
            color={statusColor}
            style={{ color: isLightColor(statusColor) ? '#333' : '#fff', border: 'none' }}
          >
            {data.status}
          </Tag>
        )}
        {data.priority && (
          <Tag color={priorityTagColor}>{data.priority}</Tag>
        )}
      </div>

      {/* 详细信息 */}
      <div style={{ fontSize: 12, color: '#595959', lineHeight: 1.6 }}>
        {data.owner && (
          <InfoRow label="负责人" value={data.owner} />
        )}
        {type === 'feature' && data.stage && (
          <InfoRow label="阶段" value={data.stage} />
        )}
        {type === 'feature' && data.iteration && (
          <InfoRow label="迭代版本" value={data.iteration} />
        )}
        {data.description && (
          <InfoRow
            label="说明"
            value={
              data.description.length > 80
                ? data.description.slice(0, 80) + '…'
                : data.description
            }
          />
        )}
        {type === 'feature' && data.docLink && (
          <div style={{ marginTop: 6 }}>
            <span style={{ color: '#8C8C8C' }}>文档: </span>
            <span style={{ color: '#1890FF' }}>双击节点打开 ↗</span>
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== 子组件 ====================

const InfoRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={{ display: 'flex', gap: 4, marginBottom: 2 }}>
    <span style={{ color: '#8C8C8C', flexShrink: 0 }}>{label}:</span>
    <span style={{ color: '#262626' }}>{value}</span>
  </div>
);

// ==================== 工具函数 ====================

function isLightColor(hexColor: string): boolean {
  const hex = hexColor.replace('#', '');
  if (hex.length !== 6) return true;
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq >= 128;
}

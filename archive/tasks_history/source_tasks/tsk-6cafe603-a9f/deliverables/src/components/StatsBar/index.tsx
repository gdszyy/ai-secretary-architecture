/**
 * StatsBar - 顶部统计栏组件
 * 设计风格：清爽专业风
 */

import React from 'react';
import type { MindMapRoot } from '../../types/mindmap';
import { STATUS_COLORS } from '../../types/mindmap';

interface StatsBarProps {
  data: MindMapRoot | null;
}

interface StatusCount {
  status: string;
  count: number;
  color: string;
}

function computeStats(data: MindMapRoot | null): { total: number; byStatus: StatusCount[] } {
  if (!data) return { total: 0, byStatus: [] };

  const counts: Record<string, number> = {};
  let total = 0;

  const traverse = (node: any) => {
    if (node.type === 'feature') {
      total++;
      const status = node.data?.status || '待规划';
      counts[status] = (counts[status] || 0) + 1;
    }
    node.children?.forEach(traverse);
  };
  traverse(data);

  const byStatus = Object.entries(counts)
    .map(([status, count]) => ({
      status,
      count,
      color: STATUS_COLORS[status] || '#D9D9D9',
    }))
    .sort((a, b) => b.count - a.count);

  return { total, byStatus };
}

export const StatsBar: React.FC<StatsBarProps> = ({ data }) => {
  const { total, byStatus } = computeStats(data);

  return (
    <div style={{
      height: 48,
      background: '#FFFFFF',
      borderBottom: '1px solid #F0F0F0',
      display: 'flex',
      alignItems: 'center',
      padding: '0 20px',
      gap: 20,
      flexShrink: 0,
      boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
    }}>
      {/* Logo + 标题 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginRight: 8 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 6,
          background: 'linear-gradient(135deg, #1677FF, #0958D9)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="3" fill="white"/>
            <path d="M8 2v2M8 12v2M2 8h2M12 8h2" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
            <path d="M4.2 4.2l1.4 1.4M10.4 10.4l1.4 1.4M4.2 11.8l1.4-1.4M10.4 5.6l1.4-1.4" stroke="white" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#1A1A2E', lineHeight: 1.2 }}>
            XPBET 功能地图
          </div>
          <div style={{ fontSize: 10, color: '#8C8C8C', lineHeight: 1.2 }}>
            全球站产品架构
          </div>
        </div>
      </div>

      {/* 分隔线 */}
      <div style={{ width: 1, height: 24, background: '#F0F0F0' }} />

      {/* 总计 */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <span style={{ fontSize: 20, fontWeight: 700, color: '#1677FF' }}>{total}</span>
        <span style={{ fontSize: 12, color: '#8C8C8C' }}>个功能点</span>
      </div>

      {/* 状态分布 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
        {/* 进度条 */}
        <div style={{
          flex: 1, height: 6, borderRadius: 3, background: '#F0F0F0',
          overflow: 'hidden', display: 'flex', maxWidth: 200,
        }}>
          {byStatus.map(({ status, count, color }) => (
            <div
              key={status}
              style={{
                width: `${(count / total) * 100}%`,
                background: color,
                transition: 'width 0.3s',
              }}
              title={`${status}: ${count}`}
            />
          ))}
        </div>

        {/* 状态标签 */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'nowrap', overflow: 'hidden' }}>
          {byStatus.slice(0, 5).map(({ status, count, color }) => (
            <div key={status} style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: color }} />
              <span style={{ fontSize: 11, color: '#595959', whiteSpace: 'nowrap' }}>
                {status} <strong style={{ color: '#1A1A2E' }}>{count}</strong>
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 右侧信息 */}
      <div style={{ marginLeft: 'auto', fontSize: 11, color: '#BFBFBF', flexShrink: 0 }}>
        数据来源：飞书多维表格
      </div>
    </div>
  );
};

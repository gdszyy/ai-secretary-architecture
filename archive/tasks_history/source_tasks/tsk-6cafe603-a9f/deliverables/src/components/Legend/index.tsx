/**
 * Legend - 图例组件
 * 设计风格：清爽专业风 - 底部浮动卡片
 */

import React, { useState } from 'react';
import { STATUS_COLORS, STATUS_TEXT_COLORS } from '../../types/mindmap';

const LEGEND_ITEMS = [
  { label: '完成', color: STATUS_COLORS['完成'], textColor: STATUS_TEXT_COLORS['完成'] },
  { label: '开发中', color: STATUS_COLORS['开发中'], textColor: STATUS_TEXT_COLORS['开发中'] },
  { label: '测试中', color: STATUS_COLORS['测试中'], textColor: STATUS_TEXT_COLORS['测试中'] },
  { label: '规划中', color: STATUS_COLORS['规划中'], textColor: STATUS_TEXT_COLORS['规划中'] },
  { label: '待规划', color: STATUS_COLORS['待规划'], textColor: STATUS_TEXT_COLORS['待规划'] },
  { label: '待技术评审', color: STATUS_COLORS['待技术评审'], textColor: STATUS_TEXT_COLORS['待技术评审'] },
  { label: '待需求评审', color: STATUS_COLORS['待需求评审'], textColor: STATUS_TEXT_COLORS['待需求评审'] },
];

export const Legend: React.FC = () => {
  const [visible, setVisible] = useState(true);

  if (!visible) {
    return (
      <button
        onClick={() => setVisible(true)}
        style={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          padding: '4px 10px',
          background: '#FFFFFF',
          border: '1px solid #E8E8E8',
          borderRadius: 6,
          fontSize: 12,
          color: '#595959',
          cursor: 'pointer',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          zIndex: 5,
        }}
      >
        图例
      </button>
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 16,
        left: 16,
        background: '#FFFFFF',
        border: '1px solid #E8E8E8',
        borderRadius: 8,
        padding: '10px 14px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        zIndex: 5,
      }}
    >
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 8,
      }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: '#8C8C8C', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          状态图例
        </span>
        <button
          onClick={() => setVisible(false)}
          style={{
            border: 'none', background: 'none', cursor: 'pointer',
            color: '#BFBFBF', fontSize: 14, padding: 0, lineHeight: 1,
          }}
        >
          ×
        </button>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxWidth: 280 }}>
        {LEGEND_ITEMS.map(({ label, color, textColor }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{
              width: 12, height: 12, borderRadius: 3,
              background: color, flexShrink: 0,
            }} />
            <span style={{ fontSize: 11, color: '#595959' }}>{label}</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid #F0F0F0' }}>
        <div style={{ fontSize: 11, color: '#8C8C8C', marginBottom: 4 }}>操作提示</div>
        <div style={{ fontSize: 11, color: '#BFBFBF', lineHeight: '1.6' }}>
          点击节点展开/收起 · 悬浮查看详情<br/>
          滚轮缩放 · 拖拽平移
        </div>
      </div>
    </div>
  );
};

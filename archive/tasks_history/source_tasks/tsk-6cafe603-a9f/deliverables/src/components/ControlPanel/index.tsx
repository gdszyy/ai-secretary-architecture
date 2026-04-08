/**
 * ControlPanel - 左侧控制面板组件
 * 设计风格：清爽专业风 - 白色侧边栏，分组清晰
 */

import React, { useState } from 'react';
import type { FilterOptions, StatusType } from '../../types/mindmap';
import {
  STATUS_COLORS,
  STATUS_TEXT_COLORS,
  ALL_STATUSES,
  ALL_PRIORITIES,
} from '../../types/mindmap';

interface ControlPanelProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  stages: string[];
  categories: string[];
  totalCount: number;
  filteredCount: number;
  direction: 'H' | 'V';
  onDirectionChange: (dir: 'H' | 'V') => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  filters,
  onFiltersChange,
  stages,
  categories,
  totalCount,
  filteredCount,
  direction,
  onDirectionChange,
}) => {
  const [collapsed, setCollapsed] = useState(false);

  const updateFilter = (key: keyof FilterOptions, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const toggleStatus = (status: StatusType) => {
    const current = filters.statuses || [];
    const next = current.includes(status)
      ? current.filter((s) => s !== status)
      : [...current, status];
    updateFilter('statuses', next);
  };

  const togglePriority = (priority: string) => {
    const current = filters.priorities || [];
    const next = current.includes(priority)
      ? current.filter((p) => p !== priority)
      : [...current, priority];
    updateFilter('priorities', next);
  };

  const clearFilters = () => {
    onFiltersChange({ keyword: '' });
  };

  const hasActiveFilters =
    filters.keyword ||
    (filters.statuses && filters.statuses.length > 0) ||
    (filters.priorities && filters.priorities.length > 0) ||
    (filters.stages && filters.stages.length > 0) ||
    filters.category;

  if (collapsed) {
    return (
      <div
        style={{
          width: 36,
          height: '100%',
          background: '#FFFFFF',
          borderRight: '1px solid #F0F0F0',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: 16,
          gap: 12,
          boxShadow: '2px 0 8px rgba(0,0,0,0.04)',
        }}
      >
        <button
          onClick={() => setCollapsed(false)}
          style={{
            width: 24, height: 24, border: 'none', background: 'none',
            cursor: 'pointer', color: '#8C8C8C', fontSize: 16, padding: 0,
          }}
          title="展开面板"
        >
          ›
        </button>
        {hasActiveFilters && (
          <div style={{
            width: 8, height: 8, borderRadius: '50%', background: '#1677FF',
          }} />
        )}
      </div>
    );
  }

  return (
    <div
      style={{
        width: 240,
        height: '100%',
        background: '#FFFFFF',
        borderRight: '1px solid #F0F0F0',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '2px 0 8px rgba(0,0,0,0.04)',
        overflow: 'hidden',
      }}
    >
      {/* 面板头部 */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid #F0F0F0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 14, color: '#1A1A2E' }}>筛选控制</div>
          <div style={{ fontSize: 11, color: '#8C8C8C', marginTop: 2 }}>
            显示 {filteredCount} / {totalCount} 个功能
          </div>
        </div>
        <button
          onClick={() => setCollapsed(true)}
          style={{
            width: 24, height: 24, border: 'none', background: 'none',
            cursor: 'pointer', color: '#8C8C8C', fontSize: 16, padding: 0,
          }}
          title="收起面板"
        >
          ‹
        </button>
      </div>

      {/* 可滚动内容区 */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px' }}>
        {/* 搜索框 */}
        <Section title="搜索">
          <input
            type="text"
            placeholder="搜索功能名称..."
            value={filters.keyword || ''}
            onChange={(e) => updateFilter('keyword', e.target.value)}
            style={{
              width: '100%',
              padding: '6px 10px',
              border: '1px solid #E8E8E8',
              borderRadius: 6,
              fontSize: 13,
              color: '#1A1A2E',
              outline: 'none',
              background: '#FAFAFA',
              boxSizing: 'border-box',
              transition: 'border-color 0.2s',
            }}
            onFocus={(e) => { e.target.style.borderColor = '#1677FF'; e.target.style.background = '#FFFFFF'; }}
            onBlur={(e) => { e.target.style.borderColor = '#E8E8E8'; e.target.style.background = '#FAFAFA'; }}
          />
        </Section>

        {/* 状态筛选 */}
        <Section title="状态">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {ALL_STATUSES.map((status) => {
              const active = (filters.statuses || []).includes(status);
              const color = STATUS_COLORS[status] || '#D9D9D9';
              const textColor = STATUS_TEXT_COLORS[status] || '#595959';
              return (
                <button
                  key={status}
                  onClick={() => toggleStatus(status)}
                  style={{
                    padding: '3px 8px',
                    borderRadius: 4,
                    border: `1px solid ${active ? color : '#E8E8E8'}`,
                    background: active ? color : '#FAFAFA',
                    color: active ? textColor : '#595959',
                    fontSize: 11,
                    cursor: 'pointer',
                    fontWeight: active ? 500 : 400,
                    transition: 'all 0.15s',
                  }}
                >
                  {status}
                </button>
              );
            })}
          </div>
        </Section>

        {/* 优先级筛选 */}
        <Section title="优先级">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {ALL_PRIORITIES.map((priority) => {
              const active = (filters.priorities || []).includes(priority);
              return (
                <button
                  key={priority}
                  onClick={() => togglePriority(priority)}
                  style={{
                    padding: '3px 8px',
                    borderRadius: 4,
                    border: `1px solid ${active ? '#1677FF' : '#E8E8E8'}`,
                    background: active ? '#E6F4FF' : '#FAFAFA',
                    color: active ? '#1677FF' : '#595959',
                    fontSize: 11,
                    cursor: 'pointer',
                    fontWeight: active ? 500 : 400,
                    transition: 'all 0.15s',
                  }}
                >
                  {priority}
                </button>
              );
            })}
          </div>
        </Section>

        {/* 分类筛选 */}
        {categories.length > 0 && (
          <Section title="分类">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <button
                onClick={() => updateFilter('category', '')}
                style={{
                  padding: '4px 8px', borderRadius: 4, textAlign: 'left',
                  border: `1px solid ${!filters.category ? '#1677FF' : '#E8E8E8'}`,
                  background: !filters.category ? '#E6F4FF' : '#FAFAFA',
                  color: !filters.category ? '#1677FF' : '#595959',
                  fontSize: 12, cursor: 'pointer', transition: 'all 0.15s',
                }}
              >
                全部分类
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => updateFilter('category', filters.category === cat ? '' : cat)}
                  style={{
                    padding: '4px 8px', borderRadius: 4, textAlign: 'left',
                    border: `1px solid ${filters.category === cat ? '#1677FF' : '#E8E8E8'}`,
                    background: filters.category === cat ? '#E6F4FF' : '#FAFAFA',
                    color: filters.category === cat ? '#1677FF' : '#595959',
                    fontSize: 12, cursor: 'pointer', transition: 'all 0.15s',
                    whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                  }}
                  title={cat}
                >
                  {cat}
                </button>
              ))}
            </div>
          </Section>
        )}

        {/* 阶段筛选 */}
        {stages.length > 0 && (
          <Section title="阶段">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {stages.map((stage) => {
                const active = (filters.stages || []).includes(stage);
                return (
                  <button
                    key={stage}
                    onClick={() => {
                      const current = filters.stages || [];
                      const next = current.includes(stage)
                        ? current.filter((s) => s !== stage)
                        : [...current, stage];
                      updateFilter('stages', next);
                    }}
                    style={{
                      padding: '3px 8px', borderRadius: 4,
                      border: `1px solid ${active ? '#722ED1' : '#E8E8E8'}`,
                      background: active ? '#F9F0FF' : '#FAFAFA',
                      color: active ? '#722ED1' : '#595959',
                      fontSize: 11, cursor: 'pointer', transition: 'all 0.15s',
                    }}
                  >
                    {stage}
                  </button>
                );
              })}
            </div>
          </Section>
        )}

        {/* 布局方向 */}
        <Section title="布局方向">
          <div style={{ display: 'flex', gap: 8 }}>
            {(['H', 'V'] as const).map((dir) => (
              <button
                key={dir}
                onClick={() => onDirectionChange(dir)}
                style={{
                  flex: 1, padding: '5px 0', borderRadius: 6,
                  border: `1px solid ${direction === dir ? '#1677FF' : '#E8E8E8'}`,
                  background: direction === dir ? '#E6F4FF' : '#FAFAFA',
                  color: direction === dir ? '#1677FF' : '#595959',
                  fontSize: 12, cursor: 'pointer', transition: 'all 0.15s',
                  fontWeight: direction === dir ? 500 : 400,
                }}
              >
                {dir === 'H' ? '水平' : '垂直'}
              </button>
            ))}
          </div>
        </Section>
      </div>

      {/* 底部清除按钮 */}
      {hasActiveFilters && (
        <div style={{ padding: '10px 16px', borderTop: '1px solid #F0F0F0', flexShrink: 0 }}>
          <button
            onClick={clearFilters}
            style={{
              width: '100%', padding: '6px 0', borderRadius: 6,
              border: '1px solid #FF4D4F', background: '#FFF1F0',
              color: '#FF4D4F', fontSize: 12, cursor: 'pointer',
              transition: 'all 0.15s', fontWeight: 500,
            }}
          >
            清除所有筛选
          </button>
        </div>
      )}
    </div>
  );
};

// 分组标题子组件
const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ marginBottom: 16 }}>
    <div style={{
      fontSize: 11, fontWeight: 600, color: '#8C8C8C',
      textTransform: 'uppercase', letterSpacing: '0.5px',
      marginBottom: 8,
    }}>
      {title}
    </div>
    {children}
  </div>
);

/**
 * Home - 主页面
 * 设计风格：清爽专业风 - 左侧控制面板 + 右侧画布 + 顶部统计栏
 */

import React, { useState, useMemo, useCallback } from 'react';
import type { NodeData } from '@antv/g6';
import type { MindMapRoot, FilterOptions } from '../types/mindmap';
import { filterMindMap, countNodes, extractStages } from '../lib/dataTransformer';
import { GraphCanvas } from '../components/GraphCanvas';
import { ControlPanel } from '../components/ControlPanel';
import { Legend } from '../components/Legend';
import { StatsBar } from '../components/StatsBar';

// 直接导入静态 JSON 数据
import rawData from '../data/mindmap_data.json';

export default function Home() {
  const originalData = rawData as MindMapRoot;

  const [filters, setFilters] = useState<FilterOptions>({});
  const [direction, setDirection] = useState<'H' | 'V'>('H');
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);

  // 过滤后的数据
  const filteredData = useMemo(() => {
    return filterMindMap(originalData, filters);
  }, [originalData, filters]);

  // 统计数量
  const totalCount = useMemo(() => countNodes(originalData, ['feature']), [originalData]);
  const filteredCount = useMemo(() => countNodes(filteredData, ['feature']), [filteredData]);

  // 提取阶段列表
  const stages = useMemo(() => extractStages(originalData), [originalData]);

  // 提取分类列表
  const categories = useMemo(() => {
    return (originalData.children || []).map((c: any) => c.label as string);
  }, [originalData]);

  const handleNodeClick = useCallback((nodeData: NodeData) => {
    setSelectedNode(nodeData);
  }, []);

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: '#F7F8FA',
      overflow: 'hidden',
      fontFamily: "'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif",
    }}>
      {/* 顶部统计栏 */}
      <StatsBar data={originalData} />

      {/* 主内容区 */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧控制面板 */}
        <ControlPanel
          filters={filters}
          onFiltersChange={setFilters}
          stages={stages}
          categories={categories}
          totalCount={totalCount}
          filteredCount={filteredCount}
          direction={direction}
          onDirectionChange={setDirection}
        />

        {/* 右侧画布区 */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          <GraphCanvas
            data={filteredData}
            direction={direction}
            onNodeClick={handleNodeClick}
          />
          <Legend />
        </div>
      </div>

      {/* 节点详情侧边栏（可选，点击节点后显示） */}
      {selectedNode && selectedNode.data?.nodeType === 'feature' && (
        <NodeDetailPanel
          nodeData={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
}

// 节点详情面板
const NodeDetailPanel: React.FC<{ nodeData: NodeData; onClose: () => void }> = ({
  nodeData,
  onClose,
}) => {
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
  const category = data.category as string || '';

  return (
    <div style={{
      position: 'fixed',
      right: 0,
      top: 48,
      bottom: 0,
      width: 320,
      background: '#FFFFFF',
      borderLeft: '1px solid #F0F0F0',
      boxShadow: '-4px 0 16px rgba(0,0,0,0.08)',
      zIndex: 50,
      display: 'flex',
      flexDirection: 'column',
      animation: 'slideIn 0.2s ease',
    }}>
      {/* 头部 */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid #F0F0F0',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: 12,
      }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: '#1A1A2E', lineHeight: '1.4' }}>
            {label}
          </div>
          {category && (
            <div style={{ fontSize: 11, color: '#8C8C8C', marginTop: 4 }}>{category}</div>
          )}
        </div>
        <button
          onClick={onClose}
          style={{
            width: 24, height: 24, border: 'none', background: 'none',
            cursor: 'pointer', color: '#BFBFBF', fontSize: 18, padding: 0,
            flexShrink: 0, lineHeight: 1,
          }}
        >
          ×
        </button>
      </div>

      {/* 内容 */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
        {/* 状态 + 优先级 */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
          {status && (
            <StatusBadge status={status} />
          )}
          {priority && (
            <span style={{
              padding: '3px 10px', borderRadius: 4, fontSize: 12,
              background: '#F0F5FF', color: '#2F54EB',
              border: '1px solid #ADC6FF',
            }}>
              {priority}
            </span>
          )}
        </div>

        {/* 描述 */}
        {description && (
          <DetailItem label="功能描述">
            <p style={{ margin: 0, color: '#595959', lineHeight: '1.7', fontSize: 13 }}>
              {description}
            </p>
          </DetailItem>
        )}

        {/* 基本信息 */}
        <DetailItem label="基本信息">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {owner && <InfoRow label="负责人" value={owner} />}
            {iteration && <InfoRow label="迭代版本" value={iteration} />}
            {stage && <InfoRow label="阶段" value={stage} />}
          </div>
        </DetailItem>

        {/* 文档链接 */}
        {docLink && (
          <DetailItem label="相关文档">
            <a
              href={docLink}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                color: '#1677FF', fontSize: 13, textDecoration: 'none',
                padding: '8px 12px', borderRadius: 6,
                background: '#E6F4FF', border: '1px solid #BAE0FF',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.background = '#BAE0FF'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.background = '#E6F4FF'; }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 12L12 2M12 2H7M12 2v5" stroke="#1677FF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              {docText || '查看文档'}
            </a>
          </DetailItem>
        )}
      </div>

      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
};

// 状态徽章
const STATUS_COLORS_MAP: Record<string, { bg: string; color: string }> = {
  '完成': { bg: '#F6FFED', color: '#52C41A' },
  '开发中': { bg: '#E6F4FF', color: '#1677FF' },
  '测试中': { bg: '#FFF7E6', color: '#FA8C16' },
  '规划中': { bg: '#F5F5F5', color: '#8C8C8C' },
  '待规划': { bg: '#FAFAFA', color: '#BFBFBF' },
  '待技术评审': { bg: '#F9F0FF', color: '#722ED1' },
  '待需求评审': { bg: '#FFF0F6', color: '#EB2F96' },
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colors = STATUS_COLORS_MAP[status] || { bg: '#F5F5F5', color: '#8C8C8C' };
  return (
    <span style={{
      padding: '3px 10px', borderRadius: 4, fontSize: 12, fontWeight: 500,
      background: colors.bg, color: colors.color,
      border: `1px solid ${colors.color}40`,
    }}>
      {status}
    </span>
  );
};

// 详情分组
const DetailItem: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div style={{ marginBottom: 16 }}>
    <div style={{
      fontSize: 11, fontWeight: 600, color: '#8C8C8C',
      textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8,
    }}>
      {label}
    </div>
    {children}
  </div>
);

// 信息行
const InfoRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
    <span style={{ color: '#8C8C8C', fontSize: 12, minWidth: 60, flexShrink: 0 }}>{label}</span>
    <span style={{ color: '#1A1A2E', fontSize: 12, flex: 1 }}>{value}</span>
  </div>
);

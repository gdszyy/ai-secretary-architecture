/**
 * App - 根组件
 * XPBET 全球站功能地图管理系统
 *
 * 组装 DataProvider、ControlPanel 和 GraphCanvas，
 * 构成完整的功能地图应用。
 */

import React, { useState, useCallback } from 'react';
import { ConfigProvider, Drawer, Descriptions, Tag, Typography, Alert } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { DataProvider, useData } from './context/DataContext';
import { GraphCanvas } from './components/GraphCanvas';
import { ControlPanel } from './components/ControlPanel';
import type { MindMapNode } from './services/transformer';
import type { FilterOptions } from './services/transformer';

const { Text, Link } = Typography;

// ==================== 环境配置 ====================
// 生产环境中，这些值应从环境变量或后端接口获取，不应硬编码在前端
const APP_CONFIG = {
  LARK_APP_ID: import.meta.env.VITE_LARK_APP_ID ?? '',
  LARK_APP_SECRET: import.meta.env.VITE_LARK_APP_SECRET ?? '',
};

// ==================== 主应用内容组件 ====================

const AppContent: React.FC = () => {
  const { filteredData, rawData, loading, error, filters, setFilters, fetchData } = useData();
  const [direction, setDirection] = useState<'H' | 'V'>('H');
  const [selectedNode, setSelectedNode] = useState<MindMapNode | null>(null);
  const [detailPanelOpen, setDetailPanelOpen] = useState(false);

  const handleNodeClick = useCallback((node: MindMapNode) => {
    if (node.type === 'feature' || node.type === 'module') {
      setSelectedNode(node);
      setDetailPanelOpen(true);
    }
  }, []);

  const handleNodeDoubleClick = useCallback((node: MindMapNode) => {
    // 双击跳转由 GraphCanvas 内部处理（openFeishuDocument）
    console.log('[App] 节点双击:', node.label);
  }, []);

  // 统计节点数量（仅统计 module 和 feature 节点）
  const countNodes = (root: MindMapNode | null): number => {
    if (!root) return 0;
    let count = 0;
    const traverse = (node: MindMapNode) => {
      if (node.type === 'module' || node.type === 'feature') count++;
      node.children?.forEach(traverse);
    };
    traverse(root);
    return count;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* 控制面板 */}
      <ControlPanel
        filters={filters}
        onFiltersChange={setFilters}
        direction={direction}
        onDirectionChange={setDirection}
        onRefresh={fetchData}
        loading={loading}
        filteredCount={countNodes(filteredData)}
        totalCount={countNodes(rawData)}
      />

      {/* 错误提示 */}
      {error && (
        <Alert
          message="数据加载失败"
          description={error}
          type="error"
          showIcon
          closable
          style={{ margin: '8px 16px' }}
        />
      )}

      {/* G6 画布 */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <GraphCanvas
          data={filteredData}
          loading={loading}
          direction={direction}
          onNodeClick={handleNodeClick}
          onNodeDoubleClick={handleNodeDoubleClick}
        />
      </div>

      {/* 节点详情侧边栏 */}
      <Drawer
        title={selectedNode?.label ?? '节点详情'}
        placement="right"
        width={400}
        open={detailPanelOpen}
        onClose={() => setDetailPanelOpen(false)}
      >
        {selectedNode && <NodeDetailContent node={selectedNode} />}
      </Drawer>
    </div>
  );
};

// ==================== 节点详情内容组件 ====================

const NodeDetailContent: React.FC<{ node: MindMapNode }> = ({ node }) => {
  const { data, type } = node;
  if (!data) return <Text type="secondary">暂无详细信息</Text>;

  return (
    <Descriptions column={1} bordered size="small">
      <Descriptions.Item label="节点类型">
        <Tag>{type === 'module' ? '模块' : '功能'}</Tag>
      </Descriptions.Item>
      {data.status && (
        <Descriptions.Item label="状态">
          <Tag color={getStatusTagColor(data.status)}>{data.status}</Tag>
        </Descriptions.Item>
      )}
      {data.priority && (
        <Descriptions.Item label="优先级">
          <Tag>{data.priority}</Tag>
        </Descriptions.Item>
      )}
      {data.owner && (
        <Descriptions.Item label="负责人">{data.owner}</Descriptions.Item>
      )}
      {type === 'feature' && data.stage && (
        <Descriptions.Item label="阶段">{data.stage}</Descriptions.Item>
      )}
      {type === 'feature' && data.iteration && (
        <Descriptions.Item label="迭代版本">{data.iteration}</Descriptions.Item>
      )}
      {data.description && (
        <Descriptions.Item label="说明">{data.description}</Descriptions.Item>
      )}
      {type === 'feature' && data.docLink && (
        <Descriptions.Item label="文档链接">
          <Link href={data.docLink} target="_blank">
            查看飞书文档 ↗
          </Link>
        </Descriptions.Item>
      )}
    </Descriptions>
  );
};

// ==================== 根组件 ====================

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <DataProvider
        appId={APP_CONFIG.LARK_APP_ID}
        appSecret={APP_CONFIG.LARK_APP_SECRET}
      >
        <AppContent />
      </DataProvider>
    </ConfigProvider>
  );
};

export default App;

// ==================== 工具函数 ====================

function getStatusTagColor(status: string): string {
  const colorMap: Record<string, string> = {
    完成: 'success',
    测试中: 'cyan',
    开发中: 'processing',
    待技术评审: 'purple',
    待需求评审: 'magenta',
    规划中: 'warning',
    待规划: 'default',
  };
  return colorMap[status] ?? 'default';
}

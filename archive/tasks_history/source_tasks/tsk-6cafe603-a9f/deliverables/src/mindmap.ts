/**
 * XPBET 功能地图数据类型定义
 * 设计风格：清爽专业风 - 浅色主题 + Ant Design 色彩体系
 */

export type NodeType = 'root' | 'category' | 'module' | 'feature';

export type StatusType =
  | '完成'
  | '测试中'
  | '开发中'
  | '待技术评审'
  | '待需求评审'
  | '规划中'
  | '待规划';

export type PriorityType =
  | 'P0-核心'
  | 'P0-1月'
  | 'P1-重要'
  | 'P1-3月'
  | 'P2-一般'
  | 'P2-6月'
  | 'P3-次要';

export interface NodeData {
  status?: StatusType;
  priority?: PriorityType;
  owner?: string;
  description?: string;
  stage?: string;
  iteration?: string;
  docLink?: string;
  docText?: string;
  category?: string;
  recordId?: string;
  simplifiedPlan?: string;
  prerequisites?: string;
}

export interface MindMapNode {
  id: string;
  label: string;
  type: NodeType;
  style?: {
    fill?: string;
    stroke?: string;
    lineWidth?: number;
  };
  data?: NodeData;
  children?: MindMapNode[];
}

export interface MindMapMeta {
  version: string;
  syncedAt: string;
  categoryCount?: number;
  moduleCount?: number;
  featureCount?: number;
  unassignedFeatures?: number;
  source?: string;
  baseId?: string;
  moduleTableId?: string;
  featureTableId?: string;
}

export interface MindMapRoot extends MindMapNode {
  type: 'root';
  _meta?: MindMapMeta;
}

export interface FilterOptions {
  keyword?: string;
  statuses?: StatusType[];
  priorities?: string[];
  stages?: string[];
  owner?: string;
  category?: string;
}

// 颜色常量
export const STATUS_COLORS: Record<string, string> = {
  '完成': '#52C41A',
  '测试中': '#FA8C16',
  '开发中': '#1677FF',
  '待技术评审': '#722ED1',
  '待需求评审': '#EB2F96',
  '规划中': '#8C8C8C',
  '待规划': '#D9D9D9',
};

export const STATUS_TEXT_COLORS: Record<string, string> = {
  '完成': '#ffffff',
  '测试中': '#ffffff',
  '开发中': '#ffffff',
  '待技术评审': '#ffffff',
  '待需求评审': '#ffffff',
  '规划中': '#ffffff',
  '待规划': '#595959',
};

export const PRIORITY_COLORS: Record<string, string> = {
  'P0-核心': '#F5222D',
  'P0-1月': '#F5222D',
  'P1-重要': '#FA8C16',
  'P1-3月': '#FA8C16',
  'P2-一般': '#1890FF',
  'P2-6月': '#1890FF',
  'P3-次要': '#8C8C8C',
};

export const CATEGORY_COLORS: Record<string, { fill: string; stroke: string }> = {
  'T0基础框架': { fill: '#E6F7FF', stroke: '#91D5FF' },
  'T1营销框架-获客': { fill: '#F6FFED', stroke: '#B7EB8F' },
  'T1营销框架-运营': { fill: '#FFF7E6', stroke: '#FFD591' },
  'T1营销框架-数据分析': { fill: '#F9F0FF', stroke: '#D3ADF7' },
  'T2商户管理': { fill: '#FFF0F6', stroke: '#FFADD2' },
};

export const ALL_STATUSES: StatusType[] = [
  '完成', '开发中', '测试中', '待技术评审', '待需求评审', '规划中', '待规划',
];

export const ALL_PRIORITIES = [
  'P0-核心', 'P0-1月', 'P1-重要', 'P1-3月', 'P2-一般', 'P2-6月', 'P3-次要',
];

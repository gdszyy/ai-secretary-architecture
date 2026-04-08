/**
 * 飞书 Bitable 数据 → G6 MindMap JSON 转换器
 * XPBET 全球站功能地图管理系统
 *
 * 将飞书多维表格的扁平记录数组转换为 AntV G6 TreeGraph 所需的嵌套树形结构
 * 数据结构规范来自: tsk-9103d528-937 数据结构设计文档
 */

import type { BitableRecord, ModuleFields, FeatureFields } from './feishuApi';

// ==================== 颜色映射常量 ====================

/** 状态 → 节点背景色映射（Ant Design 色彩规范） */
export const STATUS_COLOR_MAP: Record<string, string> = {
  完成: '#52C41A',       // Green-6
  测试中: '#13C2C2',     // Cyan-6
  开发中: '#1890FF',     // Blue-6
  待技术评审: '#722ED1', // Purple-6
  待需求评审: '#EB2F96', // Pink-6
  规划中: '#FAAD14',     // Gold-6
  待规划: '#D9D9D9',     // Gray-5
};

/** 优先级前缀 → 节点边框色映射 */
export const PRIORITY_COLOR_MAP: Record<string, string> = {
  P0: '#F5222D', // Red-6
  P1: '#FA8C16', // Orange-6
  P2: '#1890FF', // Blue-6
  P3: '#8C8C8C', // Gray-8
};

/** 分类 → 分类节点背景色映射 */
export const CATEGORY_COLOR_MAP: Record<string, string> = {
  T0基础框架: '#E6F7FF',
  'T1营销框架-获客': '#F6FFED',
  'T1营销框架-运营': '#FFFBE6',
  'T1营销框架-数据分析': '#FFF7E6',
  T2商户管理: '#F9F0FF',
};

/** 分类 → 分类节点边框色映射 */
export const CATEGORY_STROKE_MAP: Record<string, string> = {
  T0基础框架: '#91D5FF',
  'T1营销框架-获客': '#B7EB8F',
  'T1营销框架-运营': '#FFE58F',
  'T1营销框架-数据分析': '#FFD591',
  T2商户管理: '#D3ADF7',
};

// ==================== 类型定义 ====================

/** G6 节点样式 */
export interface NodeStyle {
  fill: string;
  stroke: string;
  lineWidth: number;
}

/** G6 节点业务数据 */
export interface NodeData {
  status?: string;
  priority?: string;
  owner?: string;
  description?: string;
  stage?: string;
  iteration?: string;
  docLink?: string;
  recordId?: string;
}

/** G6 MindMap 节点（与前序任务数据结构设计保持一致） */
export interface MindMapNode {
  id: string;
  label: string;
  type: 'root' | 'category' | 'module' | 'feature';
  style?: NodeStyle;
  data?: NodeData;
  children?: MindMapNode[];
}

/** MindMap 根节点（含元数据） */
export interface MindMapRoot extends MindMapNode {
  type: 'root';
  _meta: {
    version: string;
    syncedAt: string;
    moduleCount: number;
    featureCount: number;
    source: string;
    baseId: string;
  };
}

// ==================== 工具函数 ====================

/**
 * 根据状态值获取节点背景色
 */
function getStatusColor(status?: string): string {
  if (!status) return '#FFFFFF';
  return STATUS_COLOR_MAP[status] ?? '#FFFFFF';
}

/**
 * 根据优先级值获取节点边框色
 */
function getPriorityColor(priority?: string): string {
  if (!priority) return '#D9D9D9';
  const prefix = priority.slice(0, 2); // 取 P0/P1/P2/P3
  return PRIORITY_COLOR_MAP[prefix] ?? '#D9D9D9';
}

/**
 * 从飞书人员字段中提取负责人姓名
 */
function extractOwnerName(
  ownerField?: Array<{ id: string; name: string; en_name: string; email: string }>
): string {
  if (!ownerField || ownerField.length === 0) return '';
  return ownerField.map((u) => u.name || u.en_name).join(', ');
}

/**
 * 从飞书超链接字段中提取 URL
 */
function extractDocLink(
  linkField?: { link: string; text: string } | string
): string | undefined {
  if (!linkField) return undefined;
  if (typeof linkField === 'string') return linkField;
  return linkField.link || undefined;
}

/**
 * 从飞书单选字段中提取字符串值
 * 飞书单选字段可能是字符串或 { text: string } 对象
 */
function extractSingleSelect(field: unknown): string | undefined {
  if (!field) return undefined;
  if (typeof field === 'string') return field;
  if (typeof field === 'object' && field !== null && 'text' in field) {
    return (field as { text: string }).text;
  }
  return undefined;
}

// ==================== 核心转换函数 ====================

/**
 * 将飞书 Bitable 原始记录转换为 G6 MindMap 树形 JSON
 *
 * @param moduleRecords 模块表原始记录（21条）
 * @param featureRecords 功能表原始记录（114条）
 * @returns G6 MindMap 根节点（完整树形结构）
 */
export function transformToMindMap(
  moduleRecords: BitableRecord[],
  featureRecords: BitableRecord[]
): MindMapRoot {
  // ── Step 1: 按分类分组模块，构建 Category 节点 ──────────────────────
  const categoryMap = new Map<string, MindMapNode>();
  const moduleNodeMap = new Map<string, MindMapNode>();

  for (const record of moduleRecords) {
    const fields = record.fields as unknown as ModuleFields;
    const categoryName = extractSingleSelect(fields.分类) ?? '未分类';
    const status = extractSingleSelect(fields.状态);
    const priority = extractSingleSelect(fields.优先级);

    // 确保分类节点存在
    if (!categoryMap.has(categoryName)) {
      categoryMap.set(categoryName, {
        id: `cat_${categoryName}`,
        label: categoryName,
        type: 'category',
        style: {
          fill: CATEGORY_COLOR_MAP[categoryName] ?? '#F5F5F5',
          stroke: CATEGORY_STROKE_MAP[categoryName] ?? '#D9D9D9',
          lineWidth: 1,
        },
        children: [],
      });
    }

    // 构建模块节点
    const moduleNode: MindMapNode = {
      id: `mod_${record.record_id}`,
      label: String(fields.模块名称 ?? '未命名模块'),
      type: 'module',
      style: {
        fill: getStatusColor(status),
        stroke: getPriorityColor(priority),
        lineWidth: 2,
      },
      data: {
        status,
        priority,
        owner: extractOwnerName(fields.负责人 as ModuleFields['负责人']),
        description: String(fields.模块说明 ?? ''),
        recordId: record.record_id,
      },
      children: [],
    };

    // 挂载到分类节点
    categoryMap.get(categoryName)!.children!.push(moduleNode);
    // 建立 RecordID → 节点的快速索引
    moduleNodeMap.set(record.record_id, moduleNode);
  }

  // ── Step 2: 将功能节点挂载到对应模块下 ──────────────────────────────
  let unmountedFeatureCount = 0;

  for (const record of featureRecords) {
    const fields = record.fields as unknown as FeatureFields;
    const status = extractSingleSelect(fields.状态);
    const priority = extractSingleSelect(fields.功能优先级);

    // 解析所属模块关联字段
    const parentModuleRecordId =
      Array.isArray(fields.所属模块) && fields.所属模块.length > 0
        ? fields.所属模块[0].record_id
        : null;

    if (!parentModuleRecordId || !moduleNodeMap.has(parentModuleRecordId)) {
      console.warn(
        `[Transformer] 功能节点 "${fields.功能名称}" 找不到所属模块 (record_id: ${parentModuleRecordId})`
      );
      unmountedFeatureCount++;
      continue;
    }

    const featureNode: MindMapNode = {
      id: `feat_${record.record_id}`,
      label: String(fields.功能名称 ?? '未命名功能'),
      type: 'feature',
      style: {
        fill: getStatusColor(status),
        stroke: getPriorityColor(priority),
        lineWidth: 2,
      },
      data: {
        status,
        priority,
        owner: extractOwnerName(fields.负责人 as FeatureFields['负责人']),
        description: String(fields.功能说明 ?? ''),
        stage: extractSingleSelect(fields.阶段),
        iteration: extractSingleSelect(fields.迭代版本),
        docLink: extractDocLink(fields.文档链接 as FeatureFields['文档链接']),
        recordId: record.record_id,
      },
    };

    moduleNodeMap.get(parentModuleRecordId)!.children!.push(featureNode);
  }

  if (unmountedFeatureCount > 0) {
    console.warn(`[Transformer] 共 ${unmountedFeatureCount} 个功能节点未能挂载到模块`);
  }

  // ── Step 3: 组装根节点 ───────────────────────────────────────────────
  const root: MindMapRoot = {
    id: 'root',
    label: 'XPBET 全球站',
    type: 'root',
    style: {
      fill: '#001529',
      stroke: '#001529',
      lineWidth: 0,
    },
    _meta: {
      version: '1.0.0',
      syncedAt: new Date().toISOString(),
      moduleCount: moduleRecords.length,
      featureCount: featureRecords.length,
      source: 'feishu-bitable',
      baseId: 'CyDxbUQGGa3N2NsVanMjqdjxp6e',
    },
    children: Array.from(categoryMap.values()),
  };

  console.log(
    `[Transformer] 转换完成: ${categoryMap.size} 个分类, ${moduleRecords.length} 个模块, ${featureRecords.length} 个功能`
  );

  return root;
}

// ==================== 过滤函数 ====================

/** 过滤条件 */
export interface FilterOptions {
  /** 搜索关键字（模糊匹配节点 label） */
  keyword?: string;
  /** 状态过滤（多选，OR 逻辑） */
  statuses?: string[];
  /** 优先级过滤（多选，OR 逻辑） */
  priorities?: string[];
  /** 阶段过滤（多选，OR 逻辑） */
  stages?: string[];
  /** 负责人过滤 */
  owner?: string;
  /** 分类过滤（仅展示指定分类） */
  category?: string;
}

/**
 * 根据过滤条件筛选 MindMap 节点
 * 返回一个新的树形结构，不匹配的叶子节点被移除
 * 若某模块下所有功能都被过滤掉，则该模块节点也被移除
 *
 * @param root 完整的 MindMap 根节点
 * @param filters 过滤条件
 * @returns 过滤后的 MindMap 根节点（深拷贝）
 */
export function filterMindMap(
  root: MindMapRoot,
  filters: FilterOptions
): MindMapRoot {
  const hasFilters =
    (filters.keyword && filters.keyword.trim() !== '') ||
    (filters.statuses && filters.statuses.length > 0) ||
    (filters.priorities && filters.priorities.length > 0) ||
    (filters.stages && filters.stages.length > 0) ||
    filters.owner ||
    filters.category;

  // 无过滤条件时直接返回原始数据
  if (!hasFilters) return root;

  const keyword = filters.keyword?.trim().toLowerCase();

  function matchesNode(node: MindMapNode): boolean {
    // 关键字匹配
    if (keyword && !node.label.toLowerCase().includes(keyword)) {
      return false;
    }
    // 状态过滤（仅对 module 和 feature 节点生效）
    if (filters.statuses && filters.statuses.length > 0 && node.data?.status) {
      if (!filters.statuses.includes(node.data.status)) return false;
    }
    // 优先级过滤
    if (filters.priorities && filters.priorities.length > 0 && node.data?.priority) {
      const priorityPrefix = node.data.priority.slice(0, 2);
      if (!filters.priorities.some((p) => node.data!.priority!.startsWith(p))) return false;
    }
    // 阶段过滤（仅 feature 节点）
    if (filters.stages && filters.stages.length > 0 && node.type === 'feature') {
      if (!node.data?.stage || !filters.stages.includes(node.data.stage)) return false;
    }
    // 负责人过滤
    if (filters.owner && node.data?.owner) {
      if (!node.data.owner.includes(filters.owner)) return false;
    }
    return true;
  }

  function filterNode(node: MindMapNode): MindMapNode | null {
    if (node.type === 'feature') {
      return matchesNode(node) ? { ...node } : null;
    }

    if (node.type === 'module') {
      const filteredChildren = (node.children ?? [])
        .map(filterNode)
        .filter((n): n is MindMapNode => n !== null);

      if (filteredChildren.length === 0 && !matchesNode(node)) return null;
      return { ...node, children: filteredChildren };
    }

    if (node.type === 'category') {
      // 分类过滤
      if (filters.category && node.label !== filters.category) return null;

      const filteredChildren = (node.children ?? [])
        .map(filterNode)
        .filter((n): n is MindMapNode => n !== null);

      if (filteredChildren.length === 0) return null;
      return { ...node, children: filteredChildren };
    }

    // root 节点
    const filteredChildren = (node.children ?? [])
      .map(filterNode)
      .filter((n): n is MindMapNode => n !== null);

    return { ...node, children: filteredChildren } as MindMapRoot;
  }

  return filterNode(root) as MindMapRoot ?? { ...root, children: [] };
}

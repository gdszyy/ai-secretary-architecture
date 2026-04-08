/**
 * dataTransformer.ts - 数据转换工具
 * XPBET 全球站功能地图管理系统
 *
 * 功能：
 * 1. transformToMindMap()  - 将飞书 Bitable API 返回的扁平记录转换为 G6 MindMap 嵌套树形结构
 * 2. transformToG6Data()   - 将树形 MindMap 数据转换为 G6 v5 所需的 nodes + edges 格式
 * 3. filterMindMap()       - 根据过滤条件筛选 MindMap 节点
 * 4. countNodes()          - 统计树形结构中的节点数量
 * 5. extractStages()       - 提取所有唯一阶段值
 * 6. extractOwners()       - 提取所有唯一负责人
 *
 * 数据结构规范来自: tsk-9103d528-937 数据结构设计文档 v2.0
 */

import type { MindMapNode, MindMapRoot, FilterOptions } from '../types/mindmap';
import type { GraphData } from '@antv/g6';
import type { BitableRecord, ModuleFields, FeatureFields } from '../services/biTableService';

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

/** 分类排序（与飞书多维表格中的分类顺序保持一致） */
const CATEGORY_ORDER = [
  'T0基础框架',
  'T1营销框架-获客',
  'T1营销框架-运营',
  'T1营销框架-数据分析',
  'T2商户管理',
];

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

/**
 * 从飞书人员字段中提取负责人姓名
 *
 * 兼容两种格式：
 * - 模块表格式：[{ name: "Yark", ... }]（数组）
 * - 功能表格式：{ users: [{ name: "Yark", ... }] }（含 users 键的对象）
 */
function extractOwnerName(ownerField: unknown): string {
  if (!ownerField) return '';

  // 数组格式（模块表）
  if (Array.isArray(ownerField)) {
    return ownerField
      .map((u: { name?: string; en_name?: string }) => u.name || u.en_name || '')
      .filter(Boolean)
      .join(', ');
  }

  // { users: [...] } 格式（功能表）
  if (
    typeof ownerField === 'object' &&
    ownerField !== null &&
    'users' in ownerField
  ) {
    const users = (ownerField as { users: Array<{ name?: string; en_name?: string }> }).users;
    if (Array.isArray(users)) {
      return users
        .map((u) => u.name || u.en_name || '')
        .filter(Boolean)
        .join(', ');
    }
  }

  return '';
}

/**
 * 从飞书超链接字段中提取 URL 和显示文本
 */
function extractDocLink(linkField: unknown): { link?: string; text?: string } {
  if (!linkField) return {};
  if (typeof linkField === 'string') return { link: linkField };
  if (typeof linkField === 'object' && linkField !== null) {
    const obj = linkField as { link?: string; text?: string; url?: string };
    return {
      link: obj.link || obj.url,
      text: obj.text,
    };
  }
  return {};
}

/**
 * 从飞书关联字段中提取父级模块的 RecordID
 *
 * 兼容两种格式：
 * - 新格式：[{ record_ids: ["recXXX"], table_id: "...", text: "..." }]
 * - 旧格式：[{ record_id: "recXXX", table_id: "..." }]
 */
function extractParentModuleId(linkedField: unknown): string | null {
  if (!Array.isArray(linkedField) || linkedField.length === 0) return null;

  const first = linkedField[0] as {
    record_id?: string;
    record_ids?: string[];
    table_id?: string;
  };

  // 优先使用新格式 record_ids
  if (Array.isArray(first.record_ids) && first.record_ids.length > 0) {
    return first.record_ids[0];
  }

  // 兼容旧格式 record_id
  if (first.record_id) {
    return first.record_id;
  }

  return null;
}

// ==================== 核心转换函数 ====================

/**
 * 将飞书 Bitable 原始记录转换为 G6 MindMap 嵌套树形 JSON
 *
 * 转换流程：
 * 1. 遍历模块记录，按分类分组，构建 Category 节点和 Module 节点
 * 2. 遍历功能记录，解析所属模块关联字段，将功能节点挂载到对应模块下
 * 3. 按预定顺序排列分类节点，组装根节点
 *
 * @param moduleRecords 模块表原始记录（来自 fetchModuleRecords）
 * @param featureRecords 功能表原始记录（来自 fetchFeatureRecords）
 * @returns G6 MindMap 根节点（完整嵌套树形结构）
 */
export function transformToMindMap(
  moduleRecords: BitableRecord[],
  featureRecords: BitableRecord[]
): MindMapRoot {
  // ── Step 1: 按分类分组模块，构建 Category 节点和 Module 节点 ──────────
  const categoryMap = new Map<string, MindMapNode>();
  const moduleNodeMap = new Map<string, MindMapNode>();

  for (const record of moduleRecords) {
    const fields = record.fields as unknown as ModuleFields;
    const categoryName = extractSingleSelect(fields.分类) ?? '未分类';
    const status = extractSingleSelect(fields.状态);
    const priority = extractSingleSelect(fields.优先级);

    // 确保分类节点存在（首次遇到该分类时创建）
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
        data: {
          category: categoryName,
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
        status: status as MindMapNode['data'] extends undefined ? never : NonNullable<MindMapNode['data']>['status'],
        priority: priority as NonNullable<MindMapNode['data']>['priority'],
        owner: extractOwnerName(fields.负责人),
        description: String(fields.模块说明 ?? ''),
        category: categoryName,
        recordId: record.record_id,
      },
      children: [],
    };

    // 挂载到分类节点
    categoryMap.get(categoryName)!.children!.push(moduleNode);
    // 建立 RecordID → 节点的快速索引（用于功能节点挂载）
    moduleNodeMap.set(record.record_id, moduleNode);
  }

  // ── Step 2: 将功能节点挂载到对应模块下 ──────────────────────────────
  let unmountedFeatureCount = 0;

  for (const record of featureRecords) {
    const fields = record.fields as unknown as FeatureFields;
    const status = extractSingleSelect(fields.状态);
    const priority = extractSingleSelect(fields.功能优先级);

    // 解析所属模块关联字段（兼容新旧两种格式）
    const parentModuleRecordId = extractParentModuleId(fields.所属模块);

    if (!parentModuleRecordId || !moduleNodeMap.has(parentModuleRecordId)) {
      console.warn(
        `[Transformer] 功能节点 "${fields.功能名称}" 找不到所属模块 (record_id: ${parentModuleRecordId})`
      );
      unmountedFeatureCount++;
      continue;
    }

    const { link: docLink, text: docText } = extractDocLink(fields.文档链接);

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
        status: status as NonNullable<MindMapNode['data']>['status'],
        priority: priority as NonNullable<MindMapNode['data']>['priority'],
        owner: extractOwnerName(fields.负责人),
        description: String(fields.功能说明 ?? ''),
        stage: extractSingleSelect(fields.阶段),
        iteration: extractSingleSelect(fields.迭代版本),
        docLink,
        docText,
        simplifiedPlan: String(fields.简化方案 ?? ''),
        prerequisites: String(fields.前置资源 ?? ''),
        recordId: record.record_id,
      },
    };

    moduleNodeMap.get(parentModuleRecordId)!.children!.push(featureNode);
  }

  if (unmountedFeatureCount > 0) {
    console.warn(`[Transformer] 共 ${unmountedFeatureCount} 个功能节点未能挂载到模块`);
  }

  // ── Step 3: 按预定顺序排列分类节点，组装根节点 ──────────────────────
  const orderedCategories: MindMapNode[] = [];
  for (const catName of CATEGORY_ORDER) {
    if (categoryMap.has(catName)) {
      orderedCategories.push(categoryMap.get(catName)!);
    }
  }
  // 追加未在预定顺序中的分类（容错处理）
  for (const [catName, catNode] of categoryMap.entries()) {
    if (!CATEGORY_ORDER.includes(catName)) {
      orderedCategories.push(catNode);
    }
  }

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
      version: '2.0.0',
      syncedAt: new Date().toISOString(),
      categoryCount: categoryMap.size,
      moduleCount: moduleRecords.length,
      featureCount: featureRecords.length,
      unassignedFeatures: unmountedFeatureCount,
      source: 'feishu-bitable',
      baseId: 'BgjjbdZiJanHTpsboAzj9Gv7p6b',
      moduleTableId: 'tblb9Owa8P4AhVEH',
      featureTableId: 'tbluOwbl2PKxIiEz',
    },
    children: orderedCategories,
  };

  console.log(
    `[Transformer] 转换完成: ${categoryMap.size} 个分类, ${moduleRecords.length} 个模块, ${featureRecords.length} 个功能 (未挂载: ${unmountedFeatureCount})`
  );

  return root;
}

// ==================== G6 格式转换 ====================

/**
 * 将树形 MindMap 数据转换为 G6 v5 的 GraphData 格式
 * G6 v5 使用 nodes + edges 格式，NodeData.children 字段存储子节点ID数组
 */
export function transformToG6Data(root: MindMapRoot): GraphData {
  const nodes: NonNullable<GraphData['nodes']> = [];
  const edges: NonNullable<GraphData['edges']> = [];

  function traverse(node: MindMapNode, parentId?: string) {
    // 模块节点默认折叠（隐藏功能层，提升初始渲染性能）
    const isCollapsed = node.type === 'module';

    // 添加节点
    nodes.push({
      id: node.id,
      data: {
        label: node.label,
        nodeType: node.type,
        status: node.data?.status,
        priority: node.data?.priority,
        owner: node.data?.owner,
        description: node.data?.description,
        stage: node.data?.stage,
        iteration: node.data?.iteration,
        docLink: node.data?.docLink,
        docText: node.data?.docText,
        category: node.data?.category,
        recordId: node.data?.recordId,
        simplifiedPlan: node.data?.simplifiedPlan,
        prerequisites: node.data?.prerequisites,
        fill: node.style?.fill,
        stroke: node.style?.stroke,
        lineWidth: node.style?.lineWidth,
      },
      style: isCollapsed ? { collapsed: true } : undefined,
      // children 字段存储子节点ID，G6 v5 用于构建树形结构
      children: node.children?.map((c) => c.id),
    });

    // 添加边（父→子）
    if (parentId) {
      edges.push({
        id: `edge_${parentId}_${node.id}`,
        source: parentId,
        target: node.id,
      });
    }

    // 递归处理子节点
    if (node.children) {
      for (const child of node.children) {
        traverse(child, node.id);
      }
    }
  }

  traverse(root);

  return { nodes, edges };
}

// ==================== 过滤函数 ====================

/**
 * 根据过滤条件筛选 MindMap 节点（在树形结构上进行）
 * 返回过滤后的新树形结构（深拷贝，不修改原始数据）
 */
export function filterMindMap(root: MindMapRoot, filters: FilterOptions): MindMapRoot {
  const hasFilters =
    (filters.keyword && filters.keyword.trim() !== '') ||
    (filters.statuses && filters.statuses.length > 0) ||
    (filters.priorities && filters.priorities.length > 0) ||
    (filters.stages && filters.stages.length > 0) ||
    filters.owner ||
    filters.category;

  if (!hasFilters) return root;

  const keyword = filters.keyword?.trim().toLowerCase();

  function matchesNode(node: MindMapNode): boolean {
    if (keyword && !node.label.toLowerCase().includes(keyword)) {
      return false;
    }
    if (filters.statuses && filters.statuses.length > 0 && node.data?.status) {
      if (!filters.statuses.includes(node.data.status)) return false;
    }
    if (filters.priorities && filters.priorities.length > 0 && node.data?.priority) {
      if (!filters.priorities.some((p) => node.data!.priority!.startsWith(p.slice(0, 2)))) return false;
    }
    if (filters.stages && filters.stages.length > 0 && node.type === 'feature') {
      if (!node.data?.stage || !filters.stages.includes(node.data.stage)) return false;
    }
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

  return (filterNode(root) as MindMapRoot) ?? { ...root, children: [] };
}

// ==================== 统计工具函数 ====================

/**
 * 统计树形结构中指定类型的节点数量
 */
export function countNodes(
  root: MindMapNode | null,
  types: string[] = ['module', 'feature']
): number {
  if (!root) return 0;
  let count = 0;
  const traverse = (node: MindMapNode) => {
    if (types.includes(node.type)) count++;
    node.children?.forEach(traverse);
  };
  traverse(root);
  return count;
}

/**
 * 提取树形结构中所有唯一的阶段值
 */
export function extractStages(root: MindMapNode): string[] {
  const stages = new Set<string>();
  const traverse = (node: MindMapNode) => {
    if (node.type === 'feature' && node.data?.stage) {
      stages.add(node.data.stage);
    }
    node.children?.forEach(traverse);
  };
  traverse(root);
  return Array.from(stages).sort();
}

/**
 * 提取树形结构中所有唯一的负责人
 */
export function extractOwners(root: MindMapNode): string[] {
  const owners = new Set<string>();
  const traverse = (node: MindMapNode) => {
    if (node.data?.owner) {
      // 支持多个负责人（逗号分隔）
      node.data.owner.split(',').forEach((o) => {
        const trimmed = o.trim();
        if (trimmed) owners.add(trimmed);
      });
    }
    node.children?.forEach(traverse);
  };
  traverse(root);
  return Array.from(owners).sort();
}

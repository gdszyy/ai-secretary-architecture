/**
 * 数据转换工具 - 将树形 MindMap 数据转换为 G6 v5 所需的 nodes + edges 格式
 * 设计风格：清爽专业风
 */

import type { MindMapNode, MindMapRoot, FilterOptions } from '../types/mindmap';
import type { GraphData } from '@antv/g6';

/**
 * 将树形 MindMap 数据转换为 G6 v5 的 GraphData 格式
 * G6 v5 使用 nodes + edges 格式，NodeData.children 字段存储子节点ID数组
 */
export function transformToG6Data(root: MindMapRoot): GraphData {
  const nodes: NonNullable<GraphData['nodes']> = [];
  const edges: NonNullable<GraphData['edges']> = [];

  function traverse(node: MindMapNode, parentId?: string) {
    // 模块节点默认折叠（隐藏功能层）
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
        fill: node.style?.fill,
        stroke: node.style?.stroke,
        lineWidth: node.style?.lineWidth,
      },
      style: isCollapsed ? { collapsed: true } : undefined,
      // children 字段存储子节点ID，G6 v5 用于构建树形结构
      children: node.children?.map((c) => c.id),
    });

    // 添加边（父->子）
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

/**
 * 根据过滤条件筛选 MindMap 节点（在树形结构上进行）
 * 返回过滤后的新树形结构
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

/**
 * 统计树形结构中的节点数量
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
      owners.add(node.data.owner);
    }
    node.children?.forEach(traverse);
  };
  traverse(root);
  return Array.from(owners).sort();
}

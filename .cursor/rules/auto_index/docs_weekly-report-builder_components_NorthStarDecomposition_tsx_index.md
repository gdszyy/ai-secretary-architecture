# docs/weekly-report-builder/components/NorthStarDecomposition.tsx 函数索引

> 自动生成于 2026-04-22 | 总行数: 868 | 函数数: 10 | 语言: typescript
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

**巨型函数警告**: 本文件包含 1 个超过 200 行的函数，建议优先通过 `@section` 标记进行内部导航。

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| calculateLayout | function | L197 | L212 | 16 | `calculateLayout(node: DecompositionNode, level: number = 0)` |
| getSubtreeHeight | function | L213 | L225 | 13 | `getSubtreeHeight(node: LayoutNode)` |
| assignYCoordinates | function | L226 | L242 | 17 | `assignYCoordinates(node: LayoutNode, startY: number)` |
| collectNodes | function | L243 | L255 | 13 | `collectNodes(node: LayoutNode)` |
| collectEdges | function | L256 | L269 | 14 | `collectEdges(node: LayoutNode)` |
| getEdgeWidth | function | L270 | L289 | 20 | `getEdgeWidth(child: LayoutNode, parent: LayoutNode)` |
| NodeTooltip | function | L290 | L418 | 129 | `NodeTooltip({ node, visible, x, y, containerRef }: TooltipProps)` |
| TreeNode | function | L419 | L508 | 90 | `TreeNode({ node, onHover, onDrillDown }: TreeNodeProps)` |
| TreeEdge | function | L509 | L555 | 47 | `TreeEdge({ parent, child }: TreeEdgeProps)` |
| NorthStarDecomposition | function | L556 | L869 | **314** | `NorthStarDecomposition({ data, onDrillDown, className = '' }: NorthStarDecompositionProps)` |

## 巨型函数内部节点 (@section 标记)

### NorthStarDecomposition (L556-L869, 314行)

> **缺少 @section 标记**：此巨型函数内部没有节点标记，建议添加以提升导航精度。

## 其他 @section 标记

| 节点标记 | 行号 | 说明 |
|----------|------|------|
| `@section:north_star_decomposition` | L1 | 北极星因子分解图组件 |

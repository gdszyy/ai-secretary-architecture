# weekly-report-builder 模块规范

## 模块定位
`weekly-report-builder/` 目录存放周报构建器的前端组件代码，主要包含基于 React 和 TailwindCSS 的数据可视化组件。
`docs/weekly-report-builder/` 目录存放该模块的设计文档和组件库说明。

## 核心设计决策
**组件库**：基于 React、Recharts 和 TailwindCSS 构建。
**设计风格**：采用深色模式（Dark Mode）为主，强调数据可视化和科技感。
**组件分类**：
- `components/`：基础组件和初版设计。
- `components-restyled/`：重构和样式优化后的组件。

## 关键组件索引
请参考自动生成的函数索引获取组件的详细签名和内部节点映射：
- [ConversionFunnel.tsx](auto_index/weekly-report-builder_components-restyled_ConversionFunnel_tsx_index.md)
- [EcosystemHealthMap.tsx](auto_index/weekly-report-builder_components-restyled_EcosystemHealthMap_tsx_index.md)
- [HealthRadarChart.tsx](auto_index/weekly-report-builder_components-restyled_HealthRadarChart_tsx_index.md)
- [MilestoneCardList.tsx](auto_index/weekly-report-builder_components-restyled_MilestoneCardList_tsx_index.md)
- [StageProgressBar.tsx](auto_index/weekly-report-builder_components-restyled_StageProgressBar_tsx_index.md)
- [TrendMatrixGrid.tsx](auto_index/weekly-report-builder_components-restyled_TrendMatrixGrid_tsx_index.md)
- [UnitEconomicsCard.tsx](auto_index/weekly-report-builder_components-restyled_UnitEconomicsCard_tsx_index.md)
- [UserSegmentationBubble.tsx](auto_index/weekly-report-builder_components-restyled_UserSegmentationBubble_tsx_index.md)

## 禁止行为
- 禁止在组件中硬编码业务数据，必须通过 props 传入。
- 禁止直接修改 `components/` 下的旧版组件，应优先维护 `components-restyled/` 下的新版组件。

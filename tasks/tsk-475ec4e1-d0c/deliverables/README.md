# xpbet-frontend-components

**xpbet-frontend-components** 是从 `project-management-ai-secretary` 中拆分出的前端与可视化代码仓库，用于集中存放 XPBET 相关的 UI 规范、HTML 原型、React/TypeScript 历史实现与任务来源映射。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `docs/design/` | 设计系统与产品界面规范。 |
| `docs/specs/` | 从历史任务提炼出的交互规范、CMS 配置说明与数据模型。 |
| `src/prototypes/` | HTML 原型与静态模板，包括 Kanban、CMS、Homepage、App Prototype。 |
| `src/historical/` | 历史 React/TS 代码交付物，按来源任务分目录保存。 |
| `archive/task-deliverables/` | 任务级原始交付物归档，便于追溯来源。 |

## 使用约定

本仓库优先服务于 **前端重构、组件提炼、原型演进与交互规范整理**。`src/historical/` 中的代码保留原任务上下文，后续若要进行工程化升级，建议在其基础上逐步抽取公共组件，而不是直接将所有历史实现视为生产级单一事实来源。

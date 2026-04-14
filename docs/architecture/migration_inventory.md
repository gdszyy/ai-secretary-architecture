# 仓库拆分迁移清单

## 迁入本仓库的核心内容

| 类别 | 来源路径 | 去向 |
| --- | --- | --- |
| 核心文档 | 根目录 `README.md` `CORE_PHILOSOPHY.md` `IMPLEMENTATION_PLAN.md` `SOP.md` | 根目录与系统级入口文档 |
| 模块一文档 | `docs/module1_kanban/` | `docs/module1_kanban/` |
| 模块二文档 | `docs/module2_buffer/` | `docs/module2_buffer/` |
| 模块三文档 | `docs/module3_info_sources/` | `docs/module3_info_sources/` |
| 架构辅助文档 | `docs/architecture/` 与项目级说明文档 | `docs/` |
| 历史任务 | `tasks/` | `archive/tasks_history/source_tasks/` |

## 拆分后的边界

| 目标仓库 | 承载内容 | 不再保留在本仓库主上下文中的内容 |
| --- | --- | --- |
| `ai-secretary-architecture` | 核心架构、SOP、模块文档、历史归档 | 大量前端代码与通用技能定义 |
| `xpbet-frontend-components` | 设计规范、HTML 原型、React/TS 代码 | 系统级架构主文档 |
| `manus-lark-skills` | 通用 Manus/Lark 技能 | XPBET 业务设计与项目任务历史 |

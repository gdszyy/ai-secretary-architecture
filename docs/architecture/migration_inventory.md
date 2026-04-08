# ai-secretary-architecture 迁移清单

**作者**: Manus AI  
**日期**: 2026-04-08

## 1. 迁移范围总览

本次迁移从 `gdszyy/project-management-ai-secretary` 中抽取与 AI 秘书系统核心架构直接相关、且具有长期复用价值的文档，整理进入 `gdszyy/ai-secretary-architecture`。迁移目标是形成一个高信噪比、低上下文污染的架构主仓库。

## 2. 已迁移到仓库根目录的核心文档

| 源路径 | 目标路径 | 说明 |
|------|------|------|
| `README.md` | `README.md` | 重写为架构仓库入口说明，并补充阅读边界 |
| `CORE_PHILOSOPHY.md` | `CORE_PHILOSOPHY.md` | 保留核心设计哲学 |
| `IMPLEMENTATION_PLAN.md` | `IMPLEMENTATION_PLAN.md` | 保留实施路线图 |
| `SOP.md` | `SOP.md` | 保留全局 SOP |
| `SKILL_FEASIBILITY_REPORT.md` | `SKILL_FEASIBILITY_REPORT.md` | 保留 Skill 化可行性分析 |

## 3. 已迁移到 docs/ 的正式文档

| 类别 | 迁移内容 | 目标目录 |
|------|------|------|
| 模块一 | `docs/module1_kanban/*.md` | `docs/module1_kanban/` |
| 模块二 | `docs/module2_buffer/*.md` | `docs/module2_buffer/` |
| 模块三 | `docs/module3_info_sources/info_source_master_plan.md` | `docs/module3_info_sources/` |
| 模块三补充 | `tasks/tsk-2beb54e9-462/deliverables/info_source_research.md` | `docs/module3_info_sources/` |
| 模块三补充 | `tasks/tsk-41c824dc-a53/deliverables/info_source_integration_plan.md` | `docs/module3_info_sources/` |
| 架构评估 | `docs/architecture/repository_split_assessment.md` | `docs/architecture/` |
| 架构补充 | `tasks/tsk-b8220b1e-d81/deliverables/module_comparison_report.md` | `docs/architecture/` |
| 架构补充 | `tasks/tsk-b8220b1e-d81/deliverables/version_planning.md` | `docs/architecture/` |
| 架构补充 | `tasks/tsk-c87fc05b-5af/deliverables/xpbet_bitable_structure_design.md` | `docs/architecture/` |
| 项目级资料 | `docs/project-overview.md` | `docs/project/` |
| 项目级资料 | `docs/project-kickoff.md` | `docs/project/` |
| 项目级资料 | `docs/lark-doc-creation-spec.md` | `docs/project/` |

## 4. 已归档到 archive/tasks_history/ 的历史任务

以下任务目录已按“保留最终 Markdown、排除实现代码与原始数据”的原则归档：

| 任务 ID | 归档内容 | 归档说明 |
|------|------|------|
| `tsk-c67f7251-d40` | `README.md`、`review.md`、`deliverables/*.md` | 模块一历史来源 |
| `tsk-9be3bdb3-7dc` | `README.md`、`review.md`、`deliverables/*.md` | 模块二历史来源 |
| `tsk-2beb54e9-462` | `README.md`、`review.md`、`deliverables/*.md` | 模块三调研来源 |
| `tsk-41c824dc-a53` | `README.md`、`review.md`、`deliverables/*.md` | 模块三集成规划来源 |
| `tsk-b8220b1e-d81` | `README.md`、`deliverables/*.md` | 版本与模块边界来源 |
| `tsk-c87fc05b-5af` | `README.md`、`deliverables/*.md` | 多维表结构设计来源 |
| `tsk-f33ad9af-54f` | `README.md`、`deliverables/*.md` | 功能地图管理手册，保留为历史参考 |
| `tsk-9103d528-937` | `README.md`、`deliverables/*.md` | 仅保留 Markdown 设计文档，排除大文件数据 |

## 5. 明确未迁入主上下文的内容

| 内容类型 | 典型来源 | 原因 |
|------|------|------|
| React / TypeScript 前端实现 | `tsk-6cafe603-a9f`、`tsk-f7cc10f7-0df`、`tsk-b9e8ecd5-4f3` | 属于前端仓库候选内容，不应污染架构仓库主上下文 |
| 前端静态模板与可视化页面 | `kanban/` | 属于实现层与展示层，不属于架构主仓库 |
| 大型原始 JSON 数据 | `tsk-9103d528-937/deliverables/*.json` | 数据体量大、噪音高，不适合作为架构上下文 |
| 脚本与中间处理文件 | `tasks/**/*.py`、`tasks/**/*.ts`、`tasks/**/*.tsx` | 过程性强、复用性低 |

## 6. 归档读取说明

`archive/tasks_history/` 已在根目录 `README.md` 和归档目录 `README.md` 中明确标注：该目录用于历史追溯，**默认不是 Agent 必读上下文**。因此，后续 Agent 应优先读取根目录核心文档与 `docs/` 下正式版本，只有在需要核对历史来源时才进入归档目录。

## 7. 后续维护建议

后续继续向本仓库增加材料时，应优先判断其是否满足以下三个条件：其一，是否直接服务于 AI 秘书核心架构；其二，是否具备长期复用价值；其三，是否能维持较高的信息密度。如果不能满足这些条件，应优先进入其他仓库或归档，而不是扩张本仓库主上下文。

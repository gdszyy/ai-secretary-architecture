# ai-secretary-architecture 仓库迁移说明

**作者**: Manus AI  
**日期**: 2026-04-08

## 1. 迁移目标

本次迁移的目标，是将 `project-management-ai-secretary` 中与 AI 秘书系统核心架构直接相关、且具有长期复用价值的文档抽离到 `ai-secretary-architecture`，从而形成一个上下文边界清晰、适合 Agent 进行系统规划与架构演进的核心文档仓库。

迁移动作严格遵循拆分评估报告提出的原则，即保留高信噪比的核心架构文档，将前端代码、原始 JSON 数据与大量历史过程材料移出主上下文或降级归档。[1]

## 2. 已迁移内容

| 类别 | 迁移内容 | 目标位置 | 说明 |
|------|----------|----------|------|
| 根目录核心文档 | `README.md`、`CORE_PHILOSOPHY.md`、`IMPLEMENTATION_PLAN.md`、`SOP.md` | 仓库根目录 | 构成仓库主入口与核心上下文 |
| 补充核心文档 | `SKILL_FEASIBILITY_REPORT.md` | 仓库根目录 | 保留 Skill 化能力设计背景 |
| 模块一文档 | `docs/module1_kanban/` | `docs/module1_kanban/` | 原样迁移 |
| 模块二文档 | `docs/module2_buffer/` | `docs/module2_buffer/` | 原样迁移 |
| 模块三文档 | `docs/module3_info_sources/` | `docs/module3_info_sources/` | 在原始主计划基础上补充长期有效研究文档 |
| 架构类补充文档 | 仓库拆分评估、模块对比、版本规划、多维表结构设计 | `docs/architecture/` | 用于支持仓库边界与架构演进决策 |
| 项目级说明文档 | 项目总览、项目启动、Lark 文档创建规范 | `docs/project/` | 保留必要背景与协作规范 |

## 3. 从历史任务提炼进入 docs 的文档

| 来源任务 | 提炼文档 | 新位置 | 处理方式 |
|------|------|------|------|
| `tsk-2beb54e9-462` | `info_source_research.md` | `docs/module3_info_sources/` | 提升为模块三长期参考文档 |
| `tsk-41c824dc-a53` | `info_source_integration_plan.md` | `docs/module3_info_sources/` | 提升为模块三集成规划文档 |
| `tsk-b8220b1e-d81` | `module_comparison_report.md` | `docs/architecture/` | 作为模块分工与边界参考 |
| `tsk-b8220b1e-d81` | `version_planning.md` | `docs/architecture/` | 作为阶段规划参考 |
| `tsk-c87fc05b-5af` | `xpbet_bitable_structure_design.md` | `docs/architecture/` | 作为多维表结构设计参考 |

## 4. 已归档内容

以下任务目录被归入 `archive/tasks_history/`，仅保留 `README.md`、`review.md` 与 `deliverables/` 下的 Markdown / TXT 最终文档，以维持历史可追溯性：

| 任务 ID | 归档原因 | 是否进入主 docs |
|------|------|------|
| `tsk-c67f7251-d40` | 模块一来源任务，需要保留历史任务说明与审核记录 | 否，因正式文档已在 `docs/module1_kanban/` |
| `tsk-9be3bdb3-7dc` | 模块二来源任务，需要保留历史任务说明与审核记录 | 否，因正式文档已在 `docs/module2_buffer/` |
| `tsk-2beb54e9-462` | 模块三调研来源任务 | 部分进入 `docs/module3_info_sources/` |
| `tsk-41c824dc-a53` | 模块三集成规划来源任务 | 部分进入 `docs/module3_info_sources/` |
| `tsk-b8220b1e-d81` | 版本与模块对比分析 | 部分进入 `docs/architecture/` |
| `tsk-c87fc05b-5af` | 多维表结构设计 | 部分进入 `docs/architecture/` |
| `tsk-f33ad9af-54f` | 功能地图管理手册 | 否，保留为历史参考 |
| `tsk-9103d528-937` | 数据结构设计与大型原始数据来源任务 | 仅保留 Markdown 文档，排除原始数据文件 |

## 5. 明确排除的内容

本次迁移中，以下内容未进入主上下文，原因是它们会显著增加噪音、破坏仓库聚焦性，或更适合迁移到其他仓库：

| 内容类型 | 典型来源 | 处理策略 |
|------|------|------|
| React / TypeScript 前端代码 | `tsk-6cafe603-a9f`、`tsk-f7cc10f7-0df`、`tsk-b9e8ecd5-4f3` | 不迁入本仓库主上下文 |
| 前端静态模板与可视化实现 | `kanban/` | 不迁入本仓库主上下文 |
| 大型原始 JSON 数据 | `tsk-9103d528-937` 下多个 `json` 文件 | 不迁入主上下文，也不保留到归档主目录 |
| 一次性脚本与中间过程文件 | `tasks/**` 下 `.py`、`.ts`、`.tsx` 等 | 排除 |

## 6. 归档读取规则

`archive/tasks_history/` 的定位是历史审计与知识追溯，而不是日常上下文。因此：

> 默认情况下，Agent 不应将 `archive/tasks_history/` 作为新任务的必读上下文，除非当前任务明确要求回溯历史决策、核对任务原件或审阅审核记录。

这一规则已经同步写入仓库根目录 `README.md`，以确保后续协作时不会再次将高噪音历史材料重新纳入主上下文。

## References

[1]: ./repository_split_assessment.md "repository_split_assessment.md"

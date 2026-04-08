# ai-secretary-architecture

**ai-secretary-architecture** 是 AI 秘书系统的核心架构与文档仓库，同时也是当前多 Agent 协作项目的文档库。该仓库承载系统级设计、模块 SOP、项目级上下文与拆分后的历史归档，目标是为后续的系统规划、架构评审、流程升级与交接提供高信噪比的知识基座。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `CORE_PHILOSOPHY.md` `IMPLEMENTATION_PLAN.md` `SOP.md` | 系统级核心原则、实施计划与标准作业流程。 |
| `docs/module1_kanban/` | 看板模块设计、流程图与模块 SOP。 |
| `docs/module2_buffer/` | Buffer 模块设计、反积压机制与信息生命周期说明。 |
| `docs/module3_info_sources/` | 信息源治理与主计划文档。 |
| `docs/architecture/` | 体系结构相关辅助文档。 |
| `docs/*.md` | 项目概览、启动记录、交接说明与拆分清单。 |
| `archive/tasks_history/` | 历史任务归档与旧交付物快照。 |
| `tasks/` `context/` | 多 Agent 协作文档库的任务成果与上下文沉淀。 |

## 使用约定

本仓库默认作为 **架构与流程知识源** 使用。对于一般架构任务，建议优先阅读根目录核心文档及 `docs/module*` 目录；`archive/tasks_history/` 为历史归档区，默认不属于 Agent 必读上下文，仅在需要追溯历史方案、核对来源或恢复旧交付物时再进入读取。

## 拆分说明

本仓库来自对 `project-management-ai-secretary` 的拆分重构。原仓库中的前端原型、React/TS 代码与通用技能定义已分别迁移到独立仓库，以降低上下文污染并提升不同任务类型的检索效率。

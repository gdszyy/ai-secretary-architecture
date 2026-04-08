# ai-secretary-architecture

**ai-secretary-architecture** 是 AI 秘书系统的核心架构与流程文档仓库，聚焦于系统哲学、实施路线、标准作业程序（SOP）、模块设计与长期有效的项目级说明。本仓库同时作为当前拆分项目的主协作文档库，用于沉淀稳定知识，而不是继续承载高噪音的临时代码、过程草稿与原始数据。

本仓库由 `project-management-ai-secretary` 拆分而来，拆分依据见 [`docs/architecture/repository_split_assessment.md`](./docs/architecture/repository_split_assessment.md)。评估报告指出，原仓库中 `tasks/` 下的大量前端 React/TypeScript 代码、过程性交付物以及大型 JSON 原始数据会显著稀释 Agent 的有效上下文，降低后续架构任务的理解效率与执行准确性。[1]

## 仓库定位

本仓库服务于以下几类工作：一是 AI 秘书系统的顶层规划与设计对齐；二是模块级 SOP、信息流和状态流定义；三是围绕 Kanban、信息缓冲池与信息源治理的长期知识沉淀；四是项目拆分后的历史任务归档与审计追踪。

与之相对，**前端实现代码、交互原型、海量原始 JSON 数据与一次性过程材料，不应继续占据本仓库主上下文**。这些内容要么已经在拆分中被排除，要么被降级归档，仅保留必要的历史追溯能力。

## 目录结构

| 路径 | 内容定位 | 是否建议 Agent 默认阅读 |
|------|-----------|--------------------------|
| `README.md` | 仓库入口、阅读顺序、上下文边界说明 | 是 |
| `CORE_PHILOSOPHY.md` | AI 秘书系统的核心设计哲学 | 是 |
| `IMPLEMENTATION_PLAN.md` | 分阶段实施路线图 | 是 |
| `SOP.md` | 全局协作与操作 SOP | 是 |
| `SKILL_FEASIBILITY_REPORT.md` | Skill 化可行性与能力边界说明 | 视任务而定 |
| `docs/module1_kanban/` | 模块一：Kanban 与任务流转设计 | 是 |
| `docs/module2_buffer/` | 模块二：信息缓冲池与防堆积机制 | 是 |
| `docs/module3_info_sources/` | 模块三：信息源治理、调研与集成规划 | 是 |
| `docs/architecture/` | 仓库拆分评估、架构补充文档与迁移说明 | 是 |
| `docs/project/` | 项目总览、启动材料与文档规范 | 按需 |
| `tasks/` | 当前协作任务的交付与审核记录 | 按需 |
| `archive/tasks_history/` | 历史任务归档，仅供追溯，不作为主上下文 | 否 |

## 推荐阅读顺序

对于首次进入仓库的 Agent 或项目成员，建议先阅读根目录中的核心哲学、实施计划与全局 SOP，再进入各模块文档目录。若任务涉及仓库边界、拆分原则或历史知识筛选，再补充阅读 `docs/architecture/` 下的说明材料。只有当需要追溯历史决策来源时，才进入 `archive/tasks_history/`。

| 阅读阶段 | 建议文档 | 目的 |
|------|------|------|
| 第一步 | `README.md` | 理解仓库边界与阅读策略 |
| 第二步 | `CORE_PHILOSOPHY.md` | 理解系统角色定位与设计原则 |
| 第三步 | `IMPLEMENTATION_PLAN.md`、`SOP.md` | 获取执行框架与协作流程 |
| 第四步 | `docs/module1_kanban/`、`docs/module2_buffer/`、`docs/module3_info_sources/` | 获取模块级架构与 SOP |
| 第五步 | `docs/architecture/`、`docs/project/` | 了解拆分依据、项目背景与补充规范 |
| 最后 | `archive/tasks_history/` | 仅在需要历史追溯时查阅 |

## 本次拆分后的保留策略

本仓库优先保留**稳定、长期有效、适合复用的知识**。因此，本次迁移保留了根目录核心文档、三个核心模块目录，以及若干与架构拆分直接相关的项目级文档和设计说明。同时，来自原 `tasks/` 的部分最终 Markdown 交付物被提升进入 `docs/`，作为正式知识继续维护。

被显式排除出主上下文的内容包括前端 React/TypeScript 代码、静态前端模板、一次性脚本执行结果，以及大型原始 JSON 数据。这些材料即使有历史价值，也会在信息密度和上下文负载上对 Agent 造成明显干扰，因此不应继续作为本仓库的主阅读面。[1]

## 关于历史归档

`archive/tasks_history/` 用于保存与本仓库架构演进相关的历史任务说明、最终 Markdown 交付物以及审核记录。该目录的核心目的是**保留可审计性，而不是提供默认上下文**。

> **默认规则**：Agent 在执行新任务时，除非任务明确要求追溯历史过程，否则不应主动将 `archive/tasks_history/` 视为必读上下文。

通过这一规则，仓库可以同时兼顾两类需求：一方面保持当前主上下文简洁、稳定、低噪音；另一方面保留必要的历史证据链与演化脉络，便于后续人工审查或深度研究。

## 快速索引

| 类别 | 关键文档 | 说明 |
|------|----------|------|
| 核心哲学 | [`CORE_PHILOSOPHY.md`](./CORE_PHILOSOPHY.md) | 系统愿景、角色定位与方法论 |
| 实施路线 | [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) | 分阶段落地路径 |
| 全局 SOP | [`SOP.md`](./SOP.md) | 面向项目协作与操作执行的统一 SOP |
| 模块一 | [`docs/module1_kanban/`](./docs/module1_kanban/) | 看板系统与状态流转设计 |
| 模块二 | [`docs/module2_buffer/`](./docs/module2_buffer/) | 信息缓冲池与防堆积机制 |
| 模块三 | [`docs/module3_info_sources/`](./docs/module3_info_sources/) | 信息源调研、治理与集成规划 |
| 架构补充 | [`docs/architecture/`](./docs/architecture/) | 拆分评估、迁移说明与补充设计 |
| 项目资料 | [`docs/project/`](./docs/project/) | 项目总览、启动材料、文档规范 |

## 维护原则

后续向本仓库提交内容时，应优先判断材料是否具备**长期复用价值、架构相关性与上下文高信噪比**。如果内容主要服务于某次一次性执行、局部实现验证或原始数据采样，应优先放入其他更合适的仓库或进入归档，而不是直接扩大本仓库主上下文。

## References

[1]: ./docs/architecture/repository_split_assessment.md "repository_split_assessment.md"

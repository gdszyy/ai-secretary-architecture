# ai-secretary-architecture

**ai-secretary-architecture** 是 AI 项目秘书系统的核心架构设计文档库，同时也是当前多 Agent 协作项目的文档库。该仓库承载系统级设计、模块 SOP、项目级上下文与拆分后的历史归档，目标是为后续的系统规划、架构评审、流程升级与交接提供高信噪比的知识基座。

> **⚠️ Agent 必读声明**
> 本仓库为 AI 秘书系统的**核心架构与流程知识源**。Agent 在执行系统规划、架构设计或读取项目级上下文时，**应优先读取此仓库**。
> `archive/tasks_history/` 为历史归档区，默认不属于 Agent 必读上下文，仅在需要追溯历史方案、核对来源或恢复旧交付物时再进入读取。

## 仓库结构与文档索引

### 1. 系统级核心设计 (根目录)
| 文档 | 路径 | 说明 |
| --- | --- | --- |
| **核心哲学** | [`CORE_PHILOSOPHY.md`](./CORE_PHILOSOPHY.md) | AI 秘书的愿景、角色定位与核心价值观 |
| **实施方案** | [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) | 顶层实施路线图与四阶段落地计划 |
| **Skill 架构** | [`SKILL_FEASIBILITY_REPORT.md`](./SKILL_FEASIBILITY_REPORT.md) | 将 AI 秘书打包为 Manus Skill 的架构设计 |
| **全局 SOP** | [`SOP.md`](./SOP.md) | 项目经理与 AI 秘书交互的标准指令 |

### 2. 模块架构设计 (docs/)
| 模块 | 目录/文件 | 说明 |
| --- | --- | --- |
| **模块一：看板系统** | [`docs/module1_kanban/`](./docs/module1_kanban/) | 包含看板模块设计、流程图、Meegle 集成方案与模块 SOP |
| **模块二：缓冲池** | [`docs/module2_buffer/`](./docs/module2_buffer/) | 包含 Buffer 模块设计、反积压机制与信息生命周期说明 |
| **模块三：信息源** | [`docs/module3_info_sources/`](./docs/module3_info_sources/) | 包含信息源治理与主计划文档 |
| **体系结构评估** | [`docs/architecture/`](./docs/architecture/) | 体系结构相关辅助文档，如仓库拆分评估报告 |

### 3. 项目级上下文 (docs/)
| 文档 | 路径 | 说明 |
| --- | --- | --- |
| **项目总览** | [`docs/project-overview.md`](./docs/project-overview.md) | 项目全局概览 |
| **启动报告** | [`docs/project-kickoff.md`](./docs/project-kickoff.md) | 项目启动文档 |
| **交接文档** | [`docs/handover.md`](./docs/handover.md) | Agent 间的项目交接说明 |
| **派发任务** | [`docs/dispatched_tasks.md`](./docs/dispatched_tasks.md) | 派发任务记录 |
| **Lark 文档规范** | [`docs/lark-doc-creation-spec.md`](./docs/lark-doc-creation-spec.md) | 飞书云文档创建规范 |
| **技能索引** | [`docs/skill_index.md`](./docs/skill_index.md) | Agent 核心技能索引与使用指南 |

### 4. 多 Agent 协作与归档
| 目录 | 用途 |
| --- | --- |
| `tasks/` | 多 Agent 协作文档库的任务成果沉淀。 |
| `context/` | 多 Agent 协作文档库的上下文快照。 |
| `archive/tasks_history/` | 原仓库的历史任务归档与旧交付物快照。 |

## 仓库体系说明与访问场景

本仓库来自对原 `project-management-ai-secretary` 仓库的拆分重构。为了降低 AI Agent 读取上下文时的噪音污染，整个项目现已拆分为三个独立仓库。

**作为 AI Agent，请根据你当前被分配的任务类型，选择读取对应的仓库：**

| 仓库名称 | 职责边界与内容 | Agent 访问场景 |
| --- | --- | --- |
| **[ai-secretary-architecture](https://github.com/gdszyy/ai-secretary-architecture)**<br>*(本仓库)* | **核心架构文档库**<br>包含系统级设计、模块 SOP、数据结构设计与项目全局上下文。纯 Markdown，信噪比 ~100%。 | **首选仓库**。当执行「系统规划」、「架构评审」、「SOP 制定」、「流程升级」或「了解项目背景」等高阶任务时，必须读取此仓库。 |
| **[xpbet-frontend-components](https://github.com/gdszyy/xpbet-frontend-components)** | **前端工程与组件库**<br>包含所有 UI 原型、设计规范、React/TS 代码库与数据可视化组件。 | 当执行「UI 开发」、「前端组件重构」、「页面还原」或「交互效果调整」等前端工程任务时，请读取此仓库。 |
| **[manus-lark-skills](https://github.com/gdszyy/manus-lark-skills)** | **通用 Agent 技能库**<br>存放可跨项目复用的 Manus 技能定义与 Python 脚本（如 `lark-codesandbox`、`lark-md-import`），与业务逻辑完全解耦。 | 当执行「技能开发」、「Lark API 集成」或需要「引用现有通用技能」时，请读取此仓库。 |

> **提示**: 原 `project-management-ai-secretary` 仓库现已降级为**历史归档库**，主要用于存放体积庞大的废弃测试数据（如海量 JSON）和过时的中间交付物。除非需要追溯极早期的原始数据，否则 Agent **无需读取**原仓库。

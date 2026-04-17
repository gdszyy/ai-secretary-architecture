# AI Secretary Architecture 全局协作规范 (AGENTS.md)

本文档是符合 **Echo-Developer 模式** 的 AI 友好型仓库入口。它定义了全局的编辑策略、防坑指南以及各模块的路由索引，确保 Agent 能够高效协作。

## 1. 快速导航与核心入口规范 (Quick Navigation)

- **项目全局规范入口**：本文档 (`AGENTS.md`)
- **架构与防坑指南**：[`.cursor/rules/global.md`](.cursor/rules/global.md)
- **实现状态与 TODO**：[`.cursor/rules/implementation_status.md`](.cursor/rules/implementation_status.md)
- **流程洞察索引**：[`.cursor/rules/process_insights/index.md`](.cursor/rules/process_insights/index.md)

## 2. 模块路由表 (Module Routing)

| 模块 | 职责 | 规范文档 |
| :--- | :--- | :--- |
| **Architecture** | 系统全局架构与核心逻辑 | [`.cursor/rules/architecture.md`](.cursor/rules/architecture.md) |
| **Kanban** | 看板数据链路与 Bitable 同步 | [`.cursor/rules/module1_kanban.md`](.cursor/rules/module1_kanban.md) |
| **Buffer** | 信息缓冲池与意图识别 | [`.cursor/rules/module2_buffer.md`](.cursor/rules/module2_buffer.md) |
| **Info Sources** | 信息源治理与 Lark 集成 | [`.cursor/rules/module3_info_sources.md`](.cursor/rules/module3_info_sources.md) |

## 3. 编辑策略与活文档契约

- **代码-文档同步**：任何实质性修改必须同步更新 `.cursor/rules/` 下的对应规范。
- **流程洞察沉淀**：发现隐蔽逻辑或踩坑后，必须在 `process_insights/` 下记录并更新索引。
- **TODO 闭环**：完成任务后必须更新 `implementation_status.md` 中的状态及 Task ID。

# 看板系统后续迭代路线图与仓库归属说明

**作者**: Manus AI
**日期**: 2026-04-08

针对此前《看板优化方案》（`kanban_optimization_plan.md`）中提出的三项核心下一步建议（Lark 机器人 MVP、多对话分离 PoC、看板数据结构升级），本文档详细梳理了这三项工作在拆分后三大仓库体系中的归属、当前进度以及推进后的融合路径。

---

## 1. 任务归属与进度全景图

| 任务项 | 核心目标 | 所属仓库 | 当前进度 | 融合形态 |
| :--- | :--- | :--- | :--- | :--- |
| **Lark 机器人 MVP** | 验证群聊消息捕获与关键词触发链路 | `manus-lark-skills` | **未开始** (仅有规划文档) | 沉淠为独立的 Manus Skill，对应 `TODO-P1-04` |
| **多对话分离 PoC** | 验证 Thread Separation 算法准确率 | `ai-secretary-architecture` | **已实现** (`scripts/thread_separator.py`，两阶段算法) | 已沉淠为核心算法实现，评测报告待补充 |
| **看板数据结构升级** | 增加 `sourceRef` 和 `epicId` 字段 | `xpbet-frontend-components` | **未开始** (需前后端同步改造) | 沉淠为 JSON 结构变更与前端 UI 渲染更新，对应 `TODO-P1-05` |

---

## 2. 详细推进路径与融合方案

### 2.1 Lark 机器人 MVP

*   **仓库归属**: `manus-lark-skills` (通用 Agent 技能库)
*   **推进思路**:
    *   此任务本质上是开发一个与 Lark Open API 对接的集成模块。由于其具备高度的可复用性（不局限于特定项目），应作为独立的通用技能进行开发。
    *   需开发基于事件订阅（Event Callback）的接收服务，实现群聊消息的实时监听。
*   **融合路径**:
    *   在 `manus-lark-skills/skills/` 目录下新建 `lark-group-monitor` 技能。
    *   包含 `SKILL.md`（定义 Agent 如何使用该技能）和对应的 Python 脚本（处理鉴权、事件接收与基础过滤）。
    *   完成后，Agent 可跨项目调用此技能获取群聊动态。

### 2.2 多对话分离 PoC (Thread Separation)

*   **仓库归属**: `ai-secretary-architecture` (核心架构文档库)
*   **推进思路**:
    *   这是一个重算法、重逻辑的架构探索任务，旨在解决信息降噪与归因的痛点。
    *   需从真实群聊中脱敏提取一段包含多线并行讨论的历史数据。
    *   使用 LLM 结合实体聚类算法（Entity Clustering）进行处理，并输出评测报告（如准确率、召回率）。
*   **融合路径**:
    *   在 `docs/module2_buffer/` 目录下新增 `thread_separation_algorithm.md`。
    *   文档需包含算法原理、Prompt 模板设计、测试数据集特征以及最终的评测结论。
    *   该方案成熟后，将作为 SOP 指导 Agent 如何处理复杂的混杂上下文。

### 2.3 看板数据结构升级

*   **仓库归属**: `xpbet-frontend-components` (前端工程与组件库)
*   **推进思路**:
    *   这是对实际产品 UI 与数据约定的改造。当前 `kanban_data.json` 的 `items` 层级仅包含 `text` 和 `status`，无法支撑溯源与宏观规划。
    *   需在 JSON 结构中正式引入 `sourceRef`（指向信息来源的具体 URL 或 ID）和 `epicId`（关联大版本规划）。
*   **融合路径**:
    *   修改前端仓库中的 Mock 数据文件（如 `kanban_data.json`），添加新字段。
    *   修改 React 组件（如 Kanban Card），增加来源溯源的点击入口（Icon/Link）以及大版本标签（Tag）的渲染逻辑。
    *   提交 PR 并入 `main` 分支，完成前端视觉层面的闭环。

---

## 3. 跨库协同建议

这三项工作虽然归属不同仓库，但在逻辑上是紧密耦合的：
**Lark 机器人 (`manus-lark-skills`)** 捕获原始数据 -> **多对话分离 (`ai-secretary-architecture`)** 负责清洗归因 -> 最终清洗好的结构化数据通过 **看板数据结构 (`xpbet-frontend-components`)** 渲染展示。

在实际派发任务时，建议按照上述顺序（2.1 -> 2.2 -> 2.3）依次通过 `multi-agent-hub` 派发子任务，确保数据链路的上下游依赖顺畅。

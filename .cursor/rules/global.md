---
description: "AI 项目秘书系统的全局架构概述、核心工作流串联及全局禁止行为清单"
globs: ["docs/project-overview.md", "IMPLEMENTATION_PLAN.md", "CORE_PHILOSOPHY.md", "SOP.md"]
---

# 全局架构规范 (Global Architecture)

## 1. 架构概述

AI 项目秘书系统旨在将“Lark多维表格看板与Meegle关联机制”（核心模块1）与“信息缓冲区机制”（核心模块2）进行深度整合，构建一个端到端的智能自动化项目管理辅助系统。该系统极大减轻了项目经理（PM）在信息收集、清洗、分发和状态追踪上的事务性负担。

系统架构分为四个核心层级：

1.  **入口层 (Input Layer)**：支持多渠道（Telegram, Lark, 语音）接收 PM 的碎片化信息或标准指令。
2.  **处理层 (Processing Layer - Information Buffer)**：作为核心中枢，利用大语言模型（LLM）对信息进行意图识别、实体提取和完整度评分。
    *   *完整度 < 80分*：触发主动询问（即时/批量），或进入防堆积降级流程。
    *   *完整度 ≥ 80分*：状态变更为 `ready`，进入派发队列。
3.  **调度层 (Dispatcher Layer)**：根据意图和模块路由规则，将 `ready` 状态的信息转换为目标系统所需的 API Payload，并执行幂等性检查。
4.  **工作区层 (Workspace Layer)**：
    *   **Lark 多维表格**：作为产品侧的宏观看板，管理“待规划”到“已上线”的全生命周期。
    *   **Meegle**：作为研发侧的执行引擎，管理“开发中”到“已完成”的具体工作项。
    *   **GitHub Issues / Lark Wiki**：用于存储 Bug、备忘和会议纪要。

## 2. 核心工作流串联

### 2.1 需求流转主线 (Feature Workflow)
1.  PM 发送碎片想法（如“下周要把活动中心的预算配置功能加上”）。
2.  **缓冲区**接收并识别意图（如 `Feature Request`），进行完整度打分。
3.  若评分不足，触发主动询问；若达标，状态变为 `ready`。
4.  **调度器**推送到 **Lark 多维表格**，创建“待规划”的新功能记录。
5.  PM 在 Lark 中调整状态为“开发中”。
6.  **调度器**监听到变更，自动调用 **Meegle API** 创建 Story，并回写 Meegle ID 到 Lark。
7.  研发在 Meegle 中完成开发，状态改为“已完成”。
8.  **调度器**监听到 Meegle Webhook，自动更新 Lark 状态为“已上线”，并发送捷报。

### 2.2 缺陷与备忘流转副线 (Bug & Memo Workflow)
1.  PM 发送 Bug 或备忘信息。
2.  **缓冲区**识别意图（如 `Bug Report` 或 `Memo`）并提取实体。
3.  **调度器**将 Bug 推送到 **GitHub Issue** 或 **Meegle** 创建 Defect。
4.  对于备忘，**调度器**将其存入 **Lark 多维表格**的备忘视图，并设置定时任务，通过 `lark-secretary` 发送提醒。

## 3. 数据层与脚本层规范

### 3.1 数据契约（`data/dashboard_data.json`）

`dashboard_data.json` 是看板前端的**唯一数据源**，所有字段变更必须遵守以下约定：

- **Schema 权威文档**：`docs/module1_kanban/dashboard_visualization_architecture.md`，任何新增或修改字段必须同步更新该文档。
- **更新后必须 git push**：前端通过 GitHub Raw URL 读取，push 后约 5 分钟 CDN 缓存刷新，用户刷新页面即可看到最新数据。
- **禁止手动编辑 JSON**：所有数据变更必须通过 `scripts/` 下的对应脚本执行，确保数据一致性和可追溯性。

### 3.2 脚本调用规范（`scripts/`）

- 运行任何脚本前，确认 `.env` 文件中已配置 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FORGE_API_KEY` 等凭证。
- **标准更新流程**（每周执行）：
  1. 运行 `inject_weekly_updates.py` 注入本周周报
  2. 运行 `sync_bitable_docs.py` 同步 Bitable 文档链接
  3. `git add data/dashboard_data.json && git commit -m "data: update weekly dashboard" && git push`
- **里程碑变更流程**：运行 `add_group_milestones.py` → `enrich_global_milestones.py` → git push
- **冷启动流程**：按顺序执行 `cold_start_step1~4.py`，再运行 `parse_to_dashboard_json.py`

## 4. 全局禁止行为清单

为保障项目架构的纯净性和系统稳定性，特制定以下禁止行为清单：

1.  **禁止在此仓库中存放业务代码**：`ai-secretary-architecture` 仓库仅用于存储核心架构文档、SOP 和项目级上下文。前端代码（React/TS）必须存放在 `xpbet-frontend-components`，Agent 技能（Skills）必须存放在 `manus-lark-skills`。
2.  **禁止恢复已归档的历史任务**：位于 `archive/tasks_history/` 目录下的内容被视为历史废弃物，仅供追溯参考。Agent 严禁在未获明确授权的情况下，将归档内容重新引入活跃文档区（如 `docs/` 根目录）。
3.  **禁止绕过缓冲区直接操作工作区**：在系统架构设计中，所有的碎片信息输入必须经过“处理层（Information Buffer）”的清洗和打分，严禁设计绕过缓冲区直接向 Lark 或 Meegle 写入数据的流程。
4.  **禁止破坏“代码-文档同步”契约**：在修改任何架构设计、SOP 或模块规范时，必须同步更新 `.cursor/rules/` 下对应的规则文档。
5.  **禁止硬编码凭证信息**：在所有文档示例和设计方案中，严禁出现真实的飞书 App ID、App Secret、GitHub Token 或 Meegle Token，必须使用占位符（如 `<APP_ID>`）代替。

# 周报模块进度时间线 — 功能设计文档索引

本目录收录「周报模块进度时间线」功能的完整设计文档，涵盖数据模型、触发机制和 Agent 协作工作流三个维度。

## 文档列表

| 文件 | 内容 | 状态 |
|------|------|------|
| [01_data_model_design.md](./01_data_model_design.md) | 多源数据模型扩展、前端组件设计、实施步骤 | ✅ 已定稿 |
| [02_trigger_design_v1.md](./02_trigger_design_v1.md) | 触发机制初版（定时跑批 + 飞书 Bot 手动触发） | 📦 已归档（被 v2 取代） |
| [03_agent_driven_trigger_design.md](./03_agent_driven_trigger_design.md) | Agent 驱动触发机制（当前采用方案） | ✅ 已定稿 |

## 核心设计决策

**数据来源优先级**：飞书多维表格周报（`xp-weekly-report` 技能）> 多维表格需求状态 > Meegle 进度 > 群内讨论洞察。

**触发机制**：采用 Agent 驱动的双轨制——Manus 定时任务（每周二 14:00）自动唤醒主 Agent，飞书 Bot 指令支持按需触发。两者均通过 `multi-agent-hub` 进行任务编排，确保过程可追溯。

**周期定义**：每周二至下周二为一个周报周期（`start_date` / `end_date`），在前端以 `week` 字段（如 `2026-16`）作为唯一标识。

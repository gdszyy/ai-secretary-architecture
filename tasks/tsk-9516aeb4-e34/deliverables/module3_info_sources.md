---
description: "module3_info_sources 模块的设计规范与核心逻辑说明"
globs: ["module3_info_sources/**/*"]
---

# module3_info_sources 模块规范

## 1. 模块职责

信息源模块负责沿治项目的多渠道信息入口，包括 Lark Bot 消息、会议转录、Meegle Webhook 等，将多源数据统一路由到信息缓冲池。

> **架构重构说明 (2026-04-20)**：
> 群消息流水线已重构为“高价值事实提取器”。废弃对常规缺陷/需求的群内自动 @ 追问；取消“未闭环话题”对调度频率的强制提升；强化群名作为上下文辅助；彻底解耦项目级事实与个人秘书级跟进。

## 2. 核心信息源矩阵

| 信息源 | 接入方式 | 触发机制 | 处理脚本 |
|------|------|------|------|
| Lark Bot 消息 | Webhook | 实时推送 | `main.py` |
| Lark 群消息 | API 轮询 | 定时拉取 | `scripts/daily_progress_updater.py` |
| Meegle Webhook | Webhook | 状态变更回传 | `main.py` |
| 媒体文件 | 上传解析 | 手动触发 | `scripts/media_parser.py` |

### 核心脚本

- `scripts/daily_progress_updater.py` — 群消息定时拉取与进度提取（核心流水线）
- `scripts/extract_weekly_insights.py` — 群聊洞察提取（实时拉取接口 + 离线批量分析）
- `scripts/cold_start_step1_list_groups.py` — 列出 Lark 群组
- `scripts/cold_start_step2_fetch_messages.py` — 拉取群消息
- `scripts/cold_start_step3_llm_profile.py` — LLM 群组画像分析
- `scripts/media_pipeline.py` — 媒体文件处理流水线

### 群聊洞察接口（双轨统一说明）

> **架构说明 (2026-04-21)**：
> 群聊洞察模块已经完成接口统一，消除了两条平行轨道之间的断层。

之前存在两条平行轨道：
1. **日常流水线**（`daily_progress_updater.py`）：实际在跑，直接将群聊摘要写入 `dashboard_data.json`，但绕过了 `run_weekly_report.py` 的多源整合流程。
2. **周报整合线**（`run_weekly_report.py` Step 4）：试图调用 `extract_weekly_insights.py`，但该脚本只有离线分析功能，导致接口断层。

**修复后的统一架构**：

| 调用方 | 接口 | 返回格式 |
|------|------|------|
| `run_weekly_report.py` 的 `fetch_chat_insights(week_str)` | 直接函数调用 `extract_weekly_insights.get_weekly_insights_for_modules(week_str)` | `{ "mod_xxx": ["\u8bdd\u98981", ...] }` |
| CLI 离线批量分析 | `python3 extract_weekly_insights.py`（读取 `history_4weeks.json`） | 写入 `weekly_insights.json` |

**`get_weekly_insights_for_modules(week_str)` 函数说明**：
- 位于 `scripts/extract_weekly_insights.py`
- 复用 `daily_progress_updater.py` 中的 `get_token()` / `fetch_recent_messages()` 逻辑（内部重实现，避免循环导入）
- 对 `CHAT_GROUPS` 中所有群组拉取指定周的消息（以周二为边界）
- 通过 LLM 将消息内容归因到具体模块，返回 `{ module_id: [insight_text, ...] }`
- 群名作为领域边界上下文注入 LLM Prompt（遵循 PI-002 原则）

## 3. 信息源沿治规则

- **Lark Bot 权限**：需要 `im:message:receive_v1` 事件权限，仅能读取 Bot 被添加的群组消息
- **群消息读取**：需要 `im:message` 权限，存在 30 天历史消息限制
- **媒体解析**：图片/音频/视频需分别调用对应解析接口，不可混用
- **群名上下文**：群名（如“前端组”、“数据对接组”）是极其重要的上下文辅助，直接决定了提取信息的领域边界。

## 4. 详细设计文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 信息源总纲 | `docs/module3_info_sources/info_source_master_plan.md` | 多源采集架构设计 |
| Lark Bot 集成指南 | `docs/module3_info_sources/lark_bot_and_minutes_integration_guide.md` | Bot 权限配置与接入 |
| 群消息读取方案 | `docs/module3_info_sources/lark_group_message_reading_plan_v2.md` | 群消息读取 v2 方案（Skill-Driven 降噪策略） |
| 权限缺口分析 | `docs/module3_info_sources/lark_permission_gap_analysis.md` | Lark API 权限缺口评估 |

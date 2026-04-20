---
description: "module3_info_sources 模块的设计规范与核心逻辑说明"
globs: ["module3_info_sources/**/*"]
---

# module3_info_sources 模块规范

## 1. 模块职责

信息源模块负责沿治项目的多渠道信息入口，包括 Lark Bot 消息、会议转录、Meegle Webhook 等，将多源数据统一路由到信息缓冲池。

## 2. 核心信息源矩阵

| 信息源 | 接入方式 | 触发机制 | 处理脚本 |
|------|------|------|------|
| Lark Bot 消息 | Webhook | 实时推送 | `main.py` |
| Lark 群消息 | API 轮询 | 定时拉取 | `scripts/fetch_4weeks_messages.py` |
| Meegle Webhook | Webhook | 状态变更回传 | `main.py` |
| 媒体文件 | 上传解析 | 手动触发 | `scripts/media_parser.py` |

### 核心脚本

- `scripts/cold_start_step1_list_groups.py` — 列出 Lark 群组
- `scripts/cold_start_step2_fetch_messages.py` — 拉取群消息
- `scripts/cold_start_step3_llm_profile.py` — LLM 群组画像分析
- `scripts/media_pipeline.py` — 媒体文件处理流水线

## 3. 信息源沿治规则

- **Lark Bot 权限**：需要 `im:message:receive_v1` 事件权限，仅能读取 Bot 被添加的群组消息
- **群消息读取**：需要 `im:message` 权限，存在 30 天历史消息限制
- **媒体解析**：图片/音频/视频需分别调用对应解析接口，不可混用

## 4. 详细设计文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 信息源总纲 | `docs/module3_info_sources/info_source_master_plan.md` | 多源采集架构设计 |
| Lark Bot 集成指南 | `docs/module3_info_sources/lark_bot_and_minutes_integration_guide.md` | Bot 权限配置与接入 |
| 群消息读取方案 | `docs/module3_info_sources/lark_group_message_reading_plan_v2.md` | 群消息读取 v2 方案 |
| 权限缺口分析 | `docs/module3_info_sources/lark_permission_gap_analysis.md` | Lark API 权限缺口评估 |

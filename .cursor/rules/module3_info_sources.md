---
description: "模块三：信息源治理、Lark Bot 集成与多渠道输入的设计规范"
globs: ["docs/module3_info_sources/**"]
---

# 模块三：信息源规范 (Info Sources Module)

## 1. 模块职责

信息源模块是 AI 项目秘书系统的**入口层**，负责对接多种信息输入渠道（Telegram、Lark Bot、语音等），将 PM 的碎片化信息标准化后注入缓冲池（模块二）进行处理。

## 2. 支持的信息源渠道

| 渠道 | 接入方式 | 优先级 | 当前状态 |
| :--- | :--- | :--- | :--- |
| **Lark Bot** | Webhook 事件订阅 | P0 | 设计中 |
| **Telegram Bot** | Webhook / Long Polling | P1 | 概念验证 |
| **语音输入** | Lark 会议纪要 + ASR | P2 | 规划中 |
| **邮件** | IMAP 轮询 | P3 | 未启动 |

## 3. Lark Bot 集成要点

Lark Bot 是当前优先级最高的信息源渠道。集成时需注意以下关键点：

**权限要求**：Bot 需要 `im:message:receive_v1`（接收消息）和 `bitable:record:read`（读取多维表格）等权限。具体的权限清单和缺口分析见 `lark_permission_gap_analysis.md`。

**消息处理流程**：Lark Bot 接收到的消息经过标准化处理后，以统一的 JSON 格式注入缓冲池。消息中的 `@提及`、`图片附件` 和 `富文本格式` 需要在入口层完成解析和清洗。

## 4. 详细设计文档

本模块的完整设计文档位于 `docs/module3_info_sources/` 目录下：

| 文档 | 说明 |
| :--- | :--- |
| `info_source_master_plan.md` | 信息源治理主计划 |
| `lark_bot_and_minutes_integration_guide.md` | Lark Bot 与会议纪要集成指南 |
| `lark_permission_gap_analysis.md` | Lark 权限缺口分析 |
| `prereq_data_assessment.md` | 前置数据评估报告 |

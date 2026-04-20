---
id: "PI-002"
version: "v1.0"
last_updated: "2026-04-20"
author: "Manus AI"
related_modules: ["module2_buffer", "module3_info_sources"]
status: "active"
---

# PI-002: 话题提取与追问降噪策略

## 流程概述

本流程洞察记录了 AI 秘书系统在处理群聊消息时，如何从“事事追问的待办生成器”重构为“高价值事实提取器”的核心策略。该策略彻底解耦了项目级事实记录与个人秘书级跟进，大幅降低了群内机器人的打扰频率。

## 核心防坑指南

### 坑 1: 将群聊视为待办生成器导致过度打扰

**现象**：旧架构下，系统试图将群聊中的每一个 Bug 和需求都追踪到闭环，导致群内充斥着机器人的 `@` 追问，引发用户反感。
**根因**：意图分类体系过于扁平，未区分“项目级高价值事实”与“日常低价值沟通”。
**正确做法**：
1. 严格区分意图价值：仅对 `Major Decision`（重大决策）和 `Risk/Blocker`（风险/阻塞）在缺失致命信息时触发一次性追问。
2. 常规缺陷/需求（Routine Task）绝对不触发追问。如果信息不足以在 Meegle 建单，直接丢弃或降级为日志。
**关键位置**：`docs/module3_info_sources/lark_group_message_reading_plan_v2.md` -> 极简追问机制

### 坑 2: 个人跟进逻辑污染项目主线

**现象**：像“多语言翻译 pending @tao 给 @VoidZ”这类个人间的事务交接，被错误地推入项目全局看板，导致看板信息冗杂。
**根因**：未在架构层面分离“项目级事实”与“个人秘书级跟进”。
**正确做法**：
将此类意图识别为 `Personal Follow-up`（个人跟进），仅推送到特定被 `@` 人员的个人待办系统（如 Lark 任务），绝不进入项目主看板。
**关键位置**：`docs/module2_buffer/info_buffer_design.md` -> 分类体系

### 坑 3: 忽视群名作为重要上下文

**现象**：LLM 在提取信息时，由于缺乏领域边界，容易提取出与当前模块无关的噪音信息。
**根因**：未将群组定位（如“前端组”、“数据对接组”）作为 System Prompt 注入。
**正确做法**：
在调用 LLM 进行话题拆解和价值判定时，必须强制注入群名作为上下文辅助，以明确提取信息的领域边界。
**关键位置**：`scripts/daily_progress_updater.py` -> `PROGRESS_EXTRACT_PROMPT`

## 关键耦合点

- **意图分类与下游路由**：`parsed_intent` 的改变直接影响下游路由逻辑。新增的 `Major Decision`、`Milestone Fact`、`Risk/Blocker` 需映射到 Bitable 的不同视图或表格；`Routine Task` 映射到 Meegle；`Personal Follow-up` 映射到个人待办。
- **旧版跟进脚本的废弃**：`scripts/stale_topic_followup.py` 和 `scripts/topic_reply_tracker.py` 是旧版“事事追问”逻辑的产物，在新架构下应被废弃或大幅重构，不再作为核心流水线的一部分。

## 版本变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-04-20 | 初始记录：记录从待办生成器向事实提取器转型的降噪策略 | Manus AI |

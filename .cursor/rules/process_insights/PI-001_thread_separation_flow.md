---
id: "PI-001"
version: "v1.0"
last_updated: "2026-04-20"
author: "repo-indexer/code-indexer 改造任务"
related_modules: ["module2_buffer", "architecture"]
status: "active"
---

# PI-001: 多对话分离（Thread Separation）流程

## 流程概述

群聊消息经由 `main.py::lark_webhook` 接收后，通过 `handle_message_event` 路由至两条分支：前端缺陷报送（`process_defect_message`）或多对话分离（`separate_threads`）。分离结果中的高价值线程最终写入 Lark Bitable 缓冲池，待人工或下游 Agent 消费。

---

## 核心防坑指南

### 坑 1: `preprocess_messages` 函数边界被索引器误判为 205 行

**现象**：`code-indexer` 将 `preprocess_messages`（实际 L283-L305，约 23 行）的结束行标记为 L487，导致索引显示该函数为 205 行的"巨型函数"。

**根因**：索引器使用"下一个顶层函数的起始行 - 1"作为当前函数的结束行。`preprocess_messages` 之后紧跟的是模块级常量 `THREAD_SEPARATION_SYSTEM_PROMPT`（L312-L407，约 96 行的大型字符串常量），再之后才是 `separate_threads_with_llm`（L408）。索引器无法识别模块级常量，因此将 L283-L487 全部归入 `preprocess_messages`。

**正确做法**：阅读索引时，若看到 `preprocess_messages` 标记为巨型函数，需结合 `@section` 节点（L288-L296）判断实际逻辑范围。真正的巨型函数是 `separate()`，其 `@section` 节点已在 L530-L553 完整标记。

**关键位置**：`scripts/thread_separator.py` → `preprocess_messages` L283，`THREAD_SEPARATION_SYSTEM_PROMPT` 常量 L312

---

### 坑 2: `DASHSCOPE_API_KEY` 缺失导致 LLM 调用静默失败

**现象**：`separate_threads_with_llm` 调用 `call_llm` 时抛出 `EnvironmentError`，但 `handle_message_event` 中没有对 `separate_threads` 的异常进行捕获，导致后台任务静默失败，不向 Lark 群发送任何错误提示。

**根因**：`call_llm`（L169）在 `DASHSCOPE_API_KEY` 未配置时主动抛出异常，而 `handle_message_event` 的 `@section:route_thread_separation` 段未包裹 try/except。

**正确做法**：在 `.env` 中配置 `DASHSCOPE_API_KEY`；若需要在无 LLM 环境下测试，使用 `--dry-run` 参数跳过 LLM 调用。生产环境建议在 `handle_message_event` 的线程分离分支增加 try/except 并通过 `send_lark_message` 发送错误告警。

**关键位置**：`scripts/thread_separator.py` → `call_llm` L169，`main.py` → `handle_message_event::route_thread_separation` L469

---

### 坑 3: Bitable 写入失败不影响主流程（容错设计）

**现象**：`write_threads_to_bitable` 中单条记录写入失败时，仅记录日志并 `continue`，不会中断其他线程的写入，也不会向 Lark 群发送通知。

**根因**：这是有意的容错设计（`@section:write_records_loop`），避免单条 Bitable API 超时导致整批数据丢失。

**正确做法**：若需要感知写入失败，需主动监控 `ERROR` 级别日志（关键字：`写入 Bitable 失败`）。不要在上层调用处依赖 `write_threads_to_bitable` 的返回值来判断是否写入成功。

**关键位置**：`main.py` → `write_threads_to_bitable::write_records_loop` L320

---

### 坑 4: `entity_keywords` 动态加载失败时静默回退

**现象**：`load_project_context` 在 `config/project_context.json` 不存在或格式错误时，会静默回退到硬编码的 `_DEFAULT_ENTITY_KEYWORDS`，不抛出异常。

**根因**：`load_project_context`（L97）的设计目标是"优雅降级"，但这意味着实体提取精度可能在配置文件损坏时悄然下降。

**正确做法**：修改 `config/project_context.json` 后，通过日志确认 `已从 ... 动态加载实体关键词库：N 个关键词` 输出，验证配置已生效。

**关键位置**：`scripts/thread_separator.py` → `load_project_context` L97，配置文件 `config/project_context.json`

---

## 关键耦合点

- **`module2_buffer`**：`write_threads_to_bitable` 写入的 Bitable 表（`BITABLE_TABLE_PENDING_THREADS`）是 Module 2 信息缓冲池的数据入口，字段格式变更需同步更新 Module 2 的消费逻辑。
- **`module1_kanban`**：`update_cursor_record` 写入的 Cursor 表记录了每个 `chat_id` 的最后处理消息 ID，Kanban 模块的定时拉取任务依赖此游标避免重复消费。
- **`THREAD_SEPARATION_SYSTEM_PROMPT`**：Prompt 变更会影响 LLM 输出的 JSON 结构，进而影响 `build_thread_events` 的字段解析。修改 Prompt 后必须同步验证 `intent`、`confidence`、`extracted_entities` 字段的输出格式。

---

## 版本变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-04-20 | 初始记录：补充 @section 标记后沉淀的四个核心防坑点 | repo-indexer/code-indexer 改造任务 |

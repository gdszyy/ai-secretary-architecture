---
description: "module2_buffer 模块的设计规范与核心逻辑说明"
globs: ["module2_buffer/**/*"]
---

# module2_buffer 模块规范

## 1. 模块职责

信息缓冲池是 AI 秘书系统的核心中枢，负责接收所有非结构化或半结构化的碎片信息，通过 LLM 进行意图识别和完整度评分，在信息达到可执行标准后自动分发到下游系统。

## 2. 核心数据模型

### Buffer Item 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `item_id` | String | 唯一标识符 |
| `source_type` | Enum | `lark` / `meeting_notes` / `meegle_webhook` / `voice` |
| `raw_content` | String | 原始输入内容 |
| `parsed_intent` | Enum | `bug_report` / `feature_request` / `memo` / `progress_update` |
| `completeness_score` | Integer | 完整度评分 0-100 |
| `status` | Enum | `pending` / `asking` / `ready` / `archived` / `discarded` |
| `missing_fields` | List | 缺失的关键信息字段列表 |

### 核心脚本

- `scripts/thread_separator.py` — 消息线程分离算法（大文件，详见 auto_index）
- `main.py::handle_message_event()` — Lark 消息事件处理主函数

## 3. 状态流转规则

```
pending → asking → ready → archived
                         ↓
                      discarded
```

- **完整度 < 80 分**：进入 `asking` 状态，触发主动询问（即时或每日 17:30 批量）
- **完整度 ≥ 80 分**：直接进入 `ready`，等待调度器分发
- **24h 未处理**：降级处理；**72h 未处理**：强制归档；**>50 条堆积**：触发批量合并

## 4. 详细设计文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 缓冲区设计方案 | `docs/module2_buffer/info_buffer_design.md` | Buffer Item 数据模型与状态机 |
| 模块 SOP | `docs/module2_buffer/secretary_module2_sop.md` | 缓冲池操作指南 |
| 反堆积机制 | `docs/module2_buffer/buffer_anti_accumulation_sop.md` | 防堆积降级策略 |
| 线程分离算法 | `docs/module2_buffer/thread_separation_algorithm.md` | 消息线程分离设计 |

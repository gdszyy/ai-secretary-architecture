# AI项目秘书信息缓冲区机制设计方案

## 1. 概述

在项目管理过程中，项目经理（PM）每天会接收和产生大量碎片化信息，包括会议记录片段、口头需求、临时备忘、Telegram消息、Lark消息、语音转文字等。这些信息往往是不完整的、缺乏上下文的，或者尚未明确归属模块。

**信息缓冲区（Information Buffer）** 是AI项目秘书的核心机制之一，旨在提供一个“暂存、清洗、补全、分发”的中间层。它接收所有非结构化或半结构化的碎片信息，通过AI进行意图识别和信息提取，并在信息达到可执行标准（完整度达标）后，自动归档或派发到下游系统（如GitHub Issue、Lark多维表格、Meegle）。

## 2. 数据模型设计

信息缓冲区中的每一条记录称为一个 **信息条目（Buffer Item）**。

### 2.1 信息条目结构 (Buffer Item Structure)

| 字段名 | 类型 | 描述 | 示例 |
| :--- | :--- | :--- | :--- |
| `item_id` | String | 唯一标识符 | `buf-20260325-001` |
| `source_type` | Enum | 信息来源渠道 | `telegram`, `lark`, `voice`, `file` |
| `raw_content` | String | 原始输入内容 | "支付系统：发现一个Bug，支付路由在特定情况下会失效" |
| `parsed_intent` | Enum | AI解析出的意图类型 | `bug_report`, `feature_request`, `memo`, `progress_update` |
| `module_name` | String | 归属的项目模块（可为空） | "支付系统" |
| `extracted_entities` | JSON | 提取的关键实体（如时间、人员、优先级） | `{"priority": "high", "assignee": null}` |
| `completeness_score` | Integer | 信息完整度评分 (0-100) | `60` |
| `missing_fields` | List[String] | 缺失的关键信息字段列表 | `["assignee", "reproduce_steps"]` |
| `status` | Enum | 当前状态 | `pending`, `asking`, `ready`, `archived`, `discarded` |
| `created_at` | Timestamp | 接收时间 | `2026-03-25T10:00:00Z` |
| `updated_at` | Timestamp | 最后更新时间 | `2026-03-25T10:05:00Z` |
| `expires_at` | Timestamp | 预期处理截止时间（超时将触发提醒） | `2026-03-25T18:00:00Z` |

### 2.2 分类体系 (Classification System)

信息意图（`parsed_intent`）主要分为以下几类：

1.  **备忘 (Memo)**: 临时记录的想法或待办，通常缺乏具体执行细节。
2.  **缺陷报告 (Bug Report)**: 记录系统中发现的问题。
3.  **需求/特性 (Feature Request)**: 新的功能点或优化建议。
4.  **进度更新 (Progress Update)**: 某个模块或任务的最新进展。
5.  **会议纪要 (Meeting Notes)**: 会议中的关键决定或行动项。
6.  **未知 (Unknown)**: AI无法准确判断意图，需要人工介入。

### 2.3 完整度评分机制 (Completeness Scoring)

完整度评分（`completeness_score`）由AI根据意图类型和提取的实体计算得出。满分为100分，通常达到 **80分** 视为“就绪（Ready）”，可进行下游派发。

*   **基础分 (40分)**: 包含明确的意图和基本描述。
*   **模块归属 (20分)**: 明确指出了所属的项目模块。
*   **关键实体 (40分)**: 根据不同意图，包含必要的实体信息。
    *   *Bug Report*: 需要复现步骤、优先级、影响范围。
    *   *Feature Request*: 需要业务价值、预期结果。
    *   *Memo*: 需要明确的行动项或截止时间。

## 3. 状态机设计 (State Machine)

信息条目在缓冲区中的生命周期状态流转如下：

1.  **`pending` (待处理)**: 信息刚进入缓冲区，等待AI清洗和解析。
2.  **`asking` (询问中)**: 信息完整度不足，AI已向用户发起补充询问，等待回复。
3.  **`ready` (就绪)**: 信息完整度达标，等待系统自动或人工确认后归档/派发。
4.  **`archived` (已归档/已派发)**: 信息已成功推送到下游系统（如GitHub Issue）。
5.  **`discarded` (已废弃)**: 用户明确表示取消，或超时未补充且被判定为无效信息。

## 4. API 设计 (内部接口)

为了支持多Agent协作和系统集成，缓冲区提供以下核心API接口：

*   `POST /buffer/items`: 接收新的碎片信息。
*   `GET /buffer/items/{item_id}`: 获取特定信息条目的详情。
*   `PUT /buffer/items/{item_id}`: 更新信息条目（通常用于用户补充信息后）。
*   `POST /buffer/items/{item_id}/analyze`: 触发AI对条目进行清洗、意图识别和评分。
*   `POST /buffer/items/{item_id}/dispatch`: 将状态为 `ready` 的条目派发到下游系统。
*   `GET /buffer/pending_inquiries`: 获取当前需要向用户发起询问的条目列表（支持批量询问策略）。

## 5. 与下游系统的集成方案

当信息条目状态变为 `ready` 时，系统将根据 `parsed_intent` 和 `module_name` 自动路由到相应的下游系统：

1.  **GitHub Issue**:
    *   **适用场景**: Bug报告、需求特性、模块进度更新。
    *   **动作**: 调用GitHub API，在对应仓库创建新的Issue，或在已有模块Issue下添加Comment。自动打上相应的Labels（如 `Type:Bug`, `Module:支付系统`）。
2.  **Lark 多维表格 (Bitable)**:
    *   **适用场景**: 结构化的数据收集，如需求池管理、缺陷追踪表。
    *   **动作**: 调用Lark API，向指定的多维表格追加一行记录，映射提取的实体字段。
3.  **Meegle**:
    *   **适用场景**: 敏捷开发中的任务分配和迭代规划。
    *   **动作**: 调用Meegle API，创建对应的工作项（User Story, Task, Bug），并分配给相关人员。
4.  **Lark 通知 (lark-secretary)**:
    *   **适用场景**: 重要备忘提醒、高优先级Bug通知。
    *   **动作**: 通过Webhook向项目群发送格式化卡片消息。

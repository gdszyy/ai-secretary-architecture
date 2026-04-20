# AI项目秘书信息缓冲区机制设计方案

## 1. 概述

在项目管理过程中，项目经理（PM）每天会接收和产生大量碎片化信息，包括会议记录片段、口头需求、临时备忘、Lark消息、语音转文字等。这些信息往往是不完整的、缺乏上下文的，或者尚未明确归属模块。

**信息缓冲区（Information Buffer）** 是AI项目秘书的核心机制之一，旨在提供一个“暂存、清洗、补全、分发”的中间层。它接收所有非结构化或半结构化的碎片信息，通过AI进行意图识别和信息提取，并在信息达到可执行标准（完整度达标）后，自动归档或派发到下游系统（如Lark多维表格、Meegle）。

> **架构重构说明 (2026-04-20)**：
> 缓冲区已从“跟进驱动”转向“事实沉淀驱动”。系统不再将所有群聊视为待办事项生成器，而是聚焦于提取**重大决策、里程碑事实和风险阻塞**。个人跟进逻辑已与项目主线解耦。

## 2. 数据模型设计

信息缓冲区中的每一条记录称为一个 **信息条目（Buffer Item）**。

### 2.1 信息条目结构 (Buffer Item Structure)

| 字段名 | 类型 | 描述 | 示例 |
| :--- | :--- | :--- | :--- |
| `item_id` | String | 唯一标识符 | `buf-20260325-001` |
| `source_type` | Enum | 信息来源渠道 | `lark`, `meeting_notes`, `meegle_webhook`, `voice`, `file` |
| `raw_content` | String | 原始输入内容 | "支付系统：发现一个Bug，支付路由在特定情况下会失效" |
| `parsed_intent` | Enum | AI解析出的意图类型 | `major_decision`, `milestone_fact`, `risk_blocker`, `routine_task`, `personal_followup` |
| `module_name` | String | 归属的项目模块（可为空） | "支付系统" |
| `extracted_entities` | JSON | 提取的关键实体（如时间、人员、优先级） | `{"priority": "high", "assignee": null}` |
| `completeness_score` | Integer | 信息完整度评分 (0-100) | `60` |
| `missing_fields` | List[String] | 缺失的关键信息字段列表 | `["assignee", "reproduce_steps"]` |
| `status` | Enum | 当前状态 | `pending`, `asking`, `ready`, `archived`, `discarded` |
| `created_at` | Timestamp | 接收时间 | `2026-03-25T10:00:00Z` |
| `updated_at` | Timestamp | 最后更新时间 | `2026-03-25T10:05:00Z` |
| `expires_at` | Timestamp | 预期处理截止时间（超时将触发提醒） | `2026-03-25T18:00:00Z` |

### 2.2 分类体系 (Classification System)

信息意图（`parsed_intent`）已重构为以下几类，以体现“事实沉淀”的核心价值：

1.  **重大决策 (Major Decision)**: 极高价值。如商务三方选择、架构拍板。直接归档，不触发追问。
2.  **里程碑/进度事实 (Milestone Fact)**: 高价值。如某模块提测、上线。与 Meegle 交叉比对后更新看板。
3.  **风险/阻塞 (Risk/Blocker)**: 高价值。如外部依赖不配合、牌照问题。推入风险池，仅在必要时确认一次。
4.  **常规缺陷/需求 (Routine Task)**: 低价值（项目级）。如日常 Bug 修复。尝试映射到 Meegle，信息不足则直接丢弃或降级为日志，不再主动追问。
5.  **个人跟进 (Personal Follow-up)**: 中价值（仅限特定人员）。如“@tao 给 @VoidZ 翻译文件”。推送到个人待办，不进入项目全局看板。
6.  **未知 (Unknown)**: AI无法准确判断意图，直接降级为日志。

### 2.3 完整度评分机制 (Completeness Scoring)

完整度评分（`completeness_score`）由AI根据意图类型和提取的实体计算得出。满分为100分，通常达到 **80分** 视为“就绪（Ready）”，可进行下游派发。

*   **基础分 (40分)**: 包含明确的意图和基本描述。
*   **模块归属 (20分)**: 明确指出了所属的项目模块。
*   **关键实体 (40分)**: 根据不同意图，包含必要的实体信息。
    *   *Major Decision*: 需要决策背景、结论和决策人。
    *   *Milestone Fact*: 需要明确的进度节点和关联模块。
    *   *Risk/Blocker*: 需要风险点和影响范围。
    *   *Routine Task*: 评分阈值降低，只要有基础描述即可达到 80 分（避免陷入追问循环）。

## 3. 状态机设计 (State Machine)

信息条目在缓冲区中的生命周期状态流转如下：

1.  **`pending` (待处理)**: 信息刚进入缓冲区，等待AI清洗和解析。
2.  **`asking` (询问中)**: 仅针对“重大决策”缺失关键上下文，或“风险/阻塞”需要明确责任人时进入此状态。常规任务不再进入此状态。
3.  **`ready` (就绪)**: 信息完整度达标，等待系统自动或人工确认后归档/派发。
4.  **`archived` (已归档/已派发)**: 信息已成功推送到下游系统（如Lark多维表格、Meegle）。
5.  **`discarded` (已废弃)**: 用户明确表示取消，或常规任务信息不足直接丢弃。

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

1.  **Lark 多维表格 (Bitable)**:
    *   **适用场景**: 重大决策记录、里程碑事实同步、风险池管理。
    *   **动作**: 调用Lark API，向指定的多维表格追加一行记录，映射提取的实体字段。
2.  **Meegle**:
    *   **适用场景**: 常规缺陷/需求（若信息足够）。
    *   **动作**: 调用Meegle API，创建对应的工作项（User Story, Task, Bug），并分配给相关人员。
3.  **个人待办系统 (如 Lark 任务)**:
    *   **适用场景**: 个人跟进 (Personal Follow-up)。
    *   **动作**: 仅推送给特定被 @ 的人员，不污染项目主看板。

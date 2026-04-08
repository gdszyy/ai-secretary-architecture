# AI项目秘书系统落地实施方案 (Implementation Plan)

## 1. 概述

本方案旨在将“Lark多维表格看板与Meegle关联机制”（核心模块1）与“信息缓冲区机制”（核心模块2）进行深度整合，构建一个端到端的 AI 项目秘书系统。该系统将极大减轻项目经理（PM）在信息收集、清洗、分发和状态追踪上的事务性负担。

## 2. 系统全景架构

系统架构分为四个核心层级：

1.  **入口层 (Input Layer)**：支持多渠道（Telegram, Lark, 语音）接收 PM 的碎片化信息或标准指令。
2.  **处理层 (Processing Layer - Information Buffer)**：作为核心中枢，利用大语言模型（LLM）对信息进行意图识别、实体提取和完整度评分。
    *   *完整度 < 80分*：触发主动询问（即时/批量），或进入防堆积降级流程。
    *   *完整度 ≥ 80分*：状态变更为 `ready`，进入派发队列。
3.  **调度层 (Dispatcher Layer)**：根据意图和模块路由规则，将 `ready` 状态的信息转换为目标系统所需的 API Payload，并执行幂等性检查。
4.  **工作区层 (Workspace Layer)**：
    *   **Lark 多维表格**：作为产品侧的宏观看板，管理“待规划”到“已上线”的全生命周期。
    *   **Meegle**：作为研发侧的执行引擎，管理“开发中”到“已完成”的具体工作项。
    *   **GitHub Issues / Lark Wiki**：用于存储 Bug、备忘和会议纪要（飞书文档统一使用 lark-md-import 技能通过 Markdown 导入创建）。

## 3. 核心工作流串联

### 3.1 需求流转主线 (Feature Workflow)
1.  PM 通过 Telegram 发送碎片想法：“下周要把活动中心的预算配置功能加上。”
2.  **缓冲区**接收，识别意图为 `Feature Request`，但缺失细节，评分 60 分。
3.  **缓冲区**触发批量询问，PM 补充细节后，评分达到 90 分，状态变为 `ready`。
4.  **调度器**将其推送到 **Lark 多维表格**，创建一条状态为“待规划”的新功能记录。
5.  PM 在 Lark 中将状态调整为“开发中”。
6.  **调度器**监听到状态变更，自动调用 **Meegle API** 创建 Story，并将 Meegle ID 回写到 Lark。
7.  研发在 Meegle 中完成开发，状态改为“已完成”。
8.  **调度器**通过 Webhook 监听到 Meegle 状态变更，自动将 Lark 中的状态更新为“已上线”，并向 PM 发送捷报。

### 3.2 缺陷与备忘流转副线 (Bug & Memo Workflow)
1.  PM 发送：“支付系统挂了，iOS端微信支付必现。”
2.  **缓冲区**识别为高优 `Bug Report`，完整度达标，直接 `ready`。
3.  **调度器**将其推送到 **GitHub Issue**（打上 `bug` 标签）或直接推送到 **Meegle** 创建 Defect。
4.  PM 发送：“备忘：明天下午提醒我跟进EPAY路由。”
5.  **缓冲区**识别为 `Memo`，提取时间实体。
6.  **调度器**将其存入 **Lark 多维表格**的备忘视图，并设置定时任务，通过 `lark-secretary` 在明天下午发送 Webhook 提醒。

## 4. 分阶段实施计划 (Roadmap)

### 阶段一：基础设施与数据模型搭建 (Week 1)
*   **目标**：完成所有底层数据结构的配置。
*   **行动项**：
    1.  在 Lark 中创建“模块表”和“功能表”，配置看板、表格、甘特三种视图，并添加 `Meegle ID` 等新增字段。
    2.  在 Meegle 中配置项目空间，获取 API Token，确认 `story` 和 `defect` 工作项类型。
    3.  搭建 AI 秘书后端服务框架（推荐 FastAPI），集成 `feishu-bitable`、`meegle-lark` 和 `lark-md-import` 技能的核心逻辑。

### 阶段二：信息缓冲区与大模型接入 (Week 2)
*   **目标**：实现碎信息的接收、清洗和打分机制。
*   **行动项**：
    1.  实现 Telegram Bot 和 Lark Bot 的 Webhook 接收端点。
    2.  设计并调试 LLM Prompt，实现意图分类（6大类）和完整度评分（0-100分）。
    3.  实现缓冲区的状态机（`pending` -> `asking` -> `ready`）。
    4.  实现主动询问机制（即时询问与每日 17:30 的批量询问）。

### 阶段三：调度器与双向同步机制 (Week 3)
*   **目标**：打通缓冲区到工作区的“最后一公里”。
*   **行动项**：
    1.  开发 Dispatcher 引擎，实现意图到工作项的映射逻辑。
    2.  实现 Lark 到 Meegle 的单向推送（监听 Lark 状态变为“开发中”）。
    3.  实现 Meegle 到 Lark 的状态回传（监听 Meegle Webhook）。
    4.  实现防堆积策略的定时任务（24小时降级，72小时强制归档，>50条批量合并）。

### 阶段四：SOP 培训与试运行 (Week 4)
*   **目标**：系统上线，团队磨合。
*   **行动项**：
    1.  向 PM 和研发团队宣贯 `secretary_module1_sop.md` 和 `secretary_module2_sop.md`。
    2.  进行为期两周的试运行，重点监控 LLM 意图识别的准确率和状态同步的稳定性。
    3.  根据试运行反馈，微调完整度阈值和询问话术。

## 5. 关键技术难点与应对策略

1.  **人员身份映射 (Identity Mapping)**
    *   *难点*：Lark User ID 与 Meegle User Key 不一致。
    *   *策略*：在 AI 秘书数据库中维护一张全局映射表。如果匹配失败，在 Meegle 中创建工作项时将 `assignee` 留空，并在通知中提示 PM 手动分配。
2.  **状态同步冲突 (State Conflict)**
    *   *难点*：Lark 和 Meegle 同时被修改导致状态不一致。
    *   *策略*：确立 **Single Source of Truth** 原则。进入开发前，Lark 为主；进入开发后（存在 Meegle ID），Meegle 为主。在 Lark 侧通过权限设置，禁止非 AI 秘书账号手动修改已关联 Meegle 的记录状态。
3.  **LLM 意图识别的稳定性 (LLM Reliability)**
    *   *难点*：碎片信息过于模糊，导致分类错误或提取失败。
    *   *策略*：在 Prompt 中提供丰富的 Few-shot examples（结合历史项目数据）。对于评分低于 60 分且无法通过一轮询问补全的信息，直接降级转入“待认领池”，由人工介入处理，避免系统死循环。

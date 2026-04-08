# Lark 与 Meegle 关联机制设计

## 1. 概述

本设计旨在建立产品侧看板（Lark 多维表格）与技术侧执行工具（Meegle）之间的无缝连接。通过 AI 项目秘书的自动化调度，实现需求从提出到交付的全链路追踪，确保产品和研发团队的信息对齐。

## 2. 触发条件与同步时机

为了避免在 Meegle 中产生过多的无效工作项（如早期被否决的想法），我们采用**延迟创建**策略。

### 2.1 从 Lark 到 Meegle 的单向创建（触发器）

在 Meegle 中新建工作项的触发条件分为自动和手动两种：

*   **自动触发 (推荐)**: 当 Lark 功能表中的某条记录状态从“待规划”或“规划中”变更为 **“开发中”** 时，AI 秘书自动捕获此变更，并调用 Meegle API 创建对应的工作项。
*   **手动触发**: 用户通过 Telegram 向 AI 秘书发送明确指令，例如：`将功能 [功能名称] 推送到 Meegle`。AI 秘书执行创建操作，无论其当前在 Lark 中的状态如何。

**创建后的动作**:
工作项在 Meegle 创建成功后，AI 秘书必须将返回的 `work_item_id` 和访问链接回写到 Lark 功能表的 `Meegle ID` 和 `Meegle 链接` 字段中，建立硬关联。

### 2.2 双向状态同步策略

一旦 Lark 记录与 Meegle 工作项建立了关联（即 Lark 中存在 `Meegle ID`），状态的同步策略如下：

*   **Meegle 为主 (Single Source of Truth for Execution)**: 在进入开发阶段后，Meegle 作为研发执行的唯一事实来源。当 Meegle 中的工作项状态发生变更（如：开发中 -> 测试中 -> 已完成）时，通过 Meegle 的 Webhook 机制触发 AI 秘书，AI 秘书随即将最新状态更新到 Lark 对应的记录中。
*   **Lark 状态锁定**: 为了防止冲突，一旦功能推送到 Meegle，建议在 Lark 中通过权限设置或约定，禁止非 AI 秘书账号手动修改该记录的“状态”字段。
*   **冲突解决**: 如果发生并发修改（极少情况），以 Meegle 的状态和最后更新时间为准，覆盖 Lark 中的状态。

## 3. 字段映射表

在创建和同步过程中，需要进行字段的映射转换。默认将 Lark 的“功能”映射为 Meegle 的“需求 (story)”类型工作项。

| Lark 多维表格字段 (功能表) | Meegle 工作项字段 (Story) | 映射说明与转换逻辑 |
| :--- | :--- | :--- |
| 功能名称 (Text) | `name` / `title` (String) | 直接映射。建议在 Meegle 标题前加上模块前缀，如 `[用户系统] 登录注册流程`。 |
| 功能说明 (Text) | `description` (String/RichText) | 直接映射。如果 Lark 中有文档链接，也应追加到描述末尾。 |
| 状态 (SingleSelect) | `status` (String/Enum) | 需要状态机映射（见下文）。 |
| 功能优先级 (SingleSelect) | `priority` (String/Enum) | 映射关系：`P0-核心` -> `High`，`P1-重要` -> `Medium`，`P2-普通` -> `Low`。 |
| 负责人 (User) | `assignee` (String - user_key) | **关键转换**：需要通过 AI 秘书维护一个 Lark User ID 到 Meegle `user_key` 的映射表（或通过邮箱匹配）。 |
| 迭代版本 (SingleSelect) | `iteration` / `sprint` (String) | 映射到 Meegle 的迭代字段（如果 Meegle 空间已配置）。 |
| *无对应字段* | `work_item_type_key` | 固定为 `story`（需求）。 |

### 3.1 状态映射字典

| Lark 状态 | Meegle 状态 (假设的标准流) | 同步方向 |
| :--- | :--- | :--- |
| 待规划 | (不创建) | - |
| 规划中 | (不创建) | - |
| 开发中 | `In Progress` / `开发中` | Lark -> Meegle (创建时) |
| 测试中 | `Testing` / `测试中` | Meegle -> Lark (Webhook 触发) |
| 已上线 | `Done` / `已完成` | Meegle -> Lark (Webhook 触发) |
| 已归档 | `Closed` / `已关闭` | 双向 (视具体操作场景) |

## 4. AI 秘书自动化流程设计

AI 秘书（Secretary Agent）在后台运行一个轮询任务或监听 Webhook，执行以下核心流程：

### 流程 1：Lark 到 Meegle 的推送 (Push)

1.  **扫描**: AI 秘书定期（如每 5 分钟）调用 `feishu-bitable` 技能，查询 Lark 功能表中 `状态 = '开发中'` 且 `Meegle ID 为空` 的记录。
2.  **数据准备**: 提取这些记录的字段，根据【字段映射表】转换为 Meegle API 所需的 JSON 格式。
3.  **用户匹配**: 调用 Meegle 的 `/user/query` 接口，尝试将 Lark 的负责人匹配为 Meegle 的 `user_key`。
4.  **创建工作项**: 调用 `meegle-lark` 技能的 API，在 Meegle 的指定项目空间（如 `42nqu9`）中创建 `story` 类型的工作项。
5.  **回写关联**: 获取创建成功后返回的 `work_item_id`，调用飞书 API 更新 Lark 中对应记录的 `Meegle ID` 字段。
6.  **通知**: 通过 Telegram 向项目经理发送通知：“已自动将 [功能名称] 推送至 Meegle，ID: [ID]”。

### 流程 2：Meegle 到 Lark 的状态回传 (Sync)

1.  **接收变更**: AI 秘书提供一个 Webhook 接口，接收来自 Meegle 的工作项变更事件（需在 Meegle 开发者平台配置）。
2.  **解析事件**: 解析 Webhook payload，提取 `work_item_id` 和变更后的 `status`。
3.  **查找记录**: 在 Lark 功能表中，根据 `Meegle ID == work_item_id` 查找对应的记录。
4.  **状态转换**: 根据【状态映射字典】，将 Meegle 的状态转换为 Lark 的状态选项。
5.  **更新 Lark**: 调用飞书 API，更新该记录的“状态”字段。
6.  **通知 (可选)**: 如果状态变更为“已上线”，通过 Telegram 发送捷报。

## 5. 异常处理机制

*   **API 调用失败**: 如果 Meegle 或飞书 API 调用失败（如网络抖动、Token 过期），AI 秘书应记录错误日志，并在下一个轮询周期重试（最多重试 3 次）。
*   **用户匹配失败**: 如果无法将 Lark 负责人映射到 Meegle 用户，则在 Meegle 中创建工作项时将 `assignee` 留空，并在 Telegram 通知中提示项目经理手动分配。
*   **数据不一致**: 提供一个 Telegram 指令 `强制同步 [Meegle ID]`，允许项目经理在发现状态不同步时，手动触发一次从 Meegle 到 Lark 的单向强制覆盖。

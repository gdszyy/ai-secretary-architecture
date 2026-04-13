# Lark 群消息读取功能规划与架构设计

**作者**: Manus AI
**日期**: 2026-04-13
**关联文档**: [`info_source_master_plan.md`](./info_source_master_plan.md), [`lark_bot_and_minutes_integration_guide.md`](./lark_bot_and_minutes_integration_guide.md)

---

## 1. 背景与目标

在 AI Management 项目看板（Kanban）的信息源体系中，Lark 群聊是项目沟通的主阵地，包含了大量隐性知识、临时决策与碎片化需求。为了实现看板数据的自动化流转，必须建立稳定、可靠的群消息读取机制。

本文档旨在详细规划 Lark 群消息的读取功能，涵盖实时事件订阅与历史消息拉取双重机制，并针对飞书开放平台的最新 API 限制（如 2024 年 11 月生效的历史消息可见性管控）提出相应的架构设计与应对策略。

---

## 2. 核心读取机制设计

为了确保信息捕获的全面性与系统的鲁棒性，群消息读取机制采用“**实时事件驱动为主，定时拉取补偿为辅**”的双轨架构。

### 2.1 实时事件驱动（Primary）

系统依赖飞书开放平台的 `im.message.receive_v1` 事件订阅机制，实现群消息的实时捕获。

*   **权限要求**：必须具备 `im:message.group_msg`（获取群组中所有消息）敏感权限，以便接收群内所有成员的消息（不包含机器人自身发送的消息）[1]。
*   **事件链路**：当用户在目标群组发送消息时，飞书开放平台通过长连接或 Webhook 将事件推送到系统的接收网关。网关负责验签、解析消息体（提取 `chat_id`、`message_id`、`message_type` 等），并将其推入信息缓冲区（Buffer）进行后续的清洗与意图识别。
*   **幂等性保障**：由于飞书事件推送可能存在重试机制导致重复推送，系统必须在接收网关层基于 `message_id` 实现严格的去重逻辑，禁止依赖 `event_id` 进行去重[1]。

### 2.2 历史消息拉取补偿（Secondary）

为了应对服务重启、网络断开或事件丢失等异常情况，系统需提供历史消息的拉取补偿能力。

*   **接口选择**：使用飞书开放平台的 `GET /open-apis/im/v1/messages` 接口获取指定会话的历史消息[2]。
*   **拉取策略**：系统定期（如每小时）比对缓冲区中记录的最新 `message_id`，若发现时间断层，则触发补偿拉取。通过指定 `container_id_type` 为 `chat`，并结合 `start_time` 与 `end_time` 参数，分页（`page_token`）获取遗漏时间段内的消息记录。
*   **话题消息处理**：普通群中的话题（Thread）消息，通过 `chat` 容器仅能获取话题的根消息。若需获取话题内的回复，必须指定容器类型为 `thread` 并进行二次拉取[2]。

---

## 3. 关键限制与应对策略

飞书开放平台对群消息读取存在多项严格的权限管控与安全限制，系统设计必须妥善应对。

### 3.1 历史消息可见性管控（2024-11-14 变更）

飞书于 2024 年 11 月 14 日启用了严格的历史消息可见性管控。当群聊关闭“新成员可查看历史消息”设置时，操作者（包括机器人）将无法获取其入群前的历史消息，且新版本接口将报错 `230050`[3]。

*   **应对策略**：
    *   **入群规范**：在《AI 秘书使用 SOP》中明确规定，项目经理在邀请 AI 秘书入群前，必须确保该群已开启“新成员可查看历史消息”设置。
    *   **异常捕获**：在拉取历史消息时，若捕获到 `230050` 错误，系统应自动向该群发送提示消息，要求管理员修改群设置或通过 @AI秘书 的方式触发特定话题的可见性。

### 3.2 保密模式限制

若群聊开启了保密模式，系统调用拉取接口将返回 `231203` 错误（The chat type is not supported）[2]。

*   **应对策略**：AI 项目秘书不支持在保密群组中运行。当检测到保密模式时，系统应在日志中记录并标记该群为“受限群组”，停止对其的轮询拉取。

### 3.3 消息类型与富文本解析

飞书消息分为纯文本（`text`）、富文本（`post`）、图片（`image`）等多种类型。

*   **应对策略**：
    *   初期（第一阶段）仅处理 `text` 与 `post` 类型的消息。
    *   对于文本中包含的 `@提及`，飞书以 `<at user_id="xxx">` 的格式嵌入。系统在入缓冲池前，需调用通讯录 API 将 `user_id` 转换为实际的用户姓名，以提高 LLM 意图识别的准确率。

---

## 4. 数据结构与接口映射

在消息进入缓冲池前，需进行标准化的格式转换。

### 4.1 飞书原始事件 Payload 示例

```json
{
    "schema": "2.0",
    "header": {
        "event_id": "f7984f25108f8137722bb63ce9275f73",
        "event_type": "im.message.receive_v1",
        "create_time": "1609073151345"
    },
    "event": {
        "sender": {
            "sender_id": {
                "open_id": "ou_7d8a6e6df7621556ce0d21922b676706"
            },
            "sender_type": "user"
        },
        "message": {
            "message_id": "om_dc13264520533f5811c08d020c67ed37",
            "chat_id": "oc_5ad11d72b830411d72b836c20",
            "message_type": "text",
            "content": "{\"text\":\"@_user_1 下周要把活动中心的预算配置功能加上\"}"
        }
    }
}
```

### 4.2 缓冲池标准输入结构

经过清洗后的数据结构如下，直接对接模块二（Buffer Module）：

```json
{
    "source_type": "lark_group",
    "source_message_id": "om_dc13264520533f5811c08d020c67ed37",
    "metadata": {
        "chat_id": "oc_5ad11d72b830411d72b836c20",
        "sender_id": "ou_7d8a6e6df7621556ce0d21922b676706",
        "timestamp": 1609073151345
    },
    "raw_content": "下周要把活动中心的预算配置功能加上"
}
```

---

## 5. 实施计划

本功能的开发与上线分为三个阶段：

1.  **Phase 1：实时接收与解析（1周）**
    *   配置飞书应用 Webhook，订阅 `im.message.receive_v1` 事件。
    *   实现消息接收网关、验签逻辑与 `message_id` 去重机制。
    *   实现纯文本与富文本消息的初步清洗，并对接缓冲池 API。
2.  **Phase 2：历史补偿与异常处理（1周）**
    *   开发定时拉取补偿脚本，调用 `/open-apis/im/v1/messages` 接口。
    *   实现对 `230050`（历史不可见）和 `231203`（保密模式）错误码的捕获与告警。
3.  **Phase 3：富媒体与话题支持（后续迭代）**
    *   增加对话题（Thread）回复的递归拉取支持。
    *   探索图片和文件类型消息的下载与多模态解析能力。

---

## 参考资料

[1] 飞书开放平台, "接收消息 - 服务端 API," 飞书开发者文档. https://open.feishu.cn/document/server-docs/im-v1/message/events/receive?lang=zh-CN
[2] 飞书开放平台, "获取会话历史消息 - 服务端 API," 飞书开发者文档. https://open.feishu.cn/document/server-docs/im-v1/message/list?lang=zh-CN
[3] 飞书开放平台, "消息相关事件及 API 将进行历史消息可见性管控," 飞书开发者文档. https://open.feishu.cn/document/platform-notices/breaking-change/visibility-control-of-historical-messages?lang=zh-CN

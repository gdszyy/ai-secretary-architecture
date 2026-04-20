# 交接文档：飞书卡片回复自动触发信息纠正

**交接时间**：2026-04-21  
**交接人**：Manus AI  
**接收人**：VoidZ / 下一任接手 Agent  
**关联需求**：[PF-001: 飞书卡片回复自动触发信息纠正](../module2_buffer/lark_card_reply_correction_spec.md)

---

## 1. 当前进度与现状

目前，AI 秘书系统已经完成了**意图分类体系重构**和**手动信息纠正机制**的开发：
- 废弃了旧版"事事追问"的逻辑，改为只记录高价值事实（重大决策、里程碑、风险阻塞）。
- 实现了 `scripts/manual_correction.py`，支持通过脚本将 VoidZ 补充的纠正信息（如 SR 商务替换、Smartico 选型等）写入 Bitable。
- 在每周四的风险提醒卡片和周报卡片底部，已经加上了"回复本卡片进行纠正"的提示文案。

**缺失的最后一环**：飞书机器人目前无法"听到"用户在群里对卡片的回复，因此无法自动触发 `manual_correction.py`，必须依赖人工（VoidZ 告知 Manus，Manus 运行脚本）。

---

## 2. 下一步开发目标

实现**飞书事件订阅服务**，让机器人能够接收群聊消息，解析纠正指令，并自动调用写入脚本，完成信息纠正的闭环。

---

## 3. 飞书权限申请清单（必须前置完成）

要让机器人能够接收群聊消息并回复，需要在[飞书开发者后台](https://open.larksuite.com/app)为当前应用（App ID: `cli_a9d985cd40f89e1a`）申请以下权限并发布新版本：

### 3.1 权限管理 (Permissions)
在"权限管理"页面，搜索并开通以下权限：
- **获取群组信息** (`im:chat:readonly`)：用于验证消息来源群组。
- **获取用户发给机器人的单聊消息** (`im:message:readonly`)：如果支持私聊纠正。
- **获取群组中所有消息** (`im:message.group_msg:readonly`)：**核心权限**，必须开通才能收到群内回复卡片的消息。
- **读取与发送单聊、群聊消息** (`im:message`)：用于发送确认回复。

### 3.2 事件订阅 (Event Subscriptions)
在"事件订阅"页面，配置并开启以下事件：
- **接收消息** (`im.message.receive_v1`)：这是最核心的事件，当用户在群里回复卡片时，飞书会向配置的 Webhook 地址推送此事件。

### 3.3 Webhook 地址配置
在"事件订阅"页面，需要配置一个**请求网址 (Webhook URL)**。
- 飞书要求该地址必须是公网可访问的 HTTPS 地址。
- **解决方案**：在服务器上部署 `lark_webhook_server.py`（FastAPI），并通过 Nginx/Caddy 配置 HTTPS 域名，或者在开发阶段使用 ngrok/localtunnel 进行内网穿透。

---

## 4. 技术实现路径建议

接手此需求的 Agent 应按照以下步骤执行：

### Step 1: 模块化重构
将 `scripts/manual_correction.py` 中的 `update_record` 和 `create_record` 逻辑提取出来，封装成 `scripts/correction_writer.py`，使其可以被其他 Python 脚本作为模块导入调用。

### Step 2: 开发 Webhook 服务
编写 `scripts/lark_webhook_server.py`，使用 FastAPI 框架：
1. 实现飞书事件订阅的 Challenge 验证接口。
2. 实现 `im.message.receive_v1` 事件的处理逻辑。
3. 提取消息文本，使用正则匹配 `纠正：...` 或 `补充：...` 前缀。
4. （可选）集成 LLM 调用，对格式不严格的回复进行意图和标题的智能解析。

### Step 3: 部署与联调
1. 启动 FastAPI 服务。
2. 配置公网 URL 到飞书开发者后台。
3. 在测试群内回复卡片，观察服务日志，确认 Bitable 记录被正确更新。

---

## 5. 附录：参考文档

- [飞书开放平台：接收消息事件文档](https://open.larksuite.com/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/events/receive)
- [飞书开放平台：事件订阅配置指南](https://open.larksuite.com/document/ukTMukTMukTM/uUTNz4SN1MjL1UzM)

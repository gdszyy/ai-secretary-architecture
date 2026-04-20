# Agent 驱动的周报汇总触发机制设计

## 1. 设计理念：从“跑批脚本”到“Agent 协作”

传统的周报生成往往依赖死板的跑批脚本（Cron Job），但在多源数据（飞书多维表格、Meegle、群聊）的场景下，数据往往存在缺失、歧义或需要归因判断。

因此，本次触发机制设计的核心理念是：**让 AI Agent 成为周报生成的“主理人”**。通过 Manus 的定时任务唤醒主 Agent，主 Agent 利用 `multi-agent-hub` 技能派发子任务进行数据收集与分析，并在遇到信息断层时主动通过 `lark-secretary` 向人类追问，最终完成高质量的周报汇总。

## 2. 触发机制全景图

触发机制分为**定时唤醒（主线）**和**指令唤醒（副线）**，两者都将启动同一个 Agent 协作工作流。

### 2.1 主线：Manus 定时任务唤醒

*   **触发器**：利用 Manus 平台的 `schedule` 工具，设置每周二下午 14:00 自动执行。
*   **执行主体**：Manus Lite（根据用户偏好，自动化任务交由 Lite 执行）。
*   **Prompt 设定**：
    > “现在是每周二的周报汇总时间。请作为项目协调者，使用 `multi-agent-hub` 技能创建一个周报生成任务。你需要派发子 Agent 去收集飞书多维表格（使用 `xp-weekly-report` 技能）、Meegle 进度和群聊洞察。如果发现某位核心成员未填写周报，请使用 `lark-secretary` 在群内提醒他。最后将汇总结果写入 `dashboard_data.json` 并推送到 GitHub。”

### 2.2 副线：飞书 Bot 指令唤醒

*   **触发器**：PM 在飞书群内发送 `@AI秘书 开始汇总本周周报`。
*   **执行主体**：`ai-secretary-architecture` 的 Webhook 服务（`main.py`）。
*   **流转逻辑**：Webhook 接收到指令后，不直接在后台跑脚本，而是通过调用 Manus API（或通过 `multi-agent-hub` 的任务队列），向 Manus 平台下发一个高优先级的周报生成任务，唤醒 Agent 介入。

## 3. Agent 协作工作流 (Workflow)

一旦 Agent 被唤醒，将严格遵循 `multi-agent-hub` 的五道护栏，执行以下协作流程：

### Phase 1: 任务初始化与派发 (协调者 Agent)

1.  **注册与建单**：主 Agent 使用 `hub_client.py register` 注册为 `project_manager`，并使用 `create-task` 创建“W16 周报汇总”主任务。
2.  **派发数据收集子任务**：
    *   主 Agent 使用 `manus_dispatch.py` 派发子 Agent A（数据专员）。
    *   **注入上下文**：明确要求子 Agent A 使用 `xp-weekly-report` 技能提取飞书表格数据，并运行 `meegle_client.py` 和 `extract_weekly_insights.py`。
    *   **注入连接器**：传入 GitHub 仓库的连接器 ID，确保子 Agent A 有权限读取和写入数据。

### Phase 2: 数据收集与智能归因 (执行者 Agent A)

1.  **执行提取**：子 Agent A 运行脚本获取三源数据。
2.  **智能断点处理（Agent 的核心价值）**：
    *   *场景 A*：发现 VoidZ 的飞书周报状态为“未填写”。子 Agent A 暂停汇总，使用 `lark-secretary` 发送群消息：“@VoidZ 您的本周周报尚未填写，请尽快补充，以免影响全局进度汇总。”
    *   *场景 B*：Yark 填写的周报内容为“修复了登录页的几个 UI 样式”。子 Agent A 运用 LLM 推理，将其精准映射到 `mod_uiux_design` 模块下。
3.  **提交成果**：子 Agent A 将结构化好的多源数据保存为临时 JSON，使用 `hub_repo.py save-result` 提交到 Git，并执行 `complete-task`。

### Phase 3: 综合摘要与发布 (协调者 Agent)

1.  **验收数据**：主 Agent 收到子任务完成通知，执行 `hub_repo.py read-context` 读取子 Agent A 整理的数据。
2.  **生成摘要**：主 Agent 运用其强大的长文本理解能力，基于多源数据为每个模块撰写高质量的综合摘要（`update` 字段）。
3.  **数据注入与持久化**：
    *   主 Agent 运行 `inject_weekly_updates.py`，将最终数据写入 `dashboard_data.json`。
    *   执行 `git commit` 和 `git push`，触发前端看板更新。
4.  **闭环通知**：主 Agent 使用 `lark-secretary` 向飞书群发送富文本卡片（Interactive Card），通知全员：“✅ W16 周报已生成，看板已更新。点击查看详情。”
5.  **任务归档**：主 Agent 在 Hub 中执行 `review-task` 验收通过，并结束整个工作流。

## 4. 为什么必须是 Agent 驱动？

相比于纯代码跑批，Agent 驱动的触发机制具有不可替代的优势：

1.  **容错与自愈**：跑批脚本遇到数据缺失（如某人没写周报）通常只能报错或跳过；Agent 可以主动发消息催促，甚至根据历史上下文做合理推断。
2.  **非结构化数据处理**：飞书周报是自由文本，将其准确映射到具体的 Module ID 需要 LLM 的深度参与，这是传统正则匹配难以做到的。
3.  **可追溯的协作过程**：通过 `multi-agent-hub`，周报生成的每一步（数据收集、归因、摘要）都有明确的 Git 留痕和责任归属，不再是一个“黑盒”脚本。

# AI项目秘书打包为 Manus Skill 的可行性分析与架构设计

## 1. 结论：高度可行且极具价值

将“AI项目秘书系统”打包为一个 Manus Skill（例如命名为 `ai-project-secretary`）是**完全可行**的。
通过 Skill 机制，我们可以将原本需要额外部署的后端服务（如 FastAPI、定时任务、Webhook 监听）转化为 Manus Agent 的内置能力。Manus Agent 本身具备强大的自然语言理解、意图识别和工具调用能力，这使得它天然适合承担“信息缓冲区”的清洗、打分和主动询问工作，同时也能够直接调用 `feishu-bitable` 和 `meegle-lark` 技能完成工作区的调度。

## 2. 传统架构 vs. Skill 架构对比

| 维度 | 传统落地方案 (独立后端服务) | Manus Skill 方案 (Agent 承接) | 优势分析 |
| :--- | :--- | :--- | :--- |
| **核心大脑** | 需自行接入 LLM API 并编写复杂的 Prompt 链 | 直接利用 Manus Agent 的原生大模型能力 | 降低开发成本，意图识别更智能、更灵活 |
| **交互方式** | 需开发 Telegram/Lark Bot 接收 Webhook | 用户直接在 Manus 对话框中输入碎片信息 | 零开发成本，支持多模态（语音、图片）输入 |
| **主动询问** | 需实现复杂的状态机和定时推送逻辑 | Agent 根据 Skill 指令直接在对话中追问 | 交互更自然，符合人类直觉 |
| **系统集成** | 需自行编写代码调用飞书和 Meegle API | 直接复用现有的 `feishu-bitable` 和 `meegle-lark` 技能 | 模块化复用，降低维护成本 |
| **部署成本** | 需要服务器、域名、数据库、定时任务配置 | **零部署**，开箱即用 | 极大地降低了落地门槛 |

## 3. `ai-project-secretary` Skill 架构设计

根据 `skill-creator` 的规范，我们将该 Skill 设计为“高自由度（文本指令为主）+ 中自由度（辅助脚本）”的混合模式。

### 3.1 目录结构规划

```text
ai-project-secretary/
├── SKILL.md                 # 核心指令：定义秘书的角色、工作流、缓冲区规则
├── scripts/
│   ├── sync_lark_meegle.py  # 脚本：执行 Lark 到 Meegle 的状态同步与回写
│   └── check_buffer.py      # 脚本：检查本地存储的缓冲区状态，执行防堆积策略
├── references/
│   ├── intent_mapping.md    # 知识库：意图分类标准与目标系统映射表
│   └── sop_guidelines.md    # 知识库：PM 交互 SOP 与主动询问话术模板
└── templates/
    └── buffer_schema.json   # 模板：信息缓冲区条目的标准 JSON 结构
```

### 3.2 核心工作流 (定义在 SKILL.md 中)

当用户在 Manus 中触发该 Skill 时，Agent 将遵循以下工作流：

1.  **接收与清洗 (Buffer Phase)**:
    *   接收用户的自然语言输入（碎片信息）。
    *   在内存中（或本地 JSON 文件中）实例化一个 `buffer_schema.json` 对象。
    *   利用 Agent 自身的理解能力，提取意图、模块、关键实体，并进行完整度打分。
2.  **主动询问 (Inquiry Phase)**:
    *   如果评分 < 80，Agent 暂停派发，直接在当前对话中向用户发起追问（参考 `sop_guidelines.md` 中的话术）。
    *   等待用户回复后，更新 Buffer 对象并重新打分。
3.  **调度与派发 (Dispatch Phase)**:
    *   当评分 ≥ 80，Agent 根据 `intent_mapping.md` 决定去向。
    *   **调用其他 Skill**：Agent 主动调用 `feishu-bitable` 写入 Lark，或调用 `meegle-lark` 创建工作项。
4.  **状态同步 (Sync Phase)**:
    *   Agent 可以定期（或在用户指令下）运行 `scripts/sync_lark_meegle.py`，拉取 Lark 中状态为“开发中”的记录，推送到 Meegle，并完成双向状态对齐。

## 4. 关键技术调整与解决路径

在转化为 Skill 的过程中，原方案中的某些机制需要进行适配调整：

1.  **从“被动 Webhook”转为“主动轮询/触发”**:
    *   *原方案*：Meegle 状态变更通过 Webhook 通知后端。
    *   *Skill 方案*：Manus Agent 无法一直保持后台运行监听 Webhook。解决方案是：将状态同步做成一个 Python 脚本 (`sync_lark_meegle.py`)。PM 可以在对话中输入“同步状态”，Agent 执行脚本完成双向对齐；或者结合 `default_api:schedule` 工具，让 Agent 每天定时执行同步任务。
2.  **缓冲区的持久化**:
    *   *原方案*：存在数据库中。
    *   *Skill 方案*：利用沙盒文件系统，将未完成的 Buffer 条目保存在 `/home/ubuntu/.secretary/buffer.json` 中。Agent 每次启动时先读取该文件，恢复上下文。
3.  **防堆积策略的执行**:
    *   *Skill 方案*：通过 `scripts/check_buffer.py` 脚本实现。Agent 在每次处理新信息前，先运行该脚本清理过期条目，并将结果反馈给用户。

## 5. 实施建议

1.  **第一步：初始化 Skill**。使用 `skill-creator` 的 `init_skill.py` 创建基础目录。
2.  **第二步：编写 Prompt**。将现有的 `buffer_to_workspace_flow.md` 和 `inquiry_strategy.md` 转化为 `SKILL.md` 中对 Agent 的系统指令。
3.  **第三步：开发粘合脚本**。编写 `sync_lark_meegle.py`，该脚本内部封装对 `feishu-bitable` 和 `meegle-lark` API 的调用，简化 Agent 的操作步骤。
4.  **第四步：测试与迭代**。在 Manus 对话中加载该 Skill，模拟 PM 发送碎片信息，测试 Agent 的追问逻辑和派发准确率。

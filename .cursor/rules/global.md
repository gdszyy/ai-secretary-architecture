---
description: "ai-secretary-architecture 系统的全局架构概述、核心工作流串联及全局禁止行为清单"
globs: ["README.md", "docs/**/*.md"]
---

# 全局架构规范 (Global Architecture)

## 1. 架构概述

本仓库是 **AI 项目秘书系统**的核心架构设计文档库，同时也是多 Agent 协作项目的文档库。系统目标是为项目经理（PM）构建一套智能化的信息管理与状态同步体系，将碎片化信息自动转化为结构化工作项。

系统架构分为四个核心层级：

| 层级 | 名称 | 职责 |
|------|------|------|
| 入口层 | Input Layer | 多渠道接收（Telegram / Lark / 语音）PM 的碎片信息或标准指令 |
| 处理层 | Information Buffer | LLM 意图识别、实体提取、完整度评分（<80分触发询问，≥80分进入派发队列） |
| 调度层 | Dispatcher | 意图路由、API Payload 转换、幂等性检查 |
| 工作区层 | Workspace | Lark 多维表格（宏观看板）+ Meegle（研发执行引擎）+ GitHub Issues / Lark Wiki |

**关联仓库三角**：

- `gdszyy/ai-secretary-architecture`（本仓库）：核心架构文档库，信噪比 ~100%
- `gdszyy/xpbet-frontend-components`：前端工程与组件库
- `gdszyy/manus-lark-skills`：通用 Agent 技能库（Lark API 集成等）

**核心入口文件**：

| 文件 | 说明 |
|------|------|
| `main.py` | FastAPI 后端服务主入口（587行），包含 Lark Webhook 接收、消息处理、Bitable 写入逻辑 |
| `scripts/thread_separator.py` | 消息线程分离算法（713行，含巨型函数，详见 auto_index） |
| `scripts/lark_bitable_client.py` | Lark Bitable API 客户端封装 |
| `scripts/meegle_client.py` | Meegle API 客户端封装 |

## 2. 核心工作流串联

### 需求流转主线 (Feature Workflow)

1. PM 通过 Telegram/Lark 发送碎片想法
2. **缓冲区**接收，LLM 识别意图并评分
3. 完整度 < 80 分 → 触发批量询问；≥ 80 分 → 状态变为 `ready`
4. **调度器**推送到 Lark 多维表格，创建"待规划"记录
5. PM 在 Lark 中调整状态为"开发中"
6. **调度器**监听状态变更，自动调用 Meegle API 创建 Story，并将 Meegle ID 回写 Lark
7. 研发在 Meegle 完成开发后，调度器通过 Webhook 将 Lark 状态更新为"已上线"

### 缺陷与备忘流转副线 (Bug & Memo Workflow)

- **Bug**：缓冲区识别为高优 Bug Report → 直接 `ready` → 推送到 GitHub Issue 或 Meegle Defect
- **Memo**：缓冲区识别为 Memo，提取时间实体 → 存入 Lark 多维表格备忘视图 + 设置定时提醒

## 3. 全局禁止行为清单

为保障项目架构的纯净性和系统稳定性，特制定以下禁止行为清单：

1.  **禁止破坏"代码-文档同步"契约**：在修改任何架构设计、API 或核心逻辑时，必须同步更新 `.cursor/rules/` 下对应的规则文档。
2.  **禁止硬编码凭证信息**：在所有文档示例和代码中，严禁出现真实的 API Key、Token 或密码，必须使用占位符代替。
3.  **禁止跳过流程洞察沉淀**：在任务中发现隐蔽逻辑或耦合陷阱时，必须在 `.cursor/rules/process_insights/` 中记录对应洞察。
4.  **禁止手动编辑自动索引**：`.cursor/rules/auto_index/` 目录下的文件由 `code-indexer` 脚本自动生成，严禁手动编辑。
5.  **巨型函数必须标记内部节点**：当函数超过 200 行时，必须在内部按业务逻辑块添加 `// @section:{snake_case_name} - {一句话说明}` 标记，以便索引器提取内部节点。
6.  **禁止主动读取归档区**：`archive/` 和 `tasks/` 目录为历史归档区，Agent 默认严禁主动读取，除非任务明确要求追溯历史。
7.  **禁止破坏 Single Source of Truth 原则**：进入开发前 Lark 为主，进入开发后（存在 Meegle ID）Meegle 为主，严禁在两侧同时手动修改状态。
8.  **禁止 AI 自动生成里程碑**：里程碑必须由项目管理人员手动设定，AI 仅负责追踪和倒推 Buffer，严禁自动向 `dashboard_data.json` 写入新的里程碑。

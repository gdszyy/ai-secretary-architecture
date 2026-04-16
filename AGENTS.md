# AI Secretary Architecture 全局协作规范 (AGENTS.md)

本文档是 `ai-secretary-architecture` 仓库中所有 AI Agent（包括临时 Agent 和常驻 Agent）必须遵守的协作规范和工作指南。它定义了全局的编辑策略、文档风格约定以及各模块的规范文档索引。

## 1. 快速导航与核心入口规范 (Quick Navigation)

为了确保各技能 (Skills) 与本项目之间的索引契约一致，所有 Agent 在介入本项目时，**必须**优先阅读以下入口文档：

- **项目全局规范入口**：本文档 (`AGENTS.md`)，包含核心编辑策略、禁止行为与文档索引。
- **架构与防坑指南**：[`.cursor/rules/global.md`](.cursor/rules/global.md)（必读，包含系统整体架构与设计原则）。
- **核心哲学**：[`CORE_PHILOSOPHY.md`](CORE_PHILOSOPHY.md)（AI 秘书的愿景、角色定位与核心价值观）。
- **全局 SOP**：[`SOP.md`](SOP.md)（项目经理与 AI 秘书交互的标准指令）。

所有专门针对本项目的技能 (如 `ai-secretary-architect`) 仅需指引 Agent 阅读上述入口，无需在技能文件内硬编码具体的架构细节。

---

## 2. 全局 AI 编辑策略规范

本项目是一个纯 Markdown 文档仓库，不包含业务代码。为了保证文档库的高信噪比和结构一致性，所有 AI Agent 在修改文档时，必须遵循以下**智能编辑策略决策树**：

### 智能编辑策略决策树

1. **微型修改（< 20 行）**：使用搜索替换或行内编辑，适用于修复错别字、调整局部排版、更新少量数据。
2. **中型修改（20 - 200 行）**：局部重写或追加内容，适用于重构单一章节、添加新段落、调整局部结构。
3. **大型修改（> 200 行）**：全文件重写，仅在文档本身较小且需要彻底重构时使用；对于超长文档，必须先拆分为多个子文档。

### 强制要求

- **活文档契约（代码-文档同步）**：任何对系统架构、SOP 或模块设计的实质性修改，**必须在同一个 Commit 中同步更新对应模块的规范文档**（位于 `.cursor/rules/` 目录下）。
- **历史文档归档**：过期的设计方案和旧版本的任务记录应移动到 `archive/tasks_history/` 目录，保持活跃文档区的整洁。

---

## 3. 文档风格约定

本项目采用纯 Markdown 架构。所有新编写或重构的文档必须遵循以下风格：

- **结构清晰**：使用标准 Markdown 标题层级（H1, H2, H3），避免过深的嵌套。
- **高信噪比**：内容必须精炼、准确，避免冗长的废话和重复的说明。
- **表格优先**：对于结构化数据、对比分析或索引列表，优先使用 Markdown 表格呈现。
- **引用与链接**：跨文档引用时，必须使用相对路径链接，确保在 GitHub 和本地编辑器中均可点击。
- **Lark 文档规范**：如果涉及飞书云文档的生成，必须遵循 `docs/project/lark-doc-creation-spec.md` 中的规范。

---

## 4. 仓库目录结构索引

### 4.1 文档层（`docs/`）

| 目录 | 用途 |
|------|------|
| `docs/project/` | 项目级文档：总览、启动报告、Lark 规范、看板数据驱动可行性评估 |
| `docs/module1_kanban/` | 模块一（看板）的设计文档，含可视化架构、数据链路设计 |
| `docs/module2_buffer/` | 模块二（信息缓冲池）的设计文档 |
| `docs/module3_info_sources/` | 模块三（信息源治理）的设计文档 |
| `docs/architecture/` | 跨模块架构决策文档：仓库拆分评估、任务交接、技能索引、迁移清单等 |

### 4.2 数据层（`data/`）

| 文件 | 用途 | 更新方式 |
|------|------|----------|
| `data/dashboard_data.json` | 看板前端唯一数据源，包含大模块分组、小模块状态、里程碑、周报、KPI 指标 | 运行 `scripts/` 下的脚本后 git push，前端通过 GitHub Raw URL 自动读取 |

**Schema 约定**：`dashboard_data.json` 的字段结构由 `docs/module1_kanban/dashboard_visualization_architecture.md` 定义，任何字段变更必须同步更新该文档。

### 4.3 脚本层（`scripts/`）与服务入口层

所有脚本均为 Python 3，依赖飞书 Bitable API 和 OpenAI/Forge API。运行前需确保 `.env` 中配置了对应凭证（参考 `.env.example`）。

**服务入口文件（根目录）**：

| 文件 | 用途 |
|------|------|
| `main.py` | FastAPI Webhook 服务入口，接收飞书事件推送，路由至缺陷报送或对话分离流程 |
| `requirements.txt` | Python 依赖清单，供 Railway 等云平台自动安装 |
| `Procfile` | Railway 启动配置，指定 uvicorn 启动命令 |

| 脚本 | 用途 | 调用时机 |
|------|------|----------|
| `parse_to_dashboard_json.py` | 从 Markdown 文档通过 LLM 提取结构化数据，生成初始 `dashboard_data.json` | 冷启动或全量重建时 |
| `sync_bitable_docs.py` | 从飞书 Bitable 功能表同步文档链接到 `dashboard_data.json` | 每次 Bitable 更新后 |
| `inject_weekly_updates.py` | 将本周周报数据注入 `dashboard_data.json` 的 `weekly_updates` 字段 | 每周二晚截止后 |
| `add_group_milestones.py` | 为大模块分组添加里程碑列表和进度计算 | 里程碑变更时 |
| `enrich_global_milestones.py` | 为整体里程碑添加各大模块状态快照（`group_snapshots`） | 里程碑变更时 |
| `inspect_bitable.py` | 诊断脚本：打印 Bitable 实际字段名和数据，用于调试映射问题 | 调试时 |
| `lark_bitable_client.py` | 飞书 Bitable API 封装客户端，供其他脚本复用 | 被其他脚本 import |
| `cold_start_step*.py` | 冷启动四步流程：列出群组→抓取消息→LLM 画像→写入 Bitable | 系统初始化时 |
| `extract_weekly_insights.py` | 从飞书群消息中提取本周关键洞察 | 每周定期运行 |
| `generate_markdown_report.py` | 生成 Markdown 格式周报 | 每周定期运行 |
| `media_pipeline.py` | 媒体消息解析流水线（图片/语音/文件） | 按需运行 |
| `thread_separator.py` | 多对话分离算法：两阶段（实体聚类 + LLM）将混杂群聊消息分离为独立 ThreadEvent | 被 `main.py` 调用，或独立运行 `--demo` 验证 |

### 4.4 归档层（`archive/`）

| 目录 | 用途 |
|------|------|
| `archive/tasks_history/` | 历史任务交付物快照、沉淀文档（飞书周报、模块进度报告等） |
| `archive/tasks_history/source_tasks/` | 多 Agent 协作任务的原始交付物，按任务 ID 归档 |

---

## 5. 子模块规范文档索引

为了指导各个子模块的设计和演进，项目在 `.cursor/rules/` 目录下维护了详细的模块规范文档：

| 规范文件 | 覆盖范围 |
|----------|----------|
| [`.cursor/rules/global.md`](.cursor/rules/global.md) | 系统全景架构、核心工作流串联、全局禁止行为清单、`scripts/` 调用规范 |
| [`.cursor/rules/module1_kanban.md`](.cursor/rules/module1_kanban.md) | 模块一：Lark 多维表格看板、Meegle 关联、看板可视化数据链路 |
| [`.cursor/rules/module2_buffer.md`](.cursor/rules/module2_buffer.md) | 模块二：信息缓冲池机制、意图识别、防堆积策略 |
| [`.cursor/rules/module3_info_sources.md`](.cursor/rules/module3_info_sources.md) | 模块三：信息源治理、Lark Bot 集成 |
| [`.cursor/rules/agent_skills.md`](.cursor/rules/agent_skills.md) | 跨项目复用技能的调用规范（`lark-bitable`、`multi-agent-hub` 等） |
| [`.cursor/rules/implementation_status.md`](.cursor/rules/implementation_status.md) | **系统实现状态全景索引**：已实现能力清单 + TODO 任务优先级列表（P0/P1/P2） |

> **注意**：随着架构的演进，本索引应持续更新。负责重构的 Agent 需维护对应的规则文档。

---

## 6. 系统实现进度快照

> **最后更新**：2026-04-16 | 详细清单见 [`.cursor/rules/implementation_status.md`](.cursor/rules/implementation_status.md)

```
整体进度：████████░░░░░░░░░░░░  ~40%

Module 1（看板）     ████████████░░░░░░░░  60%  数据层和脚本层已完整，双向同步待实现
Module 2（缓冲池）   ████████░░░░░░░░░░░░  40%  核心算法已实现，集成层（回复/推送）待完成
Module 3（信息源）   ████░░░░░░░░░░░░░░░░  20%  冷启动脚本已实现，实时监听（Lark Bot）待开发
服务入口层           ██████████████░░░░░░  70%  Webhook 框架已就绪，签名校验和消息回复待补全
```

**最高优先级 TODO（P0）**：
- `TODO-P0-01`：实现 `send_lark_message`，让系统能将追问话术和成功通知发回飞书群
- `TODO-P0-02`：补全 Lark Webhook 签名校验（当前框架已有，返回值待接入真实比对逻辑）

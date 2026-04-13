# AI Secretary Architecture 全局协作规范 (AGENTS.md)

本文档是 `ai-secretary-architecture` 仓库中所有 AI Agent（包括临时 Agent 和常驻 Agent）必须遵守的协作规范和工作指南。它定义了全局的编辑策略、文档风格约定以及各模块的规范文档索引。

## 1. 快速导航与核心入口规范 (Quick Navigation)

为了确保各技能 (Skills) 与本项目之间的索引契约一致，所有 Agent 在介入本项目时，**必须**优先阅读以下入口文档：

*   **项目全局规范入口**：本文档 (`AGENTS.md`)，包含核心编辑策略、禁止行为与文档索引。
*   **架构与防坑指南**：[`.cursor/rules/global.md`](.cursor/rules/global.md)（必读，包含系统整体架构与设计原则）。
*   **核心哲学**：[`CORE_PHILOSOPHY.md`](CORE_PHILOSOPHY.md)（AI 秘书的愿景、角色定位与核心价值观）。
*   **全局 SOP**：[`SOP.md`](SOP.md)（项目经理与 AI 秘书交互的标准指令）。

所有专门针对本项目的技能 (如 `ai-secretary-architect`) 仅需指引 Agent 阅读上述入口，无需在技能文件内硬编码具体的架构细节。

---

## 2. 全局 AI 编辑策略规范

本项目是一个纯 Markdown 文档仓库，不包含业务代码。为了保证文档库的高信噪比和结构一致性，所有 AI Agent 在修改文档时，必须遵循以下**智能编辑策略决策树**：

### 智能编辑策略决策树

1.  **微型修改（< 20 行）**
    *   **策略**：使用搜索替换（Search and Replace）或行内编辑。
    *   **适用场景**：修复错别字、调整局部排版、更新少量数据。
    *   **工具推荐**：使用专用的文本编辑工具（如 `file` 模块的 `edit` 动作）。
2.  **中型修改（20 - 200 行）**
    *   **策略**：局部重写或追加内容。
    *   **适用场景**：重构单一章节、添加新段落、调整局部结构。
3.  **大型修改（> 200 行）**
    *   **策略**：全文件重写（Full File Rewrite）。
    *   **适用场景**：仅在文档本身较小且需要进行彻底重构时使用。对于超长文档，必须先将其拆分为多个子文档。

### 强制要求

*   **活文档契约（代码-文档同步）**：任何对系统架构、SOP 或模块设计的实质性修改，**必须在同一个 Commit 中同步更新对应模块的规范文档**（位于 `.cursor/rules/` 目录下）。
*   **历史文档归档**：过期的设计方案和旧版本的任务记录应移动到 `archive/tasks_history/` 目录，保持活跃文档区的整洁。

## 3. 文档风格约定

本项目采用纯 Markdown 架构。所有新编写或重构的文档必须遵循以下风格：

*   **结构清晰**：使用标准 Markdown 标题层级（H1, H2, H3），避免过深的嵌套。
*   **高信噪比**：内容必须精炼、准确，避免冗长的废话和重复的说明。
*   **表格优先**：对于结构化数据、对比分析或索引列表，优先使用 Markdown 表格呈现。
*   **引用与链接**：跨文档引用时，必须使用相对路径链接，确保在 GitHub 和本地编辑器中均可点击。
*   **Lark 文档规范**：如果涉及飞书云文档的生成，必须遵循 `docs/lark-doc-creation-spec.md` 中的规范。

## 4. 子模块规范文档索引

为了指导各个子模块的设计和演进，项目在 `.cursor/rules/` 目录下维护了详细的模块规范文档。以下是当前的文档索引：

*   **全局架构规范**：[`.cursor/rules/global.md`](.cursor/rules/global.md) - 包含系统全景架构、核心工作流串联及全局禁止行为清单。
*   **看板模块规范**：[`.cursor/rules/module1_kanban.md`](.cursor/rules/module1_kanban.md) - 模块一（Lark 多维表格看板与 Meegle 关联机制）的设计规范与 SOP。
*   **缓冲池模块规范**：[`.cursor/rules/module2_buffer.md`](.cursor/rules/module2_buffer.md) - 模块二（信息缓冲池机制、意图识别与防堆积策略）的设计规范。
*   **信息源模块规范**：[`.cursor/rules/module3_info_sources.md`](.cursor/rules/module3_info_sources.md) - 模块三（信息源治理、Lark Bot 集成）的设计规范。
*   **Agent 技能规范**：[`.cursor/rules/agent_skills.md`](.cursor/rules/agent_skills.md) - 跨项目复用技能的调用规范（如 `lark-bitable`、`multi-agent-hub` 等）。

> **注意**：随着架构的演进，本索引应持续更新。负责重构的 Agent 需维护对应的规则文档。

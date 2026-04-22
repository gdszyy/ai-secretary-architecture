# ai-secretary-architecture 全局协作规范 (AGENTS.md)

本文档是 `ai-secretary-architecture` 仓库中所有 AI Agent（包括临时 Agent 和常驻 Agent）必须遵守的协作规范和工作指南。它定义了全局的编辑策略、代码风格约定以及各模块的规范文档索引。

## 1. 快速导航与核心入口规范 (Quick Navigation)

为了确保各技能 (Skills) 与本项目之间的索引契约一致，所有 Agent 在介入本项目时，**必须**优先阅读以下入口文档：

*   **项目全局规范入口**：本文档 (`AGENTS.md`)，包含核心编辑策略、禁止行为与文档索引。
*   **架构与防坑指南**：[`.cursor/rules/global.md`](.cursor/rules/global.md)（必读，包含系统整体架构与设计原则）。
*   **流程洞察索引**：[`.cursor/rules/process_insights/index.md`](.cursor/rules/process_insights/index.md)（在涉及复杂跨模块流程时必读，包含历次任务沉淀的防坑经验）。
*   **自动函数索引**：[`.cursor/rules/auto_index/INDEX.md`](.cursor/rules/auto_index/INDEX.md)（在涉及大文件修改时必读，包含函数名、行号范围和 @section 内部节点映射）。

## 2. 全局 AI 编辑策略规范

本项目为了保证代码/文档库的高信噪比和结构一致性，所有 AI Agent 在修改文件时，必须遵循以下**智能编辑策略决策树**：

### 智能编辑策略决策树

1.  **微型修改（< 20 行）**
    *   **策略**：使用搜索替换（Search and Replace）或行内编辑。
    *   **适用场景**：修复错别字、调整局部排版、更新少量逻辑。
2.  **中型修改（20 - 200 行）**
    *   **策略**：局部重写或追加内容。
    *   **适用场景**：重构单一函数、添加新段落、调整局部结构。
3.  **大型修改（> 200 行）**
    *   **策略**：全文件重写（Full File Rewrite）。
    *   **适用场景**：仅在文件本身较小且需要进行彻底重构时使用。对于超长文件，必须先将其拆分为多个子文件。

### 强制要求

*   **活文档契约（代码-文档同步）**：任何对系统架构、API 设计或核心逻辑的实质性修改，**必须在同一个 Commit 中同步更新对应模块的规范文档**（位于 `.cursor/rules/` 目录下）。
*   **流程洞察沉淀**：当 Agent 在任务中发现非直观的隐蔽逻辑或跨模块耦合陷阱时，**必须在任务完成后**在 `.cursor/rules/process_insights/` 中创建或更新对应的洞察文档，并同步更新 `index.md`。
*   **历史文档归档**：过期的设计方案和旧版本的任务记录应移动到 `archive/` 等归档目录，保持活跃文档区的整洁。

## 3. 上下文防污染策略

> **⚠️ 核心警告：跳过归档区**
> 本仓库包含以下历史归档目录，Agent 默认**严禁**主动读取这些目录下的文件，除非任务明确要求追溯历史：
*   `archive/`（含 `archive/deprecated_scripts/`：旧版追问脚本归档，见 PI-002）
*   `tasks/`

## 4. 子模块规范文档索引

为了指导各个子模块的设计和演进，项目在 `.cursor/rules/` 目录下维护了详细的模块规范文档。以下是当前的文档索引：

*   **全局架构规范**：[`.cursor/rules/global.md`](.cursor/rules/global.md) - 包含系统全景架构、核心工作流串联及全局禁止行为清单。
*   **architecture 模块规范**：[`.cursor/rules/architecture.md`](.cursor/rules/architecture.md) - architecture 模块的专属设计规范与 SOP。
*   **module1_kanban 模块规范**：[`.cursor/rules/module1_kanban.md`](.cursor/rules/module1_kanban.md) - module1_kanban 模块的专属设计规范与 SOP。
*   **module2_buffer 模块规范**：[`.cursor/rules/module2_buffer.md`](.cursor/rules/module2_buffer.md) - module2_buffer 模块的专属设计规范与 SOP。
*   **module3_info_sources 模块规范**：[`.cursor/rules/module3_info_sources.md`](.cursor/rules/module3_info_sources.md) - module3_info_sources 模块的专属设计规范与 SOP。
*   **Meegle 深度集成方案**：[`docs/module3_info_sources/meegle_integration_deepening.md`](docs/module3_info_sources/meegle_integration_deepening.md) - Meegle 扩展能力与模块映射规范。
*   **里程碑管理规范**：[`docs/project/milestone_policy.md`](docs/project/milestone_policy.md) - 人工设定里程碑的强制规范。
*   **project 模块规范**：[`.cursor/rules/project.md`](.cursor/rules/project.md) - project 模块的专属设计规范与 SOP。

## 5. 流程洞察索引 (Process Insights)

流程洞察是 Agent 在完成任务后沉淀的经验文档，记录非直观的隐蔽逻辑、跨模块耦合陷阱和关键操作流程。与静态模块规范不同，流程洞察随任务持续积累，并通过版本号管理演进。

*   **洞察注册表**：[`.cursor/rules/process_insights/index.md`](.cursor/rules/process_insights/index.md) - 所有活跃与废弃洞察的版本索引。

> **注意**：随着架构的演进，本索引应持续更新。负责重构的 Agent 需维护对应的规则文档和流程洞察。

## 6. 批处理调度入口 (Batch Scheduling)

以下是系统的自动化批处理入口脚本，由 Manus 定时任务触发：

| 脚本 | 触发时机 | 功能 | 备注 |
|------|----------|------|------|
| `scripts/run_daily_batch.py` | 每日 09:00（工作日） | 群消息提取 → 写入 weekly_updates → git push；周四额外触发 weekly_issue_reminder | `--dry-run` 预览，`--hours N` 自定义拉取时长 |
| `scripts/run_weekly_batch.py` | 每周一 06:00 | 话题归档 → 三源周报生成（含 activity）→ 里程碑更新 → git push | `--dry-run` 预览，`--week YYYY-WW` 补跑历史周 |
| `scripts/weekly_issue_reminder.py` | 每周四 15:00（由 run_daily_batch 触发） | 扫描本周 risk_blocker，发飞书提醒卡片 | 独立运行：`--dry-run` 预览 |

> **注意**：Manus 只维护两个定时任务（每日批 + 每周批），周四提醒已内嵌在每日批中。

## 7. 待开发需求登记表 (Pending Features)

以下需求已记录但尚未实现，下一个接手 Agent 应优先阅读对应需求文档再开工。

| ID | 需求名称 | 优先级 | 状态 | 需求文档 | 前置条件 |
|---|---|---|---|---|---|
| PF-001 | 飞书卡片回复自动触发信息纠正 | P1 | 待开发 | [`docs/module2_buffer/lark_card_reply_correction_spec.md`](docs/module2_buffer/lark_card_reply_correction_spec.md) | 飞书机器人消息订阅权限（见交接文档） |

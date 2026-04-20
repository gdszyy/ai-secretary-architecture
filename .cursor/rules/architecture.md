---
description: "architecture 模块的设计规范与核心逻辑说明"
globs: ["architecture/**/*"]
---

# architecture 模块规范

## 1. 模块职责

系统全局架构与核心逻辑设计文档层，包括仓库拆分评估、派发任务记录、交接文档等。为所有子模块提供全局视角和架构决策支撑。

## 2. 核心文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 交接文档 | `docs/architecture/handover.md` | Agent 间项目交接说明 |
| 仓库拆分评估 | `docs/architecture/repository_split_assessment.md` | 仓库拆分方案评估 |
| 拆分验收总结 | `docs/architecture/split_repo_acceptance_summary.md` | 拆分完成验收报告 |
| 派发任务记录 | `docs/architecture/dispatched_tasks.md` | 历史派发任务汇总 |
| Skill 索引 | `docs/architecture/skill_index.md` | Agent 核心技能索引与使用指南 |

## 3. 架构决策原则

- **仓库三角**：不同职责的代码分居不同仓库，严禁将业务代码提交到本架构文档库
- **文档优先**：本仓库为纯 Markdown 文档库，不引入业务逻辑代码
- **交接规范**：每次 Agent 交接必须更新 `handover.md`，确保下一个 Agent 能无缝接手

## 4. 详细设计文档索引

详见 `docs/architecture/` 目录下的各文档。

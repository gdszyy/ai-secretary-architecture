---
description: "project 模块的设计规范与核心逻辑说明"
globs: ["project/**/*"]
---

# project 模块规范

## 1. 模块职责

项目管理与规划文档层，包括项目全局概览、启动报告、数据可行性分析和 Lark 文档创建规范。为项目经理提供项目全局视角和决策支撑。

## 2. 核心文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 项目全局概览 | `docs/project/project-overview.md` | 项目全局概览与目标 |
| 项目启动报告 | `docs/project/project-kickoff.md` | 项目启动文档 |
| 数据可行性分析 | `docs/project/kanban_data_driven_feasibility.md` | 看板数据驱动可行性评估 |
| Lark 文档创建规范 | `docs/project/lark-doc-creation-spec.md` | 飞书云文档创建规范 |

## 3. 项目管理规则

- **项目全局 SOP**：详见根目录 `SOP.md`，包含项目经理与 AI 秘书交互的标准指令
- **Lark 文档导入**：所有飞书云文档必须使用 `lark-md-import` 技能通过 Markdown 导入创建
- **数据驱动**：项目看板应尽量接入实时数据源，避免人工录入

## 4. 详细设计文档索引

详见 `docs/project/` 目录下的各文档。

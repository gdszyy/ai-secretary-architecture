---
description: "模块一：Lark 多维表格看板与 Meegle 关联机制的设计规范与 SOP"
globs: ["docs/module1_kanban/**"]
---

# 模块一：看板系统规范 (Kanban Module)

## 1. 模块职责

看板模块是 AI 项目秘书系统的**产品侧工作区**，基于 Lark 多维表格构建，负责管理"待规划"到"已上线"的全生命周期。它与 Meegle（研发侧执行引擎）通过双向同步机制保持状态一致。

## 2. 核心数据模型

看板模块的数据模型由两张表构成：

| 表名 | 职责 | 关键字段 |
| :--- | :--- | :--- |
| **模块表 (Module Table)** | 管理项目的高层级模块，作为功能的聚合层 | 模块名称、分类、优先级、状态、负责人、备注 |
| **功能表 (Feature Table)** | 管理具体的开发需求和任务，是看板的核心 | 功能名称、状态、功能优先级、所属模块、**Meegle ID**、**Meegle 链接**、计划开始/完成 |

**关键设计决策**：功能表中的 `Meegle ID` 和 `Meegle 链接` 字段是实现 Lark-Meegle 双向同步的基石。当一条功能记录拥有非空的 `Meegle ID` 时，表示该功能已进入研发阶段，此时 **Meegle 为状态的 Single Source of Truth**。

## 3. 状态流转规则

功能表中的 `状态` 字段遵循以下严格的状态机：

```
待规划 → 规划中 → 开发中 → 测试中 → 已上线 → 已归档
```

**禁止行为**：禁止跳过状态（如直接从"待规划"跳到"测试中"），禁止逆向流转（如从"已上线"退回"开发中"，除非创建新的回归任务）。

## 4. Lark-Meegle 双向同步机制

同步规则遵循 **Single Source of Truth** 原则：

| 阶段 | 状态主控方 | 同步方向 |
| :--- | :--- | :--- |
| 进入开发前（无 Meegle ID） | **Lark** | Lark → Meegle（创建 Story） |
| 进入开发后（有 Meegle ID） | **Meegle** | Meegle → Lark（状态回写） |

## 5. 详细设计文档

本模块的完整设计文档位于 `docs/module1_kanban/` 目录下：

| 文档 | 说明 |
| :--- | :--- |
| `lark_kanban_design.md` | 看板数据模型、字段设计与视图设计 |
| `secretary_module1_sop.md` | 看板模块的标准作业程序 |
| `meegle_integration_design.md` | Meegle 集成方案与 API 对接细节 |
| `status_flow_diagram.md` | 状态流转图与边界条件 |
| `kanban_optimization_plan.md` | 看板优化方案与信息源架构 |
| `ai_token_optimization.md` | AI Token 消耗优化策略 |
| `prereq_data_assessment.md` | 前置数据评估报告 |
| `dashboard_visualization_architecture.md` | 看板可视化数据链路架戶设计，包含 JSON Schema 定义 |

## 6. 看板可视化数据链路（Dashboard Visualization Pipeline）

看板可视化是看板模块的延伸层，将 Lark Bitable 和 Markdown 文档中的信息沉淀转化为结构化数据，驱动前端看板展示。

### 6.1 数据流向

```
非结构化信息源（飞书群组周报、模块进度文档）
        ↓ scripts/parse_to_dashboard_json.py
data/dashboard_data.json（唯一数据契约）
        ↓ git push 到 ai-secretary-architecture
前端通过 GitHub Raw URL 读取，刷新即生效
```

### 6.2 前端项目位置

- **仓库**：`gdszyy/xpbet-frontend-components`，路径 `kanban-v2/`
- **技栈**：React 19 + TypeScript + Tailwind CSS 4 + Recharts
- **数据源配置**：环境变量 `VITE_DATA_URL`，默认指向 GitHub Raw URL

### 6.3 数据更新 SOP

每周二执行以下步骤：

1. 编辑 `scripts/inject_weekly_updates.py` 中的 `WEEKLY_UPDATES` 字典，填入本周各模块进展
2. 运行 `python3 scripts/inject_weekly_updates.py`
3. 运行 `python3 scripts/sync_bitable_docs.py`（同步 Bitable 文档链接）
4. `git add data/dashboard_data.json && git commit -m "data: W{XX} weekly update" && git push`
5. 前端刷新页面即可看到最新数据

---
description: "module1_kanban 模块的设计规范与核心逻辑说明"
globs: ["module1_kanban/**/*"]
---

# module1_kanban 模块规范

## 1. 模块职责

看板模块负责管理项目需求的全生命周期状态流转。以 **Lark 多维表格为产品侧完观看板**，以 **Meegle 为研发侧执行引擎**，AI 秘书负责在两者之间自动同步状态。

## 2. 核心数据模型

### Meegle API 扩展能力

- `list_work_items_by_week(module_label, week_start, week_end)`: 按时间范围和模块标签查询 Work Item，并统计本周内状态变更为「已完成/已上线」的 Story 数量，以及新增的 Defect 数量。用于周报自动生成。

### Lark 多维表格字段（功能表）

| 字段 | 类型 | 说明 |
|------|------|------|
| 功能名称 | 文本 | 功能的唯一标识 |
| 状态 | 单选 | 待规划/规划中/开发中/测试中/已上线/已归档 |
| 所属模块 | 关联 | 关联到模块表 |
| Meegle ID | 文本 | 进入开发后由 AI 秘书回写 |
| 负责人 | 人员 | 功能负责人 |
| 优先级 | 单选 | P0/P1/P2 |
| 备注 | 文本 | AI 秘书备忘和特殊说明 |

### 核心 API

- `scripts/lark_bitable_client.py` — Lark Bitable CRUD 封装
- `scripts/meegle_client.py` — Meegle Story/Defect 创建与查询
- `main.py::write_threads_to_bitable()` — 批量写入 Bitable
- `main.py::get_cursor_record_id()` — 幂等性查询记录

## 3. 状态流转规则

```
待规划 → 规划中 → 开发中 → 测试中 → 已上线 → 已归档
```

- **待规划 → 规划中**：PM 手动触发
- **规划中 → 开发中**：PM 指令触发，**自动调用 Meegle API 创建 Story**，回写 Meegle ID
- **开发中 → 已上线**：Meegle Webhook 回传自动更新
- **Single Source of Truth**：开发前 Lark 为主，开发后 Meegle 为主

## 4. 度量指标设计（双轨模型）

### 设计原则

> **金色进度条 = 里程碑叙事（主线）**：表达“我们在哪里”，由人工维护，不受需求变化影响。
> **交付活跃度区块 = 本周实际发生了什么（辅线）**：自动采集客观事实，不依赖终点预测。

### weekly_progress_percentage 字段

`module["weekly_progress_percentage"]` 保持人工维护，表示里程碑进展层次。每到达一个里程碑节点（设计/开发/联调/提测/上线）就增长固定幅度，不受需求调整影响。

### activity 字段（自动采集）

`weekly_updates[].activity` 由 `run_weekly_report.py` 的 Step 5 循环自动写入，记录本周客观交付事实：

| 字段 | 来源 | 说明 |
|------|------|------|
| `completed_stories` | Meegle `list_work_items_by_week()` | 本周关闭的 Story 数量 |
| `new_defects` | Meegle `list_work_items_by_week()` | 本周新增的 Defect 数量 |
| `resolved_defects` | Meegle `list_work_items_by_week()` | 本周解决的 Defect 数量 |
| `chat_insight_count` | `extract_weekly_insights.get_weekly_insights_for_modules()` | 本周群聊洞察条数 |

### 数据流

```
Step 5 循环（每个模块）
  ↓
  meegle_progress 文本 → 正则解析 completed_stories / new_defects / resolved_defects
  chat_insights 列表 → len() 得到 chat_insight_count
  ↓
  module_updates[mid]["activity"] = { completed_stories, new_defects, resolved_defects, chat_insight_count }
  ↓
Step 6: inject_to_dashboard()
  ↓
  new_entry["activity"] = update_data["activity"]
  ↓
  写入 dashboard_data.json
```

### 前端展示（kanban-v2 hover 层）

```
金色区块：本周里程碑进展（人工维护）
  ↓
靳蓝区块：本周交付活跃度（自动采集）
  ✔ Story ×N   🔧 修复 ×N
  🐛 新增缺陷 ×N   💬 洞察 ×N
```

仅当 `activity` 字段存在且至少一项非零时渲染活跃度区块，向后兼容旧数据。

### 错误处理

任何异常情况均返回 `activity: None`，不中断主流程。

## 5. 详细设计文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 看板设计方案 | `docs/module1_kanban/lark_kanban_design.md` | Lark 多维表字段设计与视图规范 |
| 模块 SOP | `docs/module1_kanban/secretary_module1_sop.md` | PM 与 AI 秘书交互指令指南 |
| Meegle 集成设计 | `docs/module1_kanban/meegle_integration_design.md` | Meegle API 集成方案 |
| 状态流转图 | `docs/module1_kanban/status_flow_diagram.md` | 状态机可视化图表 |

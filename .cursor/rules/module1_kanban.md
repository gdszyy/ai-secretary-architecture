---
description: "module1_kanban 模块的设计规范与核心逻辑说明"
globs: ["module1_kanban/**/*"]
---

# module1_kanban 模块规范

## 1. 模块职责

看板模块负责管理项目需求的全生命周期状态流转。以 **Lark 多维表格为产品侧完观看板**，以 **Meegle 为研发侧执行引擎**，AI 秘书负责在两者之间自动同步状态。

## 2. 核心数据模型

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

## 4. 详细设计文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 看板设计方案 | `docs/module1_kanban/lark_kanban_design.md` | Lark 多维表字段设计与视图规范 |
| 模块 SOP | `docs/module1_kanban/secretary_module1_sop.md` | PM 与 AI 秘书交互指令指南 |
| Meegle 集成设计 | `docs/module1_kanban/meegle_integration_design.md` | Meegle API 集成方案 |
| 状态流转图 | `docs/module1_kanban/status_flow_diagram.md` | 状态机可视化图表 |

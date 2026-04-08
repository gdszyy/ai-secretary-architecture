# 前端资产来源映射

| 来源任务/目录 | 迁入位置 | 内容说明 |
| --- | --- | --- |
| `docs/design/` | `docs/design/` | XPBET 设计系统与界面规范。 |
| `kanban/` | `src/prototypes/kanban/` | 静态看板模板、示例页面与数据文件。 |
| `tsk-36ea6dbd-cb8` | `src/prototypes/cms/` 与 `docs/specs/` | CMS 原型、配置手册与数据模型。 |
| `tsk-9e42ac9b-ae0` | `src/prototypes/xpbet-app/` 与 `docs/specs/` | App Prototype 与相关设计说明。 |
| `tsk-dd63bbec-dc3` | `src/prototypes/xpbet-homepage/` 与 `docs/specs/` | Homepage 原型、交互规范与前端设计说明。 |
| `tsk-6cafe603-a9f` | `src/historical/task-6cafe603-a9f/` | React/TS 前端实现与数据转换逻辑。 |
| `tsk-f7cc10f7-0df` | `src/historical/task-f7cc10f7-0df/` | 前端架构设计与组件化实现参考。 |
| `tsk-b9e8ecd5-4f3` | `src/historical/task-b9e8ecd5-4f3/` | Bitable 数据接入相关前端实现。 |

## 说明

本次拆分采取 **结构化保留** 策略：不直接复制整个 `tasks/` 目录进入仓库主视图，而是将可复用的原型、规范与代码分别重组到 `docs/`、`src/` 与 `archive/`，从而保留追溯性同时降低主上下文噪音。

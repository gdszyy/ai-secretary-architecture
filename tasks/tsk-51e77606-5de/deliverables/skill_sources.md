# 技能来源映射

| 来源路径 | 迁入位置 | 说明 |
| --- | --- | --- |
| `skills/lark-codesandbox/` | `skills/lark-codesandbox/` | CodeSandbox 发布与 Lark 嵌入相关技能。 |
| `skills/lark-md-import/` | `skills/lark-md-import/` | Markdown 导入 Lark 文档技能。 |
| `docs/skill_index.md` | `docs/skill_index.md` | 原仓库的技能索引文档。 |

## 拆分原则

本次拆分以 **跨项目复用性** 为边界。只有技能定义、脚本及其索引说明被迁入本仓库；业务专属设计文档、前端原型和历史任务交付物均留在其他目标仓库或归档区。

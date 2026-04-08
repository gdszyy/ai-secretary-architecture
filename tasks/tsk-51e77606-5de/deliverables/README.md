# manus-lark-skills

**manus-lark-skills** 是从业务仓库中拆分出的通用技能仓库，用于集中管理可跨项目复用的 Manus / Lark 相关技能定义、脚本与索引文档。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `skills/lark-codesandbox/` | 将前端 Demo 发布到 CodeSandbox 并嵌入 Lark 文档的技能。 |
| `skills/lark-md-import/` | 将 Markdown 导入 Lark 文档的技能。 |
| `docs/skill_index.md` | 技能目录与索引说明。 |
| `docs/skill_sources.md` | 技能来源映射与拆分说明。 |

## 使用约定

本仓库只保留 **可跨项目复用** 的通用技能资产，不混入 XPBET 业务文档、前端原型或历史任务目录。新增技能时，建议继续遵循技能目录化组织方式，并在 `docs/` 中补充索引与来源说明。

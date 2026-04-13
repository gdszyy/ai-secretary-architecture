---
description: "跨项目复用的 Agent 技能调用规范与索引"
globs: ["docs/skill_index.md"]
---

# Agent 技能调用规范 (Agent Skills)

## 1. 概述

AI 项目秘书系统依赖多个外部 Manus 技能（Skills）来完成与飞书、多维表格和多 Agent 协作系统的集成。本规范定义了这些技能的调用场景、优先级和注意事项。

## 2. 技能索引

| 技能名称 | 调用场景 | 核心命令 |
| :--- | :--- | :--- |
| **lark-bitable** | 读取 XPBET 产品架构的飞书多维表格数据 | `python3 scripts/read_xpbet_architecture.py` |
| **multi-agent-hub** | 多 Agent 协作、任务流转、进度汇报 | `hub_client.py register / complete-task` |
| **lark-codesandbox** | 生成前端可交互 Demo 并嵌入飞书文档 | `publish_demo.mjs` + `add_to_lark.py` |
| **lark-md-import** | 将 Markdown 文件导入为飞书新版文档 | `import_md.py <文件路径> [标题]` |
| **lark-wiki-docs** | 对已有飞书 Wiki 或文档进行精细化操作 | `lark_wiki_client.py read/create_table/add_collab` |

## 3. 调用规范

**按需加载原则**：Agent 不应在任务开始时一次性加载所有技能的完整文档。应先参考本规范中的简要索引，仅在确认需要使用某个技能时，再读取对应技能目录下的 `SKILL.md` 获取详细参数。

**凭证安全**：所有技能的认证凭证已预置在运行环境中。Agent 在文档和日志中**严禁**输出任何凭证信息（如 App ID、App Secret、Token）。

**错误处理**：调用技能脚本时，如果遇到权限不足或 API 限流错误，应在任务日志中记录错误信息，并向协调者汇报，而非自行重试超过 3 次。

## 4. 详细技能文档

完整的技能使用指南见 [`docs/skill_index.md`](../docs/skill_index.md)。

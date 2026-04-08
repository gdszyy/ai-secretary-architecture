# Agent 技能索引与使用指南 (Skill Index)

本文档整理了本项目中常用的 5 个核心 Agent 技能（Skills）的使用场景与功能概要。在派发子任务时，可将此索引作为提示词（Prompt）的一部分提供给被派发的 Agent，使其能够按需调用相关技能，而无需每次都读取完整的技能文档，从而大幅节省 Token 消耗。

## 1. lark-bitable
- **使用场景**：需要快速读取 XPBET 产品架构的飞书多维表格（Bitable）数据时。
- **功能概要**：预置了凭证和表格 ID，直接运行脚本即可获取“模块表”和“功能表”的数据。
- **调用方式**：`python3 /home/ubuntu/skills/lark-bitable/scripts/read_xpbet_architecture.py`

## 2. multi-agent-hub
- **使用场景**：多 Agent 协作、任务流转、进度汇报、成果提交审核以及上下文交接时。
- **功能概要**：提供 Agent 注册、任务管理（创建/分配/更新/完成/验收）、消息通信、上下文快照等功能。强制要求以 Git 仓库作为项目持久化上下文，所有交付物必须先提交到 Git，再在 Hub 中提交审核。
- **核心命令**：
  - 注册：`python /home/ubuntu/skills/multi-agent-hub/scripts/hub_client.py register --role <角色> --type <类型>`
  - 提交结果到 Git：`python /home/ubuntu/skills/multi-agent-hub/scripts/hub_repo.py save-result --task-id <id> --summary <摘要> --file <文件路径>`
  - 提交审核：`python /home/ubuntu/skills/multi-agent-hub/scripts/hub_client.py complete-task --task-id <id> --agent-id <id> --summary <摘要>`

## 3. lark-codesandbox
- **使用场景**：在编写交互设计或产品需求文档时，需要生成前端可交互 Demo 并将其嵌入到飞书文档中。
- **功能概要**：自动化“生成前端代码 → 发布到 CodeSandbox → 作为 iframe 嵌入飞书文档”的全流程。需要配合 `lark-wiki-docs` 技能使用。
- **核心步骤**：
  1. 准备单文件 HTML Demo。
  2. 启动服务：`node /home/ubuntu/skills/lark-codesandbox/scripts/publish_demo.mjs --file <文件> --title <标题>`
  3. 浏览器访问生成的 URL 提交并获取 `sandbox_id`。
  4. 嵌入飞书：`python /home/ubuntu/skills/lark-codesandbox/scripts/add_to_lark.py --doc <文档Token> --sandbox-id <id>`

## 4. lark-md-import
- **使用场景**：需要从零开始创建包含丰富格式（标题、列表、表格、代码块等）的全新飞书文档时。
- **功能概要**：将本地的 Markdown 文件直接导入为飞书新版文档（docx），保证格式的高保真转换，比逐个调用 Block API 更高效。
- **调用方式**：`python3 /home/ubuntu/skills/lark-md-import/scripts/import_md.py <文件路径> [文档标题] [文件夹Token]`

## 5. lark-wiki-docs
- **使用场景**：需要对已有的飞书 Wiki 或文档进行精细化操作（如读取内容、追加文本、创建表格、设置多列排版、管理协作者权限）时。
- **功能概要**：提供完整的 Python 客户端库和 CLI 工具，封装了飞书文档的 Block API 和 Wiki API。预置了“XP机器人”的认证凭证。
- **核心命令**：
  - 读取文档：`python3 /home/ubuntu/skills/lark-wiki-docs/scripts/lark_wiki_client.py read <obj_token>`
  - 创建表格：`python3 /home/ubuntu/skills/lark-wiki-docs/scripts/lark_wiki_client.py create_table <obj_token> <json数据文件>`
  - 添加协作者：`python3 /home/ubuntu/skills/lark-wiki-docs/scripts/lark_wiki_client.py add_collab <file_token> <file_type> <open_id> <perm>`

---
> **给被派发 Agent 的提示**：
> 如果你需要使用上述任何功能，请直接使用对应的命令，或读取对应技能目录下的 `SKILL.md` 获取更详细的参数说明。

# 飞书云文档创建规范

> 本规范定义了 AI 秘书在需要创建飞书云文档时应遵循的标准方法。

## 核心原则

**使用 Markdown 导入方案作为主要的文档创建方式。**

飞书 Block API（逐块写入）适用于对已有文档进行精确编辑，但从零创建完整文档时存在以下缺陷：构造复杂 JSON 负担重、嵌套列表和表格需要多步 API 调用、错误率高。相比之下，Markdown 导入方案通过标准 Markdown 语法生成内容，再一次性导入为云文档，具有实现简单、格式完整、速度快的优势。

## 标准工作流

创建飞书云文档的标准流程分为三步：

**Step 1 — 生成 Markdown 文件**

将文档内容写入本地 `.md` 文件。使用标准 Markdown 语法，支持以下格式：

| Markdown 元素 | 飞书 Block 类型 | 说明 |
|---|---|---|
| `# H1` ~ `##### H5` | Heading1 ~ Heading5 | 五级标题 |
| `**加粗**` / `*斜体*` / `~~删除线~~` | Text 内联样式 | 文本修饰 |
| `` `行内代码` `` | Text code 样式 | 行内代码 |
| `> 引用` | Quote block | 引用块 |
| `- 无序列表`（支持嵌套） | Bullet block | 无序列表 |
| `1. 有序列表` | Ordered block | 有序列表 |
| ` ```lang 代码块 ``` ` | Code block | 带语言高亮的代码块 |
| `\| 表格 \|` | Table + TableCell | 标准表格 |

**Step 2 — 执行导入脚本**

使用 `lark-md-import` 技能提供的脚本执行导入：

```bash
python3 /home/ubuntu/skills/lark-md-import/scripts/import_md.py \
  <markdown_file_path> \
  "<document_title>" \
  [folder_token]
```

脚本内部自动完成三个 API 调用：
1. `POST /drive/v1/medias/upload_all` — 上传 Markdown 文件为临时素材
2. `POST /drive/v1/import_tasks` — 创建导入任务（`type=docx`, `file_extension=md`）
3. `GET /drive/v1/import_tasks/{ticket}` — 轮询任务状态，获取文档 token 和 URL

**Step 3 — 后续操作（可选）**

导入成功后，可使用 `lark-wiki-docs` 技能对文档进行二次操作：
- 添加协作者（`add_collaborator`）
- 追加内容块（`append_text_block`）
- 将文档挂载到 Wiki 节点

## 何时使用 Block API 替代

以下场景应直接使用 Block API（`lark-wiki-docs` 技能），而非导入方案：

- 对已有文档的**局部修改**（修改特定段落、追加内容）
- 需要创建**多栏布局**（Grid block）
- 需要插入**图片**或**嵌入式表格**（Sheet block）

## 关键注意事项

- `file_extension` 参数必须与实际文件后缀严格一致（`md`、`markdown`、`mark` 均支持，但不可混用），否则返回错误码 `1069910`。
- 上传的素材文件有效期为 **5 分钟**，需在此时间内完成导入任务创建。
- 单个文件大小上限为 **20 MB**。
- 导入接口速率限制为每分钟 100 次。

## 技能引用

本规范依赖以下 Manus 技能：

| 技能名称 | 用途 |
|---|---|
| `lark-md-import` | 执行 Markdown 文件导入为飞书云文档 |
| `lark-wiki-docs` | 对已有文档进行编辑、权限管理和 Wiki 挂载 |

---
id: "PI-003"
version: "v1.0"
last_updated: "2026-04-21"
author: "Manus AI"
related_modules: ["module3_info_sources", "module2_buffer"]
status: "active"
---

# PI-003: 飞书 Post 消息超链接节点解析

## 流程概述

秘书功能通过飞书 IM API 拉取群聊消息后，需要将原始消息结构解析为纯文本，再交给 LLM 提取进展。飞书消息分为多种类型（`text`、`post`、`image` 等），其中 `post`（富文本）类型包含多种子节点（`text`、`at`、`a`、`img`、`media` 等）。本洞察记录了在解析 `post` 消息时遗漏超链接（`a`）节点导致 Lark 云文档链接丢失的问题及修复方案。

## 核心防坑指南

### 坑 1: Post 消息中的超链接节点（`tag == "a"`）被静默丢弃

**现象**：用户在群内分享 Lark 云文档链接（需求文档、PRD 等），系统在每日跑批后无法识别和记录相关需求，导致话题遗漏。

**根因**：飞书 `post` 类型消息中，超链接以 `{"tag": "a", "href": "...", "text": "..."}` 节点形式传输。原始解析代码仅处理了 `text` 和 `at` 节点，`a` 节点被完全忽略，导致链接文本和 URL 在进入 LLM 分析前就被物理丢弃。

**正确做法**：在所有解析 `post` 消息节点的循环中，必须增加对 `tag == "a"` 的处理分支，将链接文本和 URL 一并保留：

```python
elif node.get("tag") == "a":
    link_text = node.get("text", "")
    link_href = node.get("href", "")
    if link_text and link_href:
        texts.append(f"{link_text}({link_href})")
    elif link_href:
        texts.append(link_href)
    elif link_text:
        texts.append(link_text)
```

**关键位置**：
- `scripts/daily_progress_updater.py` → `extract_msg_text` 约第 162 行（`post` 分支）
- `scripts/extract_weekly_insights.py` → `_normalize_messages` 约第 178 行（`post` 分支）

### 坑 2: 飞书 Post 消息节点类型不止 text/at 两种

**现象**：新增消息格式（如代码块 `code_block`、分割线 `hr`、图片 `img` 等）在解析时被静默忽略，可能导致消息内容不完整。

**根因**：飞书 `post` 消息支持的节点类型包括：`text`、`a`、`at`、`img`、`media`、`emotion`、`hr`、`code_block`。当前解析逻辑采用白名单模式，未列出的节点类型一律丢弃。

**正确做法**：在解析 `post` 消息时，至少需要覆盖以下对 LLM 有意义的节点类型：

| 节点 tag | 处理方式 | 说明 |
|---------|---------|------|
| `text` | 直接追加文本 | 普通文字 |
| `a` | 追加 `文本(URL)` | 超链接，含云文档链接 |
| `at` | 追加 `@用户名` | @提及 |
| `code_block` | 追加代码内容 | 代码块（可选） |
| `img`/`media` | 忽略或追加占位符 `[图片]` | 无文本内容 |

## 关键耦合点

1. **与 `module3_info_sources` 的耦合**：消息解析是信息获取流水线的第一道关卡，解析层的遗漏会导致后续所有 LLM 分析和 Bitable 写入均无法弥补。
2. **与高价值过滤策略的叠加效应**：当链接被丢弃后，消息上下文信息不足，LLM 更容易将相关话题判定为 `routine_task`（常规需求），进而被高价值过滤器拦截，形成双重遗漏。
3. **两处解析函数必须保持同步**：`extract_msg_text`（`daily_progress_updater.py`）和 `_normalize_messages`（`extract_weekly_insights.py`）的解析逻辑高度重复，修改一处必须同步修改另一处。建议未来将其合并为共享工具函数。

## 版本变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-04-21 | 初始记录，修复 post 消息 a 节点遗漏问题 | Manus AI |

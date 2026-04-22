# scripts/extract_weekly_insights.py 函数索引

> 自动生成于 2026-04-22 | 总行数: 522 | 函数数: 7 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| get_token | function | L76 | L92 | 17 | `get_token()` |
| lark_get | function | L93 | L157 | 65 | `lark_get(url: str, params: dict = None)` |
| _normalize_messages | function | L158 | L219 | 62 | `_normalize_messages(raw_messages: List[Dict])` |
| _week_str_to_timestamps | function | L220 | L300 | 81 | `_week_str_to_timestamps(week_str: str)` |
| messages_to_text | function | L301 | L320 | 20 | `messages_to_text(messages, max_msgs=300)` |
| extract_weekly_insights | function | L321 | L365 | 45 | `extract_weekly_insights(group_name, week_label, messages)` |
| get_weekly_insights_for_modules | function | L366 | L523 | 158 | `get_weekly_insights_for_modules(week_str: str)` |

# main.py 函数索引

> 自动生成于 2026-04-21 | 总行数: 625 | 函数数: 10 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| extract_message_from_event | function | L126 | L164 | 39 | `extract_message_from_event(payload: Dict)` |
| is_frontend_related | function | L165 | L180 | 16 | `is_frontend_related(text: str, chat_name: str = "")` |
| get_cursor_record_id | function | L181 | L214 | 34 | `get_cursor_record_id(client: "LarkBitableClient", base_id: str, table_id: str, chat_id: str)` |
| update_cursor_record | function | L215 | L289 | 75 | `update_cursor_record(chat_id: str, message_id: str)` |
| write_threads_to_bitable | function | L290 | L364 | 75 | `write_threads_to_bitable(threads: list)` |
| get_lark_tenant_access_token | function | L365 | L400 | 36 | `get_lark_tenant_access_token()` |
| send_lark_message | function | L401 | L437 | 37 | `async send_lark_message(chat_id: str, text: str)` |
| handle_message_event | function | L438 | L544 | 107 | `async handle_message_event(msg_info: Dict)` |
| health_check | function | L545 | L604 | 60 | `async health_check()` |
| root | function | L605 | L626 | 22 | `async root()` |

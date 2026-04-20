# main.py 函数索引

> 自动生成于 2026-04-19 | 总行数: 587 | 函数数: 10 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| extract_message_from_event | function | L119 | L157 | 39 | `extract_message_from_event(payload: Dict)` |
| is_frontend_related | function | L158 | L173 | 16 | `is_frontend_related(text: str, chat_name: str = "")` |
| get_cursor_record_id | function | L174 | L207 | 34 | `get_cursor_record_id(client: "LarkBitableClient", base_id: str, table_id: str, chat_id: str)` |
| update_cursor_record | function | L208 | L282 | 75 | `update_cursor_record(chat_id: str, message_id: str)` |
| write_threads_to_bitable | function | L283 | L353 | 71 | `write_threads_to_bitable(threads: list)` |
| get_lark_tenant_access_token | function | L354 | L389 | 36 | `get_lark_tenant_access_token()` |
| send_lark_message | function | L390 | L426 | 37 | `async send_lark_message(chat_id: str, text: str)` |
| handle_message_event | function | L427 | L504 | 78 | `async handle_message_event(msg_info: Dict)` |
| health_check | function | L505 | L566 | 62 | `async health_check()` |
| root | function | L567 | L588 | 22 | `async root()` |

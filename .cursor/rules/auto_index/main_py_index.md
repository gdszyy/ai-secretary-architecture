# main.py 函数索引

> 自动生成于 2026-04-21 | 总行数: 656 | 函数数: 10 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| extract_message_from_event | function | L135 | L177 | 43 | `extract_message_from_event(payload: Dict)` |
| is_frontend_related | function | L178 | L193 | 16 | `is_frontend_related(text: str, chat_name: str = "")` |
| get_cursor_record_id | function | L194 | L227 | 34 | `get_cursor_record_id(client: "LarkBitableClient", base_id: str, table_id: str, chat_id: str)` |
| update_cursor_record | function | L228 | L302 | 75 | `update_cursor_record(chat_id: str, message_id: str)` |
| write_threads_to_bitable | function | L303 | L377 | 75 | `write_threads_to_bitable(threads: list)` |
| get_lark_tenant_access_token | function | L378 | L413 | 36 | `get_lark_tenant_access_token()` |
| send_lark_message | function | L414 | L450 | 37 | `async send_lark_message(chat_id: str, text: str)` |
| handle_message_event | function | L451 | L575 | 125 | `async handle_message_event(msg_info: Dict)` |
| health_check | function | L576 | L635 | 60 | `async health_check()` |
| root | function | L636 | L657 | 22 | `async root()` |

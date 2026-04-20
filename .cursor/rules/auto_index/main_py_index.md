# main.py 函数索引

> 自动生成于 2026-04-20 | 总行数: 590 | 函数数: 10 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| extract_message_from_event | function | L119 | L157 | 39 | `extract_message_from_event(payload: Dict)` |
| is_frontend_related | function | L158 | L173 | 16 | `is_frontend_related(text: str, chat_name: str = "")` |
| get_cursor_record_id | function | L174 | L207 | 34 | `get_cursor_record_id(client: "LarkBitableClient", base_id: str, table_id: str, chat_id: str)` |
| update_cursor_record | function | L208 | L282 | 75 | `update_cursor_record(chat_id: str, message_id: str)` |
| write_threads_to_bitable | function | L283 | L357 | 75 | `write_threads_to_bitable(threads: list)` |
| get_lark_tenant_access_token | function | L358 | L393 | 36 | `get_lark_tenant_access_token()` |
| send_lark_message | function | L394 | L430 | 37 | `async send_lark_message(chat_id: str, text: str)` |
| handle_message_event | function | L431 | L509 | 79 | `async handle_message_event(msg_info: Dict)` |
| health_check | function | L510 | L569 | 60 | `async health_check()` |
| root | function | L570 | L591 | 22 | `async root()` |

## 其他 @section 标记

| 节点标记 | 行号 | 说明 |
|----------|------|------|
| `@section:guard_empty_threads` | L299 | 空线程列表快速返回 |
| `@section:validate_env_config` | L303 | 校验 Bitable 环境变量配置 |
| `@section:init_bitable_client` | L313 | 初始化 Lark Bitable 客户端 |
| `@section:write_records_loop` | L320 | 逐条写入线程记录（容错：单条失败不影响其他） |
| `@section:extract_msg_fields` | L436 | 提取消息基本字段 |
| `@section:route_frontend_defect` | L448 | 前端相关消息路由至缺陷报送流程 |
| `@section:route_thread_separation` | L469 | 通用群聊消息路由至多对话分离流程 |
| `@section:update_cursor_record` | L499 | 更新 Cursor 表（记录最后拉取消息 ID） |
| `@section:parse_request_body` | L532 | 解析请求体 |
| `@section:handle_url_challenge` | L536 | 处理飞书 URL 验证挑战（首次配置时发送） |
| `@section:verify_signature` | L541 | 签名校验（可选，生产环境建议开启） |
| `@section:dispatch_event_type` | L551 | 提取事件类型并路由到对应处理器 |

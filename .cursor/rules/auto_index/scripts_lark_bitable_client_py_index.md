# scripts/lark_bitable_client.py 函数索引

> 自动生成于 2026-04-21 | 总行数: 98 | 函数数: 8 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| LarkBitableClient | class | L5 | L10 | 6 | `LarkBitableClient()` |
| __init__ | method | L11 | L20 | 10 | `__init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None)` |
| _refresh_token | method | L21 | L36 | 16 | `_refresh_token(self)` |
| _get_headers | method | L37 | L44 | 8 | `_get_headers(self)` |
| list_records | method | L45 | L73 | 29 | `list_records(self, base_id: str, table_id: str, page_size: int = 500, filter_str: str = "")` |
| create_record | method | L74 | L82 | 9 | `create_record(self, base_id: str, table_id: str, fields: Dict[str, Any])` |
| update_record | method | L83 | L91 | 9 | `update_record(self, base_id: str, table_id: str, record_id: str, fields: Dict[str, Any])` |
| delete_record | method | L92 | L99 | 8 | `delete_record(self, base_id: str, table_id: str, record_id: str)` |

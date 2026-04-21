# scripts/meegle_client.py 函数索引

> 自动生成于 2026-04-21 | 总行数: 313 | 函数数: 12 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| MeegleAPIClient | class | L16 | L39 | 24 | `MeegleAPIClient()` |
| _get_token | method | L40 | L70 | 31 | `_get_token(self)` |
| _headers | method | L71 | L77 | 7 | `_headers(self)` |
| _post | method | L78 | L98 | 21 | `_post(self, endpoint: str, payload: Optional[dict] = None)` |
| _get | method | L99 | L121 | 23 | `_get(self, endpoint: str, params: Optional[dict] = None)` |
| get_work_item_types | method | L122 | L177 | 56 | `get_work_item_types(self, project_key: str)` |
| query_users | method | L178 | L215 | 38 | `query_users(self, user_keys: List[str])` |
| _date_to_ms | method | L216 | L222 | 7 | `_date_to_ms(date_str: str, end_of_day: bool = False)` |
| _get_field | method | L223 | L229 | 7 | `_get_field(item: dict, field_key: str)` |
| _is_done | method | L230 | L246 | 17 | `_is_done(item: dict)` |
| _is_resolved | method | L247 | L258 | 12 | `_is_resolved(item: dict)` |
| _get_tags | method | L259 | L314 | 56 | `_get_tags(item: dict)` |

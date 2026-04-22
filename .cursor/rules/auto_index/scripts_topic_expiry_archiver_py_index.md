# scripts/topic_expiry_archiver.py 函数索引

> 自动生成于 2026-04-21 | 总行数: 301 | 函数数: 7 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| get_token | function | L66 | L76 | 11 | `get_token()` |
| fetch_all_records | function | L77 | L101 | 25 | `fetch_all_records(token: str)` |
| update_record | function | L102 | L122 | 21 | `update_record(token: str, record_id: str, fields: dict)` |
| get_current_week_str | function | L123 | L131 | 9 | `get_current_week_str(override: Optional[str] = None)` |
| parse_period_to_week | function | L132 | L164 | 33 | `parse_period_to_week(period_str: str)` |
| week_is_before | function | L165 | L271 | 107 | `week_is_before(week_a: str, week_b: str)` |
| main | function | L272 | L302 | 31 | `main()` |

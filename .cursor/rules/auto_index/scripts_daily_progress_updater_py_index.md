# scripts/daily_progress_updater.py 函数索引

> 自动生成于 2026-04-20 | 总行数: 639 | 函数数: 10 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| get_token | function | L126 | L141 | 16 | `get_token()` |
| lark_get | function | L142 | L148 | 7 | `lark_get(url: str, params: dict = None)` |
| extract_msg_text | function | L149 | L180 | 32 | `extract_msg_text(msg: dict)` |
| load_cursor | function | L181 | L190 | 10 | `load_cursor()` |
| save_cursor | function | L191 | L363 | 173 | `save_cursor(cursor: Dict[str, int])` |
| get_iso_week | function | L364 | L370 | 7 | `get_iso_week()` |
| update_dashboard | function | L371 | L496 | 126 | `update_dashboard(progress_by_module: Dict[str, List[str]], dry_run: bool = False)` |
| get_current_period_label | function | L497 | L514 | 18 | `get_current_period_label()` |
| run | function | L515 | L619 | 105 | `run(hours: int = DEFAULT_HOURS, dry_run: bool = False)` |
| main | function | L620 | L640 | 21 | `main()` |

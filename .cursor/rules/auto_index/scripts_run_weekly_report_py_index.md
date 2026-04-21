# scripts/run_weekly_report.py 函数索引

> 自动生成于 2026-04-21 | 总行数: 782 | 函数数: 10 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

**巨型函数警告**: 本文件包含 1 个超过 200 行的函数，建议优先通过 `@section` 标记进行内部导航。

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| get_current_week_str | function | L85 | L91 | 7 | `get_current_week_str()` |
| week_str_to_dates | function | L92 | L100 | 9 | `week_str_to_dates(week_str: str)` |
| make_label | function | L101 | L108 | 8 | `make_label(week_str: str, start_date: str, end_date: str)` |
| get_week_tuesday_date | function | L109 | L118 | 10 | `get_week_tuesday_date(week_str: str)` |
| fetch_xp_weekly_report | function | L119 | L224 | 106 | `fetch_xp_weekly_report(week_str: str)` |
| fetch_meegle_progress | function | L225 | L271 | 47 | `fetch_meegle_progress(week_str: str)` |
| fetch_chat_insights | function | L272 | L612 | **341** | `fetch_chat_insights(week_str: str)` |
| send_lark_notification | function | L613 | L656 | 44 | `send_lark_notification(week_str: str, updated_count: int, dry_run: bool = False)` |
| run | function | L657 | L745 | 89 | `run(week_str: str, dry_run: bool = False, skip_notify: bool = False)` |
| main | function | L746 | L783 | 38 | `main()` |

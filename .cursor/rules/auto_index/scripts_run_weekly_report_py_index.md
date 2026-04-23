# scripts/run_weekly_report.py 函数索引

> 自动生成于 2026-04-23 | 总行数: 893 | 函数数: 11 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

**巨型函数警告**: 本文件包含 1 个超过 200 行的函数，建议优先通过 `@section` 标记进行内部导航。

## 函数列表

> 定位方式：在源文件中 `grep -n "函数名"` 即可跳转，行号不在此列出（行号随代码变化而失效）。

| 函数名 | 类型 | 签名 | 备注 |
|--------|------|------|------|
| get_current_week_str | function | `get_current_week_str()` |  |
| week_str_to_dates | function | `week_str_to_dates(week_str: str)` |  |
| make_label | function | `make_label(week_str: str, start_date: str, end_date: str)` |  |
| get_week_tuesday_date | function | `get_week_tuesday_date(week_str: str)` |  |
| fetch_xp_weekly_report | function | `fetch_xp_weekly_report(week_str: str)` |  |
| fetch_meegle_progress | function | `fetch_meegle_progress(week_str: str)` |  |
| _to_item | method | `_to_item(wi)` |  |
| fetch_chat_insights | function | `fetch_chat_insights(week_str: str)` | ⚠️ 巨型函数，见 @section 导航 |
| send_lark_notification | function | `send_lark_notification(week_str: str, updated_count: int, dry_run: bool = False)` |  |
| run | function | `run(week_str: str, dry_run: bool = False, skip_notify: bool = False)` |  |
| main | function | `main()` |  |

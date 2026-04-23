# scripts/lark_qa_handler.py 函数索引

> 自动生成于 2026-04-23 | 总行数: 610 | 函数数: 16 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

> 定位方式：在源文件中 `grep -n "函数名"` 即可跳转，行号不在此列出（行号随代码变化而失效）。

| 函数名 | 类型 | 签名 | 备注 |
|--------|------|------|------|
| _get_llm_client | function | `_get_llm_client()` |  |
| _get_bitable_token | function | `_get_bitable_token()` |  |
| _fetch_bitable_records | function | `_fetch_bitable_records(table_id: str, max_records: int = 200)` |  |
| _records_to_text | function | `_records_to_text(records: List[Dict], key_fields: List[str])` |  |
| _parse_intent | function | `_parse_intent(question: str)` |  |
| _fetch_topics_data | function | `_fetch_topics_data(keywords: List[str])` |  |
| _fetch_features_data | function | `_fetch_features_data(keywords: List[str])` |  |
| _fetch_modules_data | function | `_fetch_modules_data(keywords: List[str])` |  |
| _fetch_meegle_defects_data | function | `_fetch_meegle_defects_data(keywords: List[str])` |  |
| _fetch_meegle_tasks_data | function | `_fetch_meegle_tasks_data(keywords: List[str])` |  |
| _fetch_meegle_reqs_data | function | `_fetch_meegle_reqs_data(keywords: List[str])` |  |
| _generate_answer | function | `_generate_answer(question: str, context_data: Dict[str, str], intent_summary: str)` |  |
| is_at_bot | function | `is_at_bot(msg_info: Dict)` |  |
| _get_bot_open_id | function | `_get_bot_open_id()` |  |
| _clean_question | function | `_clean_question(text: str)` |  |
| handle_qa | function | `handle_qa(msg_info: Dict)` |  |

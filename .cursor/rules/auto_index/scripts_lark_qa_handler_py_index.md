# scripts/lark_qa_handler.py 函数索引

> 自动生成于 2026-04-22 | 总行数: 610 | 函数数: 16 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| _get_llm_client | function | L90 | L105 | 16 | `_get_llm_client()` |
| _get_bitable_token | function | L106 | L118 | 13 | `_get_bitable_token()` |
| _fetch_bitable_records | function | L119 | L150 | 32 | `_fetch_bitable_records(table_id: str, max_records: int = 200)` |
| _records_to_text | function | L151 | L195 | 45 | `_records_to_text(records: List[Dict], key_fields: List[str])` |
| _parse_intent | function | L196 | L229 | 34 | `_parse_intent(question: str)` |
| _fetch_topics_data | function | L230 | L247 | 18 | `_fetch_topics_data(keywords: List[str])` |
| _fetch_features_data | function | L248 | L264 | 17 | `_fetch_features_data(keywords: List[str])` |
| _fetch_modules_data | function | L265 | L278 | 14 | `_fetch_modules_data(keywords: List[str])` |
| _fetch_meegle_defects_data | function | L279 | L296 | 18 | `_fetch_meegle_defects_data(keywords: List[str])` |
| _fetch_meegle_tasks_data | function | L297 | L313 | 17 | `_fetch_meegle_tasks_data(keywords: List[str])` |
| _fetch_meegle_reqs_data | function | L314 | L356 | 43 | `_fetch_meegle_reqs_data(keywords: List[str])` |
| _generate_answer | function | L357 | L398 | 42 | `_generate_answer(question: str, context_data: Dict[str, str], intent_summary: str)` |
| is_at_bot | function | L399 | L435 | 37 | `is_at_bot(msg_info: Dict)` |
| _get_bot_open_id | function | L436 | L461 | 26 | `_get_bot_open_id()` |
| _clean_question | function | L462 | L477 | 16 | `_clean_question(text: str)` |
| handle_qa | function | L478 | L611 | 134 | `handle_qa(msg_info: Dict)` |

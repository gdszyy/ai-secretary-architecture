# tasks/tsk-c62cf5d9-d66/deliverables/thread_separator.py 函数索引

> 自动生成于 2026-04-19 | 总行数: 713 | 函数数: 9 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

**巨型函数警告**: 本文件包含 1 个超过 200 行的函数，建议优先通过 `@section` 标记进行内部导航。

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| load_project_context | function | L97 | L168 | 72 | `load_project_context()` |
| call_llm | function | L169 | L189 | 21 | `call_llm(system_prompt: str, user_content: str, model: str = None)` |
| parse_llm_json | function | L190 | L203 | 14 | `parse_llm_json(raw: str)` |
| parse_time | function | L204 | L214 | 11 | `parse_time(time_str: Optional[str])` |
| extract_entities | function | L215 | L224 | 10 | `extract_entities(content: str)` |
| build_mention_graph | function | L225 | L282 | 58 | `build_mention_graph(messages: List[Dict])` |
| preprocess_messages | function | L283 | L488 | **206** | `preprocess_messages(messages: List[Dict])` |
| filter_thread_events | function | L489 | L633 | 145 | `filter_thread_events(thread_events: List[Dict])` |
| main | function | L634 | L714 | 81 | `main()` |

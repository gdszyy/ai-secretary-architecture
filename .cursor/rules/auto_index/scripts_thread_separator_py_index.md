# scripts/thread_separator.py 函数索引

> 自动生成于 2026-04-22 | 总行数: 726 | 函数数: 9 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

**巨型函数警告**: 本文件包含 1 个超过 200 行的函数，建议优先通过 `@section` 标记进行内部导航。

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| load_project_context | function | L113 | L184 | 72 | `load_project_context()` |
| call_llm | function | L185 | L205 | 21 | `call_llm(system_prompt: str, user_content: str, model: str = None)` |
| parse_llm_json | function | L206 | L219 | 14 | `parse_llm_json(raw: str)` |
| parse_time | function | L220 | L230 | 11 | `parse_time(time_str: Optional[str])` |
| extract_entities | function | L231 | L240 | 10 | `extract_entities(content: str)` |
| build_mention_graph | function | L241 | L298 | 58 | `build_mention_graph(messages: List[Dict])` |
| preprocess_messages | function | L299 | L500 | **202** | `preprocess_messages(messages: List[Dict])` |
| filter_thread_events | function | L501 | L646 | 146 | `filter_thread_events(thread_events: List[Dict])` |
| main | function | L647 | L727 | 81 | `main()` |

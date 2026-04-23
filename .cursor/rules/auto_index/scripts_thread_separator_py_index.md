# scripts/thread_separator.py 函数索引

> 自动生成于 2026-04-23 | 总行数: 726 | 函数数: 9 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

**巨型函数警告**: 本文件包含 1 个超过 200 行的函数，建议优先通过 `@section` 标记进行内部导航。

## 函数列表

> 定位方式：在源文件中 `grep -n "函数名"` 即可跳转，行号不在此列出（行号随代码变化而失效）。

| 函数名 | 类型 | 签名 | 备注 |
|--------|------|------|------|
| load_project_context | function | `load_project_context()` |  |
| call_llm | function | `call_llm(system_prompt: str, user_content: str, model: str = None)` |  |
| parse_llm_json | function | `parse_llm_json(raw: str)` |  |
| parse_time | function | `parse_time(time_str: Optional[str])` |  |
| extract_entities | function | `extract_entities(content: str)` |  |
| build_mention_graph | function | `build_mention_graph(messages: List[Dict])` |  |
| preprocess_messages | function | `preprocess_messages(messages: List[Dict])` | ⚠️ 巨型函数，见 @section 导航 |
| filter_thread_events | function | `filter_thread_events(thread_events: List[Dict])` |  |
| main | function | `main()` |  |

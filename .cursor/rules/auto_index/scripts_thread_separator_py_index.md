# scripts/thread_separator.py 函数索引

> 自动生成于 2026-04-20 | 总行数: 713 | 函数数: 9 | 语言: python
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
| preprocess_messages | function | L283 | L487 | **205** | `preprocess_messages(messages: List[Dict])` |
| filter_thread_events | function | L488 | L633 | 146 | `filter_thread_events(thread_events: List[Dict])` |
| main | function | L634 | L714 | 81 | `main()` |

## 巨型函数内部节点 (@section 标记)

### preprocess_messages (L283-L487, 205行)

| 节点标记 | 行号 | 说明 |
|----------|------|------|
| `@section:extract_entity_map` | L288 | 逐条消息提取实体关键词 |
| `@section:build_mention_graph` | L294 | 构建 @提及和 reply_to 关联图 |
| `@section:group_by_entity` | L296 | 按实体分组生成初步聚类线索 |

## 其他 @section 标记

| 节点标记 | 行号 | 说明 |
|----------|------|------|
| `@section:guard_empty_input` | L530 | 空消息列表快速返回 |
| `@section:split_sessions` | L534 | 按时间窗口将消息切分为多个 Session |
| `@section:preprocess_per_session` | L543 | 第一阶段预处理（实体提取 + 关联图构建） |
| `@section:llm_separation` | L546 | 第二阶段 LLM 对话分离 |
| `@section:build_thread_events` | L549 | 将 LLM 原始输出转换为标准 ThreadEvent |
| `@section:filter_and_stats` | L553 | 过滤高价值线程并汇总统计信息 |

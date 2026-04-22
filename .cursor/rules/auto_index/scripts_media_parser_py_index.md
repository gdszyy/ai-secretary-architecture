# scripts/media_parser.py 函数索引

> 自动生成于 2026-04-21 | 总行数: 317 | 函数数: 12 | 语言: python
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

## 函数列表

| 函数名 | 类型 | 起始行 | 结束行 | 行数 | 签名 |
|--------|------|--------|--------|------|------|
| _get_lark_token | function | L33 | L41 | 9 | `_get_lark_token()` |
| _is_lark_doc_url | function | L42 | L47 | 6 | `_is_lark_doc_url(url: str)` |
| _extract_lark_doc_token | function | L48 | L53 | 6 | `_extract_lark_doc_token(url: str)` |
| _fetch_lark_doc_content | function | L54 | L82 | 29 | `_fetch_lark_doc_content(doc_token: str, doc_type: str = "wiki")` |
| _fetch_webpage_text | function | L83 | L89 | 7 | `_fetch_webpage_text(url: str, max_chars: int = 3000)` |
| TextExtractor | class | L90 | L90 | 1 | `TextExtractor()` |
| __init__ | method | L91 | L95 | 5 | `__init__(self)` |
| handle_starttag | method | L96 | L99 | 4 | `handle_starttag(self, tag, attrs)` |
| handle_endtag | method | L100 | L103 | 4 | `handle_endtag(self, tag)` |
| handle_data | method | L104 | L115 | 12 | `handle_data(self, data)` |
| _download_lark_image | function | L116 | L234 | 119 | `_download_lark_image(message_id: str, image_key: str)` |
| _summarize_text | function | L235 | L318 | 84 | `_summarize_text(text: str, parse_goal: str, stop_condition: str, source_label: str)` |

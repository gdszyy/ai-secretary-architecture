# 外部资料索引（refs_index）

> **维护说明**：本文件是 Agent 读取外部资料的**唯一入口**。
> 每份飞书索引文档负责维护其下所有子文档的链接清单，**新增资料只需更新飞书索引文档，无需修改本文件**。

## 三层链路

```
Agent（本文件）→ 飞书索引文档（汇总导航页）→ 各专项资料文档
```

---

## 三方集成文档索引

> 供应商 API / SDK 文档汇总。按供应商分行，含适用模块和版本信息。

- **飞书索引文档**：[📚 三方集成文档索引](https://kjpp4yydjn38.jp.larksuite.com/wiki/WWMBwtJuWi7RE1kaPR0j9eaCpih)
- `wiki_token`: `WWMBwtJuWi7RE1kaPR0j9eaCpih`
- **读取方式**：`lark-doc-reader` 读取索引文档 → 按需跳转子文档链接

---

## 参考资料库索引

> 行业报告、技术选型参考、标准规范等通用资料汇总。含核心观点摘要，方便快速判断相关性。

- **飞书索引文档**：[📖 参考资料库索引](https://kjpp4yydjn38.jp.larksuite.com/wiki/Wu8iwCPPFi6pK7k1EwtjfkkRp1b)
- `wiki_token`: `Wu8iwCPPFi6pK7k1EwtjfkkRp1b`
- **读取方式**：`lark-doc-reader` 读取索引文档 → 按需跳转子文档链接

---

## 竞品调研索引

> 竞品功能对比矩阵（置顶核心文件）+ 各竞品详细调研报告存档。按季度更新，旧版本归档保留。

- **飞书索引文档**：[🔍 竞品调研索引](https://kjpp4yydjn38.jp.larksuite.com/wiki/O3YxwzfGxidfHpk6Ygyjj3w4p8k)
- `wiki_token`: `O3YxwzfGxidfHpk6Ygyjj3w4p8k`
- **读取方式**：`lark-doc-reader` 读取索引文档 → 优先读「竞品功能对比矩阵」，再按需读详细报告

---

## Agent 使用规范

1. 处理与某供应商相关的任务时，先读「三方集成文档索引」找到对应 API 文档链接，再用 `lark-doc-reader` 按需读取。
2. 做产品决策或技术选型时，先读「参考资料库索引」的摘要列，判断是否需要精读原文。
3. 做竞品对比分析时，**优先读「竞品功能对比矩阵」**，避免逐份报告全量加载。
4. **严禁全量加载所有子文档**，按需拉取，控制 token 消耗。

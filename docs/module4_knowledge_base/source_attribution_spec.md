# 信源溯源展示规约 (Source Attribution Spec)

本文档对应 R3 需求：**任何 KB 输出都必须标注信源类型 + 信源 ID + 信源原文片段**。这是 KB 的**承诺契约**，所有输出通道（飞书、周报、Web API）必须满足。

## 1. 强制三段式

KB 任何**事实性回答**必须按以下结构输出：

```
【结论】
<不超过 3 句话的直接答案>

【信源】（共 N 条 | 置信度 X.XX）
[1] <type> | captured <YYYY-MM-DD HH:MM> | confidence <0.XX>
    excerpt: "<原文片段，≤500 字符>"
    url: <可点击链接 | 或"无公开链接">

[2] ...

[3] ...

(若 N > 3，第 4 条起折叠为 "[更多 N-3 条信源 →] kb-fact-XXX")
```

### 1.1 适用场景

| 场景 | 是否强制三段式 |
|---|---|
| 飞书 @机器人 查询 | ✅ 强制 |
| 飞书 @机器人 纠正后的确认 | ✅ 强制（展示原值/新值的信源）|
| 周报 / 进度卡片 | ✅ 强制（卡片折叠态可缩，展开必带信源）|
| Web API JSON 响应 | ✅ 强制（信源在独立字段）|
| 闲聊 / 招呼 | ❌ 免（这不是事实性回答）|
| 系统级状态（"我现在在线"等） | ❌ 免 |

### 1.2 飞书消息样例

```
【结论】
支付系统当前 iOS 微信支付仍有问题，预计延期至 5/13 上线。

【信源】（共 3 条 | 置信度 0.92）
[1] human_correction | captured 2026-05-07 10:23 | confidence 0.95
    excerpt: "iOS 还有问题，预计延期到下周三"
    url: 内部审计 kb-corr-20260507-0007

[2] meegle_workitem | captured 2026-05-07 08:31 | confidence 0.85
    excerpt: "工作项 #12345 状态：开发中（owner: 张三，剩余: 修复白屏闪退）"
    url: https://meegle.example/projects/xpbet/items/12345

[3] bitable_row | captured 2026-05-06 09:12 | confidence 0.7
    excerpt: "支付系统：iOS 微信支付路由问题已经修复并通过回归"
    url: https://kjpp4yydjn38.jp.larksuite.com/base/...

⚠ 注意：信源 [3] 与 [1][2] 存在冲突，已被 [1] 纠正覆盖（superseded_by kb-fact-20260507-0099）
```

## 2. 字段渲染细则

### 2.1 `type` 渲染映射

| `source_type` | 飞书显示 | 周报显示 | API 字段 |
|---|---|---|---|
| `bitable_row` | `Bitable` | `多维表格` | `bitable_row` |
| `meegle_workitem` | `Meegle` | `Meegle` | `meegle_workitem` |
| `lark_message` | `飞书群消息` | `群消息` | `lark_message` |
| `lark_doc` | `飞书云文档` | `云文档` | `lark_doc` |
| `github_issue` | `GitHub Issue` | `GitHub` | `github_issue` |
| `github_pr` | `GitHub PR` | `GitHub` | `github_pr` |
| `prd_section` | `PRD 文档` | `需求文档` | `prd_section` |
| `human_correction` | `人工纠正` | `人工确认` | `human_correction` |
| `weekly_report` | `历史周报` | `周报` | `weekly_report` |

### 2.2 `excerpt` 截断规则

```python
def render_excerpt(excerpt: str, max_chars: int = 200) -> str:
    """
    超过 max_chars 时取首 100 + "..." + 尾 60，并在末尾标注 (X 字)。
    保留首尾是因为：首部通常含主语 + 动作；尾部含结论 + 时间。
    """
    if len(excerpt) <= max_chars:
        return excerpt
    return f"{excerpt[:100]}...{excerpt[-60:]} ({len(excerpt)} 字)"
```

| 通道 | `max_chars` |
|---|---|
| 飞书消息 | 200 |
| 周报片段 | 150 |
| API JSON | 完整（不截断）|

### 2.3 `url` 处理

- 有 URL → 直接展示
- 无公开 URL（如飞书群消息） → 展示 `内部信源 source_id`，配合 `kb-cli source show <source_id>` 命令查看
- URL 失效（404 / 已删除）→ 抓取时探测一次，标记 `url_status: invalid`，渲染为 `~~原 URL~~ (已失效)`

### 2.4 `confidence` 显示阈值

| confidence | 渲染前缀 |
|---|---|
| ≥ 0.9 | `✓ confidence 0.9X` |
| 0.7~0.9 | `confidence 0.X` |
| 0.5~0.7 | `⚠ confidence 0.X (建议确认)` |
| < 0.5 | `⚠⚠ confidence 0.X (低置信，仅供参考)` |

整体回答的置信度 = `min(fact.confidence for fact in cited)`（保守取最低）。

## 3. 禁止行为清单

### 3.1 输出禁止

- ❌ "据我了解 / 根据我的判断 / 项目应该是"等无信源措辞
- ❌ "Bitable 显示 …"等只标信源类型不给 ID 不给原文的写法
- ❌ 把 LLM 推断包装为事实而不附 confidence
- ❌ 把多条信源合并成一条 paraphrase（必须 1 信源 1 项展示）
- ❌ 信源原文做无声修改（错别字也保留，标 `[sic]` 即可）

### 3.2 实现禁止

- ❌ Query Engine 在没有 fact 命中时凭 LLM 编造答案。规定行为：返回 `"KB 中暂无相关事实，最近一次相关扫描：<run_id>，未发现匹配。请补充信息或提问其它主题。"`
- ❌ 提示词里允许 LLM "如果信源不足可以补充"。所有 prompt 须显式禁止 LLM 凭空补充。
- ❌ 渲染层做信源**排序优化**而隐藏低置信源。规则是：**全部展示前 5 条**，按 `confidence DESC, captured_at DESC` 排序，第 6 条起折叠（不是删除）。

## 4. Query Engine 输出契约

### 4.1 函数签名

```python
@dataclass
class KBAnswer:
    summary: str                    # 结论文本
    facts_cited: list[FactView]     # 引用的事实列表
    overall_confidence: float       # min(facts.confidence)
    has_conflict: bool              # 引用的事实间是否有 superseded 关系
    fallback: bool                  # True 表示 KB 没命中，给的兜底回答
    rendered_text: str              # 已经按 §1 三段式渲染好的字符串

def answer(question: str, channel: Literal["lark", "weekly", "api"]) -> KBAnswer: ...
```

### 4.2 单元测试要求

`tests/test_kb_query_engine.py` 必须覆盖：

1. **零命中**：问 KB 不存在的主题 → `fallback=True`，`rendered_text` 不包含编造内容
2. **单源命中**：问只有 1 个 fact 的主题 → `facts_cited` 长度 1，`overall_confidence` = 该 fact.confidence
3. **多源一致**：3 个一致信源 → `overall_confidence` 取最低；渲染中 3 条都展示
4. **多源冲突**：有 superseded 链 → `has_conflict=True`，渲染中标⚠提示链
5. **超长 excerpt**：信源 1000 字 → 截断到 200 + "..."
6. **URL 失效**：mock 信源 url_status=invalid → 渲染中划线标记
7. **禁止幻觉**：mock LLM 返回多余文本 → 渲染层剥离仅留 facts_cited 中的内容

## 5. 周报集成

`scripts/extract_weekly_insights.py` 与 `scripts/run_weekly_batch.py` 改造点（P5 阶段）：

- 周报每个段落如果引用了项目状态，必须从 `kb_facts` 拉而非直接 query Bitable
- 段落末尾追加 `[来源] [1][2][3]` 链接列表，链到对应 source_id
- 周报飞书卡片底部增加 `[展开信源 →]` 折叠区，点开看完整 §1 三段式

## 6. PRD 摘要的特殊处理

PRD 文档（`docs/mod_*/PRD_*.md`）通常很长，`source_excerpt` 不可能容纳整篇。规则：

- `excerpt` 取**章节首段 + 第一个 H3 之前的内容**，最多 500 字
- `source_locator.line_range` 必填，让 PM 能精确跳到 GitHub 对应行
- KB 回答如果引用 PRD，URL 必须使用 `https://github.com/.../blob/main/{path}#L{from}-L{to}` 锚定行号

## 7. API 响应 JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["summary", "facts_cited", "overall_confidence", "has_conflict", "fallback"],
  "properties": {
    "summary": {"type": "string"},
    "overall_confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "has_conflict": {"type": "boolean"},
    "fallback": {"type": "boolean"},
    "facts_cited": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["fact_id", "subject", "predicate", "object", "confidence", "sources"],
        "properties": {
          "fact_id": {"type": "string", "pattern": "^kb-fact-"},
          "subject": {"type": "string"},
          "predicate": {"type": "string"},
          "object": {"type": "string"},
          "confidence": {"type": "number"},
          "sources": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "required": ["source_id", "source_type", "excerpt", "captured_at"],
              "properties": {
                "source_id": {"type": "string", "pattern": "^kb-src-"},
                "source_type": {"type": "string"},
                "excerpt": {"type": "string", "maxLength": 500},
                "url": {"type": ["string", "null"]},
                "captured_at": {"type": "string", "format": "date-time"}
              }
            }
          }
        }
      }
    }
  }
}
```

> **API 契约**：`facts_cited[].sources` 的 `minItems: 1` 是硬约束。任何返回 `sources: []` 的 fact 都被视为 schema 违规，调用方应直接报错而非显示。

## 8. 验收标准

KB 上线前必须通过以下回归：

1. **回归 1**：随机抽 20 个真实 PM 历史问题，KB 回答中每个 fact 都能展开到≥1 个有 url 或 source_id 的信源
2. **回归 2**：在 KB 中故意制造冲突（手动写两条 fact），查询时必须标⚠且展示两边
3. **回归 3**：删除一条 source 后查询，相关 fact 渲染必须显式提示"信源已不可访问"而非静默
4. **回归 4**：用 `pytest tests/test_kb_query_engine.py -v` 全过
5. **回归 5**：让 LLM 接收一个"猜测式"问题（如"你觉得 X 模块下周能上吗"），KB 必须返回 fallback 而不是 LLM 自由发挥

# 主动聚合扫描 (Active Aggregation) 设计

本文档对应 R2 需求：**KB 必须能定时主动从多个信源拼出项目状态**。

## 1. 扫描频率与入口

| 扫描类型 | 触发 | 入口脚本 | 说明 |
|---|---|---|---|
| **每日全量扫描** | 每日 08:30 (UTC+8) | `scripts/kb_aggregator.py --mode=daily` | 工作日 + 周末都跑；扫描所有信源 |
| **增量轮询** | 每小时 1 次 | `scripts/kb_aggregator.py --mode=hourly` | 仅扫上次成功扫描后变更的记录（按 `updated_at`）|
| **手动触发** | CLI / Web API | `scripts/kb_aggregator.py --mode=manual --subject="支付系统"` | PM 想立即重算某主语 |
| **事件驱动（P5+）** | Bitable / Meegle webhook | 暂未实现，依赖飞书订阅权限 | 见风险栏 |

接入到现有调度：在 `scripts/run_daily_batch.py` 末尾新增 `kb_aggregator.run(mode="daily")` 调用。

## 2. 信源扫描器（Scanner）矩阵

每个信源对应一个 Scanner 类，输出统一的 `SourceCandidate` 流。

| Scanner | 输入 | 输出（每条）| 备注 |
|---|---|---|---|
| `BitableTopicScanner` | 话题表 `tblKscoaGp6VwhQe` 全量 | `(subject, predicate=status, object, source_locator, excerpt)` | 现有六张表的主入口 |
| `BitableFeatureScanner` | 功能表 `tblLzX7wqGWFr9KP` | 同上 | |
| `BitableModuleScanner` | 模块表 `tblaDW4D2hQS2xCw` | 同上 | |
| `MeegleScanner` | Meegle 三类工作项 | `(subject=工作项标题, predicate=status, object=Meegle 状态字段)` | 复用 `scripts/meegle_client.py` |
| `GitHubScanner` | `gdszyy/ai-secretary-architecture` Issues + PR | `(subject=Issue 标题, predicate=status, object=open/closed + 最新评论)` | 通过 GitHub MCP |
| `PRDScanner` | `docs/mod_*/PRD_*.md` 增量 | `(subject=feature_id, predicate=spec_summary, object=章节正文摘要)` | 走 git diff，仅扫变更段 |
| `WeeklyReportScanner` | 历史周报 Bitable | `(subject=模块, predicate=进度快照, object=周报当周原文)` | 给 PM 回看历史的能力 |

**统一接口**：

```python
class SourceScanner(Protocol):
    def scan(self, since: datetime | None) -> Iterator[SourceCandidate]: ...

@dataclass
class SourceCandidate:
    source_type: str
    source_locator: dict
    excerpt: str
    url: str | None
    captured_at: datetime
    derived_facts: list[FactDraft]  # 一条信源可以衍生 0~N 个 fact 候选
```

## 3. 事实抽取（Fact Extraction）

### 3.1 LLM 抽取 Prompt 骨架

输入：一条 `SourceCandidate.excerpt` + 信源类型上下文
输出：JSON 数组，每元素一个 `FactDraft`

```text
你是一个项目事实抽取器。从以下信源原文中抽取**显式陈述**的事实。
严禁推断未明说的内容。

输入信源类型: {source_type}
输入原文:
"""
{excerpt}
"""

输出 JSON 格式：
[
  {
    "subject": "...",            // 主语：模块/功能/话题/人名
    "subject_type": "module|feature|topic|person|risk",
    "predicate": "status|progress|decision|owner|risk|milestone|dependency",
    "object": "...",             // 不超过200字的事实陈述
    "evidence_quote": "..."     // 原文中支撑该事实的引语，必须出现在 excerpt 内
  }
]

如果原文是闲聊/无关内容，返回空数组 []。
```

> **关键约束**：`evidence_quote` 必须是 `excerpt` 的子串。Aggregator 在写库前用 `assert evidence_quote in excerpt` 校验，否则丢弃该 draft（防止 LLM 幻觉）。

### 3.2 模型选择

复用项目现有 `qwen-plus`（`DASHSCOPE_API_KEY`），抽取任务相对简单不需要更强模型。
后续可配 `KB_EXTRACT_MODEL` 切换。

## 4. 与现有 KB 对齐（Alignment）

抽取得到的 `FactDraft` 进入对齐器：

```python
def align(draft: FactDraft) -> AlignmentDecision:
    """
    返回三种决策之一：
      - MATCH (existing_fact_id, similarity): 与现有 fact 一致 → 增信
      - CONFLICT (existing_fact_id, similarity): 主谓相同但宾语不同 → 进冲突队列
      - NEW: 全新事实 → 直接落库
    """
```

### 4.1 对齐算法

1. 用 `(subject, predicate)` 在 `kb_facts` 中找当前 active 的 fact（`superseded_by IS NULL`）
2. 如果命中：
   - 计算 `object` 的语义相似度（向量索引余弦相似度）
   - `similarity >= 0.85` → **MATCH**
   - `similarity < 0.85` → **CONFLICT**
3. 如果未命中：**NEW**

### 4.2 决策动作

| 决策 | 写库动作 | confidence 变化 |
|---|---|---|
| MATCH | 在已有 fact.source_refs 中追加新 source_id；不新建 fact | `+0.1`（封顶 1.0）|
| CONFLICT | 创建 `kb_conflicts` 行；不直接覆盖 fact | 待人工解决 |
| NEW | 新建 fact + source；status active | `0.7`（单源默认）|

## 5. 冲突解决

### 5.1 冲突类型

| 冲突 | 例子 |
|---|---|
| **状态冲突** | Bitable 说"已完成"，Meegle 说"开发中" |
| **决策冲突** | 周一会议说选 A，周三周会说选 B（且时间均当周）|
| **负责人冲突** | PRD 写张三，Meegle 分配李四 |

### 5.2 自动尝试解决（轻量规则）

在 LLM 介入前先跑 3 条规则：

1. **时间优先**：同主谓两条候选，`captured_at` 晚的胜出，但 confidence 给 0.6（提示降权）
2. **SSOT 偏好**：如果一方是 Meegle 且 fact 类型是"开发状态"，按 `global.md` SSOT 规则，Meegle 胜
3. **多源一致**：3 条候选中 2 条说 X、1 条说 Y → X 胜，confidence 0.85；Y 进 `kb_conflicts`

### 5.3 升级到 PM 追问

规则解决不了 → 落 `kb_conflicts.status = pending` → 每日 17:00 触发追问推送：

```
@PM 今日发现 1 处项目认知冲突：
【主语】支付系统
【谓语】status
【候选 1】(来自 Bitable, 2026-05-06 09:12)
   "iOS 微信支付已修复"
【候选 2】(来自 Meegle, 2026-05-06 14:30)
   "iOS 工作项 #12345 状态：开发中"

请回复：
  1 → 采纳 Bitable
  2 → 采纳 Meegle
  3 → 都不对，我手动纠正
```

PM 回复 1/2 → 写入采纳的 fact，confidence 1.0（人工确认）
PM 回复 3 → 进入纠正流程（[`correction_flow.md`](./correction_flow.md)）

## 6. 调度器实现要点

```python
# scripts/kb_aggregator.py 核心结构（伪代码）

def run(mode: str):
    run_id = f"agg-{datetime.now():%Y%m%d-%H%M}"
    since = _last_run_time() if mode == "hourly" else None

    scanners: list[SourceScanner] = [
        BitableTopicScanner(),
        BitableFeatureScanner(),
        BitableModuleScanner(),
        MeegleScanner(),
        GitHubScanner(),
        PRDScanner(),
    ]

    stats = AggStats()
    for scanner in scanners:
        for candidate in scanner.scan(since=since):
            source_id = upsert_source(candidate)  # 含 hash 去重
            for draft in candidate.derived_facts:
                draft.evidence_quote in candidate.excerpt or _drop_and_log(draft, "evidence_not_in_excerpt")
                decision = align(draft)
                _apply(decision, draft, source_id, run_id)
                stats.tick(decision.kind)

    _record_run_summary(run_id, stats)
    if stats.conflicts > 0:
        _send_conflict_card_to_pm(run_id)
```

## 7. 性能与限流

| 维度 | 数值 |
|---|---|
| Bitable 拉取 | `page_size=100`，间隔 200ms（沿用 `correction_writer.py` 节奏）|
| Meegle 拉取 | 沿用 `meegle_client.py` 配置 |
| LLM 抽取 | 单次 ≤ 100 candidate；超出排队下一轮；批次内并发 5 |
| 单次 daily run | 预计 < 10 分钟（基于现有 6 张表 ~2000 行规模）|

## 8. 可观测性

每次 run 写一条 `agg_runs` 元数据（落到 `state/kb_agg_runs.jsonl`，不进 Bitable 避免噪音）：

```json
{
  "run_id": "agg-20260507-0830",
  "mode": "daily",
  "started_at": "...",
  "ended_at": "...",
  "scanned_records": 1843,
  "candidates": 412,
  "facts_match": 380,
  "facts_new": 18,
  "conflicts": 14,
  "errors": [{"scanner": "MeegleScanner", "error": "..."}]
}
```

PM 可以通过 `@AI秘书 KB 最近一次扫描结果` 看上一份 run summary。

## 9. 与现有 `daily_progress_updater.py` 的关系

现有 `scripts/daily_progress_updater.py` 已经做了一部分"从 Bitable 推断进度"的事。

**KB Aggregator 不替换它**，而是：
- 进度类 fact 的"预计完成日期 / 完成度百分比" 仍由 daily_progress_updater 计算后写 Bitable
- KB Aggregator 把 daily_progress_updater 的产出**作为信源之一**抓取到 kb_facts

避免重复造轮子。

## 10. 风险

| 风险 | 缓解 |
|---|---|
| 飞书群消息没有公开 webhook 权限 → KB 拿不到群事实 | 短期：仍依赖现有 `thread_separator` 落库 Bitable，KB 从 Bitable 间接拿；长期等 PF-001 |
| LLM 抽取错把"我觉得 / 可能"包装为事实 | Prompt 强约束 + `evidence_quote` 必须存在 + confidence 强制 ≤ 0.8 |
| 冲突队列爆炸（PM 不及时确认）| `pending` > 7 天自动降级为 `auto_resolved`（采纳最新源），但 confidence 降到 0.5 标记给 PM |

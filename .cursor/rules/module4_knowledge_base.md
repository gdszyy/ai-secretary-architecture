---
description: "module4_knowledge_base 模块（KB 知识库）的设计规范、红线约束与核心逻辑说明"
globs: ["docs/module4_knowledge_base/**/*", "scripts/kb_*.py"]
---

# module4_knowledge_base 模块规范

## 1. 模块职责

KB（Knowledge Base）是 AI 秘书系统对项目的**长期事实记忆层**。三大刚性需求：

1. **R1 实时纠正认知**：PM 在飞书 @机器人 用自然语言纠正，30 秒内生效
2. **R2 主动获取信息**：定时扫描 Bitable/Meegle/GitHub/PRD，自动构建项目认知
3. **R3 信源标注**：所有回答必须带 `[type | excerpt | url | confidence]`，禁止无信源回答

## 2. 三条红线（违反必须驳回 PR）

| 红线 | 检查点 |
|---|---|
| **R-1：信源完整** | 任何 KB 输出必须含 `source_id` + `excerpt` + `confidence`；excerpt 不能为空 |
| **R-2：审计完整** | 任何对 `kb_facts` 的写入必须先在 `kb_corrections` 落账（Aggregator 自动写入除外，但需带 `agg_run_id`）|
| **R-3：禁止幻觉** | LLM 抽取必须有 `evidence_quote` 字段且 `evidence_quote in source_excerpt`；查询路径禁止 LLM 补充原文之外内容 |

## 3. 核心数据模型

4 张 Bitable 表（详见 [`docs/module4_knowledge_base/data_model.md`](../docs/module4_knowledge_base/data_model.md)）：

| 表 | 主键 | 职责 |
|---|---|---|
| `kb_facts` | `fact_id` | 事实主表（subject + predicate + object + 信源 + 置信度）|
| `kb_sources` | `source_id` | 信源表（type + locator + excerpt + url）|
| `kb_corrections` | `correction_id` | 纠正流水（永远追加不删除）|
| `kb_conflicts` | `conflict_id` | 冲突队列（待 PM 解决）|

**关键不变量**：
- `kb_facts.superseded_by` 形成纠正链；`active fact` = `superseded_by IS NULL`
- 同 `(subject, predicate)` 同时只能有 1 条 active
- 任何 source 写入前必须按 `hash` 去重

## 4. 核心脚本

待实现（见 [`docs/module4_knowledge_base/README.md`](../docs/module4_knowledge_base/README.md) 路线图）：

| 脚本 | 职责 |
|---|---|
| `scripts/kb_schema_init.py` | 创建/校验 4 张 KB 表 |
| `scripts/kb_aggregator.py` | 多源扫描、事实抽取、对齐、冲突识别 |
| `scripts/kb_nl_correction_parser.py` | LLM 解析自然语言纠正 |
| `scripts/kb_correction_writer.py` | 纠正写入 + 审计 |
| `scripts/kb_query_engine.py` | 向量检索 + 三段式回答 |
| `scripts/kb_router.py` | 飞书 webhook KB 路由分发 |
| `scripts/kb_cli.py` | CLI 工具（`kb query / kb fact / kb agg / kb schema`）|

## 5. 路由优先级（main.py）

```
1. is_at_bot + is_correction_command  → lark_correction_handler  (现有结构化纠正)
2. is_at_bot + kb_router.is_kb_correction → kb_router.handle_correction  (新增 NL 纠正)
3. is_at_bot + kb_router.is_kb_query  → kb_router.handle_query        (新增 KB 查询)
4. is_at_bot                          → lark_qa_handler           (现有 QA 兜底)
5. ...其它现有路径
```

> KB 路由必须**插入**在现有路径之间，不替换；`lark_qa_handler` 内部应优先 `kb_query_engine.try_answer_first()`。

## 6. 输出契约（强制三段式）

任何 KB 事实性回答（飞书、周报、API）必须按 [`source_attribution_spec.md`](../docs/module4_knowledge_base/source_attribution_spec.md) §1 输出：

```
【结论】<不超过 3 句话>
【信源】（共 N 条 | 置信度 X.XX）
[1] type | captured 时间 | confidence
    excerpt: "..."
    url: ...
[2] ...
```

`facts_cited[].sources.minItems = 1` 是 schema 硬约束，违反必须报错。

## 7. 与现有模块的关系（不破坏 SSOT）

| 现有模块 | KB 关系 | 禁止 |
|---|---|---|
| `module1_kanban` | KB 是 kanban 周报的信源 | ❌ 禁止 KB 直接修改 kanban 看板状态 |
| `module2_buffer` | Buffer 落 Bitable 后，KB Aggregator 间接抓 | ❌ 禁止 KB 直接消费 Buffer 内部状态 |
| `module3_info_sources` | 共享多源采集思路 | ❌ 禁止重复实现已有 Scanner |
| 现有 `correction_writer.py` | KB 包装它，附加审计 | ❌ 禁止绕过 `kb_corrections` 直写 Bitable |
| 现有 `lark_qa_handler.py` | KB 优先；qa_handler 兜底 | ❌ 禁止删除 qa_handler 兜底路径 |

## 8. 测试覆盖要求

`tests/test_kb_*.py` 必须覆盖：

1. NL Parser 在 0.6/0.8 阈值的边界行为
2. 信源 evidence_quote 校验（必须是 excerpt 子串）
3. Supersession 链多跳的回放
4. 强制三段式渲染的零命中、单源、多源冲突场景
5. URL 失效的渲染降级

详见 [`source_attribution_spec.md`](../docs/module4_knowledge_base/source_attribution_spec.md) §8 验收标准。

## 9. 详细设计文档索引

| 文档 | 路径 | 说明 |
|---|---|---|
| 模块 README | `docs/module4_knowledge_base/README.md` | 模块入口，速读路径 |
| 总体设计 | `docs/module4_knowledge_base/knowledge_base_design.md` | 架构、组件、风险 |
| 数据模型 | `docs/module4_knowledge_base/data_model.md` | 4 表字段定义 |
| 主动聚合 | `docs/module4_knowledge_base/active_aggregation.md` | 多源扫描设计 |
| 纠正流程 | `docs/module4_knowledge_base/correction_flow.md` | NL 纠正交互 |
| 信源溯源规约 | `docs/module4_knowledge_base/source_attribution_spec.md` | 三段式输出契约 |
| API 设计 | `docs/module4_knowledge_base/api_design.md` | webhook / CLI / HTTP API |
| 生命周期图 | `docs/module4_knowledge_base/lifecycle_flow.md` | Mermaid 全链路图 |

## 10. 流程洞察沉淀

实施过程中如发现以下情况，必须在 `.cursor/rules/process_insights/` 沉淀洞察：

- 多源 fact 对齐的相似度阈值需要按主语类型差异化（如 status 类阈值低、决策类阈值高）
- 飞书 NL 纠正在某种句式下解析率显著下降
- 某信源类型的 URL 失效率高（如 Meegle 接口频繁变动），需要降级展示策略
- KB 与现有 `daily_progress_updater.py` 的进度数据不一致

按 [`global.md`](./global.md) 第 6 节"流程洞察沉淀"规则记录。

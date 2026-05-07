# 模块四：项目知识库 (Knowledge Base)

> **状态**：架构设计 v0.1（2026-05-07）
> **分支**：`claude/knowledge-base-system-jmztX`
> **范围**：本目录仅包含设计文档，实现脚本将在后续 PR 落地

## 模块定位

KB 是 AI 秘书系统对项目的**长期事实记忆层**，为 PM 提供：

1. **可纠正的项目认知** —— 飞书 @机器人 一句"这个不对，实际是…"即可改正
2. **主动获取多源信息** —— 定时扫描 Bitable / Meegle / GitHub / PRD，自己拼出项目状态
3. **强制信源标注** —— 每个回答都带 `[type | excerpt | url | confidence]`，PM 一眼看清依据

## 文档索引

| 文件 | 说明 | 必读优先级 |
|---|---|---|
| [`knowledge_base_design.md`](./knowledge_base_design.md) | 总体架构、三大刚性需求、组件清单、风险 | ★★★ |
| [`data_model.md`](./data_model.md) | 4 张 Bitable 表的字段、约束、样例数据 | ★★★ |
| [`active_aggregation.md`](./active_aggregation.md) | 多源扫描、事实抽取、对齐、冲突解决 | ★★ |
| [`correction_flow.md`](./correction_flow.md) | 自然语言纠正解析、写入、撤销 | ★★ |
| [`source_attribution_spec.md`](./source_attribution_spec.md) | 信源溯源展示规约（强制三段式）、禁止行为 | ★★★ |
| [`api_design.md`](./api_design.md) | webhook 路由扩展、CLI、HTTP API | ★★ |
| [`lifecycle_flow.md`](./lifecycle_flow.md) | 全链路 Mermaid 流程图与状态机 | ★ |

## 关键决策（速读）

| 决策 | 选择 | 理由 |
|---|---|---|
| **存储** | Bitable + 本地 FAISS 向量索引 | 事实落 Bitable 可视，向量索引支持语义检索；不引入新数据库 |
| **主动获取** | 定时扫描 + LLM 抽取 + 对齐 | 现成数据源（6 张 Bitable + Meegle + GitHub）已涵盖 90% 项目信息 |
| **纠正入口** | @机器人 自然语言（保留现有 `纠正：xxx` 格式作并行入口） | 降低 PM 心智成本；两条路径共享 `kb_corrections` 审计 |
| **纠正语义** | 永远追加，不删除（superseded 链）| 支持回看历史；审计完整 |
| **信源展示** | 强制三段式（结论 + 信源 + 置信度），禁止无信源回答 | R3 红线需求；任何违反必须驳回 |
| **冲突解决** | 自动规则（时间/SSOT/多数）→ 失败则飞书追问 PM | 减少 PM 打扰但保留人工兜底 |

## 三大红线

任何 PR 或 Agent 工作如果违背任一条，必须驳回：

1. ❌ KB 输出不带信源 / 不带原文片段 / 不带置信度
2. ❌ KB 写入路径绕过 `kb_corrections` 审计
3. ❌ Aggregator / Parser 把 LLM 推断当事实写库（必须有 `evidence_quote` 校验）

## 与其它模块的关系

| 模块 | 关系 |
|---|---|
| `module1_kanban` | 看板是 KB 的**展示通道**之一；周报集成 KB 输出 |
| `module2_buffer` | Buffer 落 Bitable 后，KB Aggregator 间接抓取（不双写）|
| `module3_info_sources` | KB 与 module3 共享多源采集思路；KB 扩展为"采集 + 长期记忆 + 信源追溯" |

## 实施路线图

| 阶段 | 内容 | 输出 | 状态 |
|---|---|---|---|
| **P1** | 架构设计 | 本目录全部文档 | ✅ 当前 PR |
| **P2** | 数据骨架 | Bitable 4 张表 + `scripts/kb_schema_init.py` | ⏳ 下一 PR |
| **P3** | 聚合器 | `scripts/kb_aggregator.py` | ⏳ |
| **P4** | 纠正闭环 | `scripts/kb_nl_correction_parser.py` + `main.py` 路由 | ⏳ |
| **P5** | 查询引擎 | `scripts/kb_query_engine.py` + 向量索引 | ⏳ |
| **P6** | 试运行 | 上线 1 周，看 `kb_corrections` 频率与冲突解决率 | ⏳ |

## 给 Agent 的速查

如果你被分配了 KB 相关任务：

1. **先读** [`knowledge_base_design.md`](./knowledge_base_design.md) §1~§3（5 分钟读完）
2. **改数据模型** → 改 [`data_model.md`](./data_model.md)；同时更新 `scripts/kb_schema_init.py`
3. **加新信源** → 改 [`active_aggregation.md`](./active_aggregation.md) §2 矩阵；实现新 Scanner
4. **改输出格式** → 必须先改 [`source_attribution_spec.md`](./source_attribution_spec.md)；prompt 与渲染层同步改
5. **加新错误码** → 改 [`api_design.md`](./api_design.md) §7
6. **任何写入路径** → 检查是否有 `kb_corrections` 审计；没有就驳回

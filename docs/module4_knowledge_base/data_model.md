# KB 数据模型详解

本文档展开 [`knowledge_base_design.md`](./knowledge_base_design.md) §4 的三张核心表的字段定义、约束、索引与样例数据。所有表都落在飞书 Bitable，遵循 `BITABLE_BASE_ID` 环境变量指向的同一 App。

## 1. `kb_facts` — 事实表

### 1.1 字段定义

| 字段 | Bitable 类型 | 必填 | 默认值 | 校验 | 说明 |
|---|---|---|---|---|---|
| `fact_id` | 单行文本（主键）| ✅ | 自动生成 | 唯一；格式 `kb-fact-YYYYMMDD-NNNN` | KB 内部 ID |
| `subject` | 单行文本 | ✅ | — | ≤ 100 字 | 主语：模块名/功能/话题/人名 |
| `subject_type` | 单选 | ✅ | — | `module` / `feature` / `topic` / `person` / `risk` | 主语类型 |
| `predicate` | 单选 | ✅ | — | `status` / `progress` / `decision` / `owner` / `risk` / `milestone` / `dependency` | 谓语 |
| `object` | 多行文本 | ✅ | — | ≤ 2000 字 | 事实内容 |
| `confidence` | 数字（小数）| ✅ | 0.7 | 0.0~1.0 | 置信度 |
| `source_refs` | 多行文本（JSON）| ✅ | `[]` | JSON Array of `source_id` | 关联信源 ID 列表 |
| `valid_from` | 日期时间 | ✅ | now() | — | 事实生效时间 |
| `superseded_by` | 单行文本 | ❌ | null | 引用 `fact_id` | 纠正后指向新 fact |
| `corrected_by` | 用户（飞书）| ❌ | null | open_id | 谁纠正的（仅纠正路径有值）|
| `agg_run_id` | 单行文本 | ❌ | null | — | 聚合扫描批次 ID（便于回滚）|
| `created_at` | 创建时间 | ✅ | 自动 | — | |
| `updated_at` | 修改时间 | ✅ | 自动 | — | |

### 1.2 唯一性约束

- `(subject, predicate, valid_from)` 联合唯一：同一主谓在同一时刻只能有一条 active fact
- "active" 定义：`superseded_by IS NULL`

### 1.3 查询索引（应用层维护，Bitable 不支持二级索引）

写入 `data/kb_index/`：
- `subject_index.json`：`{subject: [fact_id, ...]}` 倒排
- `vector_index.faiss`：`object` 字段的 384 维向量（bge-small-zh）
- `predicate_index.json`：`{predicate: [fact_id, ...]}`

### 1.4 样例

```json
{
  "fact_id": "kb-fact-20260507-0042",
  "subject": "支付系统",
  "subject_type": "module",
  "predicate": "status",
  "object": "iOS 微信支付路由问题已修复，已通过回归测试，预计本周五随版本上线",
  "confidence": 0.95,
  "source_refs": ["kb-src-20260507-0103", "kb-src-20260507-0104"],
  "valid_from": "2026-05-06T09:12:00+08:00",
  "superseded_by": null,
  "corrected_by": null,
  "agg_run_id": "agg-20260507-0830",
  "created_at": "2026-05-07T08:33:12+08:00",
  "updated_at": "2026-05-07T08:33:12+08:00"
}
```

### 1.5 状态机

```
[新建 active]
    │
    ├─ 聚合扫描发现一致 → confidence += 0.1（封顶 1.0）
    ├─ 聚合扫描发现冲突 → 创建 kb_conflicts，等待人工
    ├─ PM 纠正 → 当前 fact.superseded_by = new_fact_id；new_fact 为 active
    └─ 6 个月未被引用 → 归档到 archive/kb_facts_YYYYMM
```

## 2. `kb_sources` — 信源表

### 2.1 字段定义

| 字段 | Bitable 类型 | 必填 | 校验 | 说明 |
|---|---|---|---|---|
| `source_id` | 单行文本（主键）| ✅ | `kb-src-YYYYMMDD-NNNN` 唯一 | 信源 ID |
| `source_type` | 单选 | ✅ | 见 §2.2 | 信源类型 |
| `source_locator` | 多行文本（JSON）| ✅ | 合法 JSON | 可定位元数据 |
| `source_excerpt` | 多行文本 | ✅ | 1~500 字 | **必填**，原文片段 |
| `url` | URL | ❌ | http(s):// | 跳转链接 |
| `captured_at` | 日期时间 | ✅ | — | 抓取时间 |
| `captured_by` | 单选 | ✅ | `aggregator` / `webhook` / `manual` | 谁抓的 |
| `hash` | 单行文本 | ✅ | md5(source_locator + excerpt) | 去重用 |

### 2.2 `source_type` 枚举与 `source_locator` schema

| `source_type` | `source_locator` 必填字段 | URL 模板 |
|---|---|---|
| `bitable_row` | `app_token`, `table_id`, `record_id` | `https://{tenant}.feishu.cn/base/{app_token}?table={table_id}&view={view_id}` |
| `meegle_workitem` | `project_key`, `work_item_id`, `type` | `https://meegle.{domain}/projects/{project_key}/items/{work_item_id}` |
| `lark_message` | `chat_id`, `message_id`, `sender_open_id` | 飞书消息没有公开 URL，存 `chat_id+message_id`，前端自行拼跳转 |
| `lark_doc` | `doc_token`, `block_id` | `https://{tenant}.feishu.cn/docx/{doc_token}#{block_id}` |
| `github_issue` | `repo`, `issue_number` | `https://github.com/{repo}/issues/{issue_number}` |
| `github_pr` | `repo`, `pr_number` | `https://github.com/{repo}/pull/{pr_number}` |
| `prd_section` | `file_path`, `section_anchor`, `line_range` | `https://github.com/gdszyy/ai-secretary-architecture/blob/main/{file_path}#L{from}-L{to}` |
| `human_correction` | `corrector_open_id`, `correction_log_id` | 内部跳转 `kb_corrections` 表行 |
| `weekly_report` | `report_id`, `period`, `section` | 周报 Bitable 行链接 |

### 2.3 去重策略

写入前先算 `hash = md5(source_locator_canonical_json + excerpt[:200])`：
- 命中已有 hash → 复用 `source_id`，不新建
- 未命中 → 创建新 `source_id`

这样 PM 同一句话被多次扫描，只产生 1 条 source 记录。

### 2.4 样例

```json
{
  "source_id": "kb-src-20260507-0103",
  "source_type": "bitable_row",
  "source_locator": {
    "app_token": "CyDxbUQGGa3N2NsVanMjqdjxp6e",
    "table_id": "tblKscoaGp6VwhQe",
    "record_id": "recABC123"
  },
  "source_excerpt": "支付系统：iOS 微信支付路由问题已经修复并通过回归。来源：技术周会 2026-05-06",
  "url": "https://kjpp4yydjn38.jp.larksuite.com/base/CyDxbUQGGa3N2NsVanMjqdjxp6e?table=tblKscoaGp6VwhQe",
  "captured_at": "2026-05-07T08:30:42+08:00",
  "captured_by": "aggregator",
  "hash": "a4f21c..."
}
```

## 3. `kb_corrections` — 纠正流水表

### 3.1 字段定义

| 字段 | Bitable 类型 | 必填 | 说明 |
|---|---|---|---|
| `correction_id` | 单行文本（主键）| ✅ | `kb-corr-YYYYMMDD-NNNN` |
| `target_fact_id` | 单行文本 | ❌ | 被纠正的 fact_id；新增事实场景留空，落库后回填 |
| `created_fact_id` | 单行文本 | ❌ | 纠正后产生的新 fact_id |
| `corrector_open_id` | 用户（飞书）| ✅ | open_id |
| `corrector_name` | 单行文本 | ✅ | 飞书显示名（冗余但便于人读）|
| `entry_channel` | 单选 | ✅ | `lark_at_bot` / `lark_card_reply` / `manual_script` / `web_api` |
| `raw_message` | 多行文本 | ✅ | 用户原话 |
| `parsed_intent` | 多行文本（JSON）| ✅ | NL Parser 解析结果 |
| `parser_confidence` | 数字（小数）| ✅ | 解析置信度 |
| `applied` | 复选框 | ✅ | 是否落库成功 |
| `apply_error` | 多行文本 | ❌ | 失败原因 |
| `created_at` | 创建时间 | ✅ | |

### 3.2 `parsed_intent` 结构

```json
{
  "action": "update" | "create" | "delete" | "ambiguous",
  "subject": "支付系统",
  "subject_type": "module",
  "predicate": "status",
  "old_object_hint": "已修复",
  "new_object": "iOS 还有问题，预计延期到下周三",
  "ambiguity": null
}
```

`action = "ambiguous"` 时 webhook 反问 PM 二选一，不直接落库（见 [`correction_flow.md`](./correction_flow.md) §3.4）。

### 3.3 永不删除原则

`kb_corrections` 是**追加日志**。即使纠正失败、被撤销，也只新建一条 `applied=false` 的记录解释原因，从不修改/删除历史行。

## 4. 辅助表：`kb_conflicts`（冲突队列）

聚合扫描发现"同主谓多源不一致"时落账。

| 字段 | Bitable 类型 | 说明 |
|---|---|---|
| `conflict_id` | 主键 | `kb-conf-YYYYMMDD-NNNN` |
| `subject` / `predicate` | 文本 | 冲突点 |
| `candidate_facts` | JSON | 多源给出的候选 fact 列表（含 source_refs）|
| `status` | 单选 | `pending` / `asked_pm` / `resolved` |
| `resolution_fact_id` | 文本 | 解决后落地的 fact_id |
| `created_at` / `resolved_at` | 时间戳 | |

冲突解决路径见 [`active_aggregation.md`](./active_aggregation.md) §5。

## 5. 表创建脚本契约

`scripts/kb_schema_init.py`（P2 阶段交付）应：
1. 检查 4 张表是否存在；不存在则按本文档字段创建
2. 字段类型与本文档不一致时，**报错退出**而不是静默修复
3. 输出环境变量片段供 `.env` 复制：
   ```
   BITABLE_TABLE_KB_FACTS=tblXXXXX
   BITABLE_TABLE_KB_SOURCES=tblXXXXX
   BITABLE_TABLE_KB_CORRECTIONS=tblXXXXX
   BITABLE_TABLE_KB_CONFLICTS=tblXXXXX
   ```

## 6. 命名空间约定

| 前缀 | 含义 |
|---|---|
| `kb-fact-` | Fact ID |
| `kb-src-` | Source ID |
| `kb-corr-` | Correction ID |
| `kb-conf-` | Conflict ID |
| `agg-` | 聚合扫描批次 ID |

所有 ID 后缀采用 `YYYYMMDD-NNNN`（4 位序号当日重置），确保人读和时间排序友好。

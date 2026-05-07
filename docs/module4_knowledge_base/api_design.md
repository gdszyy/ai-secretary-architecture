# KB API 与 Webhook 集成设计

## 1. 系统集成视图

```mermaid
flowchart LR
    subgraph 入口
        FW[/lark/webhook<br/>main.py/]
        CLI[scripts/kb_cli.py<br/>命令行]
        API[/api/kb/*<br/>FastAPI]
    end

    subgraph KB核心
        ROUTER[KB Router]
        QE[Query Engine]
        CW[Correction Writer]
        AGG[Aggregator]
    end

    subgraph 存储
        BT[(Bitable<br/>4 张 KB 表)]
        VEC[(FAISS<br/>data/kb_vector.faiss)]
        ST[(state/kb_*.jsonl)]
    end

    FW --> ROUTER
    CLI --> ROUTER
    API --> ROUTER
    ROUTER --> QE & CW & AGG
    QE --> BT & VEC
    CW --> BT
    AGG --> BT & ST
```

## 2. Webhook 路由扩展（`main.py`）

### 2.1 现有路由（参考）

```python
# main.py 当前路由优先级（高 → 低）
1. is_at_bot + is_correction_command  → lark_correction_handler  (现有"纠正：xxx"格式)
2. is_at_bot                          → lark_qa_handler           (问答)
3. is_explicit_record_intent          → requirement_tracker
4. (前端群组)                          → frontend_defect_reporter
5. (其它)                              → thread_separator
```

### 2.2 新增 KB 路由（最小侵入）

```python
# main.py 改造（插入到现有 1, 2 之间）
def handle_message_event(event):
    text = extract_text(event)
    if not text:
        return _ok()

    # ── 现有逻辑（保留）：「纠正：xxx」结构化指令 ──
    if is_correction_command(text):
        return lark_correction_handler.handle_correction(event)

    # ── 新增：KB 自然语言纠正（@ 机器人 + 纠正语义）──
    if is_at_bot(event) and kb_router.is_kb_correction(text):
        return kb_router.handle_correction(event)

    # ── 新增：KB 查询（@ 机器人 + 项目状态类问题）──
    if is_at_bot(event) and kb_router.is_kb_query(text):
        return kb_router.handle_query(event)

    # ── 现有逻辑（保留）：通用 QA / 默认问答 ──
    if is_at_bot(event):
        return lark_qa_handler.handle_qa(event)

    # ── 现有逻辑（保留）：requirement_tracker / 前端群 / thread_separator ──
    ...
```

### 2.3 `is_kb_query` 判别

```python
KB_QUERY_TRIGGERS = [
    # 项目状态类问题特征
    r"(进度|状态|完成情况|还剩|什么时候|预计|延期|阻塞|风险)",
    r"(谁负责|owner|负责人|对接人)",
    r"(决策|结论|定下来|拍板|选了)",
    r"(模块|功能|话题).*(怎么样|如何|进展)",
]

def is_kb_query(text: str) -> bool:
    cleaned = strip_at_mention(text)
    if any(re.search(p, cleaned) for p in KB_QUERY_TRIGGERS):
        return True
    # 兜底：如果含有已知 subject 又像疑问句，走 KB
    if contains_known_subject(cleaned) and is_question(cleaned):
        return True
    return False
```

> **路由保守策略**：判错宁可"漏判"走 `lark_qa_handler`（现有 QA），也不要"过判"把闲聊路由到 KB。`lark_qa_handler` 本身已能 fallback。

## 3. KB Router 模块

新文件：`scripts/kb_router.py`

```python
"""
KB Router — 飞书 webhook 入口分发器

职责：
  - 暴露 is_kb_query / is_kb_correction 给 main.py
  - 接收 event，路由到 query_engine / correction_writer
  - 统一处理飞书签名 / 鉴权 / 异步回复
"""

from kb_query_engine import answer
from kb_correction_writer import handle_correction as _handle_correction
from kb_nl_correction_parser import is_correction_intent

def is_kb_correction(text: str) -> bool:
    return is_correction_intent(strip_at_mention(text))

def is_kb_query(text: str) -> bool:
    # ... 见 §2.3
    ...

def handle_query(event: dict) -> dict:
    text = strip_at_mention(extract_text(event))
    kb_answer = answer(text, channel="lark")
    _reply_to_lark(event, kb_answer.rendered_text)
    return {"code": 0}

def handle_correction(event: dict) -> dict:
    ctx = build_correction_context(event)
    result = _handle_correction(ctx)
    return {"code": 0, "applied": result.applied}
```

## 4. CLI 工具：`scripts/kb_cli.py`

供运维和调试使用。所有命令默认输出 JSON，加 `--pretty` 美化。

| 命令 | 功能 |
|---|---|
| `kb query "<question>"` | 执行查询，返回 KBAnswer |
| `kb fact show <fact_id>` | 展示一个 fact 的全部字段 + 信源 |
| `kb fact list --subject=<s>` | 按 subject 列出 active facts |
| `kb fact history <fact_id>` | 展开 superseded 链 |
| `kb source show <source_id>` | 展示信源原文（包括飞书消息无 URL 的情况）|
| `kb correction list --since=<date>` | 列出最近纠正流水 |
| `kb correction undo <correction_id>` | 撤销纠正（同 §correction_flow §4.3）|
| `kb agg run --mode=daily\|hourly\|manual` | 触发聚合扫描 |
| `kb agg last` | 查看最近一次聚合 run summary |
| `kb conflict list --status=pending` | 列出待解决冲突 |
| `kb conflict resolve <conf_id> --pick=<n>` | 解决冲突（n = 候选编号）|
| `kb schema verify` | 校验 4 张 KB 表的字段是否符合 `data_model.md` |
| `kb schema init` | 创建 4 张 KB 表（首次部署用）|

## 5. HTTP API（FastAPI，预留）

新文件 `scripts/kb_http_api.py`，挂在 `main.py` 同一 FastAPI 实例下，路由前缀 `/api/kb`。

| 端点 | 方法 | 功能 |
|---|---|---|
| `/api/kb/query` | POST | 自然语言查询；body: `{"question": str, "channel": "api"}` |
| `/api/kb/facts/{fact_id}` | GET | 取单个 fact + 信源 |
| `/api/kb/facts` | GET | 列表查询 `?subject=&predicate=&active_only=true&limit=50` |
| `/api/kb/sources/{source_id}` | GET | 取单个信源 |
| `/api/kb/corrections` | POST | API 路径纠正（需 token + 在白名单）|
| `/api/kb/corrections` | GET | 审计查询 `?since=&corrector=&applied=true` |
| `/api/kb/conflicts` | GET | 列出待解决冲突 |
| `/api/kb/agg/runs` | GET | 聚合 run 列表 |
| `/api/kb/agg/run` | POST | 触发聚合（需 admin token）|

### 5.1 鉴权

- 飞书 webhook 路径用现有 `LARK_VERIFICATION_TOKEN` 签名校验（不变）
- HTTP API 路径用 `KB_API_TOKEN`（Bearer token）；写操作额外要求 `KB_ADMIN_TOKEN`
- CLI 直读环境变量，无网络鉴权

### 5.2 速率限制

- 查询：每 IP 60 req/min（防爬）
- 纠正：每 corrector 10 req/min（防误触）
- 聚合：全局并发 1（队列化，因 LLM 抽取串行）

## 6. 与现有脚本的接口契约

### 6.1 `correction_writer.py` → KB

`correction_writer.upsert_correction(...)` 在写入 Bitable 话题表后**额外**调用：

```python
kb_correction_writer.audit_external(
    correction_id=...,
    target_subject=title,
    target_predicate="status",
    new_object=summary,
    entry_channel="lark_card_reply",  # PF-001 场景
    corrector_open_id=ctx.sender_open_id,
)
```

这样 PF-001 / 手动脚本两条历史路径也都能在 KB 看到。

### 6.2 `lark_qa_handler.py` → KB

旧 QA 路径在以下情况**回退到 KB**：

- LLM 回答置信度低（自我评估 < 0.6）
- 查询匹配到 KB 已有 fact（先查 KB，命中则直接走 KB Query Engine 输出）

新增辅助函数 `kb_query_engine.try_answer_first(question) -> KBAnswer | None`：

```python
def handle_qa(event):
    text = ...
    # 优先 KB
    kb_attempt = kb_query_engine.try_answer_first(text)
    if kb_attempt and not kb_attempt.fallback:
        return _reply(event, kb_attempt.rendered_text)
    # 兜底：现有 QA 流程
    return _legacy_qa(event)
```

### 6.3 `daily_progress_updater.py` → KB

每次跑完 daily updater 后，给 KB Aggregator 一个 hint：

```python
# scripts/daily_progress_updater.py 末尾
from kb_aggregator import notify_external_update
notify_external_update(
    source_type="bitable_row",
    affected_records=updated_record_ids,
    reason="daily_progress_updater",
)
```

KB Aggregator 收到 hint 后，下一次 hourly run 优先扫描这些 record，缩短认知更新延迟。

## 7. 错误码

KB 各组件统一错误码命名空间 `KB_*`：

| 错误码 | 含义 | 处理建议 |
|---|---|---|
| `KB_E_AUTH` | 用户不在白名单 | 飞书回复"无权限" |
| `KB_E_PARSE` | NL Parser 失败 | 飞书回复"解析失败，请用结构化格式" |
| `KB_E_AMBIGUOUS` | 解析不确定 | 飞书反问 |
| `KB_E_NO_FACT` | 查询无命中 | 返回 fallback 答案 |
| `KB_E_BITABLE` | Bitable API 错误 | 重试 1 次 → 失败则告警 |
| `KB_E_LLM` | LLM API 错误 | 降级到关键词检索 |
| `KB_E_SCHEMA` | KB 表 schema 不符 | 阻断启动，提示运行 `kb schema verify` |

## 8. 部署变量清单（`.env.example` 追加段）

```bash
# ========== Module 4: Knowledge Base ==========
# 4 张表的 ID（运行 `python scripts/kb_cli.py schema init` 后填入）
BITABLE_TABLE_KB_FACTS=
BITABLE_TABLE_KB_SOURCES=
BITABLE_TABLE_KB_CORRECTIONS=
BITABLE_TABLE_KB_CONFLICTS=

# 白名单：可触发 KB 纠正/纠正撤销 的 open_id（逗号分隔）
KB_AUTHORIZED_USERS=

# NL Parser 阈值
KB_PARSER_AUTO_APPLY_THRESHOLD=0.8
KB_PARSER_ASK_CLARIFY_THRESHOLD=0.6

# 聚合
KB_AGGREGATE_CRON=30 8 * * *      # daily 默认 08:30
KB_AGG_CONCURRENCY=5              # LLM 抽取并发
KB_VECTOR_INDEX_PATH=data/kb_vector.faiss
KB_AGG_STATE_PATH=state/kb_agg_runs.jsonl

# HTTP API
KB_API_TOKEN=
KB_ADMIN_TOKEN=
KB_API_RATE_LIMIT_PER_MIN=60

# 模型
KB_PARSER_MODEL=qwen-plus
KB_EXTRACT_MODEL=qwen-plus
KB_EMBED_MODEL=bge-small-zh       # 通过通义千问 embedding 接口或本地模型
```

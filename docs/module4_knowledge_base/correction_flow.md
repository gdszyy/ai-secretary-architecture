# 实时纠正交互流程 (Real-time Correction Flow)

本文档对应 R1 需求：**PM 在飞书群里 @ 机器人，自然语言说一句"这个不对，实际是…"，30 秒内 KB 就被改正且留下审计**。

## 1. 入口路由

`main.py` 的 `/lark/webhook` 路由优先级（高 → 低）：

```
1. is_at_bot(msg) and is_kb_correction(text) → kb_correction_handler
2. is_at_bot(msg) and is_kb_query(text)      → kb_query_handler
3. is_at_bot(msg) (其它)                       → lark_qa_handler  (现有 QA 入口)
4. is_correction_command(text)                → lark_correction_handler  (现有「纠正：xxx」格式入口)
5. (前端群组消息)                              → frontend_defect_reporter
6. (其它群组消息)                              → thread_separator
```

> **决策**：KB 纠正路径**优先**于现有 QA 路径，但**不替换**现有 `「纠正：xxx」` 命令路径。两条纠正入口共享 `kb_corrections` 审计表。

## 2. 纠正语义判别 (`is_kb_correction`)

判别函数返回 `True` 时进入 KB 纠正分支。判别条件（OR 关系）：

| 触发模式 | 例子 |
|---|---|
| 否定 + 修正连接词 | "支付系统**不是**已完成**而是**还在测试" |
| 显式修正动词 | "**改成**李四 / **更新为** xxx / **应该是** xxx / **实际**是 xxx" |
| 否定 + 新事实 | "iOS 还有 bug，**不**像周报说的已修" |
| 直陈句包含已知 subject | （兜底）句子里出现已知 `subject` + 跟现有 fact 矛盾的 object（需 LLM 判别）|

实现：

```python
def is_kb_correction(text: str) -> bool:
    # 第一道：关键词正则（成本 0，覆盖 80% 场景）
    if KB_CORRECTION_REGEX.search(text):
        return True
    # 第二道：与已知 subject 比对（去掉机器人 @ 前缀后）
    cleaned = strip_at_mention(text)
    if not contains_known_subject(cleaned):
        return False
    # 第三道：LLM 判别（仅在前两道不确定时调用）
    return llm_is_correction_intent(cleaned)
```

`KB_CORRECTION_REGEX` 维护在 `scripts/kb_nl_correction_parser.py`：

```python
KB_CORRECTION_REGEX = re.compile(
    r"(不是|不对|错了|不准|改成|改为|应该是|实际是|实际上是|更新为|更正为|纠正一下|订正)"
)
```

## 3. 自然语言解析 (`kb_nl_correction_parser`)

### 3.1 输入

去掉 `@机器人` 后的纯文本 + 上下文：

```python
@dataclass
class CorrectionContext:
    text: str
    sender_open_id: str
    sender_name: str
    chat_id: str
    message_id: str
    timestamp: datetime
    # 用于消歧：拉最近 5 条同 chat 消息作为对话上下文
    recent_messages: list[str] = field(default_factory=list)
```

### 3.2 LLM Prompt 骨架

```text
你是项目知识库的纠正解析器。用户在飞书群里说了下面这句话，
试图纠正项目认知。请抽取结构化指令。

【用户原话】
{text}

【最近 5 条对话上下文（用于消歧）】
{recent_messages}

【已知 subject 列表（前 50 个）】
{known_subjects_csv}

请输出 JSON：
{
  "action": "update" | "create" | "delete" | "ambiguous",
  "subject": "...",                  // 必填，必须是已知 subject 之一，否则进入 ambiguous
  "subject_type": "module|feature|topic|person|risk",
  "predicate": "status|progress|decision|owner|risk|milestone|dependency",
  "old_object_hint": "...",          // 用户暗示的旧值（用于做对齐）
  "new_object": "...",               // 纠正后的事实，限 200 字
  "confidence": 0.0~1.0,             // 你对这次解析的信心
  "ambiguity": null | "..."          // ambiguous 时填写：你需要 PM 澄清什么
}

强约束：
1. 如果 subject 在已知列表中模糊匹配多个 → action=ambiguous
2. 如果原话只是询问而非陈述 → action=ambiguous，ambiguity="可能是查询而非纠正"
3. new_object 不准包含原话之外的信息（不要脑补背景）
```

### 3.3 解析后的决策

| `action` | `confidence` | 处理 |
|---|---|---|
| `update` | ≥ 0.8 | 直接进入 §4 写入流程 |
| `update` | 0.6~0.8 | 写入 + 飞书回复 "已纠正，但解析置信度仅 X，请确认" |
| `update` | < 0.6 | **不写**，反问 PM 二选一 |
| `create` | ≥ 0.7 | 当作 NEW 落库（confidence=0.9，因为是 PM 主动陈述）|
| `delete` | 任意 | 不允许直接 delete，改为新建 fact `predicate=status, object=已撤销 + 原因` |
| `ambiguous` | 任意 | 反问澄清，不写 |

### 3.4 反问模板

```
@PM 我没听明白这次纠正，能再确认一下吗？
原话："{text}"

我猜你想说的是：
A. {candidate_a_subject} 的 {candidate_a_predicate} 改为 "{candidate_a_new_object}"
B. {candidate_b_subject} 的 {candidate_b_predicate} 改为 "{candidate_b_new_object}"
C. 都不是，让我重说

回复 A / B / C 即可。
```

## 4. 写入流程

### 4.1 主流程伪代码

```python
def handle_kb_correction(ctx: CorrectionContext) -> CorrectionResult:
    # Step 1: 权限校验
    if ctx.sender_open_id not in KB_AUTHORIZED_USERS:
        return _send_reply(ctx, "您当前没有 KB 纠正权限，已忽略。")

    # Step 2: NL 解析
    parsed = kb_nl_correction_parser.parse(ctx)

    # Step 3: 落审计流水（无论是否成功，先写日志）
    correction_id = audit.create({
        "corrector_open_id": ctx.sender_open_id,
        "corrector_name": ctx.sender_name,
        "entry_channel": "lark_at_bot",
        "raw_message": ctx.text,
        "parsed_intent": parsed.dict(),
        "parser_confidence": parsed.confidence,
        "applied": False,
    })

    # Step 4: 处理 ambiguous
    if parsed.action == "ambiguous" or parsed.confidence < 0.6:
        _ask_for_clarification(ctx, parsed)
        return CorrectionResult(applied=False, reason="ambiguous")

    # Step 5: 找到现有 fact
    target_fact = kb_facts.find_active(parsed.subject, parsed.predicate)

    # Step 6: 创建新 fact
    new_fact_id = kb_facts.create({
        "subject": parsed.subject,
        "predicate": parsed.predicate,
        "object": parsed.new_object,
        "confidence": 0.95,                    # 人工纠正高置信度
        "source_refs": [_create_human_correction_source(ctx, correction_id)],
        "valid_from": ctx.timestamp,
        "corrected_by": ctx.sender_open_id,
    })

    # Step 7: 旧 fact 标记 superseded_by
    if target_fact:
        kb_facts.update(target_fact.id, {"superseded_by": new_fact_id})

    # Step 8: 回填审计
    audit.update(correction_id, {
        "target_fact_id": target_fact.id if target_fact else None,
        "created_fact_id": new_fact_id,
        "applied": True,
    })

    # Step 9: 飞书确认回复
    _send_confirmation(ctx, target_fact, new_fact_id, parsed)

    return CorrectionResult(applied=True, fact_id=new_fact_id)
```

### 4.2 确认回复模板

```
✅ 已纠正

【主语】支付系统
【字段】status

【原值】
"iOS 微信支付路由已修复" (信源 Bitable, 2026-05-06)

【新值】
"iOS 还有问题，预计延期到下周三" (来源：您的纠正, 2026-05-07 10:23)

新事实 ID: kb-fact-20260507-0099
审计 ID: kb-corr-20260507-0007

如需撤销，回复"撤销 kb-corr-20260507-0007"。
```

### 4.3 撤销机制

PM 回复 `撤销 kb-corr-XXXXX` 时：

1. 找到 correction，取出 `created_fact_id`（A）和 `target_fact_id`（B）
2. 创建 fact C：内容回到 B 的 `object`，confidence=0.9，source 标注"撤销 corr-XXX 后回退到 B"
3. A.superseded_by = C
4. 审计追加新行（`raw_message="撤销 kb-corr-XXX"`，原审计行不动）

> 撤销也是**追加**，不是删除。链：B → A → C，每一跳都有信源。

## 5. 创建型纠正（CREATE）

PM 也能用纠正语法**新增**事实：

```
@AI秘书 补充：用户中心模块的负责人是李四
@AI秘书 风险记录：Sportradar 接口下周二要做兼容性升级
```

NL Parser 解析为 `action=create`，跳过"找旧 fact"步骤，直接写新 fact，`confidence=0.9`，`source_refs` 仅含 `human_correction`。

## 6. 边界情况

| 场景 | 处理 |
|---|---|
| PM 一条消息纠正多个 fact | NL Parser 返回数组，串行处理；批量回复一条总结 |
| 同一 fact 短时间内多次纠正 | 链式 supersede（A → B → C → D）；每跳留审计 |
| LLM 解析失败（API 错误）| 不写库，飞书回复"解析服务暂时不可用，请稍后重试或用 `纠正：[标题] xxx` 格式" |
| 非白名单用户 @ 机器人说"xxx 不是 xxx" | 不进 KB 纠正分支，按现有 QA 路径处理（仅查询）|
| 撤销别人的纠正 | 同样要白名单；撤销动作也写 audit |

## 7. 与 Lark 卡片回复纠正（PF-001）的协作

PF-001（`docs/module2_buffer/lark_card_reply_correction_spec.md`）是**结构化指令**入口（`纠正：[话题] xxx`），KB 纠正是**自然语言**入口。两者：

| 维度 | PF-001 | KB 纠正 |
|---|---|---|
| 入口 | 回复周报卡片 | @机器人 |
| 语法 | 结构化（`纠正：xxx`）| 自然语言 |
| 写入位置 | Bitable 话题表 | KB facts 三表 |
| 审计 | 暂未明确 | `kb_corrections` 强制审计 |

**整合方案**：PF-001 落地后，其写入逻辑也调用 `kb_correction_writer.upsert_with_audit`，把对话题表的覆盖**同时**记录到 `kb_corrections`。这样无论从哪个入口纠正，KB 都能看到完整历史。

## 8. 配置项（`.env`）

```bash
# 白名单：可触发 KB 纠正的飞书 open_id（逗号分隔）
KB_AUTHORIZED_USERS=ou_xxxxxx,ou_yyyyyy

# NL Parser 置信度阈值
KB_PARSER_AUTO_APPLY_THRESHOLD=0.8
KB_PARSER_ASK_CLARIFY_THRESHOLD=0.6

# LLM 模型
KB_PARSER_MODEL=qwen-plus

# Bitable KB 表 ID（由 kb_schema_init.py 创建后填入）
BITABLE_TABLE_KB_FACTS=tblXXXXX
BITABLE_TABLE_KB_SOURCES=tblXXXXX
BITABLE_TABLE_KB_CORRECTIONS=tblXXXXX
BITABLE_TABLE_KB_CONFLICTS=tblXXXXX
```

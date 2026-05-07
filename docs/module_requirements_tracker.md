# 模块：需求记录跟踪 (requirements_tracker)

## 1. 背景

PM/项目经理在飞书里把零散的「我想做 XX」直接告诉 AI 秘书时，希望机器人能：

1. **接收对话**：每次单独 @ 它（私聊或群里 @），都能稳定接住消息。
2. **登记需求**：把这条「我想做的事」写进多维表格的需求池。
3. **核对完善程度**：当字段缺失时，机器人主动追问，直到完善度达到入库阈值。
4. **每天定时跟进**：所有未确认 / 不完善的需求，机器人会私聊主动续问。
5. **群里 @ 时读上下文**：用户在群里 @ 它，机器人会拉一段最近的群历史，从中
   读出用户真正想登记的需求，并跟该用户确认后再写入表格。

## 2. 模块组成

| 文件 | 职责 |
| --- | --- |
| `scripts/lark_sdk_client.py` | 基于官方 `lark-oapi` 的 Lark Client 单例；封装发送文本/卡片、拉取群消息历史、获取机器人 open_id 等能力 |
| `scripts/requirement_tracker.py` | 需求记录核心逻辑：判定意图、调用 LLM 抽取字段、完善度评分、Bitable 读写、生成回复 |
| `scripts/requirement_followup.py` | 每日跟进任务：扫描未完成需求 → 私聊提出者 |
| `main.py` 中的 `route_requirement` 段 | Webhook 路由：决定何时进入需求记录流程 |
| `scripts/run_daily_batch.py` | 已加入对 `requirement_followup.py` 的调用（与原有 `daily_progress_updater` 并列） |

## 3. 触发逻辑

`main.py` 的 `handle_message_event` 在收到 `im.message.receive_v1` 后：

1. 判断消息是否 `is_at_bot`（私聊 or mentions 命中机器人）；
2. 如果**已有未确认草稿**（任意状态属于 `草稿/待澄清/待确认` 的、提出者是当前用户）
   → 进入需求记录流程（视为多轮澄清的延续）。
3. 否则按 chat_type 区分：
   - `p2p` 私聊 + 文本不像查询（`?` / `查询` / `请问` 开头）→ 进入需求登记。
   - `group` 群聊 + 显式 `记录需求 / 需求：/ /req` 等前缀 → 进入需求登记。
4. 进入需求登记后由 LLM 二次判定：若判定 `is_requirement = false` 且没有现存草稿，会
   `handled = false` 退回，让既有 QA 路由继续处理（保持向后兼容）。

## 4. 完善度模型

字段权重：

| 字段 | 权重 | 说明 |
| --- | ---: | --- |
| 标题 | 15 | ≤ 20 字短句 |
| 描述 | 25 | 详细的 What |
| 动机 | 10 | Why |
| 涉及模块 | 15 | 优先复用 `mod_*` 前缀 |
| 验收标准 | 20 | How（可观察的判定条件） |
| 优先级 | 5 | P0/P1/P2/P3 |
| 期望交付时间 | 10 | YYYY-MM-DD |

满分 100。当 ≥ `REQUIREMENT_COMPLETE_THRESHOLD`（默认 80）时，机器人会让你回复
「确认」入库；否则机器人会按权重从高到低挑前 3 项发问。

## 5. Bitable 表结构

需要在 `BITABLE_BASE_ID` 下手工新建一个表（建议命名「需求池」），并把表 ID 配到
`BITABLE_TABLE_REQUIREMENTS`。字段如下（与 `requirement_tracker.BITABLE_FIELDS_SCHEMA`
保持一致）：

| 字段 | 类型 | 备注 |
| --- | --- | --- |
| 需求ID | 单行文本 | `REQ-XXXXXXXX`，由模块生成 |
| 标题 | 单行文本 | |
| 描述 | 多行文本 | |
| 动机 | 多行文本 | |
| 涉及模块 | 单行文本 | 也可以改成单选 |
| 验收标准 | 多行文本 | |
| 优先级 | 单选 | `P0 / P1 / P2 / P3` |
| 期望交付时间 | 单行文本 | `YYYY-MM-DD` |
| 状态 | 单选 | `草稿 / 待澄清 / 待确认 / 已确认 / 已取消` |
| 完善度 | 数字 | 0-100 |
| 缺失字段 | 单行文本 | 逗号分隔 |
| 提出者open_id | 单行文本 | 用于追问私聊 |
| 提出者姓名 | 单行文本 | |
| 来源chat_id | 单行文本 | |
| 来源chat_type | 单行文本 | `p2p / group` |
| 原始消息ID | 单行文本 | |
| 群上下文消息IDs | 单行文本 | LLM 引用过的 message_id |
| 跟进次数 | 数字 | |
| 最后跟进时间 | 单行文本 | `YYYY-MM-DD HH:MM:SS` |
| 创建时间 | 单行文本 | |
| 最后更新时间 | 单行文本 | |
| 备注 | 多行文本 | |

> 单选字段需要预先在 Bitable 里把所有选项填上，否则 API 写入会失败。

## 6. 环境变量

```bash
# 必填
LARK_APP_ID=cli_xxx
LARK_APP_SECRET=xxx
LARK_DOMAIN_TYPE=lark           # 或 feishu
DASHSCOPE_API_KEY=sk-xxx
BITABLE_BASE_ID=xxx
BITABLE_TABLE_REQUIREMENTS=tblxxx

# 可选
QWEN_MODEL=qwen-plus
REQUIREMENT_GROUP_CONTEXT_SIZE=20
REQUIREMENT_COMPLETE_THRESHOLD=80
REQUIREMENT_FOLLOWUP_MIN_HOURS=20
REQUIREMENT_FOLLOWUP_MAX_PER_RUN=50
```

## 7. 使用示例

### 7.1 私聊登记

```
You ▶︎ @AI秘书  我想加一个 VIP 等级配置页，方便运营自助调整门槛
Bot ▶︎ 📝 我已暂存需求 [REQ-AB12CD34]（完善度 60/100）
       概要：新增 VIP 等级配置页，由运营自助调整门槛
       📋 当前已记录：…
       ❓ 还差几个关键信息：
         1. 期望什么时候上线？给个日期或大概时间窗。
         2. 如何判定这条需求做完了？给我一两条可观察的验收点。
         3. 你希望排到 P0 / P1 / P2 / P3 哪个优先级？
You ▶︎ 下个迭代上线、能改门槛积分和加成系数、P1
Bot ▶︎ 完善度提升至 95/100，回「确认」入库
You ▶︎ 确认
Bot ▶︎ ✅ 已入库需求 [REQ-AB12CD34]
```

### 7.2 群里 @ 读上下文

```
[群里讨论了 5 分钟充提合规话题]
You ▶︎ @AI秘书  把上面这个记录一下需求
Bot ▶︎  📝 我已暂存需求 [REQ-…]
        概要：在 mod_settlement 增加合规预警，触发后自动暂停提现
        当前已记录：…
        还差：验收标准 / 期望交付时间 …
```

### 7.3 每日跟进

```
# Manus / Railway Cron / GitHub Actions 每天跑一次
python scripts/requirement_followup.py
```

或者已经接入 `scripts/run_daily_batch.py`，它会作为一个步骤自动执行。

## 8. 与既有模块的关系

- **lark_qa_handler**：保持不变；当本模块判定「不是需求」且用户也没有草稿时，
  `main.py` 仍会把消息交给 QA。
- **lark_correction_handler / frontend_defect_reporter / thread_separator**：
  路由顺序在 QA 之后，仍按原逻辑工作。
- **lark_bitable_client**：复用既有的 HTTP 直连客户端做 Bitable 读写。
- **lark_sdk_client**：仅用于发送消息和读群历史，不取代 `lark_bitable_client`。

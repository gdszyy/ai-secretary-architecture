---
description: "AI 秘书系统已实现能力清单与 TODO 任务全景索引，作为所有 Agent 进入本仓库时的进度基准文档"
globs: ["main.py", "scripts/*.py", "docs/**/*.md"]
---

# 系统实现状态全景索引 (Implementation Status)

> **最后更新**：2026-04-16（P0 任务完成）
> **维护规则**：每次完成一个功能模块或关闭一个 TODO 后，必须在同一 Commit 中更新本文档。

---

## 1. 已实现能力清单 (Implemented Capabilities)

### 1.1 服务入口层

| 文件 | 状态 | 核心能力描述 |
| :--- | :---: | :--- |
| `main.py` | ✅ 已实现 | FastAPI Webhook 服务入口；接收飞书 `im.message.receive_v1` 事件；支持 URL Challenge 验证；**签名校验（TODO-P0-02 ✅ 已完成：HMAC-SHA256 真实比对）**；**Lark 消息回复（TODO-P0-01 ✅ 已完成：send_lark_message + token 缓存）**；异步后台任务处理（避免超时重试）；路由至 `frontend_defect_reporter` 或 `thread_separator` |
| `requirements.txt` | ✅ 已实现 | 完整 Python 依赖清单（fastapi / uvicorn / openai / requests / python-dotenv / python-dateutil） |
| `Procfile` | ✅ 已实现 | Railway 启动配置（`uvicorn main:app --host 0.0.0.0 --port $PORT`） |

### 1.2 信息缓冲池层（Module 2）

| 脚本 | 状态 | 核心能力描述 |
| :--- | :---: | :--- |
| `scripts/thread_separator.py` | ✅ 已实现 | **两阶段多对话分离算法**：第一阶段（时间窗口切分 + @提及图谱 + 实体聚类，启发式无 LLM 成本）；第二阶段（Qwen LLM 深度语义分离，含 Few-shot 示例）；输出标准 `ThreadEvent` JSON；置信度过滤（< 0.8 → `needs_review`）；无效意图过滤（`casual_chat` / `other`）；支持 `--demo` / `--dry-run` / `--input` / `--output` CLI |
| `scripts/frontend_defect_reporter.py` | ✅ 已实现 | **前端缺陷自动报送**：LLM 意图分析（判断是否为前端 Bug，置信度 ≥ 0.6）；完整度打分（0-100，阈值 70）；不足时生成追问话术；完整时构建 Meegle Defect Payload 并调用 Meegle API 创建工单；返回结构化结果（`action` / `inquiry_message` / `work_item_id` / `notify_message`）；支持 `--dry-run` |
| `scripts/meegle_client.py` | ✅ 已实现 | Meegle API 封装客户端：获取工作项类型、创建 Defect 工单、查询项目信息 |
| `scripts/lark_bitable_client.py` | ✅ 已实现 | 飞书 Bitable CRUD 客户端：`list_records` / `create_record` / `update_record` / `delete_record`；支持分页和过滤 |

### 1.3 看板数据层（Module 1）

| 脚本 | 状态 | 核心能力描述 |
| :--- | :---: | :--- |
| `scripts/parse_to_dashboard_json.py` | ✅ 已实现 | 从 Markdown 文档通过 LLM 提取结构化数据，生成初始 `dashboard_data.json` |
| `scripts/sync_bitable_docs.py` | ✅ 已实现 | 从飞书 Bitable 功能表同步文档链接到 `dashboard_data.json` |
| `scripts/inject_weekly_updates.py` | ✅ 已实现 | 将本周周报数据注入 `dashboard_data.json` 的 `weekly_updates` 字段 |
| `scripts/add_group_milestones.py` | ✅ 已实现 | 为大模块分组添加里程碑列表和进度计算 |
| `scripts/enrich_global_milestones.py` | ✅ 已实现 | 为整体里程碑添加各大模块状态快照（`group_snapshots`） |
| `data/dashboard_data.json` | ✅ 已实现 | 看板前端唯一数据源（通过 GitHub Raw URL 供前端读取） |

### 1.4 信息源采集层（Module 3 / 冷启动）

| 脚本 | 状态 | 核心能力描述 |
| :--- | :---: | :--- |
| `scripts/cold_start_step1_list_groups.py` | ✅ 已实现 | 列出飞书所有群组 |
| `scripts/cold_start_step2_fetch_messages.py` | ✅ 已实现 | 批量抓取群组历史消息 |
| `scripts/cold_start_step3_llm_profile.py` | ✅ 已实现 | LLM 对群组画像（提取主题、参与者、活跃度） |
| `scripts/cold_start_step4_write_bitable.py` | ✅ 已实现 | 将群组画像写入 Bitable |
| `scripts/extract_weekly_insights.py` | ✅ 已实现 | 从飞书群消息中提取本周关键洞察 |
| `scripts/generate_markdown_report.py` | ✅ 已实现 | 生成 Markdown 格式周报 |
| `scripts/media_pipeline.py` | ✅ 已实现 | 媒体消息解析流水线（图片 / 语音 / 文件） |

---

## 2. TODO 任务清单 (Pending Tasks)

### 2.1 P0 — 阻塞上线的关键缺失

| ID | 任务描述 | 所属模块 | 关联文件 | 预估工作量 |
| :--- | :--- | :--- | :--- | :--- |
| `TODO-P0-01` | ✅ **[已完成]** **Lark 消息回复集成**：已实现 `send_lark_message(chat_id, text)` 函数，调用飞书 `im.message.create` API 将追问话术和成功通知发回群里；实现 `get_lark_tenant_access_token()` 并缓存 token（有效期 2h，提前 5min 刷新） | Module 2 | `main.py` | 0.5d |
| `TODO-P0-02` | ✅ **[已完成]** **Lark Webhook 签名校验补全**：已从请求头提取 `X-Lark-Signature`，使用 HMAC-SHA256(timestamp + nonce + body, token) 计算签名并与请求头比对；未配置 `LARK_VERIFICATION_TOKEN` 时跳过校验（向后兼容） | 服务入口 | `main.py` | 0.5d |

### 2.2 P1 — 核心功能完善

| ID | 任务描述 | 所属模块 | 关联文件 | 预估工作量 |
| :--- | :--- | :--- | :--- | :--- |
| `TODO-P1-01` | **高价值线程推入缓冲池**：`thread_separator` 输出的 `high_value_threads` 当前只记录日志，需实现写入 Bitable（`BITABLE_TABLE_PENDING_THREADS`）或内存队列，供下游调度器消费 | Module 2 | `main.py` L142-152 | 1d |
| `TODO-P1-02` | **实体关键词库动态加载**：`thread_separator.py` 中 `PROJECT_ENTITY_KEYWORDS` 当前为硬编码列表，需从 `project_context.json` 或 Bitable 动态加载，支持跨项目复用 | Module 2 | `scripts/thread_separator.py` L57-72 | 0.5d |
| `TODO-P1-03` | **Thread Separation 评测报告**：基于真实脱敏群聊数据，对 `thread_separator.py` 进行准确率 / 召回率评测，输出 `docs/module2_buffer/thread_separation_eval_report.md` | Module 2 | 新建文档 | 1d |
| `TODO-P1-04` | **Lark 机器人 MVP**：在 `manus-lark-skills` 仓库开发 `lark-group-monitor` 技能，实现群聊消息实时监听与事件推送至本系统 Webhook | Module 3 | 跨仓库（`manus-lark-skills`） | 2d |
| `TODO-P1-05` | **看板数据结构升级**：在 `xpbet-frontend-components` 仓库的 `kanban_data.json` 中引入 `sourceRef` 和 `epicId` 字段，更新 React 组件渲染逻辑 | Module 1 | 跨仓库（`xpbet-frontend-components`） | 1d |

### 2.3 P2 — 体验优化与运维

| ID | 任务描述 | 所属模块 | 关联文件 | 预估工作量 |
| :--- | :--- | :--- | :--- | :--- |
| `TODO-P2-01` | **Railway 定时启停**：按 `docs/module2_buffer/railway-schedule.yml.template` 配置定时唤醒/休眠，降低空闲成本 | 运维 | `docs/module2_buffer/railway-schedule.yml.template` | 0.5d |
| `TODO-P2-02` | **防堆积定时任务**：实现 24h 降级 / 72h 强制归档 / >50 条批量合并策略（`buffer_anti_accumulation_sop.md` 中已设计） | Module 2 | `docs/module2_buffer/buffer_anti_accumulation_sop.md` | 1d |
| `TODO-P2-03` | **Dispatcher 引擎**：实现意图到工作项的完整映射逻辑（`Feature Request` → Lark Bitable；`Bug Report` → Meegle Defect；`Memo` → 定时提醒），目前仅实现了 Bug 报送 | Module 2 | `IMPLEMENTATION_PLAN.md` 阶段三 | 3d |
| `TODO-P2-04` | **Lark ↔ Meegle 双向同步**：监听 Lark 状态变更触发 Meegle 创建 Story；监听 Meegle Webhook 回传 Lark 状态 | Module 1 | `IMPLEMENTATION_PLAN.md` 阶段三 | 2d |
| `TODO-P2-05` | **`project_context.json` 配置文件**：创建统一的项目上下文配置（群组→项目映射、用户→Meegle User Key 映射、实体关键词库），供多个脚本共享 | 基础设施 | 新建 `config/project_context.json` | 0.5d |

---

## 3. 系统实现进度总览

```
整体进度：█████████░░░░░░░░░░░  ~45%

Module 1（看板）     ████████████░░░░░░░░  60%  数据层和脚本层已完整，双向同步待实现
Module 2（缓冲池）   ████████░░░░░░░░░░░░  40%  核心算法已实现，集成层（回复/推送）待完成
Module 3（信息源）   ████░░░░░░░░░░░░░░░░  20%  冷启动脚本已实现，实时监听（Lark Bot）待开发
服务入口层           ████████████████████  100%  Webhook 框架已就绪，签名校验和消息回复均已完成（P0 任务）
```

---

## 4. 下一步推荐行动序列

按照依赖关系和优先级，建议按以下顺序推进：

1. **`TODO-P0-01`** → 实现 `send_lark_message`，让系统能真正"说话"（追问 + 通知）
2. **`TODO-P0-02`** → 补全签名校验，确保生产安全
3. **`TODO-P1-01`** → 将 ThreadEvent 写入 Bitable，打通缓冲池数据链路
4. **`TODO-P2-05`** → 创建 `project_context.json`，解除 `TODO-P1-02` 的硬编码依赖
5. **`TODO-P1-04`** → 跨仓库开发 Lark Bot，实现真正的实时消息捕获
6. **`TODO-P2-03`** → 实现完整 Dispatcher 引擎，覆盖全意图类型

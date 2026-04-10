# Module3 信息来源前置数据完备性诊断评估报告

**作者**: Manus AI
**日期**: 2026-04-09
**关联文档**: [`info_source_master_plan.md`](./info_source_master_plan.md)

---

## 1. 评估背景与目标

Module3（信息来源层）作为 AI Management 项目秘书系统的数据入口，承担着接收多渠道信息的重任 [1]。根据《AI Management 项目看板信息源体系总纲》，目前大部分接入凭证和配置均未建立。本报告旨在诊断并评估 Module3 正常运行所需的前置数据完备性，涵盖接入凭证、路由配置、去重机制、降级策略及隐私合规五个维度，为后续实施提供可落地的基础设施方案。

---

## 2. 各数据源接入凭证清单及管理方案

为确保信息缓冲区的安全稳定运行，各外部数据源均需提供相应的接入凭证。

### 2.1 凭证需求清单

| 数据源 | 优先级 | 所需凭证/配置项 | 当前状态预估 | 后续操作建议 |
| :--- | :--- | :--- | :--- | :--- |
| **Meegle** | P0 | API Token、项目空间 ID、Webhook Secret | 待建立 | 在 Meegle 开发者后台生成长效 Token，配置工作项变更 Webhook。 |
| **Lark Bot** | P0 | App ID、App Secret、Event Verification Token | 待建立 | 需在飞书开放平台创建企业自建应用，申请"接收群聊消息"及"读取多维表格"等权限。 |
| **飞书妙记** | P1 | 妙记 API 读取权限 (Tenant Access Token) | 待验证可行性 | 需确认飞书开放平台是否提供直接读取会议转录文本的 API，若无，需考虑使用 RPA 或手动导出方案。 |
| **GitHub** | 参考级 | Personal Access Token (PAT) | 按需建立 | 仅作为 Meegle 状态的辅助核验依据，不驱动看板状态流转。如需接入，获取仓库只读 PAT 即可。 |

### 2.2 凭证管理方案

采用 **`.env` + Secret Manager** 的混合管理方案，确保本地开发便捷性与生产环境安全性。

本地开发与测试环境使用 `.env` 文件存储，通过 `.gitignore` 排除，防止硬编码泄露。生产环境则使用云厂商的 Secret Manager（如 AWS Secrets Manager 或 HashiCorp Vault）统一管理，应用启动时动态拉取注入内存。

**示例 `.env` 结构：**

```env
# Lark Configuration
LARK_APP_ID=cli_a1b2c3d4e5f6g7h8
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LARK_VERIFICATION_TOKEN=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

# Meegle Configuration
MEEGLE_API_TOKEN=mt_xxxxxxxxxxxxxxxxxxxx
MEEGLE_WEBHOOK_SECRET=wh_sec_xxxxxxxxxxxxxxxx
```

---

## 3. 消息路由规则前置配置 (routing_config.yaml)

路由配置用于决定哪些群组或项目的数据允许进入缓冲区，避免无关信息干扰。

### 3.1 数据结构设计

`routing_config.yaml` 采用声明式结构，按数据源分类管理白名单。

```yaml
version: "1.0"
description: "Module3 Information Routing Configuration"

sources:
  lark:
    enabled: true
    # 允许接收消息的群组 ID 白名单
    allowed_groups:
      - "oc_1a2b3c4d5e6f7g8h9i0j"  # 核心研发群
      - "oc_0987654321fedcba"      # 产品需求群
    # 允许触发 AI 秘书的用户角色/ID（可选）
    allowed_users:
      - "ou_1234567890"            # PM 账号

  meegle:
    enabled: true
    # 关联的 Meegle 项目空间 ID
    monitored_projects:
      - "PRJ-XP-BET"
      - "PRJ-AI-SEC"
```

---

## 4. 消息去重与幂等性基础设施

为防止外部数据源（如 Webhook 重试、群聊重复发送）导致的系统重复处理与数据污染，需建立基于消息 ID 的去重机制。

### 4.1 方案设计 (SQLite + message_id 索引)

采用轻量级 SQLite 数据库（生产环境可平滑迁移至 Redis 或 PostgreSQL）存储已处理消息的指纹。

唯一标识 (Message Fingerprint) 组合 `source_type` 和 `source_message_id`。例如：`lark:msg_12345`。

### 4.2 表结构设计

```sql
CREATE TABLE IF NOT EXISTS processed_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL, -- e.g., 'processed', 'ignored', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_message_fingerprint ON processed_messages(message_fingerprint);
CREATE INDEX idx_created_at ON processed_messages(created_at);
```

### 4.3 查询与拦截逻辑

在接收到外部消息后，网关层首先执行拦截查询：

1. 生成 `message_fingerprint`。
2. 执行 `SELECT status FROM processed_messages WHERE message_fingerprint = ?`。
3. 若存在且状态为 `processed`，则直接丢弃并返回 200 OK。
4. 若不存在，则插入记录并标记状态为 `processing`，进入后续流程。

### 4.4 过期清理机制

为控制数据库体积，设置定时任务（如每日凌晨）清理过期数据。通常保留 7-14 天即可满足去重需求。

```sql
-- 清理 14 天前的记录
DELETE FROM processed_messages WHERE created_at < datetime('now', '-14 days');
```

---

## 5. 数据源降级策略与健康检查

为保障系统在部分数据源故障时仍能提供核心服务，需建立降级与健康检查机制。

### 5.1 健康检查 (Health Check)

网关层提供 `/health` 接口，定期检查各数据源的连通性（如尝试调用 Lark API 获取 Token，Ping Meegle 接口）。核心指标包括 API 响应延迟、Webhook 接收成功率和 Token 有效期。

### 5.2 降级策略 (Degradation Policy)

| 场景 | 触发条件 | 降级策略 |
| :--- | :--- | :--- |
| **LLM 服务不可用** | API 连续 3 次超时或返回 5xx | 暂停 Lark 的非结构化消息处理，将消息暂存于 SQLite 死信队列；Meegle 等结构化 Webhook 继续通过规则引擎直接处理。 |
| **Lark API 阻断** | 触发频率限制 (Rate Limit) | 降低消息拉取频率；对于主动询问，改为每小时批量发送一次。 |
| **Meegle 故障** | Webhook 接收中断或 API 报错 | 暂停 Lark 状态回写 Meegle，Lark 看板进入"只读/手动"模式，待恢复后执行全量状态对齐。 |

---

## 6. 隐私合规评估清单

在处理来自群聊和会议记录的数据时，需严格遵守隐私保护与数据合规要求。

| 评估维度 | 检查项 | 状态 | 备注说明 |
| :--- | :--- | :--- | :--- |
| **用户授权** | Lark 机器人进群是否需要管理员审批？ | 需要处理 | 需在企业内部制定机器人进群审批 SOP。 |
| **数据保留** | 缓冲区的原始对话数据是否定期销毁？ | 已满足 | 依据设计，信息流转完成后不长期保留原始对话，仅在看板沉淀结构化数据。 |
| **脱敏处理** | 飞书妙记转录文本是否包含高管薪酬等敏感机密？ | 风险项 | 需限制机器人仅能读取指定白名单会议的妙记，禁止全局搜索。 |
| **第三方共享** | 调用外部 LLM（如 OpenAI/DeepSeek）时，是否签署了不用于模型训练的协议 (Zero Data Retention)？ | 需要处理 | 必须使用企业级 API，并在配置中明确禁用数据留存。 |

---

## 参考文献

[1] [AI Management 项目看板信息源体系总纲](./info_source_master_plan.md)

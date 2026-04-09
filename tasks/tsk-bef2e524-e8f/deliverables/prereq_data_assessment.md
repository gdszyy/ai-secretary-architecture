# Module2 信息缓冲池前置数据完备性诊断评估报告

**作者**: Manus AI
**角色**: Analyst
**日期**: 2026-04-09
**关联任务**: tsk-bef2e524-e8f
**关联文档**: [`info_buffer_design.md`](./info_buffer_design.md)

---

## 1. 评估背景与目标

在 AI Management 项目秘书系统中，**信息缓冲池（Information Buffer，即 Module2）**是核心枢纽，负责接收来自多渠道的非结构化信息，进行清洗、意图识别与分发。为了保证缓冲池中的大语言模型（LLM）能够准确识别意图并将其正确归因至业务模块，必须依赖一套高质量的前置数据体系作为上下文基座。

目前，这些前置数据在实际运行中存在缺失，导致 AI 意图识别准确率下降、模块归属错误以及下游派发失败。本报告旨在诊断 Module2 正常运行所需的前置数据完备性，重点围绕以下四个维度展开设计与评估：

1. **项目背景知识库**：设计 `project_context.json` 数据结构，为 LLM 提供系统模块、成员及业务术语的全局视图。
2. **意图分类规则库扩展**：评估并扩展现有意图类型，制定完整度评分标准。
3. **模块归因关键词映射表**：建立从非结构化文本到标准模块的映射规则。
4. **数据源接入就绪度矩阵**：评估核心数据源的接入状态与所需凭证。

---

## 2. 项目背景知识库数据结构设计 (`project_context.json`)

为了让 AI 秘书能够准确理解 XPBET 体育投注项目的业务上下文，需要将项目的基础信息结构化为 JSON 格式，并作为 System Prompt 的一部分动态注入。该结构必须包含模块列表、成员名单、业务术语表和常见缩写 [2]。

### 2.1 数据结构设计与示例

以下是基于 XPBET 项目（21 个模块、2 位核心负责人）的 `project_context.json` 完整示例数据：

```json
{
  "project_name": "XPBET 全球站",
  "project_id": "prj-xpbet-001",
  "description": "面向全球用户的综合性体育投注与娱乐平台",
  "current_stage": "开发与测试阶段",
  "modules": [
    {
      "module_id": "mod_recv7D8lYjnzJs",
      "module_name": "用户系统",
      "category": "T0基础框架",
      "owner": "Yark",
      "description": "包含登录注册、KYC、用户信息编辑、用户自我封禁等核心用户功能。",
      "priority": "P0-1月",
      "status": "开发中"
    },
    {
      "module_id": "mod_finance_001",
      "module_name": "财务系统",
      "category": "T0基础框架",
      "owner": "Yark",
      "description": "处理充值、提现、资金流水记录等财务相关业务。",
      "priority": "P0-1月",
      "status": "开发中"
    },
    {
      "module_id": "mod_sports_001",
      "module_name": "体育注单系统",
      "category": "T0基础框架",
      "owner": "VoidZ",
      "description": "赛事展示、赔率计算、注单生成与结算。",
      "priority": "P1-3月",
      "status": "开发中"
    },
    {
      "module_id": "mod_risk_001",
      "module_name": "风控系统",
      "category": "T0基础框架",
      "owner": "VoidZ",
      "description": "用户行为风险识别、异常账号封禁、限额管理。",
      "priority": "P2-6月",
      "status": "规划中"
    },
    {
      "module_id": "mod_campaign_001",
      "module_name": "活动系统",
      "category": "T1营销框架-运营",
      "owner": "VoidZ",
      "description": "签到、首充奖励、营销活动配置与发放。",
      "priority": "P1-3月",
      "status": "待规划"
    }
  ],
  "members": [
    {
      "user_id": "usr_yark_01",
      "name": "Yark",
      "en_name": "Yark",
      "email": "yark@xpbet.com",
      "role": "Product Manager / Backend Lead",
      "focus_modules": ["用户系统", "财务系统", "客服系统", "CRM系统", "礼券系统"],
      "meegle_user_key": "mgl_yark_001"
    },
    {
      "user_id": "usr_voidz_01",
      "name": "VoidZ",
      "en_name": "VoidZ",
      "email": "voidz@xpbet.com",
      "role": "Frontend Lead / Architect",
      "focus_modules": ["体育注单系统", "风控系统", "活动系统", "Casino管理", "C端包网"],
      "meegle_user_key": "mgl_voidz_001"
    }
  ],
  "business_glossary": {
    "KYC": "Know Your Customer，用户实名认证流程。",
    "C端包网": "面向普通用户的白标建站服务，允许商户快速搭建自有投注平台。",
    "注单": "用户在体育赛事中提交的投注记录，包含赛事、赔率、金额等信息。",
    "打码量": "用户需要完成的有效投注额度，通常作为领取奖励的前提条件。",
    "盘口": "体育赛事的投注选项，包含赔率和可投注金额限制。",
    "EPAY": "一种第三方支付路由渠道，用于处理跨境支付。",
    "SR验证": "System Requirement Verification，系统需求验证阶段，通常为上线前的最终测试。"
  },
  "abbreviations": {
    "PRD": "Product Requirements Document，产品需求文档",
    "PM": "Project Manager，项目经理",
    "OOM": "Out of Memory，内存溢出",
    "SSOT": "Single Source of Truth，单一事实来源",
    "KPI": "Key Performance Indicator，关键绩效指标",
    "CRM": "Customer Relationship Management，客户关系管理",
    "CI/CD": "Continuous Integration/Continuous Deployment，持续集成/持续部署"
  }
}
```

### 2.2 设计说明

该数据结构的设计遵循以下原则：

**模块列表 (`modules`)** 直接映射自 XPBET 飞书多维表格中的 21 个模块，包含唯一标识、名称、分类及负责人，便于 LLM 进行精确的模块归因。完整的 21 个模块涵盖 5 大分类：T0基础框架（8个）、T1营销框架-获客（4个）、T1营销框架-运营（5个）、T1营销框架-数据分析（1个）、T2商户管理（3个）[2]。

**成员名单 (`members`)** 记录核心成员及其关注领域。当碎片信息未明确指明模块，但提到了特定人员时，LLM 可借此推断可能的关联模块，实现间接归因。

**术语与缩写 (`business_glossary` / `abbreviations`)** 消解业务沟通中的黑话，提高意图识别的准确率，防止 LLM 将专业术语误解为通用词汇。

---

## 3. 意图分类规则库评估与扩展

当前系统定义了 5 种基础意图类型：备忘 (Memo)、缺陷报告 (Bug Report)、需求/特性 (Feature Request)、进度更新 (Progress Update)、会议纪要 (Meeting Notes) 以及未知 (Unknown) [1]。

### 3.1 业务覆盖度评估

在实际的 XPBET 项目运作中，这 5 种基础意图无法完全覆盖所有的业务场景。通过分析 Thread Separation 算法的评测场景（如 SQL 注入漏洞修复、版本发布状态确认等），以及 XPBET 体育投注业务的特殊性（风险管控、合规审查），识别出以下覆盖盲区：

- **生产环境紧急事故**（如支付网关宕机、OOM 故障）被错误归类为普通 Bug，无法触发最高级别的即时响应。
- **架构决策与方案拍板**（如选定第三方支付渠道、确定技术方案）被归类为"备忘"，导致无法自动沉淀到决策记录库。
- **状态查询请求**（如"v2.5 发布了吗？"）被归类为"未知"，AI 秘书无法主动触发查询动作。

### 3.2 新增意图类型建议

为了提升意图识别的精准度和下游处理的针对性，建议新增以下 3 种意图类型：

**风险升级 (Risk Escalation)**：适用于生产环境宕机、核心数据异常、严重安全漏洞（如 SQL 注入）等重大风险场景。此类意图需要触发最高级别的即时询问，并抄送项目干系人，区别于普通 Bug 的常规处理流程。

**决策记录 (Decision Record)**：适用于架构方案选型确定、重大需求变更批准、排期调整确认等场景。此类意图应自动归档至项目的决策记录库（如 Lark Wiki），并关联至相关的 Meegle 工作项，防止临时决策遗忘。

**状态查询 (Status Check)**：适用于 PM 询问某个版本、某个功能的当前进度（如"v2.5 发布状态如何？"）。此类意图应触发 AI 秘书主动查询 Meegle 或 GitHub，而非仅仅作为被动记录者。

### 3.3 完整度评分标准设计

针对所有 7 种意图类型，设计以下完整度评分标准（满分 100 分，**≥80 分视为 Ready**）：

| 意图类型 | 基础分 (40分) | 模块归属 (20分) | 关键实体 (40分) |
| :--- | :--- | :--- | :--- |
| **缺陷报告 (Bug Report)** | 包含明确的错误现象 | 明确归属模块 | 复现步骤 (15分), 优先级 (15分), 影响范围 (10分) |
| **需求/特性 (Feature Request)** | 包含明确的功能诉求 | 明确归属模块 | 业务价值/场景 (20分), 预期结果 (20分) |
| **进度更新 (Progress Update)** | 包含明确的进度状态 | 明确归属模块 | 关联任务/人员 (20分), 预计完成时间 (20分) |
| **备忘 (Memo)** | 包含待办事项描述 | 明确归属模块 | 明确的行动项 (20分), 截止时间 (20分) |
| **会议纪要 (Meeting Notes)** | 包含会议核心议题 | 明确归属模块 | 明确动作 (15分), 责任人 (15分), 时间点 (10分) |
| **风险升级 (Risk Escalation)** | 包含明确的风险描述 | 明确受影响模块 | 风险级别/影响评估 (20分), 建议应对措施/当前处理人 (20分) |
| **决策记录 (Decision Record)** | 包含明确的决策结论 | 明确归属模块 | 决策背景/原因 (20分), 决策人/批准人 (20分) |

---

## 4. 模块归因关键词映射表

为了提高 LLM 从非结构化文本中提取 `module_name` 的准确率，需要建立一份模块归因关键词映射表。该表将日常沟通中的口语化表达、缩写和英文名称映射到标准的模块名称 [2]。

| 标准模块名称 | 英文标识 | 同义词 / 口语化表达 | 常见相关术语 / 缩写 |
| :--- | :--- | :--- | :--- |
| **用户系统** | User System | 账号系统、登录注册、会员中心 | KYC、Referral、自我封禁、Profile、sign in、sign up |
| **财务系统** | Finance System | 支付网关、充提系统、资金模块 | 存款、提款、流水、对账、Deposit、Withdraw、EPAY |
| **体育注单系统** | Sports Betting | 投注引擎、赛事模块、盘口系统 | 赔率、结算、串关、单关、Odds、Settlement、注单 |
| **风控系统** | Risk Control | 安全系统、反欺诈模块 | 封号、限额、异常行为、风控规则、Risk |
| **活动系统** | Campaign System | 营销活动、任务中心、促销模块 | 签到、首充奖励、Banner、打码量要求、Campaign |
| **礼券系统** | Coupon System | 优惠券、红包、福利中心 | 优惠码、Coupon、Voucher、发券 |
| **客服系统** | CS System | 在线客服、帮助中心 | 聊天窗、工单、Ticket、FAQ、CS |
| **CRM系统** | CRM | 用户运营、客户关系管理 | 用户分层、标签、生命周期 |
| **代理系统** | Agent System | 推广系统、分销系统 | 佣金、下线、代理商、Agent |
| **数据分析** | Analytics | 数据报表、BI、统计 | Dashboard、报表、漏斗、留存率 |
| **商户管理** | Merchant | 后台管理、运营后台 | 商户、白标、B端、Admin |
| **Casino管理** | Casino | 娱乐城、电子游戏 | 老虎机、真人荷官、Slot、Live Casino |

*说明：此表应在 `project_context.json` 的基础上进一步丰富，并在实际运行中通过 LLM 的反馈回路不断迭代。*

---

## 5. 数据源接入就绪度矩阵

信息缓冲池的运转高度依赖外部数据源的输入。基于 Module3 的架构规划，以下是当前各核心数据源的接入就绪度评估。

| 数据源 | 定位与价值 | 所需凭证 / 前置配置 | 当前状态 | 预计接入阶段 |
| :--- | :--- | :--- | :--- | :--- |
| **Meegle** | 研发状态的唯一事实源 (SSOT) | API Token、项目空间 ID、Webhook Secret、`Lark ↔ Meegle` 用户映射表 | **凭证缺失**。需在开发者后台生成长效 Token 并配置工作项变更 Webhook。 | 第一阶段 (Quick Win, 1周) |
| **Lark Bot** | 核心沟通阵地，处理多对话混杂 | App ID/Secret、Verification Token、`im:message.group_msg` 敏感权限、目标群组 ID 白名单 | **待建立**。需申请企业自建应用及历史消息拉取权限，敏感权限审批周期较长。 | 第二阶段 (核心建设, 1-2周) |
| **GitHub** | 代码落地的物理证据 | GitHub App 私钥、Webhook Secret、目标仓库列表 | **待建立**。已在使用 GitHub，需配置项目仓库的 Webhook 监听 Issues/PRs/Actions 事件。 | 第二阶段 (核心建设, 1周) |
| **飞书妙记** | 决策层的核心会议记录来源 | Tenant Access Token、妙记 API 读取权限 | **待验证可行性**。需确认飞书开放平台是否开放相关 API，若无则需考虑 RPA 或手动导出方案。 | 第三阶段 (长期规划, 2-3周) |
| **Telegram Bot** | 移动端碎片化备忘快捷入口 | Bot Token (来自 BotFather)、允许交互的 Chat ID 白名单 | **待建立**。需向 BotFather 申请 Token，配置 Webhook URL 指向缓冲区网关。 | 第一阶段 (Quick Win, 1-2周) |

### 5.1 接入建议与风险提示

**权限申请前置**：Lark Bot 获取群组全量消息的权限 (`im:message.group_msg`) 属于敏感权限，审批流程较长，**必须优先启动申请**，否则多对话分离算法（Thread Separation）将无法落地。

**幂等性基础设施**：在全面接入数据源前，必须先完成 SQLite/Redis 的去重表（`processed_messages`）建设，防止 Webhook 重试导致的缓冲池数据污染。

**用户身份映射**：建立统一的 `Lark User ID ↔ Meegle user_key ↔ GitHub username` 三方映射表，是实现跨系统自动分配任务的关键前提。

---

## 6. 总结与后续行动

本报告完成了 Module2 信息缓冲池正常运行所需的四项前置数据设计，主要结论如下：

1. **立即执行**：将 `project_context.json` 模板和模块关键词映射表录入系统配置中心，并优先启动 Lark Bot 敏感权限申请。
2. **短期目标（1-2周）**：完成 Meegle Webhook 和 Telegram Bot 的接入（第一阶段），并推进 GitHub Webhook 配置。
3. **中期目标（2-4周）**：完成 Lark Bot 接入，启用多对话分离算法，并根据新增意图类型（Risk Escalation、Decision Record、Status Check）更新 LLM Prompt 和状态机逻辑。
4. **长期目标（5-8周）**：验证飞书妙记 API 可行性，完成会议纪要自动提取功能。

---

## 参考文献

[1] [`info_buffer_design.md`](./info_buffer_design.md) — AI项目秘书信息缓冲区机制设计方案
[2] [`xpbet_data_structure_design_v2.md`](../../archive/tasks_history/source_tasks/tsk-9103d528-937/deliverables/xpbet_data_structure_design_v2.md) — XPBET 全球站功能地图管理系统数据结构设计方案 (v2.0)
[3] [`info_source_master_plan.md`](../module3_info_sources/info_source_master_plan.md) — AI Management 项目看板信息源体系总纲
[4] [`thread_separation_algorithm.md`](./thread_separation_algorithm.md) — 多对话分离算法设计与评测报告
[5] [`meegle_integration_design.md`](../../archive/tasks_history/source_tasks/tsk-c67f7251-d40/deliverables/meegle_integration_design.md) — Lark↔Meegle 集成设计文档

---
**文档结束**

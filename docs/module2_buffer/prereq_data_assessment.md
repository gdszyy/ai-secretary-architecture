# Module2 信息缓冲池前置数据完备性诊断评估报告

**作者**: Manus AI
**日期**: 2026-04-09
**关联任务**: tsk-bef2e524-e8f

---

## 1. 概述

Module2（信息缓冲池）是 AI 项目秘书系统的核心处理层，负责接收、清洗、意图识别和分发来自多渠道的碎片化信息 [1]。其高效运行高度依赖于项目背景知识库、意图分类规则等前置数据。目前，这些前置数据在实际运行中存在缺失，导致 AI 意图识别准确率下降、模块归属错误以及下游派发失败。

本报告旨在诊断 Module2 正常运行所需的前置数据完备性，设计标准化的数据结构（`project_context.json`），扩展意图分类规则，建立模块归因关键词映射表，并输出数据源接入的就绪度矩阵，为后续系统升级提供数据基础。

---

## 2. 项目背景知识库数据结构设计 (`project_context.json`)

为了让 AI 秘书能够准确理解 XPBET 体育投注项目的业务上下文，我们需要将项目的基础信息结构化为 JSON 格式。该结构必须包含模块列表、成员名单、业务术语表和常见缩写 [2]。

### 2.1 数据结构设计与示例

以下是基于 XPBET 项目的 `project_context.json` 示例数据：

```json
{
  "project_name": "XPBET 全球站",
  "project_id": "prj-xpbet-001",
  "modules": [
    {
      "module_id": "mod_recv7D8lYjnzJs",
      "module_name": "用户系统",
      "category": "T0基础框架",
      "owner": "Yark",
      "description": "包含登录注册、KYC、用户信息编辑、用户自我封禁等核心用户功能。"
    },
    {
      "module_id": "mod_finance_001",
      "module_name": "财务系统",
      "category": "T0基础框架",
      "owner": "VoidZ",
      "description": "处理充值、提现、资金流水记录等财务相关业务。"
    }
  ],
  "members": [
    {
      "user_id": "usr_yark_01",
      "name": "Yark",
      "en_name": "Yark",
      "email": "yark@xpbet.com",
      "role": "Product Manager",
      "meegle_user_key": "mgl_yark_001"
    },
    {
      "user_id": "usr_voidz_01",
      "name": "VoidZ",
      "en_name": "VoidZ",
      "email": "voidz@xpbet.com",
      "role": "Backend Developer",
      "meegle_user_key": "mgl_voidz_001"
    }
  ],
  "business_glossary": {
    "KYC": "Know Your Customer，用户实名认证流程。",
    "EPAY": "一种第三方支付路由渠道。"
  },
  "abbreviations": {
    "PRD": "Product Requirements Document",
    "PM": "Project Manager"
  }
}
```

---

## 3. 意图分类规则库评估与扩展

当前系统定义了 5 种基础意图类型：备忘 (Memo)、缺陷报告 (Bug Report)、需求/特性 (Feature Request)、进度更新 (Progress Update)、会议纪要 (Meeting Notes) 以及未知 (Unknown) [1]。

### 3.1 业务覆盖度评估

在实际的 XPBET 项目运作中，这 5 种基础意图无法完全覆盖所有的业务场景。特别是在涉及项目风险管理和重大架构决策时，现有的分类会使得关键信息被错误地归类为“备忘”或“会议纪要”，从而无法触发适当的跟进流程。

### 3.2 新增意图类型建议

为了提升意图识别的精准度和下游处理的针对性，建议新增以下 2 种意图类型：

1. **风险升级 (Risk Escalation)**
   - **适用场景**：项目进度严重延期、核心资源流失、第三方依赖阻断等重大风险。
   - **处理逻辑**：触发最高级别的即时询问，并抄送项目干系人。
2. **决策记录 (Decision Record)**
   - **适用场景**：架构方案选型确定、重大需求变更批准、排期调整确认。
   - **处理逻辑**：自动归档至项目的决策记录库（如 Lark Wiki），并关联至相关的 Meegle 工作项。

### 3.3 完整度评分标准设计

针对所有 7 种意图类型，设计以下完整度评分标准（满分 100 分，80 分及格）：

| 意图类型 | 基础分 (40分) | 模块归属 (20分) | 关键实体 (40分) |
| :--- | :--- | :--- | :--- |
| **缺陷报告 (Bug Report)** | 包含明确的错误现象 | 明确归属模块 | 复现步骤 (15分), 优先级 (15分), 影响范围 (10分) |
| **需求/特性 (Feature Request)** | 包含明确的功能诉求 | 明确归属模块 | 业务价值 (20分), 预期结果 (20分) |
| **进度更新 (Progress Update)** | 包含明确的进度状态 | 明确归属模块 | 关联任务/人员 (20分), 预计完成时间 (20分) |
| **备忘 (Memo)** | 包含待办事项描述 | 明确归属模块 | 明确的行动项 (20分), 截止时间 (20分) |
| **会议纪要 (Meeting Notes)** | 包含会议核心议题 | 明确归属模块 | 明确动作 (15分), 责任人 (15分), 时间点 (10分) [3] |
| **风险升级 (Risk Escalation)** | 包含明确的风险描述 | 明确归属模块 | 影响评估 (20分), 建议应对措施 (20分) |
| **决策记录 (Decision Record)** | 包含明确的决策结论 | 明确归属模块 | 决策背景/原因 (20分), 批准人 (20分) |

---

## 4. 模块归因关键词映射表

为了提高 AI 从非结构化文本中提取 `module_name` 的准确率，需要建立一份模块归因关键词映射表。该表将日常沟通中的口语化表达、缩写和英文名称映射到标准的模块名称 [2]。

| 标准模块名称 | 关键词映射 (含同义词、缩写、英文) |
| :--- | :--- |
| 用户系统 | 用户, 登录, 注册, KYC, 封禁, User System, login, register, sign in, sign up |
| 财务系统 | 财务, 充值, 提现, 资金, 流水, Finance, deposit, withdraw, EPAY |
| 营销框架-获客 | 获客, 营销, 邀请, 裂变, referral, marketing |
| 营销框架-运营 | 运营, 活动, 任务, 奖励, operations, campaign, reward |
| 商户管理 | 商户, 后台, 代理, 佣金, merchant, admin, agent, commission |

---

## 5. 数据源接入就绪度矩阵

基于前期调研，我们梳理了核心数据源的接入就绪度，明确了各数据源所需的凭证、当前状态以及预计接入时间 [4] [5]。

| 数据源 | 价值/成本比值 | 所需凭证/配置 | 当前状态 | 预计接入时间 |
| :--- | :--- | :--- | :--- | :--- |
| **Meegle 工作项** | 最高 | Meegle Webhook URL, Meegle API Key, 用户映射表 | 凭证缺失，需配置 Webhook，需建立 `Lark User ID` ↔ `Meegle user_key` 映射 | 1 周 |
| **Lark 群聊/机器人** | 高 | Lark App ID, App Secret, Event Subscription | 已具备基础机器人，需配置事件订阅并联调 AI 接口 | 1-2 周 |
| **GitHub Issues/PRs** | 高 | GitHub Webhook URL, GitHub Personal Access Token | 已在使用 GitHub，需配置项目仓库的 Webhook | 1 周 |
| **飞书妙记/会议记录** | 中 | Lark API 权限 (读取会议纪要) | 需申请 Lark API 相关权限 | 2-3 周 |
| **Telegram Bot** | 较高 | Telegram Bot Token | 需申请 Bot Token 并开发基础接收服务 | 1-2 周 |

---

## 6. 总结与后续行动

1. **数据初始化**：立即将 `project_context.json` 模板和模块关键词映射表录入到系统的配置中心或代码库中。
2. **系统升级**：根据新增的意图类型（Risk Escalation, Decision Record）和评分标准，更新 Module2 的 AI 提示词和状态机逻辑。
3. **集成推进**：优先推进 Meegle 和 GitHub Webhook 的接入，获取所需的凭证，并建立 Lark 与 Meegle 之间的用户映射表。

---

## 参考文献

[1] [info_buffer_design.md](./info_buffer_design.md) - AI项目秘书信息缓冲区机制设计方案
[2] [xpbet_data_structure_design_v2.md](../../archive/tasks_history/source_tasks/tsk-9103d528-937/deliverables/xpbet_data_structure_design_v2.md) - XPBET 全球站功能地图管理系统数据结构设计方案
[3] [info_source_master_plan.md](../module3_info_sources/info_source_master_plan.md) - AI Management 项目看板信息源体系总纲
[4] [info_source_research.md](../../archive/tasks_history/source_tasks/tsk-2beb54e9-462/deliverables/info_source_research.md) - 信息源调研报告
[5] [meegle_integration_design.md](../../archive/tasks_history/source_tasks/tsk-c67f7251-d40/deliverables/meegle_integration_design.md) - Lark↔Meegle 集成设计文档

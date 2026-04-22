# ai-secretary-architecture

**ai-secretary-architecture** 是 AI 项目秘书系统的核心架构设计文档库，同时也是当前多 Agent 协作项目的文档库。该仓库承载系统级设计、模块 SOP、项目级上下文与拆分后的历史归档，目标是为后续的系统规划、架构评审、流程升级与交接提供高信噪比的知识基座。

> **⚠️ Agent 必读声明**
> 本仓库为 AI 秘书系统的**核心架构与流程知识源**。Agent 在执行系统规划、架构设计或读取项目级上下文时，**应优先读取此仓库**。
> `archive/tasks_history/` 为历史归档区，默认不属于 Agent 必读上下文，仅在需要追溯历史方案、核对来源或恢复旧交付物时再进入读取。

## 仓库结构与文档索引

### 1. 系统级核心设计 (根目录)
| 文档 | 路径 | 说明 |
| --- | --- | --- |
| **核心哲学** | [`CORE_PHILOSOPHY.md`](./CORE_PHILOSOPHY.md) | AI 秘书的愿景、角色定位与核心价值观 |
| **实施方案** | [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) | 顶层实施路线图与四阶段落地计划 |
| **Skill 架构** | [`SKILL_FEASIBILITY_REPORT.md`](./SKILL_FEASIBILITY_REPORT.md) | 将 AI 秘书打包为 Manus Skill 的架构设计 |
| **全局 SOP** | [`SOP.md`](./SOP.md) | 项目经理与 AI 秘书交互的标准指令 |

### 2. 模块架构设计 (docs/)
| 模块 | 目录/文件 | 说明 |
| --- | --- | --- |
| **模块一：看板系统** | [`docs/module1_kanban/`](./docs/module1_kanban/) | 包含看板模块设计、流程图、Meegle 集成方案与模块 SOP |
| **模块二：缓冲池** | [`docs/module2_buffer/`](./docs/module2_buffer/) | 包含 Buffer 模块设计、反积压机制与信息生命周期说明 |
| **模块三：信息源** | [`docs/module3_info_sources/`](./docs/module3_info_sources/) | 包含信息源治理与主计划文档 |
| **体系结构评估** | [`docs/architecture/`](./docs/architecture/) | 体系结构相关辅助文档，如仓库拆分评估报告 |

### 3. 项目级上下文 (docs/)
| 文档 | 路径 | 说明 |
| --- | --- | --- |
| **项目总览** | [`docs/project-overview.md`](./docs/project-overview.md) | 项目全局概览 |
| **启动报告** | [`docs/project-kickoff.md`](./docs/project-kickoff.md) | 项目启动文档 |
| **交接文档** | [`docs/handover.md`](./docs/handover.md) | Agent 间的项目交接说明 |
| **派发任务** | [`docs/dispatched_tasks.md`](./docs/dispatched_tasks.md) | 派发任务记录 |
| **Lark 文档规范** | [`docs/lark-doc-creation-spec.md`](./docs/lark-doc-creation-spec.md) | 飞书云文档创建规范 |
| **技能索引** | [`docs/skill_index.md`](./docs/skill_index.md) | Agent 核心技能索引与使用指南 |

### 4. 多 Agent 协作与归档
| 目录 | 用途 |
| --- | --- |
| `tasks/` | 多 Agent 协作文档库的任务成果沉淀。 |
| `context/` | 多 Agent 协作文档库的上下文快照。 |
| `archive/tasks_history/` | 原仓库的历史任务归档与旧交付物快照。 |

## 仓库体系说明与访问场景

本仓库来自对原 `project-management-ai-secretary` 仓库的拆分重构。为了降低 AI Agent 读取上下文时的噪音污染，整个项目现已拆分为三个独立仓库。

**作为 AI Agent，请根据你当前被分配的任务类型，选择读取对应的仓库：**

| 仓库名称 | 职责边界与内容 | Agent 访问场景 |
| --- | --- | --- |
| **[ai-secretary-architecture](https://github.com/gdszyy/ai-secretary-architecture)**<br>*(本仓库)* | **核心架构文档库**<br>包含系统级设计、模块 SOP、数据结构设计与项目全局上下文。纯 Markdown，信噪比 ~100%。 | **首选仓库**。当执行「系统规划」、「架构评审」、「SOP 制定」、「流程升级」或「了解项目背景」等高阶任务时，必须读取此仓库。 |
| **[xpbet-frontend-components](https://github.com/gdszyy/xpbet-frontend-components)** | **前端工程与组件库**<br>包含所有 UI 原型、设计规范、React/TS 代码库与数据可视化组件。 | 当执行「UI 开发」、「前端组件重构」、「页面还原」或「交互效果调整」等前端工程任务时，请读取此仓库。 |
| **[manus-lark-skills](https://github.com/gdszyy/manus-lark-skills)** | **通用 Agent 技能库**<br>存放可跨项目复用的 Manus 技能定义与 Python 脚本（如 `lark-codesandbox`、`lark-md-import`），与业务逻辑完全解耦。 | 当执行「技能开发」、「Lark API 集成」或需要「引用现有通用技能」时，请读取此仓库。 |

> **提示**: 原 `project-management-ai-secretary` 仓库现已降级为**历史归档库**，主要用于存放体积庞大的废弃测试数据（如海量 JSON）和过时的中间交付物。除非需要追溯极早期的原始数据，否则 Agent **无需读取**原仓库。
| `mod_activity` | [自动化活动管理系统需求文档](docs/mod_activity/PRD_Unknown.md) | 构建一个高度可配置的活动管理平台，提升活动上线效率和运营管理能力 |
| `mod_casino` | [优化清单](docs/mod_casino/PRD_mod_casino_Optimization_List.md) | 提升游戏大厅及游戏相关功能的用户体验和管理效率 |
| `mod_casino` | [产品设计文档 (PRD)](docs/mod_casino/PRD_Casino_BetBasket_Enhancement.md) | 提升投注篮的视觉吸引力和操作效率，优化PC端和移动端的交互体验。 |
| `mod_casino` | [钱包有效流水系数](docs/mod_casino/PRD_Wallet_Flow_Coefficient.md) | 解决多币别配置问题及风控用户的钱包冻结机制，保障充提投行为的合规与安全 |
| `mod_activity` | [代投配置与管理系统需求说明](docs/mod_activity/PRD_代投配置与管理系统.md) | 建立一套代投配置与管理系统，支持第三方代理推广并整合主流广告媒体的Pixel/Tracking工具，实现代投流程规范、广 |
| `mod_casino` | [游戏大厅入口与游戏管理系统设计文档](docs/mod_casino/PRD_Casino_Game_Lobby_Management.md) | 实现游戏大厅入口、游戏类型、游戏标签及游戏管理的后台配置与前台展示，提升游戏展示与管理效率。 |
| `mod_casino` | [投注记录及报表字段说明文档](docs/mod_casino/PRD_Casino_Betting_Records_and_Reports.md) | 提供统一的投注记录查询及报表展示字段定义，支持多角色权限查询和多语言翻译 |
| `mod_casino` | [游戏商户后台管理与钱包流程说明](docs/mod_casino/PRD_mod_casino_GameMerchant_Wallet.md) | 实现游戏商户的后台管理及游戏钱包的准确结算与校验 |
| `mod_settlement` | [手机号绑定国家与币别展示规范](docs/mod_settlement/PRD_PhoneBinding_CurrencyDisplay.md) | 根据手机号绑定的国家，展示对应的单一币别，确保注册及相关功能的币别一致性。 |
| `mod_activity` | [](docs/mod_activity/README.md) |  |
| `mod_customer_service` | [问与答（FAQ）管理功能需求说明](docs/mod_customer_service/PRD_FAQ_Management.md) | 提供后台统一管理FAQ内容并在前台多情境展示，提升客服效率和用户体验。 |
| `mod_settlement` | [第三方 KYC 验证流程整合](docs/mod_settlement/PRD_mod_settlement_KYC_Integration.md) | 优化平台身份验证流程，实现通过输入ID Number后自动跳转第三方KYC验证并动态展示验证结果。 |
| `mod_riskcontrol` | [KYC 三方身份验证配置与流程](docs/mod_riskcontrol/PRD_KYC_Configuration_and_Flow.md) | 为满足合规与风控要求，提供可配置的第三方 KYC 服务及前台动态展示，限制未完成验证用户的关键业务操作。 |
| `mod_settlement` | [Sportradar UOF结算与冲正消息处理规范](docs/mod_settlement/PRD_Sportradar_UOF_Settlement.md) | 实现平台对Sportradar统一赔率接口(UOF)结算及纠错消息的自动化准确处理，保障资金安全和用户账户准确性。 |
| `mod_settlement` | [支付调用统计与评分系统](docs/mod_settlement/PRD_Settlement_Payment_Stats_Scoring.md) | 通过统计支付商调用数据，计算综合评分以优化支付调用表现 |
| `mod_casino` | [后台 Sample](docs/mod_casino/PRD_mod_casino_Sample.md) | 提供钱包明细和注单记录的查询与展示功能 |
| `mod_settlement` | [钱包范围与流程说明](docs/mod_settlement/PRD_Wallet_Settlement.md) | 规范用户钱包及相关资金流动行为，支持多币别及活动流水限制管理 |
| `mod_activity` | [站内信系统需求说明](docs/mod_activity/PRD_mod_activity_station_message.md) | 通过站内信系统向用户推送多样化消息，提升信息接收效率与活动参与度。 |
| `mod_customer_service` | [客服系统整合与强化需求说明](docs/mod_customer_service/PRD_Customer_Service_Integration.md) | 整合线上即时文字客服与电话客服，提供多元便捷的沟通渠道，并通过用户等级配置实现VIP专属服务。 |
| `mod_customer_service` | [客服系统整合与强化需求说明](docs/mod_customer_service/PRD_Customer_Service_Integration.md) | 整合并强化平台内客服系统，提供多元便捷的沟通渠道，确保高价值用户获得专属快速协助。 |
| `mod_activity` | [详情页嵌入Statscore组件需求文档](docs/mod_activity/PRD_Unknown.md) | 通过嵌入Statscore组件，为用户提供一站式赛事分析体验，增加页面停留时间，辅助投注决策 |
| `mod_activity` | [用户推广奖励机制需求文档](docs/mod_activity/PRD_mod_activity.md) | 通过建立用户推广奖励机制，激励用户分享邀请链接，带动新用户注册及参与，实现低成本高效用户增长。 |
| `mod_activity` | [Bonus 流程需求说明](docs/mod_activity/PRD_Unknown.md) | 规范和说明不同类型Bonus的使用流程、展示及结算规则 |
| `mod_activity` | [有效流水说明参考文档](docs/mod_activity/PRD_Unknown.md) | 明确体育和娱乐场有效投注流水的计算规则，保障活动流水统计的准确性 |
| `mod_activity` | [快手：快手文档](docs/mod_activity/PRD_Unknown.md) | 依据用户渠道号进行精准事件埋点发送，实现多渠道数据归因和分析 |
| `mod_activity` | [网页底部导航及移动端适配修改点](docs/mod_activity/PRD_mod_activity.md) | 优化网页底部导航及移动端页面布局和跳转体验，提升用户访问便捷性和界面适配性 |
| `mod_settlement` | [新增功能及验收记录](docs/mod_settlement/PRD_Settlement_NewFeatures.md) | 完善订单查询、后台代付重送、钱包明细及代收商务配置，提升系统功能和用户体验 |
| `mod_activity` | [用户标签管理功能需求说明](docs/mod_activity/PRD_mod_activity_User_Tag_Management.md) | 通过标签化管理平台用户，实现动态控制用户权限和资源领取。 |
| `mod_activity` | [责任博彩机制需求说明](docs/mod_activity/PRD_Unknown.md) | 确保平台符合巴西当地法规，落实责任博彩机制，保障用户身心健康与财务安全。 |
| `mod_unknown` | [未知](docs/mod_unknown/PRD_未知.md) |  |
| `mod_settlement` | [有效流水说明参考文档](docs/mod_settlement/PRD_Effective_Turnover_Rules.md) | 明确各类投注的有效流水计算规则，保障活动流水统计的准确性 |
| `mod_riskcontrol` | [KYC 三方身份验证配置与流程](docs/mod_riskcontrol/PRD_KYC_ThirdParty_Verification.md) | 为满足合规与风控要求，提供可配置的第三方 KYC 服务及前台动态展示与校验能力，限制未完成 KYC 用户的关键业务操作。 |
| `mod_activity` | [站内信系统需求说明](docs/mod_activity/PRD_站内信系统需求说明.md) | 建立完整的站内信系统以提升用户信息接收效率与活动参与度 |
| `mod_activity` | [站内信系统需求说明](docs/mod_activity/PRD_mod_activity_station_message.md) | 通过站内信系统向用户推送多样化消息，提升信息接收效率与活动参与度。 |

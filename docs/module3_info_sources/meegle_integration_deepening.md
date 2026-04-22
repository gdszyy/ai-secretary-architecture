# Meegle 深度集成方案

**状态**：设计文档（待实现）  
**优先级**：P1  
**背景**：当前 Meegle 集成仅用于被动拉取 Story/Defect 数量统计，未能充分利用 Meegle 作为研发执行引擎的核心价值。

---

## 一、 现状问题分析

当前 `run_weekly_report.py` 中的 Meegle 集成存在以下不足：

1.  **归因依赖 LLM 猜测**：Story/Defect 没有与模块 ID 直接绑定，依赖 LLM 根据名称文本进行归因，准确率不稳定。
2.  **只读不写**：系统只从 Meegle 读取数据，无法将 Lark Bitable 中的决策/里程碑反向同步到 Meegle。
3.  **缺少 Meegle → 里程碑联动**：当 Meegle 中某个 Epic/Story 完成时，无法自动触发对应里程碑状态的更新建议。
4.  **模块映射已过期**：`run_weekly_report.py` 中的 `MODULE_NAMES` 字典仍使用旧的 12 个模块 ID，与重构后的 27 个模块不匹配。
5.  **缺乏 Meegle 迭代周期感知**：系统不感知 Meegle 中的 Sprint/迭代，无法基于迭代维度做进度诊断。

---

## 二、 深化集成目标

### 2.1 近期目标（P1）：修复模块映射，确保数据准确

**行动项**：更新 `run_weekly_report.py` 中的 `MODULE_NAMES` 字典，与重构后的 27 个模块对齐。

新的模块映射如下（需在代码中同步更新）：

```python
MODULE_NAMES = {
    # 引流获客
    "mod_ads_placement":    "投放平台（GA埋点/投手后台）",
    "mod_affiliate":        "代理后台（代理管理/支付等级/结算）",
    # 国别 & 站点
    "mod_tenant_country":   "租户 & 国别系统（IP限制/支付路由/短信三方）",
    "mod_site_config":      "站点活动配置（单站点上线/语言/金额）",
    # 用户 & 实名
    "mod_auth":             "注册 & 登录（手机号注册/PIN码/个人设置）",
    "mod_kyc":              "实名认证 KYC（身份证/CURP/税号/活体认证）",
    # CMS
    "mod_cms":              "CMS 内容管理（比赛管理/热门算法/首页推荐/Super Odds）",
    # 体育博彩
    "mod_data_feed":        "体育数据源（Sportradar UOF / LSports Trade）",
    "mod_sr_matching":      "SR→TS 匹配引擎（匹配率≥95%）",
    "mod_ls_matching":      "LS→TS 匹配引擎（Defend 风控对接）",
    "mod_odds_display":     "盘口展示（赛前/滚球/冠军盘/前端UI）",
    "mod_betting":          "投注下单（单关/串关/Cash Out/限额查询）",
    "mod_risk_control":     "风控系统（MTS/Defend/套利防控/水位平衡）",
    "mod_settlement":       "结算模块（实时结算/回滚/Void Factor/串关）",
    # Casino
    "mod_casino":           "Casino 游戏（三方厂商/无缝钱包/Bonus注入）",
    # 留存激励
    "mod_activity_config":  "活动配置平台（入口/准入/时间/预算池）",
    "mod_coupon":           "礼券系统（5种礼券/降落伞机制/流水计算）",
    "mod_vip":              "VIP 系统（100等级/升级奖励/每周每月权益）",
    "mod_pass":             "通行证（付费/免费/每日任务/经验积分）",
    "mod_daily_activity":   "日常活动（抽奖/流水榜/0:0退赔/串关加赔）",
    # 财务 & 钱包
    "mod_wallet":           "钱包系统（主钱包/Bonus钱包/先入先出）",
    "mod_payment":          "充值 & 提现（Epay/支付路由）",
    "mod_finance_ops":      "财务审核（代付/提款/重送/全民代理结算）",
    # 平台支撑
    "mod_user_tag":         "用户标签系统（活动准入/风控/限额/投放）",
    "mod_personal_center":  "个人中心（信息管理/钱包/实名/负责任博彩）",
    "mod_im_cs":            "站内信 & 客服（TG客服/VIP电话/CRM Smartico）",
    "mod_data_platform":    "数据平台（Metabase/埋点/财务指标/注单报表）",
}
```

### 2.2 中期目标（P2）：Meegle 标签与模块直接绑定

**问题**：当前 Story/Defect 归因依赖 LLM 文本匹配，不稳定。

**方案**：在 Meegle 中为每个工作项的 `tags` 字段增加模块标签（如 `mod_betting`、`mod_settlement`），使 `meegle_client.py` 中的 `list_work_items_by_week` 能够精准过滤，无需 LLM 归因。

**操作步骤**：
1.  在 Meegle 项目中创建与 27 个模块对应的标签（Tags）。
2.  研发人员在创建/更新 Story 和 Defect 时，必须选择对应的模块标签。
3.  更新 `meegle_client.py` 的 `list_work_items_by_week` 方法，支持按 `module_id` 精准过滤（而非模糊文本匹配）。

### 2.3 中期目标（P2）：Meegle Epic → 里程碑状态联动

**方案**：在 Meegle 中创建与项目里程碑对应的 Epic，当 Epic 下所有 Story 完成时，自动向 AI 秘书发送里程碑完成建议，由项目经理确认后更新 `dashboard_data.json`。

**实现路径**：
1.  在 `meegle_client.py` 中增加 `get_epic_progress(project_key, epic_id)` 方法。
2.  在 `run_weekly_batch.py` 中增加 Epic 进度扫描步骤，生成里程碑状态建议报告。
3.  将建议报告通过飞书卡片发送给项目经理，由其手动确认并更新里程碑状态。

### 2.4 远期目标（P3）：Lark Bitable → Meegle 双向同步

**方案**：当 Lark Bitable 中的话题（`major_decision`、`milestone_fact`）被确认后，自动在 Meegle 中创建对应的 Story 或 Epic，并将 Meegle ID 回写 Bitable，实现 SSOT（Single Source of Truth）。

**当前 SSOT 规则**（需在 `global.md` 中强化）：
- **进入开发前**：Lark Bitable 为主（话题/决策管理）。
- **进入开发后**（存在 Meegle Story/Epic ID）：Meegle 为主（研发执行追踪）。
- **禁止**在两侧同时手动修改状态。

---

## 三、 立即可执行的改进项

以下改进项不依赖新的 API 权限，可立即实施：

| 改进项 | 文件 | 工作量 |
|---|---|---|
| 更新 `MODULE_NAMES` 字典（27个模块） | `scripts/run_weekly_report.py` | 0.5h |
| 更新 `daily_progress_updater.py` 中的模块映射 | `scripts/daily_progress_updater.py` | 0.5h |
| 在 `meegle_client.py` 中增加 `get_epic_progress` 方法 | `scripts/meegle_client.py` | 2h |
| 在 `run_weekly_batch.py` 中增加 Epic 进度扫描 | `scripts/run_weekly_batch.py` | 3h |

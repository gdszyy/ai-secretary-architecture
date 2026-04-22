# mod_settlement — PRD 文档索引
> 自动生成于 2026-04-22，共 7 份 PRD 文档

| 文件 | 行数 | 功能点数 | Feature 列表 |
|---|---|---|---|
| [有效流水说明参考文档](docs/mod_settlement/PRD_Effective_Turnover_Rules.md) | 40 | 3 | FP-SETTLEMENT-001, FP-SETTLEMENT-002, FP-SETTLEMENT-003 |
| [手机号绑定国家与币别展示规范](docs/mod_settlement/PRD_PhoneBinding_CurrencyDisplay.md) | 102 | 11 | FP-SETTLEMENT-001, FP-SETTLEMENT-002, FP-SETTLEMENT-003, FP-SETTLEMENT-004, FP-S |
| [新增功能及验收记录](docs/mod_settlement/PRD_Settlement_NewFeatures.md) | 56 | 6 | FP-SETTLEMENT-001, FP-SETTLEMENT-002, FP-SETTLEMENT-003, FP-SETTLEMENT-004, FP-S |
| [支付调用统计与评分系统](docs/mod_settlement/PRD_Settlement_Payment_Stats_Scoring.md) | 32 | 2 | FP-SETTLEMENT-001, FP-SETTLEMENT-002 |
| [Sportradar UOF结算与冲正消息处理规范](docs/mod_settlement/PRD_Sportradar_UOF_Settlement.md) | 71 | 6 | FP-SETTLEMENT-001, FP-SETTLEMENT-002, FP-SETTLEMENT-003, FP-SETTLEMENT-004, FP-S |
| [钱包范围与流程说明](docs/mod_settlement/PRD_Wallet_Settlement.md) | 34 | 2 | FP-SETTLEMENT-001, FP-SETTLEMENT-002 |
| [第三方 KYC 验证流程整合](docs/mod_settlement/PRD_mod_settlement_KYC_Integration.md) | 40 | 3 | FP-SETTLEMENT-001, FP-SETTLEMENT-002, FP-SETTLEMENT-003 |

## 有效流水说明参考文档
> docs/mod_settlement/PRD_Effective_Turnover_Rules.md

**业务目标**：明确各类投注的有效流水计算规则，保障活动流水统计的准确性

**Feature 章节**：

- L0013 `1. Sport 有效投注规则 (FP-SETTLEMENT-001)`  `FP-SETTLEMENT-001`
- L0023 `2. Casino 有效投注规则 (FP-SETTLEMENT-002)`  `FP-SETTLEMENT-002`
- L0033 `3. 不计入流水的投注或玩法 (FP-SETTLEMENT-003)`  `FP-SETTLEMENT-003`

## 手机号绑定国家与币别展示规范
> docs/mod_settlement/PRD_PhoneBinding_CurrencyDisplay.md

**业务目标**：根据手机号绑定的国家，展示对应的单一币别，确保注册及相关功能的币别一致性。

**Feature 章节**：

- L0013 `1. 登入 (FP-SETTLEMENT-001)`  `FP-SETTLEMENT-001`
- L0022 `2. KYC (FP-SETTLEMENT-002)`  `FP-SETTLEMENT-002`
- L0032 `3. 充/提 (FP-SETTLEMENT-003)`  `FP-SETTLEMENT-003`
- L0041 `4. 首页钱包 (FP-SETTLEMENT-004)`  `FP-SETTLEMENT-004`
- L0048 `5. 钱包详情 (FP-SETTLEMENT-005)`  `FP-SETTLEMENT-005`
- L0055 `6. 责任博彩 (FP-SETTLEMENT-006)`  `FP-SETTLEMENT-006`
- L0062 `7. 投注 (FP-SETTLEMENT-007)`  `FP-SETTLEMENT-007`
- L0071 `8. 语系选择 (FP-SETTLEMENT-008)`  `FP-SETTLEMENT-008`
- L0079 `9. 币别符号 (FP-SETTLEMENT-009)`  `FP-SETTLEMENT-009`
- L0087 `10. 充提功能调整 (FP-SETTLEMENT-010)`  `FP-SETTLEMENT-010`
- L0096 `11. 帐户信息 (FP-SETTLEMENT-011)`  `FP-SETTLEMENT-011`

## 新增功能及验收记录
> docs/mod_settlement/PRD_Settlement_NewFeatures.md

**业务目标**：完善订单查询、后台代付重送、钱包明细及代收商务配置，提升系统功能和用户体验

**Feature 章节**：

- L0013 `1. 订单查询(Transaction Order) (FP-SETTLEMENT-001)`  `FP-SETTLEMENT-001`
- L0017 `2. 后台代付重送机制 (FP-SETTLEMENT-002)`  `FP-SETTLEMENT-002`
- L0024 `3. 配置平台充提最高与最低 (FP-SETTLEMENT-003)`  `FP-SETTLEMENT-003`
- L0031 `4. 后台用户明细/钱包明细 (FP-SETTLEMENT-004)`  `FP-SETTLEMENT-004`
- L0040 `5. 注单详情内的多个 Bonus 钱包投注及返奖金额展示 (FP-SETTLEMENT-005)`  `FP-SETTLEMENT-005`
- L0047 `6. 代收商务配置调整 (FP-SETTLEMENT-006)`  `FP-SETTLEMENT-006`

## 支付调用统计与评分系统
> docs/mod_settlement/PRD_Settlement_Payment_Stats_Scoring.md

**业务目标**：通过统计支付商调用数据，计算综合评分以优化支付调用表现

**Feature 章节**：

- L0013 `1. 支付调用统计 (FP-SETTLEMENT-001)`  `FP-SETTLEMENT-001`
- L0025 `2. 支付商综合评分计算 (FP-SETTLEMENT-002)`  `FP-SETTLEMENT-002`

## Sportradar UOF结算与冲正消息处理规范
> docs/mod_settlement/PRD_Sportradar_UOF_Settlement.md

**业务目标**：实现平台对Sportradar统一赔率接口(UOF)结算及纠错消息的自动化准确处理，保障资金安全和用户账户准确性。

**Feature 章节**：

- L0013 `1. bet_settlement (投注结算) (FP-SETTLEMENT-001)`  `FP-SETTLEMENT-001`
- L0023 `2. rollback_bet_settlement (回滚投注结算) (FP-SETTLEMENT-002)`  `FP-SETTLEMENT-002`
- L0033 `3. bet_cancel (投注取消) (FP-SETTLEMENT-003)`  `FP-SETTLEMENT-003`
- L0043 `4. rollback_bet_cancel (回滚投注取消) (FP-SETTLEMENT-004)`  `FP-SETTLEMENT-004`
- L0051 `5. 冲正操作 (FP-SETTLEMENT-005)`  `FP-SETTLEMENT-005`
- L0061 `6. 累积投注与系统投注特殊结算 (FP-SETTLEMENT-006)`  `FP-SETTLEMENT-006`

## 钱包范围与流程说明
> docs/mod_settlement/PRD_Wallet_Settlement.md

**业务目标**：规范用户钱包及相关资金流动行为，支持多币别及活动流水限制管理

**Feature 章节**：

- L0013 `1. 资金流动行为管理 (FP-SETTLEMENT-001)`  `FP-SETTLEMENT-001`
- L0025 `2. 钱包数据表设计 (FP-SETTLEMENT-002)`  `FP-SETTLEMENT-002`

## 第三方 KYC 验证流程整合
> docs/mod_settlement/PRD_mod_settlement_KYC_Integration.md

**业务目标**：优化平台身份验证流程，实现通过输入ID Number后自动跳转第三方KYC验证并动态展示验证结果。

**Feature 章节**：

- L0013 `1. ID Number 验证标准化 (FP-SETTLEMENT-001)`  `FP-SETTLEMENT-001`
- L0022 `2. 第三方KYC验证流程 (FP-SETTLEMENT-002)`  `FP-SETTLEMENT-002`
- L0031 `3. 验证状态行为管理 (FP-SETTLEMENT-003)`  `FP-SETTLEMENT-003`

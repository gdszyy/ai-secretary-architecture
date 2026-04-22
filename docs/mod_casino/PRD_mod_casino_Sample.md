# 后台 Sample

> **文档类型**: PRD  
> **来源**: https://kjpp4yydjn38.jp.larksuite.com/docx/QeRWduKOXo5d9nxBJkOjpBMxpAf  
> **归属模块**: `mod_casino`  

## 业务目标

提供钱包明细和注单记录的查询与展示功能

## 功能详情

### 1. Wallet (FP-CASINO-001)

**功能描述**: 钱包明细展示与查询

**业务规则**:
- 区分「钱包展示」与「用户账变」展示
- 钱包展示功能查询列表上展示「主钱包、子钱包」的总额
- 钱包总额的查询条件，下拉可选「币别」
- 用户账变记录由近到远，预设为一周
- 查询区间下拉可选今日、昨日、本周、本月、2个月
- 查询条件下拉可选「币别」
- 展示栏位包括 Currency 币别、Currency Type 币种、Amount 钱包内总额、Freeze 钱包内总冻结额度、WithdrawLimit 划转的有效流水总限制、Remaining Amount 完成的有效流水总额度

### 2. Transcation (更名为 Bet History) (FP-CASINO-002)

**功能描述**: 注单记录查询与展示

**业务规则**:
- 查询条件包括「Order ID」、「eventId」、「betType」、「status」、「投注时间(createdAt)」
- betType 下拉选项为 ['1-单关 2-串关']
- status 下拉选项为 ['0-未派彩', '1-已派彩(赢)', '2-已派彩(输)', '3-已派彩(无结果)']
- 投注时间(createdAt)为时间选择，支持投注时间区间查询
- 查询无资料时，在表格处展示「No Data」

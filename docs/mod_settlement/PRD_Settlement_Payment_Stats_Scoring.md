# 支付调用统计与评分系统

> **文档类型**: PRD  
> **来源**: https://kjpp4yydjn38.jp.larksuite.com/docx/P1xddmGQsolaJwx5GsEj9rPRpDh  
> **归属模块**: `mod_settlement`  

## 业务目标

通过统计支付商调用数据，计算综合评分以优化支付调用表现

## 功能详情

### 1. 支付调用统计 (FP-SETTLEMENT-001)

**功能描述**: 系统定时统计各支付商的调用情况，包括调用总数、成功次数、失败次数、平均响应时间、使用率和失败率

**业务规则**:
- 调用总数（Total Calls）
- 成功次数（Success Count）
- 失败次数（Fail Count）
- 平均响应时间（Latency）
- 使用率（Usage Rate = 调用次数 ÷ 总调用数）
- 失败率（Fail Rate = 失败次数 ÷ 调用次数）

### 2. 支付商综合评分计算 (FP-SETTLEMENT-002)

**功能描述**: 根据成功率、平均响应时间和使用率计算支付商的综合评分

**业务规则**:
- 综合评分 = (成功率×0.7) + (平均回应时间(秒)×0.2) + (使用率×0.1)
- Score = (Success Rate × 0.7) + (Response Speed × 0.2) + (Usage Stability × 0.1)

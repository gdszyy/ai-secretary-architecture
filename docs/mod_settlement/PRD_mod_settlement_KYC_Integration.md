# 第三方 KYC 验证流程整合

> **文档类型**: PRD  
> **来源**: https://kjpp4yydjn38.jp.larksuite.com/docx/CEVTdBQEFoom7fxhVP7j7u47pwh  
> **归属模块**: `mod_settlement`  

## 业务目标

优化平台身份验证流程，实现通过输入ID Number后自动跳转第三方KYC验证并动态展示验证结果。

## 功能详情

### 1. ID Number 验证标准化 (FP-SETTLEMENT-001)

**功能描述**: 实现对巴西CPF、墨西哥INE/IFE及护照号码的格式及校验规则验证。

**业务规则**:
- 巴西CPF校验码算法，排除全相同数字，计算两个校验位并验证
- 墨西哥INE/IFE CURP格式校验：^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$
- 墨西哥护照格式校验：^[A-Z0-9]{9}$

### 2. 第三方KYC验证流程 (FP-SETTLEMENT-002)

**功能描述**: 用户输入ID Number后点击Start KYC，系统跳转至第三方KYC验证页面，完成后返回平台并展示验证结果。

**业务规则**:
- 输入ID Number后点击Start KYC，自动跳转第三方验证页面
- 第三方完成验证并回传结果后，平台动态展示对应验证状态信息及后续操作提示
- 根据验证状态（通过、待审核、失败、未满18岁）展示不同提示和限制

### 3. 验证状态行为管理 (FP-SETTLEMENT-003)

**功能描述**: 根据KYC验证状态控制用户权限及提示信息。

**业务规则**:
- Approved状态开放投注、充值、提款，提示身份验证通过
- Pending Review状态限制部分功能，提示人工审核中
- Fail状态提示重新提交KYC，限制操作
- Under 18状态冻结账号，禁止使用平台

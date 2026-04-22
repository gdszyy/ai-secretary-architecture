# KYC 三方身份验证配置与流程

> **文档类型**: PRD  
> **来源**: https://kjpp4yydjn38.jp.larksuite.com/docx/HCDOdfxZdoYVckxJ4mdjfN06pmg  
> **归属模块**: `mod_riskcontrol`  

## 业务目标

为满足合规与风控要求，提供可配置的第三方 KYC 服务及前台动态展示与校验能力，限制未完成 KYC 用户的关键业务操作。

## 功能详情

### 1. KYC 商户配置管理 (FP-RISKCONTROL-001)

**功能描述**: 后台管理不同国家/地区的第三方 KYC 服务配置。

**业务规则**:
- 支持按国家和 KYC 名称查询和排序
- 必填栏位包括 Id、KYC Name、Country、API URL、API Key、Secret Key、ConfigId、Status、Description、Update Date
- Webhook Key 和 Update By 为非必填项

### 2. KYC 商户信息创建 (FP-RISKCONTROL-002)

**功能描述**: 后台创建新的 KYC 商户配置信息。

**业务规则**:
- 点击 Create 按钮进入创建流程
- 必填栏位未填写时，提交时显示红色错误提示
- 创建成功后返回列表并展示新增配置

### 3. KYC 商户信息修改 (FP-RISKCONTROL-003)

**功能描述**: 后台编辑已存在的 KYC 商户配置信息。

**业务规则**:
- 点击 Edit 按钮进入编辑模式
- 所有栏位均可修改
- 必填栏位未填写时，提交时显示红色错误提示

### 4. KYC 商户信息删除 (FP-RISKCONTROL-004)

**功能描述**: 后台删除指定的 KYC 商户配置信息。

**业务规则**:
- 点击 Del 按钮触发删除确认框
- 确认后删除该笔资料

### 5. 前台 KYC 流程展示与校验 (FP-RISKCONTROL-005)

**功能描述**: 前台根据后台配置动态展示 KYC 流程并限制未完成 KYC 用户的关键业务操作。

**业务规则**:
- 未完成 KYC 验证用户限制充值、提款、体育投注/线上游戏下注等操作
- 后台关闭三方 KYC 时，前台仅收集身份证号/证件号码并进行格式校验
- 完成 KYC 验证后方可进行关键业务操作

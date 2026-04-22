# 站内信系统需求说明

> **文档类型**: PRD  
> **来源**: https://kjpp4yydjn38.jp.larksuite.com/docx/RP8kdEVHEoxFPJxiXJ2j1Vabpbf  
> **归属模块**: `mod_activity`  

## 业务目标

建立完整的站内信系统以提升用户信息接收效率与活动参与度

## 功能详情

### 1. Messages (FP-ACTIVITY-001)

**功能描述**: 站内信展示

### 2. 红点 (FP-ACTIVITY-002)

**功能描述**: 未读取信息显示红点，点击 Show Detail 后变为已读

### 3. Show Detail (FP-ACTIVITY-003)

**功能描述**: 展示完整信息，点击后标记为已读

### 4. Claim (FP-ACTIVITY-004)

**功能描述**: 领取奖励按钮，点击后领取奖励

### 5. Recevied (FP-ACTIVITY-005)

**功能描述**: 已领取奖励状态展示

### 6. Fail(按钮置灰，字样换成 Fail) (FP-ACTIVITY-006)

**功能描述**: 超时未领取奖励，按钮置灰显示 Fail

**业务规则**:
- RewardsStatus == 0 && today > Vaild_To

### 7. All Read (FP-ACTIVITY-007)

**功能描述**: 全部标记为已读，但不领取奖励

### 8. All Claim (FP-ACTIVITY-008)

**功能描述**: 全部领取奖励，并读取所有信息

### 9. All Delete (FP-ACTIVITY-009)

**功能描述**: 全部删除已读无奖励及已读已领取奖励的信息

### 10. Announcements (FP-ACTIVITY-010)

**功能描述**: 推荐信息以 Banner 为主，点击图片进入全页介绍

### 11. 提示 iCon (FP-ACTIVITY-011)

**功能描述**: 未读信息时铃铛处显示红点或数字提示

**业务规则**:
- 不建议数字提示，避免未读信息过多导致界面跑版

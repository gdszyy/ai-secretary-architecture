# 飞书多维表格文档链接扫描审计报告

**任务 ID**: tsk-7aa357a0-a7e  
**扫描时间**: 2026-03-30 02:19 UTC  
**执行人**: developer Agent (agt-38c05020-50c)  
**多维表格**: BgjjbdZiJanHTpsboAzj9Gv7p6b / 功能表 tbluOwbl2PKxIiEz  
**文档链接字段**: fldWL5xcZV（文档链接）

---

## 一、扫描概要

| 指标 | 数量 |
|------|------|
| 总功能点记录数 | 114 |
| 已正确（飞书 Wiki 链接，无参数） | 6 |
| 需修复（非 Wiki 链接或空链接） | 108 |
| 可自动修复（映射表匹配成功） | 107 |
| 需人工处理 | 1 |

---

## 二、链接类型分布（修复前）

| 链接类型 | 数量 | 说明 |
|---------|------|------|
| `lark_wiki` | 6 | 正确的飞书 Wiki 链接（`/wiki/`） |
| `lark_docx` | 14 | 飞书 Docx 文档链接（`/docx/`，非 Wiki 格式） |
| `figma` | 1 | Figma 设计稿链接 |
| `empty` | 93 | 空链接（字段未填写） |

> **注意**: 修复前无 GitHub 链接（`github.com`），与任务背景描述不同。实际问题主要是大量空链接（93条）和部分 Docx 格式链接（14条）。

---

## 三、非 Wiki 链接详细清单

### 3.1 飞书 Docx 链接（14 条）

这些记录的文档链接指向 `/docx/` 格式，而非 `/wiki/` 格式，需替换为对应的 Wiki 地址。

| record_id | 功能名称 | 旧链接（Docx） |
|-----------|---------|--------------|
| recveY0tlunxpN | 登录注册流程 | https://kjpp4yydjn38.jp.larksuite.com/docx/WLdFdU0emoh1K8xiYy9j4iPTpre |
| recveY0tluJ8rT | KYC流程 | https://kjpp4yydjn38.jp.larksuite.com/docx/PgEgdGleco9TddxCgmcjPqUSpEg |
| recveY0tluxEYr | 用户自我封禁(Gambling Games) | https://kjpp4yydjn38.jp.larksuite.com/docx/EpzWdiGpVo6m8mxaM92j4L3gp7b |
| recveY0tluLcic | 用户打标签 | https://kjpp4yydjn38.jp.larksuite.com/docx/GsxNdQ8Noo0bssxN5vqjP8nipad |
| recveY0tlugtoG | 站内信 | https://kjpp4yydjn38.jp.larksuite.com/docx/RP8kdEVHEoxFPJxiXJ2j1Vabpbf |
| recveY0tlunbE6 | 主钱包划转 | https://kjpp4yydjn38.jp.larksuite.com/docx/AFsSdqWoVoZcZtxTCOdjcdyspSe |
| recveY0tluS6W4 | KYC前端兼容多国别配置 | https://kjpp4yydjn38.jp.larksuite.com/docx/HCDOdfxZdoYVckxJ4mdjfN06pmg |
| recveY0tluffzX | KYC 流程优化 V1.1 | https://kjpp4yydjn38.jp.larksuite.com/docx/CEVTdBQEFoom7fxhVP7j7u47pwh |
| recveY0tluRWtK | FAQ | https://kjpp4yydjn38.jp.larksuite.com/docx/OAx8dQZPKosnwkxDsZXjoax0p0f |
| recveY0tlukC4d | Bonus 钱包划转 | https://kjpp4yydjn38.jp.larksuite.com/docx/AFsSdqWoVoZcZtxTCOdjcdyspSe |
| recveY0tlutZWf | 币种钱包设置 | https://kjpp4yydjn38.jp.larksuite.com/docx/YfJ9dsMA2o9XUtx5qaGjbrIUpJg |
| recveY0tluCm3H | C端客服入口 | https://kjpp4yydjn38.jp.larksuite.com/docx/DiLydsC6koKwPQxPQJFjX41upNe |
| recveY0tlurvCF | VIP客服 | https://kjpp4yydjn38.jp.larksuite.com/docx/JrJddX9JSoshhoxPqfnjGhmgp3g |
| recveY0tluSHXe | 代理参数配置 | https://kjpp4yydjn38.jp.larksuite.com/docx/LiYRdVnrEoPNRJxhKSTjrzoVpUg |

### 3.2 Figma 链接（1 条）

| record_id | 功能名称 | 旧链接 |
|-----------|---------|--------|
| recveY0tluvTQ1 | 新版视觉（比赛卡片、详情页分组作为重点） | https://www.figma.com/design/bnINV7AJU1oB8MatpAkAIV/XPbot-web?node-id=0-1 |

### 3.3 空链接（93 条）

以下功能点的文档链接字段为空，已通过映射表补充 Wiki 地址：

| record_id | 功能名称 | 所属模块 |
|-----------|---------|---------|
| recveY0tlu0ibq | 订单清结算 | 体育注单系统 |
| recveY0tluNrgm | UOF数据呈现 | 体育注单系统 |
| recveY0tlu6lnT | MTS注单单关/串关 | 体育注单系统 |
| recveY0tluMoIi | 赛果回滚冲正 | 体育注单系统 |
| recveY0tluqyih | MTS高级投注 | 体育注单系统 |
| recveY0tluX6Y6 | 订单风险管理 | 风控系统 |
| recveY0tluV7n3 | 标签用户风控 | 风控系统 |
| recveY0tluuHwv | 标签规则集 | 风控系统 |
| recveY0tluUQWG | 赛事异常监控 | 风控系统 |
| recveY0tluOAYV | 活动参数配置 | 活动系统 |
| recveY0tluPnm3 | 活动模版 | 活动系统 |
| recveY0tlu3phL | CASHOUT | 体育注单系统 |
| recveY0tlubDpF | 返水机制 | 活动系统 |
| recveY0tluHIYB | Bonus创建 | 礼券系统 |
| recveY0tluEqqt | Freebet创建 | 礼券系统 |
| recveY0tlubSgp | 礼券发放 | 礼券系统 |
| recveY0tlu8eu3 | 礼券核销 | 礼券系统 |
| recveY0tluAfzv | 赔率抽水调整 | 体育注单系统 |
| recveY0tlumAix | 三方赔率对接 | 体育注单系统 |
| recveY0tluE1s1 | 投注栏迭代 | 体育注单系统 |
| recveY0tluv441 | FAQ管理 | 客服系统 |
| recveY0tluc0z5 | 系统分享 | 分享系统 |
| recveY0tlujtg4 | 三方分享 | 分享系统 |
| recveY0tluqM4I | 注册落地页 | 落地页系统 |
| recveY0tlujja6 | 绑定落地页 | 落地页系统 |
| recveY0tluPZTa | Superodds | 活动系统 |
| recveY0tlusgIp | 串关加赔 | 活动系统 |
| recveY0tluxYzm | 0-0退赔 | 活动系统 |
| recveY0tlucXzw | Bet Builder | 体育注单系统 |
| recveY0tluGOwW | 营销入口配置 | 活动系统 |
| recveY0tluDWCq | Freespin创建 | 礼券系统 |
| recveY0tlus0wq | 有效期管理 | 礼券系统 |
| recveY0tluXNtl | 余额查询 | 礼券系统 |
| recveY0tluXeMr | 使用记录 | 礼券系统 |
| recveY0tluRZ2E | 批次管理 | 礼券系统 |
| recveY0tlurkd9 | 用户标签宽表 | CRM系统 |
| recveY0tlulDgd | 触达-站内信 | CRM系统 |
| recveY0tlueM11 | 串关推荐卡片 | 首页推荐系统 |
| recveY0tlu1jPx | 中奖订单推荐 | 首页推荐系统 |
| recveY0tluJNpP | 卡片管理后台 | 首页推荐系统 |
| recveY0tluv04D | 公告管理 | 内容管理 |
| recveY0tlubNqH | Banner管理 | 内容管理 |
| recveY0tluzTMC | Head to Head数据对接 | 体育注单系统 |
| recveY0tluVtBM | Icon数据对接 | 体育注单系统 |
| recveY0tlu2MYa | 用户信息编辑 | 用户系统 |
| recveY0tluRfMs | 自创盘口 | 风控系统 |
| recveY0tluoEUJ | 角色管理 | 权限系统 |
| recveY0tlurMbf | 权限管理 | 权限系统 |
| recveY0tlui2n7 | 国别设置 | 国别管理系统 |
| recveY0tlu7PXB | 多语言 | 国别管理系统 |
| recveY0tlu0vcv | 流程设置 | 国别管理系统 |
| recveY0tluXwel | 功能开关 | 国别管理系统 |
| recveY0tluNYPP | Casino优先级 | Casino管理 |
| recveY0tluj4jK | Casino参数 | Casino管理 |
| recveY0tluEoMz | 图片分享 | 分享系统 |
| recveY0tlubMHp | 分享场景 | 分享系统 |
| recveY0tlu9jOx | 渠道数据查询 | 投手后台 |
| recveY0tluoi8Q | Pixel绑定 | 投手后台 |
| recveY0tluly3D | 归因平台对接 | 投手后台 |
| recveY0tluYONK | 活动周期 | 代理系统 |
| recveY0tluH6Hx | 分享渠道管理 | 代理系统 |
| recveY0tlubMvr | 分享物料管理 | 代理系统 |
| recveY0tluQply | Optimove对接 | CRM系统 |
| recveY0tluaXY3 | 其他CRM对接 | CRM系统 |
| recveY0tluj2ge | 用户圈选引擎 | CRM系统 |
| recveY0tluLKOJ | 营销活动创建 | CRM系统 |
| recveY0tlup0QI | AB测试 | CRM系统 |
| recveY0tlubx4m | 触达-SMS | CRM系统 |
| recveY0tluq0NM | 触达-邮件 | CRM系统 |
| recveY0tluX3WU | 触达-Push | CRM系统 |
| recveY0tluiaSY | 触达-RCS | CRM系统 |
| recveY0tluEgNH | 推荐算法 | 首页推荐系统 |
| recveY0tluoIk8 | 个性化推荐 | 首页推荐系统 |
| recveY0tluMs8B | 文章系统 | 内容管理 |
| recveY0tluEKaz | Metabase集成 | 数据分析 |
| recveY0tluNNml | GA集成 | 数据分析 |
| recveY0tlu1329 | Adjust/AF数据 | 数据分析 |
| recveY0tlu8nvJ | Pixel数据 | 数据分析 |
| recveY0tluN8MH | 标签算法 | 数据分析 |
| recveY0tEYQKCX | 业务报表 | 数据分析 |
| recveY0tEYu1jt | 多租户系统 | 商户管理 |
| recveY0tEYayBb | 租户参数配置 | 商户管理 |
| recveY0tEYmM2N | 租户信息 | 商户管理 |
| recveY0tEYzHZg | API接口 | 商户管理 |
| recveY0tEY2NCc | 包网方案 | C端包网 |
| recveY0tEYA7LM | 定制化 | C端包网 |
| recveY0tEYlxOy | 聊天室建立 | 聊天室系统 |
| recveY0tEYpLTy | 头像 / 昵称修改 | 聊天室系统 |
| recveY0tEYCCf3 | 分赛事群聊天 | 聊天室系统 |
| recveY0tEYVRuY | 推单 / 晒单 | 聊天室系统 |
| recveY0tEYKdIE | Transaction 优化V1.1 | 用户系统 |
| recveY0tEYOoac | 发版维护 | 风控系统 |

---

## 四、修复结果汇总

| 状态 | 数量 | 说明 |
|------|------|------|
| 已正确（无需修复） | 6 | 修复前已是标准 Wiki 格式 |
| 自动修复成功 | 107 | 通过功能名称匹配映射表，成功更新为 Wiki 链接 |
| 修复失败 | 0 | 无 |
| 待人工处理 | 1 | 功能名称为空，无法匹配 |

**修复后状态**: 113 条记录已更新为正确的飞书 Wiki 链接格式，1 条记录（功能名称为空）需人工处理。

---

## 五、技术说明

**修复方法**: 通过功能名称（`功能名称` 字段）在 tsk-92d7c861-577 任务生成的映射表（`feature_doc_mapping.csv`）中查找对应的 Wiki URL，然后通过飞书 Bitable API 更新记录。

**API 使用**: 飞书 Bitable Records Update API (`PUT /bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}`)，使用字段名称（`文档链接`）而非字段 ID 进行更新。

**数据来源**: 映射表来自 `gdszyy/project-management-ai-secretary` 仓库 `tasks/tsk-92d7c861-577/deliverables/feature_doc_mapping.csv`。

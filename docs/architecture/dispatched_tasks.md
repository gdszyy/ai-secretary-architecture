# 子任务派发记录

**派发时间**：2026-03-29
**派发人**：项目负责人 Agent（当前任）
**派发方式**：Manus API 直接派发（Hub 服务不可用）
**GitHub Connector**：`bbb0df76-66bd-4a24-ae4f-2aac4750d90b`（已附加，子 Agent 可访问私有仓库）

---

## 派发背景

根据 `docs/coverage_mapping.md` 的优化分析，XPBET 前端需求文档库（`gdszyy/xpbet-frontend-requirements`）中真正缺失的 C 端文档已从原来误报的 83 个缩减至 33 个。其中，大量文档（用户系统、分享、聊天室、落地页、推荐、活动促销）已由前任负责人完成。

本次派发针对剩余 4 个功能域的缺失文档，每个子任务对应一个独立的 Manus 对话，并通过 GitHub connector 直接提交到仓库。

---

## 派发任务清单

| 任务编号 | 任务标题 | Manus Task ID | 任务链接 | 状态 |
|:--|:--|:--|:--|:--|
| TSK-001 | XPBET 钱包/财务系统前端需求文档 | `A7GTqgKgzub9CZfPce4zCv` | [查看](https://manus.im/app/A7GTqgKgzub9CZfPce4zCv) | 进行中 |
| TSK-002 | XPBET 礼券系统前端需求文档 | `8FVNpYknLJSE4tFo3dxUwr` | [查看](https://manus.im/app/8FVNpYknLJSE4tFo3dxUwr) | 进行中 |
| TSK-003 | XPBET 客服与内容系统前端需求文档 | `BFkhvhPK8g4g4WaAPhxRJB` | [查看](https://manus.im/app/BFkhvhPK8g4g4WaAPhxRJB) | 进行中 |
| TSK-004 | XPBET C 端包网前端需求文档 | `JBvndJgH3vAGsRcTVq4nKu` | [查看](https://manus.im/app/JBvndJgH3vAGsRcTVq4nKu) | 进行中 |

---

## 各任务覆盖功能点

### TSK-001：钱包/财务系统

| 功能点ID | 功能名称 | 目标文档 |
|:--|:--|:--|
| recv8NWvDvCc7t | 主钱包划转 | PRD_12_Wallet.md + UX_15_WalletCenter.md |
| recv7D8msMRWFh | Bonus 钱包划转 | PRD_12_Wallet.md + UX_15_WalletCenter.md |
| recv7D8mS7cWUs | 余额查询 | PRD_12_Wallet.md + UX_15_WalletCenter.md |
| recv8V4hBEt6bB | Transaction 优化 V1.1 | PRD_12_Wallet.md + UX_15_WalletCenter.md |

### TSK-002：礼券系统

| 功能点ID | 功能名称 | 目标文档 |
|:--|:--|:--|
| recv7D8mS7QBdb | 礼券核销 | PRD_13_Coupon.md + UX_16_CouponCenter.md |
| recv7D8mS7hQ4b | 使用记录 | PRD_13_Coupon.md + UX_16_CouponCenter.md |

### TSK-003：客服与内容系统

| 功能点ID | 功能名称 | 目标文档 |
|:--|:--|:--|
| recv7D8msMrc4O | C 端客服入口 | PRD_14_Support.md + UX_17_SupportContent.md |
| recv7D8msMjPKn | 站内信 | PRD_14_Support.md + UX_17_SupportContent.md |
| recv7D8msMZ3SM | VIP 客服 | PRD_14_Support.md + UX_17_SupportContent.md |
| recvaex4RoB0We | FAQ | PRD_14_Support.md + UX_17_SupportContent.md |
| recv7D8mS7LSNd | 文章系统 | PRD_14_Support.md + UX_17_SupportContent.md |
| recv7D8mS7VtK7 | 触达-站内信 | PRD_14_Support.md + UX_17_SupportContent.md |

### TSK-004：C 端包网

| 功能点ID | 功能名称 | 目标文档 |
|:--|:--|:--|
| recv7D8nfdRhGy | 包网方案 | PRD_15_WhiteLabel.md + UX_18_WhiteLabel.md |
| recv7D8nfdph5B | 定制化 | PRD_15_WhiteLabel.md + UX_18_WhiteLabel.md |

---

## 技能索引

子任务的提示词中已内置技能索引（详见 `docs/skill_index.md`），子 Agent 可按需调用以下技能而无需读取完整文档：

- `lark-bitable`：读取飞书多维表格数据
- `lark-md-import`：将 Markdown 导入为飞书文档
- `lark-wiki-docs`：操作飞书 Wiki 和文档
- `lark-codesandbox`：生成交互 Demo 并嵌入飞书
- `multi-agent-hub`：多 Agent 协作（当前不可用）

---

## 第二批派发：文档规范整改任务（2026-03-29）

**派发背景**：根据文档规范执行情况审查报告，发现三类规范缺口，按优先级 P0→P1 依次派发整改任务。

| 任务编号 | 优先级 | 任务标题 | Manus Task ID | 任务链接 | 状态 |
|:--|:--|:--|:--|:--|:--|
| TSK-005 | P0 | UX Spec 设计规范引用补全（Design Token） | `mNPrrTSmbYW9dkiMqsedof` | [查看](https://manus.im/app/mNPrrTSmbYW9dkiMqsedof) | 进行中 |
| TSK-006 | P0 | 批量上传飞书 + 回填多维表格文档链接 | `2P7zYUjeKDZ98ve9wTPTup` | [查看](https://manus.im/app/2P7zYUjeKDZ98ve9wTPTup) | 进行中 |
| TSK-007 | P1 | 统一文档状态标签（Draft/Stable/In Review） | `iHrx78oiSzStbURnptdYxZ` | [查看](https://manus.im/app/iHrx78oiSzStbURnptdYxZ) | 进行中 |

### TSK-005：设计规范引用补全
- **问题**：18 份 UX Spec 无任何 Design Token 引用，颜色/字体使用模糊表述
- **交付物**：`docs/DESIGN_SYSTEM_REF.md`（Token 速查表）+ 18 份 UX Spec 头部补充规范引用行 + `DOC_Methodology.md` 更新
- **完成标准**：全部 UX Spec 头部有 `| 设计规范 | [XPBET Design System](...) |` 行，无裸露模糊颜色表述

### TSK-006：批量上传飞书 + 回填多维表格
- **问题**：33 份文档（15 PRD + 18 UX）仅存 Git，未上传飞书；多维表格"文档链接"字段大量为空
- **交付物**：33 份飞书云文档 URL + 多维表格功能点"文档链接"字段回填
- **完成标准**：所有文档可通过飞书 URL 访问，多维表格中有对应文档的功能点链接均已填写

### TSK-007：统一文档状态标签
- **问题**：变更日志中"状态"列不统一，部分文档有、部分没有
- **交付物**：33 份文档变更日志均包含"状态"列，统一初始状态为 `Draft`
- **完成标准**：全部文档变更日志格式一致，`DOC_Methodology.md` 补充状态标签规范

---

## 第三批派发：验收修复任务（2026-03-29）

**派发背景**：第二批任务验收发现部分遗漏，本批针对具体缺口精确派发，每个任务范围聚焦以避免大批量中断。

| 任务编号 | 优先级 | 任务标题 | Manus Task ID | 任务链接 | 状态 |
|:--|:--|:--|:--|:--|:--|
| TSK-005-fix | P0 | 补全 7 份 UX Spec 设计规范引用行（UX_01~04, UX_06~08） | `87NxdnmSpLwPpa4QyfEFv5` | [查看](https://manus.im/app/87NxdnmSpLwPpa4QyfEFv5) | 进行中 |
| TSK-006A | P0 | 上传 PRD_01~05 至飞书并回填多维表格 | `GVSMY8ieTmskBMMUxasnSB` | [查看](https://manus.im/app/GVSMY8ieTmskBMMUxasnSB) | 进行中 |
| TSK-006B | P0 | 上传全部 18 份 UX Spec 至飞书并回填头部 URL | `fPYNBJtZULyJgJaDCkNwWV` | [查看](https://manus.im/app/fPYNBJtZULyJgJaDCkNwWV) | 进行中 |

### 拆分策略说明
TSK-006B 仅处理 UX Spec（18 份），与 TSK-006A（5 份 PRD）相互独立，避免单任务处理 33 份文件导致超时中断。

---

## 第四批派发：2.4 阶段 — 核心交互组件 Demo 制作（2026-03-29）

**派发背景**：所有文档规范整改已 100% 完成，进入最终阶段：为核心 UX Spec 制作 lark-codesandbox 可交互 Demo 并嵌入飞书文档。每个任务聚焦 1 个组件，避免批量中断。

| 任务编号 | 组件 | 目标飞书文档 Token | Manus Task ID | 任务链接 | 状态 |
|:--|:--|:--|:--|:--|:--|
| Demo-01 | 钱包划转表单（UX_15） | `RiQLdY9wSov01cx0LxLjzbI2pZc` | `2TZgue4kNyeuSkgkG53aVG` | [查看](https://manus.im/app/2TZgue4kNyeuSkgkG53aVG) | 进行中 |
| Demo-02 | 投注单注单卡片（UX_05） | `U57DdA0JpoDYiPxPHFej2CbqpJG` | `3WufGBZjSANj2rRCbjAD6M` | [查看](https://manus.im/app/3WufGBZjSANj2rRCbjAD6M) | 进行中 |
| Demo-03 | 登录注册表单（UX_09） | `VoQEdoTLbo8cF2x1TAIj3P4hp1d` | `dkvuD2kejNYUpPSFn3LgcS` | [查看](https://manus.im/app/dkvuD2kejNYUpPSFn3LgcS) | 进行中 |
| Demo-04 | 礼券核销组件（UX_16） | `C8Nld95a9oH4DyxsaCMj8sAJpBd` | `ZHbCeMnyzE7tLpBAk8KMzz` | [查看](https://manus.im/app/ZHbCeMnyzE7tLpBAk8KMzz) | 进行中 |
| Demo-05 | 全局导航组件（UX_01） | `JtNWd91b1oV4QixLHt4jrAtWpec` | `nDsN5FWvZUet6kQZ8Qj2oC` | [查看](https://manus.im/app/nDsN5FWvZUet6kQZ8Qj2oC) | 进行中 |

### Demo 制作规范
- 每个 Demo 为单文件 HTML（内联 CSS/JS），通过 lark-codesandbox 工作流发布到 CodeSandbox 后嵌入飞书
- 严格使用 XPBET Design Token（`#E80104` 品牌红、`ft-a~h` 灰阶、Poppins 字体）
- 移动端优先，宽度 375px，触控目标 ≥ 48px

---

## 第五批派发：Demo 修复任务（2026-03-29）

**派发背景**：验收发现 Demo-02 和 Demo-05 的 CodeSandbox 沙箱已生成但飞书 iframe 嵌入未完成，本批精确修复。提示词中强化了 Step 4（飞书嵌入）和验证步骤，要求子 Agent 必须确认 `block_type=26` 块存在。

| 任务编号 | 组件 | 目标飞书文档 Token | Manus Task ID | 任务链接 | 状态 |
|:--|:--|:--|:--|:--|:--|
| Demo-02-fix | 投注单注单卡片（UX_05） | `U57DdA0JpoDYiPxPHFej2CbqpJG` | `n2PphsGSnmdW7Lshtaomy4` | [查看](https://manus.im/app/n2PphsGSnmdW7Lshtaomy4) | 进行中 |
| Demo-05-fix | 全局导航组件（UX_01） | `JtNWd91b1oV4QixLHt4jrAtWpec` | `9Bt7ZTgdi3w6rxyyDUN5jK` | [查看](https://manus.im/app/9Bt7ZTgdi3w6rxyyDUN5jK) | 进行中 |

# match-pc 前端业务索引入口

本文档是 `match-pc-test1.zip` 前端包在本仓库中的 **repo-indexer 风格入口**。它不替代源码，而是为后续 Agent、开发者和产品/架构协作提供高信噪比的业务导航：从业务功能出发，快速定位到页面路由、业务模块、关键组件、接口 handler 与取数逻辑。


## 强制索引访问规则

当任务涉及 **用户体验、功能修改或前端修改** 时，Agent 必须先访问并查询本目录的前端业务索引，再开始方案设计或代码修改。该规则适用于但不限于页面结构调整、交互流程变更、组件样式修改、接口取数调整、表单/弹窗/导航/投注单/账户中心等前端相关改动。

推荐查询顺序为：`repo-indexer/match-pc/INDEX.md` → `repo-indexer/match-pc/business_oriented_index.md` → 按需进入 `repo-indexer/match-pc/frontend_breakdown_report.md`、`repo-indexer/match-pc/generated_frontend_index.md` 或 `repo-indexer/match-pc/data/*.csv`。如果变更影响路由、模块边界、功能归属、关键组件或取数逻辑，必须在同一提交中同步更新这些索引文件。

## 读取路径

建议所有后续前端相关任务按以下顺序读取。首先阅读本入口，明确当前任务所属业务域；其次根据业务域进入 `business_oriented_index.generated.md` 的功能索引；最后再按需要进入完整拆解报告、自动路由索引或 CSV 数据文件。

| 读取目的 | 推荐文件 | 说明 |
|---|---|---|
| 快速判断从哪里改 | [`business_oriented_index.generated.md`](business_oriented_index.generated.md) | 按功能、模块、页面、API handler、模块取数调用五个维度组织。 |
| 理解项目 coding 习惯 | [`frontend_breakdown_report.md`](frontend_breakdown_report.md) | 解释薄路由、厚模块、接口统一封装、状态分层、i18n 与样式习惯。 |
| 查完整 App Router 与 handler 表 | [`generated_frontend_index.md`](generated_frontend_index.md) | 自动抽取的路由、模块、组件、接口全量清单。 |
| 做二次分析或导入表格 | [`data/features.csv`](data/features.csv)、[`data/pages.csv`](data/pages.csv)、[`data/modules.csv`](data/modules.csv)、[`data/api_usage.csv`](data/api_usage.csv) | 结构化数据源，适合脚本、表格或数据库导入。 |

## 业务域索引

当前索引将前端包拆为九个业务域。每个业务域都以“功能 → 路由 → 模块 → 组件 → 取数”作为定位主线，避免只按目录树理解代码。

| 业务域 | 主要功能 | 入口路由/挂载方式 | 核心目录 |
|---|---|---|---|
| `sports_match` | 体育首页、滚球、按运动/联赛赛事列表、比赛详情、赛事分析 | `/[locale]/sports`、`/[locale]/sports-live`、`/[locale]/sports/[sport_id]`、`/[locale]/leagues/[tournament_id]`、`/[locale]/matches/[match_id]` | `src/modules/home`、`src/modules/match`、`src/modules/match-info` |
| `bet_slip` | 投注单购物车、单关/串关、投注提交、ticket | 全局抽屉、桌面右栏、赔率按钮联动 | `src/modules/bet-slip` |
| `casino` | 赌场大厅、lobby、游戏筛选、游戏启动 | `/[locale]/casino/[lobbyId]`、`/[locale]/casino/game/[gameCode]` | `src/modules/casino` |
| `marketing` | 体育/赌场促销、首充活动、优惠码 | `/[locale]/sports/promotions`、`/[locale]/casino/promotions` | `src/modules/marketing` |
| `account_balance` | 充值、提现、收款账户、轮询 | `/[locale]/account/deposit`、`/[locale]/account/withdraw` | `src/modules/balance` |
| `account_user_center` | 账户菜单、KYC、通知、FAQ、客服、责任博彩、安全中心 | `/[locale]/account/*` | `src/modules/user-center`、`src/modules/user`、`src/modules/security-center` |
| `transaction` | 交易流水、余额、投注历史、转账订单 | `/[locale]/account/transactions` | `src/modules/transaction` |
| `auth` | 登录、短信、移动端登录页 | `/[locale]/signin` 与桌面登录弹窗 | `src/modules/user/auth` |
| `docs_legal` | 法务文档、体育规则 | `/[locale]/legal/*`、`/[locale]/sports/rules` | `src/modules/docs` |

## 取数逻辑速记

项目接口层的基本定位方式是：页面或模块通过 React Query、Zustand action 或 hook 调用 `src/api/handlers/*`；handler 再选择 `uofFetcher`、`userFetcher`、`paymentFetcher`、`gameFetcher`、`sportFetcher` 等统一 fetcher。禁止在页面或组件里直接硬编码后端 URL。

| 数据类别 | Handler 线索 | 消费方线索 | 备注 |
|---|---|---|---|
| 体育赛事与盘口 | `match.ts`、`matches.ts`、`menu.ts`、`tournament.ts` | `modules/match`、`modules/home`、`modules/match/sidebar` | 比赛详情还会合并 HTTP 与 WS 更新，避免覆盖新鲜赔率。 |
| 足球/篮球分析 | `match-football.ts`、`match-basketball.ts` | `modules/match-info` | 赛事分析、阵容、趋势等使用 sport 统计接口。 |
| 投注单与订单 | `cart.ts`、`order.ts`、`match.ts` | `modules/bet-slip`、`modules/match/_components` | 赔率按钮、购物车 store、订单结果处理强耦合。 |
| 赌场 | `casino.ts` | `modules/casino`、`modules/home/_constants/nav-menus.ts` | lobby 数据同时影响页面和导航入口。 |
| 账户与认证 | `passport.ts`、`user.ts`、`user-kyc.ts` | `stores/session-store.ts`、`modules/user`、`modules/user-center` | 登录态从 localStorage 恢复并通过接口校验。 |
| 资金与交易 | `deposit.ts`、`withdraw.ts`、`wallet.ts`、`transfer-instrument.ts`、`transaction.ts` | `modules/balance`、`modules/transaction` | 充值/提现包含轮询和账户校验逻辑。 |
| 通知/客服/FAQ | `notification.ts`、`faq.ts`、`support.ts` | `modules/user-center/notification`、`faq`、`support` | 账户中心页面壳统一承载。 |

## 后续维护规范

当后续任务修改了页面路由、模块边界、关键组件或接口 handler，应同步更新本目录下的业务索引。若只修改源码而不更新索引，下一位 Agent 很容易从旧路径进入，导致重复分析或误改。建议每次前端结构性变更至少更新 `business_oriented_index.generated.md` 中相关功能行，并视情况更新 `.cursor/rules/frontend_match_pc.md`。


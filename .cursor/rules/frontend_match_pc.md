# match-pc 前端包索引规范

## 定位

本文档是 `match-pc` 前端包在本仓库内的轻量规则入口，目标是把一次性代码拆解结果沉淀为可复用的 **业务导向索引**。后续 Agent 处理 match-pc 前端问题时，应先从业务功能定位，再进入页面、模块、组件、接口与取数逻辑。

> 主入口：[`repo-indexer/match-pc/INDEX.md`](../../repo-indexer/match-pc/INDEX.md)  
> 强化索引：[`repo-indexer/match-pc/business_oriented_index.md`](../../repo-indexer/match-pc/business_oriented_index.md)  
> 完整拆解：[`repo-indexer/match-pc/frontend_breakdown_report.md`](../../repo-indexer/match-pc/frontend_breakdown_report.md)


## 强制触发条件

当任务涉及 **用户体验、功能修改或前端修改** 时，必须先查询 match-pc 前端业务索引，禁止直接凭记忆或只读局部源码开工。触发场景包括页面交互、视觉与布局、导航、表单、弹窗、投注单、账户中心、接口取数、React Query key、WebSocket/SSE 同步、模块拆分与组件复用等。

强制读取路径：`repo-indexer/match-pc/INDEX.md` → `repo-indexer/match-pc/business_oriented_index.md` → 按业务域进入功能行，再定位页面、模块、关键组件和取数接口。若任务只涉及非前端后端脚本，也应在判断“不涉及前端/用户体验”后再跳过。

## 三层读取路径

| 层级 | 读取目标 | 文件 |
|---|---|---|
| 第一层 | 判断业务域、功能与入口路由 | `docs/frontend/match-pc/README.md` |
| 第二层 | 查功能到模块、组件、取数逻辑的映射 | `docs/frontend/match-pc/business_oriented_index.generated.md` |
| 第三层 | 查完整路由、handler、组件目录或结构化数据 | `docs/frontend/match-pc/generated_frontend_index.md` 与 `docs/frontend/match-pc/data/*.csv` |

## 核心业务域

| 业务域 | 典型改动入口 | 代码索引线索 |
|---|---|---|
| 体育赛事与盘口 | 首页、滚球、赛事列表、联赛、比赛详情、赔率按钮 | `sports_match`、`src/modules/match`、`src/modules/home`、`src/modules/match-info` |
| 投注单 | 购物车、单关/串关、投注提交、ticket | `bet_slip`、`src/modules/bet-slip` |
| 赌场 | lobby、游戏卡片、游戏启动、赌场导航 | `casino`、`src/modules/casino` |
| 账户与资金 | 充值、提现、KYC、交易、通知、FAQ、客服 | `account_balance`、`account_user_center`、`transaction` |
| 登录认证 | 登录弹窗、移动端登录、短信流程、session | `auth`、`src/modules/user/auth`、`src/stores/session-store.ts` |
| 营销与文档 | 促销、首充、法务、规则 | `marketing`、`docs_legal` |

## 修改约束

任何新 patch 若影响以下内容，必须同步更新索引文档。

| 变更类型 | 必须同步更新 |
|---|---|
| 新增、删除、迁移 App Router 页面 | `business_oriented_index.generated.md` 的页面路由索引与 `data/pages.csv` |
| 新增业务功能或重组模块 | `business_oriented_index.generated.md` 的功能索引与模块索引 |
| 新增/重命名 API handler 或 Interface | API Handler 索引、模块取数调用索引与 `data/api_usage.csv` |
| 新增跨业务共享组件 | 组件索引与相关功能行的“关键组件”列 |
| 调整取数策略，例如 React Query key、WS/SSE、轮询、store 同步 | 对应功能行的“取数逻辑”列 |

## 后续 Agent 防坑提示

`src/app/[locale]` 下的页面多数是薄入口，真正的业务逻辑通常在 `src/modules/<domain>`。不要只读 `page.tsx` 就下结论。接口也不要从组件内直接拼 URL，应通过 `src/api/handlers/*` 进入，再查看 `src/api/client.ts` 的统一 fetcher、鉴权和错误处理规则。涉及内部导航时，应优先使用项目的 locale-aware navigation，而不是直接依赖普通 `next/link` 或 `next/navigation` 的路由跳转。


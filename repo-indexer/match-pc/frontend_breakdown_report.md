# match-pc 前端包拆解报告

作者：**Manus AI**  
日期：2026-05-01

## 摘要

本次拆解对象是用户上传的 `match-pc-test1.zip` 前端包。该项目是一个以 **Next.js App Router + React + TypeScript** 为核心的体育投注与赌场前端，目录呈现明显的“路由层很薄、业务模块承载页面逻辑、API handler 统一封装接口、全局与模块状态分离”的组织方式。`package.json` 显示项目使用 Next、React、TanStack Query、Zustand、next-intl、Radix、Motion、Biome、MSW、Playwright 等依赖，运行脚本则围绕 `next dev/build`、Biome 检查、TypeScript 检查与 mock 开发展开。[1]

代码定位上，应优先从 `src/app/[locale]` 的 App Router 文件定位页面入口，再跳转到 `src/modules/<domain>` 的业务实现；组件查找应先看 `src/components` 的共享 UI，再看模块内 `_components`；接口查找应从 `src/api/handlers` 的 `*Interface` 函数进入，再下钻到 `src/api/client.ts`、`src/api/models` 与调用方的 React Query 或 store 逻辑。项目自身规则也明确将 `src/modules` 定义为 DDD 风格业务模块，并约定 `_components/_hooks/_logic/_utils/_constants` 等下划线目录为模块私有实现，公共导出通过模块根 `index.ts` 暴露。[2]

## 一、技术栈与工程分层

项目根部的 `package.json` 表明这是一个 Next 16、React 19、TypeScript 5、Tailwind CSS 4 与 pnpm 管理的前端工程；业务状态主要由 **TanStack Query** 和 **Zustand** 支撑，表单相关依赖包括 React Hook Form 与 Zod，国际化依赖 next-intl，Mock 依赖 MSW。[1] 结合项目规则文档可知，工程预期的数据流是 `UI → 状态层 → 数据层 → 持久层`，其中服务端状态优先进入 React Query，全局状态进入 `src/stores`，模块状态进入 `src/modules/*/stores`，实时数据通过 WebSocket、BroadcastChannel 与观察者链路进入 React Query 或 Zustand。[3]

| 层级 | 主要目录 | 核心职责 | 代码定位要点 |
|---|---|---|---|
| 路由层 | `src/app/[locale]` | Next App Router、locale、layout、metadata、动态路由参数传递 | 页面文件通常只负责 `generateMetadata` 与挂载模块组件。 |
| 业务模块层 | `src/modules` | 体育、比赛详情、投注单、赌场、账户、交易、用户等业务实现 | 优先看模块根 `index.ts`，再看页面级组件、私有 `_hooks/_logic/_components`。 |
| 接口层 | `src/api` | 多服务 fetcher、业务 handler、模型与 SSR fetch 工具 | 业务代码不应直接硬编码 URL，应调用 `handlers/*`。 |
| 共享组件层 | `src/components` | Button、Input、Modal、Drawer、Sidebar、Toast、Table 等 UI 原语 | 新 UI 先复用共享组件，再补模块组件。 |
| 全局状态与 Hook | `src/stores`、`src/hooks` | session、ui、timezone、region、socket、wallet、媒体查询等 | 跨页面共享状态放全局，页面局部状态放模块或组件内。 |
| 工具与集成 | `src/utils`、`src/libs`、`src/i18n` | class 合并、错误、时间、导航、Firebase、事件常量、区域与语言 | 导航必须优先使用 `@/i18n` 导出的 locale-aware API。 |

项目的布局层级非常清晰。根布局 `src/app/layout.tsx` 负责全局 CSS、字体、Provider、Toast 与 DOM 容器；locale 布局 `src/app/[locale]/layout.tsx` 负责校验 locale、注入 `NextIntlClientProvider`、挂载 `AppShell`、导航栏、全局弹窗、时区同步和投注单清理；`(main)` 布局再通过 `MainShell` 管理侧边栏 padding、移动底栏与语言弹窗。[4] [5] [6]

> 代码定位原则：先找 App Router 入口，再找模块实现，再找 handler 与共享组件。不要从组件目录反向猜页面，因为多数复杂页面的真实业务状态、接口与实时订阅都在 `src/modules` 内编排。

## 二、路由定位索引

项目使用 `[locale]` 作为顶层动态段，实际 URL 以 `/es`、`/pt`、`/en` 等语言前缀进入。`next.config.ts` 配置了 `/:locale(pt|es|en)` 到 `/:locale/sports` 的重定向，`src/app/[locale]/page.tsx` 也提供到 `/sports` 的兜底重定向。[7]

### 2.1 路由壳层

| 路由层级 | 文件 | 职责 | 关键依赖 |
|---|---|---|---|
| 根布局 | `src/app/layout.tsx` | 全局样式、字体、RootProviders、Toast、App/Modal/Toast 容器 | `RootProviders`、`ToastProvider`、`DomIdEnum`。[5] |
| Locale 布局 | `src/app/[locale]/layout.tsx` | locale 校验、metadata、i18n provider、AppShell、导航、时区同步、投注单清理 | `NextIntlClientProvider`、`NavigationBar`、`CartCleanupListener`。[4] |
| 主站布局 | `src/app/[locale]/(main)/layout.tsx`、`main-shell.tsx` | 桌面侧边栏 padding、移动底栏、开发回放控制、语言弹窗 | `checkHasSidebar`、`BottomTabBar`、`LanguageModal`。[6] |
| Sports 布局 | `src/app/[locale]/(main)/(sports)/layout.tsx` | 体育分支侧边栏与内容容器 | 进入 `sports-layout-client.tsx` 与 `modules/match/sidebar`。 |
| Casino 布局 | `src/app/[locale]/(main)/(casino)/layout.tsx` | 赌场分支侧边栏与内容容器 | 进入 `casino-layout-client.tsx` 与 `modules/casino`。 |
| Account 布局 | `src/app/[locale]/(main)/account/layout.tsx` | 账户中心认证与 KYC 守卫、账户侧边栏、右侧工具栏 | `AccountLayoutClient`、`ACCOUNT_ROUTES`、`AccountSidebar`。[8] |

### 2.2 体育与比赛路由

体育路由是当前项目业务密度最高的部分。`/sports` 进入热门赛事首页，`/sports-live` 进入滚球页，`/sports/[sport_id]` 与 `/leagues/[tournament_id]` 进入列表壳，`/matches/[match_id]` 进入比赛详情。体育侧边栏通过 `useParams` 读取 `sport_id/tournament_id/match_id`，在树节点未加载时会用 `GetBreadcrumbInterface` 回查 sport 与 tournament，以确保从直达 URL 进入时仍能点亮正确菜单。[9]

| URL 模式 | 路由文件 | 页面/模块入口 | 主要接口线索 | 说明 |
|---|---|---|---|---|
| `/[locale]/sports` | `src/app/[locale]/(main)/(sports)/sports/page.tsx` | `src/modules/home/home-page.tsx` → `SportsPage type="hot"` | banner、hot matches | 路由页很薄，主要设置 metadata 并渲染模块。 |
| `/[locale]/sports-live` | `src/app/[locale]/(main)/(sports)/sports-live/page.tsx` | `src/modules/home/live-page.tsx` → `SportsPage type="live"` | live matches | 与热门页共享 `SportsPage` 容器。 |
| `/[locale]/sports/[sport_id]` | `src/app/[locale]/(main)/(sports)/sports/[sport_id]/page.tsx` | `src/modules/match/list` | `api/handlers/matches.ts` | 按运动维度展示赛事列表。 |
| `/[locale]/leagues/[tournament_id]` | `src/app/[locale]/(main)/(sports)/leagues/[tournament_id]/page.tsx` | `MatchListContent`、`TournamentShell` | `GetTournamentMarketsInterface`、breadcrumb | 按联赛维度展示赛事或市场。 |
| `/[locale]/leagues/[tournament_id]/outright` | `.../outright/page.tsx` | `OutrightContent` | outright markets | 冠军盘/优胜盘独立内容。 |
| `/[locale]/matches/[match_id]` | `src/app/[locale]/(main)/(sports)/matches/[match_id]/page.tsx` | `src/modules/match/detail` | `GetMatchInterface`、`GetMarketTabsInterface`、`GetStatscoreEventIdInterface` | 比赛详情，集成 HTTP 查询、缓存合并、WS 观察器、Statscore、小屏 tab。 |
| `/[locale]/sports/promotions` | `.../sports/promotions/page.tsx` | `src/modules/marketing/promotion/list` | `api/handlers/promotion.ts` | 体育促销列表。 |
| `/[locale]/sports/rules` | `.../sports/rules/page.tsx` | `src/modules/docs/sports-rules` | 静态/文档数据 | 体育规则说明页。 |

比赛详情模块 `src/modules/match/detail/layout.tsx` 是理解复杂页面 coding 逻辑的最佳样本。它在组件内集中编排 breadcrumb、market tabs、Statscore event、match detail 等查询；比赛详情查询会从 HTTP 获取最新数据，再和 React Query cache 中的旧数据通过 `mergeMatchData` 合并，避免 WebSocket 更新过的新鲜 odds/specifier 被 HTTP 回包覆盖；随后再挂载 `useGameSubscription`、`useMatchLiveScoreObserver`、`useMatchItemObserver`、`useDetailMatchStatusObserver` 与 `useMatchItemFixtureObserver` 等实时观察器。[10]

### 2.3 赌场路由

赌场路由位于 `(casino)` 分组下，入口包括 lobby、游戏详情、回调页与促销页。主导航中的赌场入口不是完全静态的，而是由 `lobbiesToNavItems(lobbies)` 将后端 lobby 数据转换为菜单项；桌面端每个 lobby 一个导航入口，移动端则通过 `getCasinoNavItem(lobbies)` 合成单一 casino tab。[11]

| URL 模式 | 路由文件 | 页面/模块入口 | 主要接口线索 | 说明 |
|---|---|---|---|---|
| `/[locale]/casino` | `src/app/[locale]/(main)/(casino)/casino/page.tsx` | casino home fallback | `GetCasinoGameLobbiesInterface` | 可根据 lobby 数据重定向或渲染入口。 |
| `/[locale]/casino/[lobbyId]` | `.../casino/[lobbyId]/page.tsx` | `src/modules/casino/home/casino-home` | casino games、tags、merchants | 赌场 lobby 首页。 |
| `/[locale]/casino/game/[gameCode]` | `.../casino/game/[gameCode]/page.tsx` | `src/modules/casino/game/game-detail-page` | `LaunchGameInterface` 等 | 游戏详情/启动页，可能涉及外部 URL。 |
| `/[locale]/casino/game/callback` | `.../callback/page.tsx` | `Loading` | - | 游戏回调过渡页。 |
| `/[locale]/casino/promotions` | `.../casino/promotions/page.tsx` | `src/modules/marketing/promotion/list` | promotion handlers | 赌场促销列表。 |

### 2.4 账户中心路由

账户中心路由全部是 URL 可见的 `account/` 段，而不是隐藏 route group。项目用 `ACCOUNT_ROUTES` 集中声明菜单、路径、标题 i18n key、图标、KYC 要求与分组；`AccountLayoutClient` 会基于该配置判断当前路由是否需要 KYC，未登录时跳首页，已登录但未完成 KYC 时将需 KYC 页面替换到 `/account/kyc`。[12] [8]

| URL 模式 | 路由文件 | 页面/模块入口 | 权限/布局线索 | 说明 |
|---|---|---|---|---|
| `/[locale]/account` | `src/app/[locale]/(main)/account/page.tsx` | `AccountMenuClient` 或重定向 | 移动端菜单/桌面默认页 | 移动端入口页，桌面偏向 deposit。 |
| `/[locale]/account/deposit` | `.../account/deposit/page.tsx`、`deposit-page-client.tsx` | `src/modules/balance/deposit` | `kycRequired: true` | 充值页，右侧 FAQ 通过 React Query 拉取。 |
| `/[locale]/account/withdraw` | `.../withdraw/page.tsx`、`withdraw-page-client.tsx` | `src/modules/balance/withdraw` | `kycRequired: true` | 提现页，含账户/密码/轮询 hooks。 |
| `/[locale]/account/kyc` | `.../kyc/page.tsx`、`kyc-page-client.tsx` | `src/modules/user/kyc` | KYC 核心页 | 账户守卫回落目标。 |
| `/[locale]/account/transactions` | `.../transactions/page.tsx` | `src/modules/transaction` | 账户页壳 + 交易模块 | 交易、余额、投注历史等。 |
| `/[locale]/account/security` | `.../security/page.tsx` | `src/modules/security-center` | 账户页壳 | 密码与安全中心。 |
| `/[locale]/account/gambling-games` | `.../gambling-games/page.tsx` | `src/modules/user-center/health-setting` | group 2 | 责任博彩/健康设置。 |
| `/[locale]/account/affiliate` | `.../affiliate/page.tsx` | `src/modules/user-center/affiliate` | group 2 | 联盟/推广。 |
| `/[locale]/account/settings` | `.../settings/page.tsx` | `src/modules/user-center` | group 2 | 设置页。 |
| `/[locale]/account/support` | `.../support/page.tsx` | `src/modules/user-center/support` | group 3 | 客服支持。 |
| `/[locale]/account/notifications`、`announcements` | 对应 page | `src/modules/user-center/notification` | group 3 | 通知/公告。 |
| `/[locale]/account/faq` | `.../faq/page.tsx` | `src/modules/user-center/faq` | group 3 | 帮助问答。 |

### 2.5 法务、登录与健康检查路由

| URL 模式 | 路由文件 | 模块入口 | 说明 |
|---|---|---|---|
| `/[locale]/legal/terms` | `src/app/[locale]/(main)/legal/terms/page.tsx` | `src/modules/docs/legal/legal-doc-page` | 条款文档。 |
| `/[locale]/legal/privacy` | `.../privacy/page.tsx` | `LegalDocPage` | 隐私文档。 |
| `/[locale]/legal/aml-kyc` | `.../aml-kyc/page.tsx` | `LegalDocPage` | AML/KYC 文档。 |
| `/[locale]/legal/responsible-gaming` | `.../responsible-gaming/page.tsx` | `LegalDocPage` | 责任博彩文档。 |
| `/[locale]/signin` | `src/app/[locale]/signin/page.tsx` | `src/modules/user/auth/h5-signin` | 移动端独立登录页。 |
| `/health` | `src/app/health/route.ts` | Route Handler | 健康检查接口。 |

## 三、组件索引与页面组合方式

该项目的组件分为两类：一类是 `src/components` 下跨业务复用的 UI 原语，另一类是 `src/modules/<domain>` 下围绕特定业务场景的模块组件。共享组件应优先复用，不建议在业务模块内重复实现已有 UI 原语；模块组件则应尽量保持私有，通过模块根 `index.ts` 仅暴露页面需要的入口。[2]

| 组件层级 | 代表路径 | 职责 | 新 patch 融入建议 |
|---|---|---|---|
| 全局 Provider | `src/components/providers/root-providers.tsx`、`src/components/tanstack-provider` | MSW、Theme、TanStack Query、移动缩放锁等上下文 | 不要在页面内重复创建 QueryClient；新增全局 provider 需要评估是否应挂根。 |
| 通用 UI 原语 | `button`、`input`、`select`、`modal`、`drawer`、`tabs`、`toast`、`pagination` | 基础交互组件 | 新 UI 先检索这里；样式通过 props、variant、className 组合。 |
| Sidebar 系统 | `src/components/sidebar` | 通用侧边栏 primitive、group、item、shell | 体育、赌场、账户侧边栏共用此壳；不要单独实现平行 sidebar 体系。 |
| 导航与壳层组件 | `src/modules/home/_components` | NavigationBar、BottomTabBar、AppShell、AppInitializer、RightAside | 跨页面初始化和主导航逻辑集中在 home 模块，不应散落在页面。 |
| 体育比赛组件 | `src/modules/match/_components`、`detail`、`list`、`sidebar` | 赛事卡片、赔率按钮、市场列表、详情页、体育侧边栏 | 赔率、market、specifier 逻辑优先放 `_logic/_utils/_hooks`，UI 放 `_components`。 |
| 投注单组件 | `src/modules/bet-slip` | 购物车、投注面板、ticket、store slices、订阅 | 与赔率按钮和实时更新强耦合，新增投注相关逻辑需先看 store slices。 |
| 账户页组件 | `src/modules/user-center`、`balance`、`transaction`、`user/kyc` | AccountPageShell、菜单、充值提现、交易、KYC | 统一走 `AccountPageShell`，权限走 `ACCOUNT_ROUTES` 和布局守卫。 |
| 赌场组件 | `src/modules/casino` | lobby、筛选、game card、game detail | 赌场导航来自 lobby API，新增分类应考虑 nav-menus 与 sidebar 同步。 |

共享 Button 组件展示了项目的基础组件写法：使用 `class-variance-authority` 管理 variant，通过 `cn()` 合并 Tailwind class，组件 API 以 `variant/block/loading/icon/onClick` 这类有限 props 暴露，内部处理 loading 状态与 disabled 状态。[13] `cn()` 则通过 `tailwind-merge` 扩展了项目自定义 `text-*` token，避免字体大小 token 和颜色 token 被错误合并。[14]

## 四、接口索引与数据流

`src/api/client.ts` 是接口层底座。它按服务域创建 `uofFetcher`、`userFetcher`、`paymentFetcher`、`gameFetcher`、`sportFetcher`，请求时会自动处理鉴权 token、trace headers、`Accept-Language`、`X-Timezone`、`X-Source`、GET 参数、JSON body、HTTP 错误、业务 code 错误、token 轮换、登录过期清理与可选 Zod 校验。[15]

| 接口域 | Handler 文件 | 典型导出 | 主要调用场景 |
|---|---|---|---|
| 体育比赛详情 | `src/api/handlers/match.ts` | `GetMatchInterface`、`PostLocalCartInterface` | 比赛详情、购物车 specifier 状态检查；返回前归一化 markets。[16] |
| 体育列表/搜索 | `src/api/handlers/matches.ts` | `GetHotMatchesInterface`、`GetBreadcrumbInterface`、`GetMarketTabsInterface`、`SearchMatchesInterface` | 热门/滚球/列表/详情 breadcrumb/market tabs。 |
| 体育菜单 | `src/api/handlers/menu.ts` | `GetMenuSportsInterface`、`GetTopSportsInterface`、`GetMenuCategoriesInterface`、`GetMenuTournamentsInterface` | 体育侧边栏树、Top Sports、分类/联赛下钻。 |
| 赛事分析 | `match-football.ts`、`match-basketball.ts` | `GetFootballMatchTrendById`、`GetBasketballMatchPlayersById` 等 | 足球/篮球详情分析、阵容、趋势。 |
| 赌场 | `src/api/handlers/casino.ts` | `GetCasinoGameLobbiesInterface`、`GetCasinoGamesInterface`、`LaunchGameInterface` | lobby、游戏列表、游戏启动。 |
| 用户与认证 | `passport.ts`、`user.ts`、`user-kyc.ts` | `LoginInterface`、`CheckLoginInterface`、`GetProfileInterface`、`CreateKycInterface` | 登录、会话校验、profile、KYC。 |
| 资金 | `deposit.ts`、`withdraw.ts`、`wallet.ts`、`transfer-instrument.ts` | `CreateDepositInterface`、`CreateWithdrawInterface`、`GetBalanceInterface` | 充值、提现、钱包余额、收款账户。 |
| 交易 | `transaction.ts`、`transaction-bethistory.ts` | `GetTransactionsListPageInterface`、`GetSportReportInterface` | 交易记录、余额列表、投注历史。 |
| 通知与支持 | `notification.ts`、`faq.ts`、`support.ts` | `GetSystemMessagesInterface`、`GetFrontFaqListInterface`、`GetSupportPhoneInterface` | 通知、FAQ、客服。 |
| 营销 | `promotion.ts` | `GetPromotionsInterface`、`ValidatePromoCodeInterface` | 促销列表、首充活动、优惠码。 |
| 埋点与外部组件 | `analytics.ts`、`statscore.ts` | `ReportAnalyticsInterface`、`GetStatscoreEventIdInterface` | 分析上报、Statscore widget event id。 |

接口命名习惯是 `Verb + Domain + Interface`，例如 `GetMatchInterface`、`CreateDepositInterface`、`GetFrontFaqListInterface`。handler 通常只做轻量参数组装、endpoint 选择、返回类型声明与必要的响应归一化，不把页面状态、副作用或 UI fallback 混入接口层。比赛详情 handler 是一个典型样本：`GetMatchInterface({ event_id })` 调用 `uofFetcher.get('/v1/match/${eventId}')` 后，再执行 `normalizeMarketGroups(match.markets)`。[16]

React Query 是页面侧消费接口的主要方式。全局 QueryClient 默认 `staleTime: 0`、`retry: 0`、`refetchOnWindowFocus: false`、`refetchOnReconnect: false`，而具体页面可按业务覆盖，例如比赛详情对 match detail 明确设置 `refetchOnWindowFocus: true` 与 `placeholderData: keepPreviousData`，Statscore event id 则设置 `staleTime: Infinity`。[17] [10]

## 五、编码逻辑与开发习惯总结

### 5.1 页面文件保持“薄”，业务集中在 modules

路由页的普遍形态是服务端文件负责 metadata、params 解码与模块挂载。例如比赛详情路由页读取 `match_id` 后渲染 `<MatchDetail matchId={...} />`，具体查询、缓存、实时订阅、UI 状态、market 过滤和 Statscore 展示都下沉到 `src/modules/match/detail/layout.tsx`。[10] 这意味着新增页面时，应优先新建或复用模块入口，而不是在 `src/app` 的 `page.tsx` 中堆业务逻辑。

### 5.2 路由、菜单、侧边栏偏好“配置表 + 策略函数”

账户中心的 `ACCOUNT_ROUTES` 用数组集中声明菜单、路径、标题、图标、KYC 要求与分组，布局和侧边栏都消费这份配置。[12] 主导航同样使用 `FIXED_NAV_ITEMS` 加 `lobbiesToNavItems(lobbies)` 的配置化转换方式生成菜单，并将 active 判断函数挂在配置项上。[11] 体育侧边栏则进一步把路由参数、breadcrumb 接口与树形 store 组合起来，以保证直接访问深层赛事或联赛时仍能恢复侧边栏激活态。[9]

### 5.3 状态管理分层清楚：React Query 管服务端状态，Zustand 管全局/模块状态

全局 QueryClient 的默认策略偏保守：不自动 retry，默认 stale 立即过期，不在窗口聚焦时自动重拉，避免过多隐式请求。[17] 需要更强实时性的页面会在局部显式覆盖策略并结合 WebSocket 观察器更新缓存。Zustand 则用于 session、ui、timezone、region、sharedSocket、slipSettings 等全局状态，以及投注单、提现等模块状态。`session-store.ts` 展示了典型 store 写法：登录态从 localStorage 恢复，`CheckLoginInterface` 校验，`GetProfileInterface` 刷新 profile，`update()` 有 2 秒节流与 pending promise 复用，`getSessionToken()` 则供非 React 场景如 API client 读取 token。[18]

### 5.4 全局副作用集中在 AppInitializer，不散落在页面

`AppInitializer` 只在客户端运行，集中负责 app info 初始化、弱网检测、未读消息、投注观察、SSE、钱包同步、Firebase analytics 懒初始化、WebSocket 连接/断开、session 初始化、登录后 toast 与 KYC 跳转、钱包余额/币种同步、手机号推断地区、向 WebSocket 发送语言与鉴权命令。[19] 后续 patch 如果涉及“应用启动时必须做一次”的逻辑，应先判断是否属于该入口或其下游 hook，而不是放进某个页面组件。

### 5.5 API 层统一处理鉴权、错误与环境 URL，页面不直接拼 URL

项目规则和 `api/client.ts` 都强调禁止硬编码 API URL，应使用服务 fetcher。`baseRequest` 自动注入 token、语言、时区与 trace 信息，HTTP 错误抛 `NetworkError`，业务 code 700 抛 `ApiError` 并上报，其他非零 code 抛 `ForbiddenError`，1000/1001 触发清 session 与打开登录弹窗。[15] 新接口 patch 应新增或修改 `api/handlers/<domain>.ts`，再在页面或 hook 中通过 React Query/Mutation 调用。

### 5.6 国际化与 locale-aware navigation 是硬约束

项目通过 `NextIntlClientProvider` 在 `[locale]/layout.tsx` 注入消息和时区。[4] 项目规则明确要求内部 `Link`、`useRouter`、`redirect` 从 `@/i18n` 导入，避免丢失 locale 前缀；`next/navigation` 仅用于 `useParams`、`useSearchParams`、`notFound` 等非 locale navigation 场景。[3] 新文案应写入 locale 消息并使用 `useTranslations()`，不应硬编码到组件中。

### 5.7 样式习惯是 Tailwind token + `cn()` + 少量 CVA

样式以 Tailwind CSS token 为核心，`cn()` 结合 `clsx` 与扩展后的 `tailwind-merge`，并注册项目自定义字体与文本颜色 token。[14] Button 组件使用 CVA 管理 variant，说明基础组件倾向用有限 variant 暴露 API，而业务组件则通过 `className` 和组合完成定制。[13] 新 patch 应优先使用 `text-body-*`、`text-title-*`、`bg-filltext-*`、`rounded-*` 等项目 token；若新增 text token，应同步更新 `extendTailwindMerge()`，否则 class merge 可能错误。[14]

### 5.8 错误处理与 fire-and-forget promise 要显式兜底

项目代码中可见异步副作用的 `.catch(reportError)` 处理，例如比赛详情在 HTTP 合并后重新校验投注单时捕获并上报错误。[10] 项目规则也强调 fire-and-forget promise 必须 `.catch()`，Toast 应使用固定 `id` 去重。[2] 这类习惯对赔率、投注、支付、KYC 等敏感路径尤其重要。

## 六、新 patch 融入建议

| 场景 | 推荐落点 | 不建议做法 | 检查点 |
|---|---|---|---|
| 新增页面 | `src/app/[locale]/.../page.tsx` 只做 metadata 与模块挂载；业务放 `src/modules/<domain>` | 在 page 文件内直接写大段 client 逻辑 | 是否有 `generateMetadata`；是否使用 i18n 标题；是否导出模块入口。 |
| 新增 API | `src/api/handlers/<domain>.ts` + `src/api/models/<domain>.ts` | 在组件内直接 `fetch('https://...')` | 是否选对 fetcher；是否声明参数/响应类型；是否需要 schema。 |
| 新增账户菜单 | 修改 `ACCOUNT_ROUTES`，必要时补 page 与模块 | 在 sidebar 中手写一个特殊菜单 | 是否配置 `kycRequired/group/icon/titleKey`；移动端菜单是否自动覆盖。 |
| 新增主导航/赌场入口 | 修改 `nav-menus.ts` 或 lobby 转换策略 | 在 `NavigationBar` 和 `BottomTabBar` 分别硬编码 | active 规则是否统一；桌面/移动是否一致。 |
| 新增体育列表/详情行为 | `modules/match/_hooks/_logic/_utils` 或 `detail/list/sidebar` 对应目录 | 跨模块导入另一个模块 `_` 私有目录 | 是否保持 market/specifier 标准化；是否兼容 WS 缓存更新。 |
| 新增全局副作用 | `AppInitializer` 下游 hook 或相关 store | 放在任意页面 `useEffect` 中 | 是否只应客户端运行；是否有清理函数；是否会重复执行。 |
| 新增共享 UI | 先查 `src/components`；确需新增则放组件目录并提供清晰 props | 业务模块内复制已有 Button/Input/Modal | 是否使用 token、`cn()`、可访问性属性、loading/disabled 语义。 |
| 新增状态 | 服务端数据进 React Query；跨页面 UI 状态进 `src/stores`；模块私有状态进 `modules/*/stores` | 把所有状态都塞进全局 store | 是否需要持久化；是否需要非 React 场景 `getState()`；是否会造成重复请求。 |

建议在写任何 patch 前先用以下顺序定位：第一，按 URL 找 `src/app/[locale]` 下对应 `page.tsx` 或 `layout.tsx`；第二，查看该路由导入的 `src/modules` 页面入口；第三，查看模块内 `_hooks/_logic/_utils/_constants/stores` 是否已有可复用逻辑；第四，查看 `src/api/handlers` 是否已有接口；第五，查看 `src/components` 是否已有 UI 原语。这样可以最大程度贴合当前仓库“薄路由、厚模块、统一接口、共享 UI、状态分层”的开发习惯。

## 七、随附索引文件说明

我已额外生成 `generated_frontend_index.md`，其中包含自动提取的 App Router 路由表、API handler 导出表、模块体量表与共享组件目录表。该文件适合在后续开发中作为快速检索清单使用；本报告则对其中的重点路径进行了业务化归纳。

## References

[1]: match-pc-test1/package.json "package.json：依赖、脚本与包管理配置"
[2]: match-pc-test1/AGENTS.md "AGENTS.md：项目目录结构、模块私有约定与核心编码规范"
[3]: match-pc-test1/.agent/rules/frontend.md "frontend.md：前端架构、状态管理、布局层级、路由与 i18n 规则"
[4]: match-pc-test1/src/app/[locale]/layout.tsx "LocaleLayout：next-intl、AppShell、NavigationBar、DialogProvider、TimezoneSynchronizer"
[5]: match-pc-test1/src/app/layout.tsx "RootLayout：全局 CSS、字体、RootProviders、Toast 与 DOM 容器"
[6]: match-pc-test1/src/app/[locale]/(main)/main-shell.tsx "MainShell：侧边栏 padding、BottomTabBar、LanguageModal"
[7]: match-pc-test1/next.config.ts "next.config.ts：Next Intl、redirects、security headers、Serwist、Sentry"
[8]: match-pc-test1/src/app/[locale]/(main)/account/account-layout-client.tsx "AccountLayoutClient：认证守卫、KYC 守卫、AccountSidebar 与 RightAside"
[9]: match-pc-test1/src/modules/match/sidebar/sidebar.tsx "Sports Sidebar：路由参数、breadcrumb 回填、Top/All Sports 渲染"
[10]: match-pc-test1/src/modules/match/detail/layout.tsx "MatchDetail：查询、缓存合并、WS observer、Statscore 与市场渲染"
[11]: match-pc-test1/src/modules/home/_constants/nav-menus.ts "nav-menus：固定导航、casino lobby 动态菜单与 active 策略"
[12]: match-pc-test1/src/constants/account-routes.ts "ACCOUNT_ROUTES：账户菜单、路径、KYC 与分组配置"
[13]: match-pc-test1/src/components/button/button.tsx "Button：CVA variant、loading、disabled 与 cn 组合"
[14]: match-pc-test1/src/utils/common.ts "common.ts：cn 与 tailwind-merge 项目 token 扩展"
[15]: match-pc-test1/src/api/client.ts "API client：fetcher、headers、鉴权、错误处理与 token 轮换"
[16]: match-pc-test1/src/api/handlers/match.ts "match handler：GetMatchInterface 与 market 标准化"
[17]: match-pc-test1/src/components/tanstack-provider/tanstack-provider.tsx "TanstackProvider：QueryClient 默认策略与错误日志"
[18]: match-pc-test1/src/stores/session-store.ts "session-store：登录态恢复、profile 刷新、token 工具函数"
[19]: match-pc-test1/src/modules/home/_components/app-initializer.tsx "AppInitializer：全局客户端副作用、WS/SSE、session、wallet 同步"

# match-pc 业务导向索引数据

## 功能索引

| 功能 | 业务域 | 路由 | 模块 | 关键组件 | 取数接口 | 取数逻辑 |
|---|---|---|---|---|---|---|
| 体育首页/热门赛事 | sports_match | /[locale]/sports | modules/home/home-page.tsx; modules/home/sports-page.tsx; modules/match/home/hot-matches | BannerCarousel; MatchFilter; HotMatches; MatchListBase | GetHotMatchesInterface; getBanners; useKycTips | React Query + region/locale queryKey; desktop/mobile offset |
| 滚球赛事 | sports_match | /[locale]/sports-live | modules/home/live-page.tsx; modules/match/home/live-matches | LiveMatches; MatchListBase | GetHotMatchesInterface 或 live list handler; useGameSubscription | 列表 query + WebSocket 赔率/状态更新 |
| 按运动赛事列表 | sports_match | /[locale]/sports/[sport_id] | modules/match/list; modules/match/sidebar | MatchListContent; TournamentShell; SportItem; Sidebar | GetMenuSportsInterface; GetTopSportsInterface; GetBreadcrumbInterface; SearchMatchesInterface | 侧边栏树 store + breadcrumb 回填 + React Query 列表 |
| 联赛赛事/冠军盘 | sports_match | /[locale]/leagues/[tournament_id]; /outright | modules/match/list; modules/match/outright | TournamentShell; OutrightContent; BetItem | GetTournamentMarketsInterface; GetOutrightMarketsInterface; GetBreadcrumbInterface | tournament_id params + UOF markets |
| 比赛详情与盘口 | sports_match | /[locale]/matches/[match_id] | modules/match/detail; modules/match/_components; modules/match/_logic | MatchDetail; Card; CardCompact; Filters; Chips; BetItem; StatscoreWidget | GetMatchInterface; GetMarketTabsInterface; GetStatscoreEventIdInterface | React Query match-detail + mergeMatchData + WS observers + market filter |
| 赛事资料/分析 | sports_match | /[locale]/test; match-info components | modules/match-info/football; modules/match-info/basketball | MatchDetailTabs; MatchHistoricalStat; MatchLiveWrapper; StatscoreWidget | match-football handlers; match-basketball handlers | sportFetcher 获取足球/篮球分析、阵容、趋势 |
| 投注单购物车 | bet_slip | 全局抽屉/右栏 | modules/bet-slip/cart; modules/bet-slip/slip; modules/bet-slip/stores | BetSlipPanel; BetSlipDrawer; SingleStakeCard; ParlayFooter; PlaceBetButton | GetCartInterface; PutCartItemInterface; CreateOrderInterface; PostLocalCartInterface | Zustand slices + query/cache sync + order result handler |
| 赌场大厅 | casino | /[locale]/casino/[lobbyId] | modules/casino/home; modules/casino/_components | CasinoSidebar; GameSection; GameCard; KeywordFilter; MerchantFilter; TagsFilter | GetCasinoGameLobbiesInterface; GetCasinoGamesInterface; GetCasinoGameTagsInterface; GetCasinoGameMerchantsInterface | lobby_id + filters + React Query |
| 赌场游戏启动 | casino | /[locale]/casino/game/[gameCode] | modules/casino/game/game-detail-page.tsx | GameDetailPage | LaunchGameInterface | 外部游戏 iframe/跳转 + game message hook |
| 促销活动 | marketing | /[locale]/sports/promotions; /casino/promotions | modules/marketing/promotion/list; detail; first-deposit-bonus | PromotionCard; PromotionsHeader; HeroSection; TermsSection | GetPromotionsInterface; GetActivePromotionInterface; ValidatePromoCodeInterface | 静态活动数据 + API 状态/优惠码校验 |
| 充值 | account_balance | /[locale]/account/deposit | modules/balance/deposit; app account/deposit-page-client.tsx | Deposit; PromoCodeInput; PromoValidationResult; AccountPageShell | CreateDepositInterface; GetDepositInterface; GetFrontFaqListInterface | React Query FAQ + deposit polling hook |
| 提现 | account_balance | /[locale]/account/withdraw | modules/balance/withdraw; app account/withdraw-page-client.tsx | WithdrawForm; FundAccount; AddAccountModal; EnterPasswordModal | CreateWithdrawInterface; GetWithdrawInterface; GetTransferInstrumentTypeInterface; GetListTransferInstrumentInterface | withdraw store + transfer instrument hooks + polling |
| KYC | account_user_center | /[locale]/account/kyc | modules/user/kyc; app account/kyc-page-client.tsx | KycForm; KycStepChip; KycVerifyResult | CreateKycInterface; GetKycEnabledInterface; GetWebKycUrl | AccountLayout KYC guard + schema validation |
| 账户菜单/权限壳 | account_user_center | /[locale]/account/* | modules/user-center/_components; constants/account-routes.ts | AccountPageShell; AccountSidebar; AccountMenuClient | GetProfileInterface; CheckLoginInterface | session-store + ACCOUNT_ROUTES kycRequired + i18n navigation |
| 交易/投注历史 | transaction | /[locale]/account/transactions | modules/transaction/transactions; betHistory; balance; transferOrder | TransactionsShell; TransactionsPage; BetHistoryList; BalanceList | GetTransactionsListPageInterface; GetBalanceListPageInterface; GetSportReportInterface; GetCasinoBetHistoryInterface | URL params filters + page/scroll pagination hooks |
| 通知/公告 | account_user_center | /[locale]/account/notifications; /announcements | modules/user-center/notification | NotificationCard; ContentContainer; EmptyState; Footer | GetSystemMessagesInterface; GetAnnouncementsInterface; ReadSystemMessagesInterface | unread hook + paginated list + read/delete mutations |
| 安全中心 | account_user_center | /[locale]/account/security | modules/security-center | PasswordsForms; NewPasswordInput | GetUserPasswordCheckInterface; SetUserPasswordInterface; SetWalletPasswordInterface | React Hook Form/Zod + account shell |
| FAQ/客服 | account_user_center | /[locale]/account/faq; /support | modules/user-center/faq; support | FAQItem; FAQAccordionItem; LiveChat; Online; Vip | GetFrontFaqListInterface; GetSupportPhoneInterface; GetVipSupportListInterface | userFetcher + i18n content |
| 登录/短信 | auth | /[locale]/signin; login modal | modules/user/auth | Signin; PhoneForm; H5Signin; OutlineInput | LoginInterface; SendSmsCodeInterface; CheckNewUserInterface | useSigninForm/usePhoneForm + session-store signIn reload |

## 模块索引

| 模块 | 业务名 | 职责 | 路径 | TSX | TS | 内部分层 | 关联接口域 |
|---|---|---|---|---:|---:|---|---|
| `balance` | 资金充提 | 充值、提现、提现账户、轮询、钱包密码校验 | `src/modules/balance` | 9 | 10 | withdraw(13), deposit(6) | deposit, promotion, transfer-instrument, withdraw |
| `bet-slip` | 投注单 | 选项购物车、单关/串关、投注提交、订单结果、ticket | `src/modules/bet-slip` | 32 | 28 | cart(20), stores(11), ticket(10), slip(7), _components(5), _hooks(2), _logic(2), (root)(1), _constants(1), _utils(1) | cart, match, order |
| `casino` | 赌场 | 游戏 lobby、游戏卡片、标签/商户筛选、游戏启动详情 | `src/modules/casino` | 10 | 3 | home(6), _components(3), _constants(2), game(2) | casino |
| `docs` | 文档页 | 法务文档、体育规则 | `src/modules/docs` | 2 | 0 | legal(1), sports-rules(1) |  |
| `home` | 首页/全局壳层 | 主导航、移动底栏、App 初始化、体育首页容器 | `src/modules/home` | 13 | 5 | _components(10), (root)(3), _constants(2), _logic(2), _hooks(1) | casino, user-kyc |
| `marketing` | 营销活动 | 促销列表、首充活动详情、活动说明 | `src/modules/marketing` | 11 | 4 | promotion(15) | promotion |
| `match` | 体育赛事与盘口 | 赛事列表、比赛详情、赔率按钮、market/specifier 过滤、体育侧边栏 | `src/modules/match` | 41 | 36 | _components(15), _hooks(12), home(11), sidebar(10), detail(8), list(6), _logic(5), _constants(4), _utils(4), outright(2) | match, matches, menu, statscore, tournament |
| `match-info` | 赛事资料与分析 | 足球/篮球详情分析、阵容、历史战绩、Statscore/趋势组件 | `src/modules/match-info` | 106 | 10 | football(55), basketball(33), _components(12), components(12), _constants(2), services(2) | match-basketball, match-football |
| `security-center` | 安全中心 | 登录密码/资金密码等安全表单 | `src/modules/security-center` | 3 | 0 | _components(2), (root)(1) | user |
| `transaction` | 交易与投注历史 | 余额列表、交易流水、投注历史、转账订单 | `src/modules/transaction` | 26 | 16 | betHistory(11), transactions(7), _hooks(6), balance(5), _components(4), _constants(3), transferOrder(3), (root)(2), _utils(1) | casino, transaction, transaction-bethistory |
| `user` | 用户认证与 KYC | 登录/短信、手机号表单、KYC 表单与结果 | `src/modules/user` | 14 | 5 | auth(13), kyc(6) | passport, user-kyc |
| `user-center` | 账户中心 | 账户页面壳、菜单、FAQ、通知、客服、责任博彩设置 | `src/modules/user-center` | 28 | 11 | health-setting(12), notification(10), support(6), faq(5), _components(2), (root)(1), _constants(1), _types(1), affiliate(1) | faq, health-setting, notification, support |

## 页面路由索引

| 业务域 | 路由 | 文件 | 页面角色 | 模块导入 | API 导入 | 组件导入 |
|---|---|---|---|---|---|---|
| casino | `/[locale]/casino/[lobbyId]` | `src/app/[locale]/(main)/(casino)/casino/[lobbyId]/page.tsx` | metadata/params + module mount | @/modules/casino/home/casino-home | - | - |
| casino | `/[locale]/casino/game/[gameCode]` | `src/app/[locale]/(main)/(casino)/casino/game/[gameCode]/page.tsx` | metadata/params + module mount | @/modules/casino/game/game-detail-page | @/api/handlers/casino | - |
| casino | `/[locale]/casino/game/callback` | `src/app/[locale]/(main)/(casino)/casino/game/callback/page.tsx` | thin route / redirect / simple view | - | - | @/components/loading/loading |
| casino | `/[locale]/casino` | `src/app/[locale]/(main)/(casino)/casino/page.tsx` | thin route / redirect / simple view | - | @/api/handlers/casino | - |
| casino | `/[locale]/casino/promotions/[slug]` | `src/app/[locale]/(main)/(casino)/casino/promotions/[slug]/page.tsx` | thin route / redirect / simple view | - | - | - |
| casino | `/[locale]/casino/promotions` | `src/app/[locale]/(main)/(casino)/casino/promotions/page.tsx` | metadata/params + module mount | @/modules/marketing/promotion/list | - | - |
| sports_match | `/[locale]/leagues/[tournament_id]/outright` | `src/app/[locale]/(main)/(sports)/leagues/[tournament_id]/outright/page.tsx` | metadata/params + module mount | @/modules/match/outright/outright-content | @/api/handlers/matches | - |
| sports_match | `/[locale]/leagues/[tournament_id]` | `src/app/[locale]/(main)/(sports)/leagues/[tournament_id]/page.tsx` | metadata/params + module mount | @/modules/match/list/match-list-content | @/api/handlers/matches | - |
| sports_match | `/[locale]/matches/[match_id]` | `src/app/[locale]/(main)/(sports)/matches/[match_id]/page.tsx` | metadata/params + module mount | @/modules/match/detail | @/api/handlers/match | - |
| sports_match | `/[locale]/sports/[sport_id]` | `src/app/[locale]/(main)/(sports)/sports/[sport_id]/page.tsx` | metadata/params + module mount | @/modules/match/list | @/api/handlers/matches | - |
| sports_match | `/[locale]/sports/live` | `src/app/[locale]/(main)/(sports)/sports/live/page.tsx` | thin route / redirect / simple view | - | @/api/models/match | - |
| sports_match | `/[locale]/sports` | `src/app/[locale]/(main)/(sports)/sports/page.tsx` | metadata/params + module mount | @/modules/home/home-page | - | - |
| sports_match | `/[locale]/sports/promotions/[slug]` | `src/app/[locale]/(main)/(sports)/sports/promotions/[slug]/page.tsx` | thin route / redirect / simple view | - | - | - |
| sports_match | `/[locale]/sports/promotions` | `src/app/[locale]/(main)/(sports)/sports/promotions/page.tsx` | metadata/params + module mount | @/modules/marketing/promotion/list | - | - |
| sports_match | `/[locale]/sports/rules` | `src/app/[locale]/(main)/(sports)/sports/rules/page.tsx` | metadata/params + module mount | @/modules/docs/sports-rules/sports-rules-page | - | - |
| sports_match | `/[locale]/sports-live` | `src/app/[locale]/(main)/(sports)/sports-live/page.tsx` | metadata/params + module mount | @/modules/home/live-page | - | - |
| account_user_center | `/[locale]/account/affiliate` | `src/app/[locale]/(main)/account/affiliate/page.tsx` | metadata/params + module mount | @/modules/user-center; @/modules/user-center/affiliate/affiliate-faq | - | - |
| account_user_center | `/[locale]/account/announcements` | `src/app/[locale]/(main)/account/announcements/page.tsx` | metadata/params + module mount | @/modules/user-center; @/modules/user-center/notification/home | - | - |
| account_balance | `/[locale]/account/deposit` | `src/app/[locale]/(main)/account/deposit/page.tsx` | thin route / redirect / simple view | - | - | - |
| account_user_center | `/[locale]/account/faq` | `src/app/[locale]/(main)/account/faq/page.tsx` | metadata/params + module mount | @/modules/user-center; @/modules/user-center/faq | - | - |
| account_user_center | `/[locale]/account/gambling-games` | `src/app/[locale]/(main)/account/gambling-games/page.tsx` | metadata/params + module mount | @/modules/user-center; @/modules/user-center/health-setting | - | - |
| account_user_center | `/[locale]/account/kyc` | `src/app/[locale]/(main)/account/kyc/page.tsx` | thin route / redirect / simple view | - | - | - |
| account_user_center | `/[locale]/account/notifications` | `src/app/[locale]/(main)/account/notifications/page.tsx` | metadata/params + module mount | @/modules/user-center; @/modules/user-center/notification/home | - | - |
| account_user_center | `/[locale]/account` | `src/app/[locale]/(main)/account/page.tsx` | thin route / redirect / simple view | - | - | - |
| account_user_center | `/[locale]/account/security` | `src/app/[locale]/(main)/account/security/page.tsx` | metadata/params + module mount | @/modules/security-center/security-center; @/modules/user-center | - | - |
| account_user_center | `/[locale]/account/settings` | `src/app/[locale]/(main)/account/settings/page.tsx` | metadata/params + module mount | @/modules/user-center | - | - |
| account_user_center | `/[locale]/account/support` | `src/app/[locale]/(main)/account/support/page.tsx` | metadata/params + module mount | @/modules/user-center; @/modules/user-center/support | - | - |
| account_user_center | `/[locale]/account/transactions` | `src/app/[locale]/(main)/account/transactions/page.tsx` | metadata/params + module mount | @/modules/transaction; @/modules/user-center | - | - |
| account_balance | `/[locale]/account/withdraw` | `src/app/[locale]/(main)/account/withdraw/page.tsx` | thin route / redirect / simple view | - | - | - |
| account_user_center | `/[locale]/legal/aml-kyc` | `src/app/[locale]/(main)/legal/aml-kyc/page.tsx` | metadata/params + module mount | @/modules/docs/legal/legal-doc-page | - | - |
| docs_legal | `/[locale]/legal/privacy` | `src/app/[locale]/(main)/legal/privacy/page.tsx` | metadata/params + module mount | @/modules/docs/legal/legal-doc-page | - | - |
| docs_legal | `/[locale]/legal/responsible-gaming` | `src/app/[locale]/(main)/legal/responsible-gaming/page.tsx` | metadata/params + module mount | @/modules/docs/legal/legal-doc-page | - | - |
| docs_legal | `/[locale]/legal/terms` | `src/app/[locale]/(main)/legal/terms/page.tsx` | metadata/params + module mount | @/modules/docs/legal/legal-doc-page | - | - |
| platform_shell | `/[locale]` | `src/app/[locale]/page.tsx` | thin route / redirect / simple view | - | - | - |
| auth | `/[locale]/signin` | `src/app/[locale]/signin/page.tsx` | metadata/params + module mount | @/modules/user/auth/h5-signin | - | - |
| sports_match | `/[locale]/test` | `src/app/[locale]/test/page.tsx` | metadata/params + module mount | @/modules/match-info/basketball/detail/detail; @/modules/match-info/football/detail/detail | - | - |

## API Handler 索引

| Handler | 文件 | Fetcher | 导出 Interface | Endpoint 线索 |
|---|---|---|---|---|
| `analytics` | `src/api/handlers/analytics.ts` | userFetcher | `ReportAnalyticsInterface` | `/v1/ads/track` |
| `app` | `src/api/handlers/app.ts` | uofFetcher | `GetMatchStatusInterface` | `/v1/static/match-status` |
| `cart` | `src/api/handlers/cart.ts` | uofFetcher | `GetCartInterface`, `GetSlipSettingsInterface`, `PutCartItemInterface`, `UpdateSlipSettingsInterface` | `/v1/mts/cart`, `/v1/mts/cart/setting` |
| `casino` | `src/api/handlers/casino.ts` | gameFetcher | `GetCasinoGameLobbiesInterface`, `GetCasinoGameMerchantsInterface`, `GetCasinoGameTagsInterface`, `GetCasinoGameTypesInterface`, `GetCasinoGamesInterface`, `LaunchGameInterface` | `/v1/games/launch`, `/v1/oc/game/list`, `/v1/oc/game/lobby`, `/v1/oc/game/merchant`, `/v1/oc/game/tag`, `/v1/oc/game/type` |
| `currency` | `src/api/handlers/currency.ts` | userFetcher | `GetListCurrencyInterface` | `/v1/currency` |
| `deposit` | `src/api/handlers/deposit.ts` | paymentFetcher | `CreateDepositInterface`, `GetDepositInterface` | `/v1/payin/$`, `/v1/payin/order` |
| `faq` | `src/api/handlers/faq.ts` | userFetcher | `GetFrontFaqListInterface` | `/v1/faq` |
| `health-setting` | `src/api/handlers/health-setting.ts` | userFetcher | `GetRGConfigInterface`, `SetDepositLimitInterface`, `SetLossLimitInterface`, `SetRestTimeInterface` | `/v1/rg/config`, `/v1/rg/deposit/limit`, `/v1/rg/loss/limit`, `/v1/rg/rest/time` |
| `match-basketball` | `src/api/handlers/match-basketball.ts` | sportFetcher | - | `/v1/basketball/match/$`, `/v2/basketball/match/$` |
| `match-football` | `src/api/handlers/match-football.ts` | sportFetcher | - | `/v1/football/match/$` |
| `match` | `src/api/handlers/match.ts` | uofFetcher | `GetMatchInterface`, `PostLocalCartInterface` | `/v1/match/$`, `/v1/match/market/specifier/status/check` |
| `matches` | `src/api/handlers/matches.ts` | uofFetcher | `GetBreadcrumbInterface`, `GetHotMatchesInterface`, `GetMarketChipInterface`, `GetMarketTabsInterface`, `PostMatchRowBatchCountInterface`, `SearchMatchesInterface` | `/v1/match/hot`, `/v1/match/market/chip`, `/v1/match/market/tab`, `/v1/match/row/batch/count`, `/v1/match/search`, `/v1/menu/breadcrumb` |
| `menu` | `src/api/handlers/menu.ts` | uofFetcher | `GetMenuCategoriesInterface`, `GetMenuHotTournamentsInterface`, `GetMenuSportsInterface`, `GetMenuTournamentsInterface`, `GetTopSportsInterface` | `/v1/menu/category`, `/v1/menu/hot-tournament`, `/v1/menu/sports`, `/v1/menu/sports/top`, `/v1/menu/tournament` |
| `merchant` | `src/api/handlers/merchant.ts` | userFetcher | `GetMerchantAggregationLimitRangeInterface` | `/v1/currency/limit` |
| `notification` | `src/api/handlers/notification.ts` | uofFetcher | `DeleteAllSystemMessagesInterface`, `DeleteSystemMessagesInterface`, `GetAnnouncementsInterface`, `GetSystemMessagesInterface`, `ReadAllSystemMessagesInterface`, `ReadSystemMessagesInterface` | `/v1/users/message`, `/v1/users/message/$`, `/v1/users/message/category/$`, `/v1/users/message/status`, `/v1/users/message/status/$` |
| `order` | `src/api/handlers/order.ts` | uofFetcher | `CreateOrderInterface`, `GetOrderListInterface` | `/v1/mts/order` |
| `passport` | `src/api/handlers/passport.ts` | userFetcher | `CheckLoginInterface`, `CheckNewUserInterface`, `LoginInterface`, `LogoutInterface`, `SendSmsCodeInterface` | `/v1/check/account`, `/v1/check/login`, `/v1/login`, `/v1/sms/code` |
| `promotion` | `src/api/handlers/promotion.ts` | paymentFetcher, userFetcher | `GetActivePromotionInterface`, `GetFirstRechargeDefaultStatusInterface`, `GetFirstRechargeStatusInterface`, `GetPromotionsInterface`, `ValidatePromoCodeInterface` | `/v1/first-recharge/default-status`, `/v1/first-recharge/status`, `/v1/promo/active`, `/v1/promo/list` |
| `statscore` | `src/api/handlers/statscore.ts` | uofFetcher | `GetStatscoreEventIdInterface` | `/v1/ls/livescorepro` |
| `support` | `src/api/handlers/support.ts` | uofFetcher | `GetSupportPhoneInterface`, `GetVipSupportListInterface` | `/v1/customer/support/tel`, `/v1/customer/support/vip` |
| `tournament` | `src/api/handlers/tournament.ts` | uofFetcher | `GetOutrightMarketsInterface`, `GetTournamentMarketsInterface` | `/v1/outright`, `/v1/season/market` |
| `transaction-bethistory` | `src/api/handlers/transaction-bethistory.ts` | userFetcher | `GetCasinoBetHistoryInterface`, `GetGameReportInterface`, `GetSportReportInterface` | `/v1/user/casino/report`, `/v1/user/game/report`, `/v1/user/sport/report` |
| `transaction` | `src/api/handlers/transaction.ts` | userFetcher | `GetBalanceListInterface`, `GetBalanceListPageInterface`, `GetMainEfficientBalanceInterface`, `GetTotalBetWinInterface`, `GetTransactionsListInterface`, `GetTransactionsListPageInterface`, `GetTransferOrderListInterface`, `PostBonusWithdrawInterface` | `/v1/account/bonus/list`, `/v1/account/total/betwin`, `/v1/account/transaction/history`, `/v1/account/transaction/order`, `/v1/bonus/withdraw`, `/v1/main/efficient/balance` |
| `transfer-instrument` | `src/api/handlers/transfer-instrument.ts` | userFetcher | `CreateTransferInstrumentInterface`, `DeleteTransferInstrumentInterface`, `GetListTransferInstrumentInterface`, `GetTransferInstrumentTypeInterface` | `/v1/bank/account`, `/v1/bank/account/type` |
| `user-kyc` | `src/api/handlers/user-kyc.ts` | userFetcher | `CreateKycInterface`, `GetKycEnabledInterface`, `GetKycTipsInterface` | `/v1/check/kyc/enabled`, `/v1/idnumber`, `/v1/kyc`, `/v1/user/kyc/tips` |
| `user` | `src/api/handlers/user.ts` | userFetcher | `GetProfileInterface`, `GetUserPasswordCheckInterface`, `SendUserPasswordCodeInterface`, `SendWalletPasswordCodeInterface`, `SetUserPasswordInterface`, `SetWalletPasswordInterface` | `/v1/password/check`, `/v1/profile`, `/v1/user/password`, `/v1/user/password/sms/code`, `/v1/wallet/password`, `/v1/wallet/password/sms/code` |
| `wallet` | `src/api/handlers/wallet.ts` | userFetcher | `GetBalanceInterface` | `/v1/account/balance` |
| `withdraw` | `src/api/handlers/withdraw.ts` | paymentFetcher | `CreateWithdrawInterface`, `GetWithdrawInterface` | `/v1/payout/$`, `/v1/payout/order` |

## 模块取数调用索引

| 业务域 | 模块 | 文件 | Handler | Interface | Query Key 线索 |
|---|---|---|---|---|---|
| sports_match | `(global/app/components)` | `src/api/loaders/match.ts` | `matches` | PostMatchRowBatchCountInterface | - |
| casino | `(global/app/components)` | `src/app/[locale]/(main)/(casino)/casino/game/[gameCode]/page.tsx` | `casino` | getTranslations } from 'next-intl/server';
import { GetCasinoGamesInterface | - |
| casino | `(global/app/components)` | `src/app/[locale]/(main)/(casino)/casino/page.tsx` | `casino` | useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { GetCasinoGameLobbiesInterface | ['casino' |
| sports_match | `(global/app/components)` | `src/app/[locale]/(main)/(sports)/leagues/[tournament_id]/outright/page.tsx` | `matches` | getLocale, getTranslations } from 'next-intl/server';
import { GetBreadcrumbInterface | - |
| sports_match | `(global/app/components)` | `src/app/[locale]/(main)/(sports)/leagues/[tournament_id]/page.tsx` | `matches` | getLocale, getTranslations } from 'next-intl/server';
import { GetBreadcrumbInterface | - |
| sports_match | `(global/app/components)` | `src/app/[locale]/(main)/(sports)/matches/[match_id]/page.tsx` | `match` | getLocale, getTranslations } from 'next-intl/server';
import { GetMatchInterface | - |
| sports_match | `(global/app/components)` | `src/app/[locale]/(main)/(sports)/sports/[sport_id]/page.tsx` | `matches` | getLocale, getTranslations } from 'next-intl/server';
import { GetBreadcrumbInterface | - |
| account_balance | `(global/app/components)` | `src/app/[locale]/(main)/account/deposit/deposit-page-client.tsx` | `faq` | useQuery } from '@tanstack/react-query';
import { useLocale, useTranslations } from 'next-intl';
import { Accordion } from 'radix-ui';
import { useEffect, useMemo, useState } from 'react';
import { GetFrontFaqListInterface | ['faq' |
| account_balance | `(global/app/components)` | `src/app/[locale]/(main)/account/withdraw/withdraw-page-client.tsx` | `faq` | useQuery } from '@tanstack/react-query';
import Image from 'next/image';
import { useLocale, useTranslations } from 'next-intl';
import { Accordion } from 'radix-ui';
import { useEffect, useMemo, useState } from 'react';
import { GetFrontFaqListInterface | ['faq' |
| casino | `(global/app/components)` | `src/components/footer/components/sitemap/index.tsx` | `casino` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FunctionComponent } from 'react';
import { GetCasinoGameLobbiesInterface, GetCasinoGameTagsInterface | ['casino' |
| platform_shell | `(global/app/components)` | `src/hooks/use-currency-limit.ts` | `merchant` | useQuery } from '@tanstack/react-query';

import { GetMerchantAggregationLimitRangeInterface | generateQueryKey(ModuleKeys.MERCHANT |
| auth | `(global/app/components)` | `src/hooks/use-logout.ts` | `passport` | useMutation } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { LogoutInterface | - |
| platform_shell | `(global/app/components)` | `src/hooks/use-password-setting-check.ts` | `user` | useQuery } from '@tanstack/react-query';
import { GetUserPasswordCheckInterface | passwordSettingCheckKey() |
| platform_shell | `(global/app/components)` | `src/hooks/use-report-analytics.ts` | `analytics` | useMutation } from '@tanstack/react-query';
import { ReportAnalyticsInterface | - |
| sports_match | `(global/app/components)` | `src/hooks/use-sports.ts` | `menu` | create } from 'zustand';
import { persist } from 'zustand/middleware';
import { GetMenuSportsInterface, GetTopSportsInterface | - |
| account_balance | `(global/app/components)` | `src/hooks/use-wallet.ts` | `currency` | create } from 'zustand';
import { GetListCurrencyInterface | - |
| account_balance | `(global/app/components)` | `src/hooks/use-wallet.ts` | `wallet` | GetBalanceInterface | - |
| account_user_center | `(global/app/components)` | `src/mocks/handlers/user-center.handlers.ts` | `notification` | HttpResponse, http } from 'msw';
import { SystemMessageListResponse | - |
| account_balance | `balance` | `src/modules/balance/deposit/_hooks/use-deposit-polling.ts` | `deposit` | useMutation, useQueryClient } from '@tanstack/react-query';
import { useInterval } from 'ahooks';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useRef, useState } from 'react';
import { GetDepositInterface | ['first-recharge' |
| account_balance | `balance` | `src/modules/balance/deposit/home.tsx` | `deposit` | zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useDebounceFn } from 'ahooks';
import { useTranslations } from 'next-intl';
import { FC, useEffect, useState } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import z from 'zod';
import { CreateDepositInterface | ['first-recharge' |
| account_balance | `balance` | `src/modules/balance/deposit/home.tsx` | `promotion` | GetFirstRechargeDefaultStatusInterface, GetFirstRechargeStatusInterface, isFirstRechargeCampaignActive, ValidatePromoCodeInterface | ['first-recharge' |
| account_balance | `balance` | `src/modules/balance/withdraw/_hooks/use-list-transfer-instrument-type.ts` | `transfer-instrument` | useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

import { GetTransferInstrumentTypeInterface | generateQueryKey(ModuleKeys.WITHDRAW |
| account_balance | `balance` | `src/modules/balance/withdraw/_hooks/use-list-transfer-instrument.ts` | `transfer-instrument` | useMutation } from '@tanstack/react-query';
import { GetListTransferInstrumentInterface | - |
| account_balance | `balance` | `src/modules/balance/withdraw/_hooks/use-withdraw-polling.ts` | `withdraw` | useMutation } from '@tanstack/react-query';
import { useInterval } from 'ahooks';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useRef, useState } from 'react';
import { GetWithdrawInterface | - |
| account_balance | `balance` | `src/modules/balance/withdraw/add-account-modal.tsx` | `transfer-instrument` | zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useBoolean } from 'ahooks';
import { useTranslations } from 'next-intl';
import { FC, useEffect, useMemo, useRef } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import z from 'zod';
import { CreateTransferInstrumentInterface | - |
| account_balance | `balance` | `src/modules/balance/withdraw/fund-account.tsx` | `transfer-instrument` | useMutation } from '@tanstack/react-query';
import { useBoolean } from 'ahooks';
import Image from 'next/image';
import { useTranslations } from 'next-intl';
import { FC, useState } from 'react';
import { DeleteTransferInstrumentInterface | - |
| account_balance | `balance` | `src/modules/balance/withdraw/stores/use-withdraw-store.ts` | `transfer-instrument` | create } from 'zustand';
import { GetListTransferInstrumentInterface | - |
| account_balance | `balance` | `src/modules/balance/withdraw/withdraw-form.tsx` | `withdraw` | zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useBoolean } from 'ahooks';
import { useTranslations } from 'next-intl';
import { FC, useEffect, useState } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import z from 'zod';
import { CreateWithdrawInterface | - |
| bet_slip | `bet-slip` | `src/modules/bet-slip/cart/parlay-footer.tsx` | `order` | useMutation } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'motion/react';
import { useTranslations } from 'next-intl';
import { FC } from 'react';
import { useState } from 'react';
import { CreateOrderBody, CreateOrderInterface | - |
| bet_slip | `bet-slip` | `src/modules/bet-slip/cart/single-footer.tsx` | `order` | useMutation } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'motion/react';
import { useTranslations } from 'next-intl';
import { FC } from 'react';
import { CreateOrderBet, CreateOrderBody, CreateOrderInterface | - |
| bet_slip | `bet-slip` | `src/modules/bet-slip/slip/slip-settings.tsx` | `cart` | useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useDebounceFn } from 'ahooks';
import { useTranslations } from 'next-intl';
import { ChangeEvent, FC, RefObject } from 'react';
import { useEffect, useRef, useState } from 'react';
import { GetSlipSettingsInterface, UpdateSlipSettingsInterface | ['cart-settings'] | ['cart-settings'] }); |
| bet_slip | `bet-slip` | `src/modules/bet-slip/stores/internal/lifecycle.ts` | `match` | PostLocalCartInterface, SpecifierStatusCheckItem | - |
| bet_slip | `bet-slip` | `src/modules/bet-slip/stores/slices/sync-slice.ts` | `cart` | GetCartInterface, PutCartItemInterface | - |
| bet_slip | `bet-slip` | `src/modules/bet-slip/ticket/_hooks/use-orders.ts` | `order` | useInfiniteQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { GetOrderListInterface | generateQueryKey(ModuleKeys.ORDER |
| casino | `casino` | `src/modules/casino/_components/game-card.tsx` | `casino` | useLocale, useTranslations } from 'next-intl';
import { FC, memo, useCallback, useState } from 'react';
import { LaunchGameInterface | - |
| casino | `casino` | `src/modules/casino/game/game-detail-page.tsx` | `casino` | useQuery, useQueryClient } from '@tanstack/react-query';
import Image from 'next/image';
import { useSearchParams } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
import { FC, useCallback, useEffect, useRef, useState } from 'react';
import { GetCasinoGamesInterface, LaunchGameInterface | ['casino' |
| casino | `casino` | `src/modules/casino/home/components/merchant-filter.tsx` | `casino` | useQuery } from '@tanstack/react-query';
import { FunctionComponent, useMemo } from 'react';
import { GetCasinoGameMerchantsInterface | ['casino' |
| casino | `casino` | `src/modules/casino/home/components/page-store.tsx` | `casino` | useQueries, useQuery } from '@tanstack/react-query';
import { useDebounce } from 'ahooks';
import { keyBy, uniqBy } from 'lodash-es';
import { useSearchParams } from 'next/navigation';
import {
    ContextType, createContext, Dispatch, FunctionComponent, PropsWithChildren, SetStateAction, useContext, useEffect, useMemo, useState, } from 'react';
import {
    GetCasinoGameLobbiesInterface, GetCasinoGameMerchantsInterface, GetCasinoGamesInterface, GetCasinoGameTagsInterface | ['casino' |
| casino | `home` | `src/modules/home/_components/bottom-tab-bar.tsx` | `casino` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FC, memo, useEffect, useMemo, useState } from 'react';
import { GetCasinoGameLobbiesInterface | ['casino' |
| casino | `home` | `src/modules/home/_components/navigation-bar.tsx` | `casino` | useQuery } from '@tanstack/react-query';
import useEmblaCarousel from 'embla-carousel-react';
import WheelGesturesPlugin from 'embla-carousel-wheel-gestures';
import Image from 'next/image';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FC, FunctionComponent, useEffect, useMemo, useRef, useState } from 'react';
import { GetCasinoGameLobbiesInterface | ['casino' |
| account_user_center | `home` | `src/modules/home/_hooks/use-kyc-tips.ts` | `user-kyc` | useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useEffect } from 'react';
import { GetKycTipsInterface, KycTipKey | - |
| account_balance | `marketing` | `src/modules/marketing/promotion/first-deposit-bonus/_components/hero-section.tsx` | `promotion` | useQuery } from '@tanstack/react-query';
import { motion } from 'motion/react';
import Image from 'next/image';
import { useLocale, useTranslations } from 'next-intl';
import { FunctionComponent } from 'react';
import { GetFirstRechargeDefaultStatusInterface, isFirstRechargeCampaignActive | ['first-recharge' |
| marketing | `marketing` | `src/modules/marketing/promotion/list/index.tsx` | `promotion` | useQuery } from '@tanstack/react-query';
import { useLocale, useTranslations } from 'next-intl';
import { useMemo } from 'react';
import { GetFirstRechargeDefaultStatusInterface, GetPromotionsInterface | ['first-recharge' | ['promotions' |
| sports_match | `match` | `src/modules/match/_hooks/use-breadcrumb.ts` | `matches` | useQuery } from '@tanstack/react-query';
import { GetBreadcrumbInterface | ['breadcrumb' |
| sports_match | `match` | `src/modules/match/_hooks/use-odds-change-observer.ts` | `tournament` | useQueryClient } from '@tanstack/react-query';
import { TournamentMarkets | key }).catch((error) => { |
| sports_match | `match` | `src/modules/match/detail/layout.tsx` | `match` | keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'motion/react';
import { useLocale, useTranslations } from 'next-intl';
import { FC, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { GetMatchInterface | ['market-tabs' | ['statscore-event-id' | matchDetailKey |
| sports_match | `match` | `src/modules/match/detail/layout.tsx` | `matches` | GetMarketTabsInterface | ['market-tabs' | ['statscore-event-id' | matchDetailKey |
| sports_match | `match` | `src/modules/match/detail/layout.tsx` | `statscore` | GetStatscoreEventIdInterface | ['market-tabs' | ['statscore-event-id' | matchDetailKey |
| sports_match | `match` | `src/modules/match/home/hot-matches/layout.tsx` | `matches` | useTranslations } from 'next-intl';
import { FC } from 'react';
import { GetHotMatchesInterface | - |
| sports_match | `match` | `src/modules/match/home/live-matches/layout.tsx` | `matches` | useTranslations } from 'next-intl';
import { FC } from 'react';
import { SearchMatchesInterface | - |
| sports_match | `match` | `src/modules/match/home/match-filters/use-sport-live-counts.ts` | `matches` | useQueries } from '@tanstack/react-query';
import { SearchMatchesInterface | ['sport-live-count' |
| sports_match | `match` | `src/modules/match/list/match-list-content.tsx` | `matches` | useInfiniteQuery } from '@tanstack/react-query';
import { useInViewport, useSize } from 'ahooks';
import { AnimatePresence, motion } from 'motion/react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FC, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { SearchMatchesInterface | - |
| sports_match | `match` | `src/modules/match/outright/outright-content.tsx` | `tournament` | keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FC, useMemo } from 'react';
import { GetOutrightMarketsInterface, TournamentMarkets | key |
| sports_match | `match` | `src/modules/match/sidebar/category-item.tsx` | `menu` | useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FC, useEffect } from 'react';
import { GetMenuHotTournamentsInterface, GetMenuTournamentsInterface | ['menuTournaments' |
| sports_match | `match` | `src/modules/match/sidebar/sidebar.tsx` | `matches` | useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { FC } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { GetBreadcrumbInterface | - |
| sports_match | `match` | `src/modules/match/sidebar/sport-item.tsx` | `menu` | useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FC, memo, useEffect, useState } from 'react';
import { GetMenuCategoriesInterface, GetMenuHotTournamentsInterface | ['menuCategories' | ['menuTournaments' |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/_components/historical/_components/team-battle.tsx` | `match-basketball` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { ComponentProps, FunctionComponent, useState } from 'react';
import { GetBasketballMatchAnalysisVsV2 | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/_components/historical/_components/team-performance.tsx` | `match-basketball` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { ComponentProps, FunctionComponent, useState } from 'react';
import { GetBasketballMatchAnalysisRecentV2 | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/_components/lineup/_components/injured-list.tsx` | `match-basketball` | useTranslations } from 'next-intl';
import { FunctionComponent } from 'react';
import { GetBasketballMatchPlayersById | - |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/_components/lineup/_components/presence-list.tsx` | `match-basketball` | useTranslations } from 'next-intl';
import { FunctionComponent } from 'react';
import { GetBasketballMatchPlayersById | - |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/_components/lineup/lineup.tsx` | `match-basketball` | useQuery } from '@tanstack/react-query';
import Image from 'next/image';
import { useTranslations } from 'next-intl';
import { FunctionComponent, useMemo } from 'react';
import { GetBasketballMatchPlayersById | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/_components/overview/_components/trend.tsx` | `match-basketball` | useQuery } from '@tanstack/react-query';
import { range } from 'lodash-es';
import { ComponentProps, FunctionComponent, useMemo } from 'react';
import { GetBasketballMatchTrendById | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/_components/page-store.tsx` | `match-basketball` | keepPreviousData, QueryObserverResult, useQuery } from '@tanstack/react-query';
import {
    ContextType, createContext, Dispatch, FunctionComponent, PropsWithChildren, SetStateAction, useContext, useEffect, useState, } from 'react';
import { GetBasketballMatchById | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/components/Historical/components/TeamBattle/index.tsx` | `match-basketball` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { ComponentProps, FunctionComponent, useState } from 'react';
import { GetBasketballMatchAnalysisVsV2 | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/components/Historical/components/TeamPerformance/index.tsx` | `match-basketball` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { ComponentProps, FunctionComponent, useState } from 'react';
import { GetBasketballMatchAnalysisRecentV2 | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/components/Lineup/components/InjuredList/index.tsx` | `match-basketball` | useTranslations } from 'next-intl';
import { FunctionComponent } from 'react';
import { GetBasketballMatchPlayersById | - |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/components/Lineup/components/PresenceList/index.tsx` | `match-basketball` | useTranslations } from 'next-intl';
import { FunctionComponent } from 'react';
import { GetBasketballMatchPlayersById | - |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/components/Lineup/index.tsx` | `match-basketball` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FunctionComponent, useMemo } from 'react';
import { GetBasketballMatchPlayersById | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/components/Overview/components/Trend/index.tsx` | `match-basketball` | useQuery } from '@tanstack/react-query';
import { range } from 'lodash-es';
import { ComponentProps, FunctionComponent, useMemo } from 'react';
import { GetBasketballMatchTrendById | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/components/PageStore/index.tsx` | `match-basketball` | keepPreviousData, QueryObserverResult, useQuery } from '@tanstack/react-query';
import {
    ContextType, createContext, Dispatch, FunctionComponent, PropsWithChildren, SetStateAction, useContext, useEffect, useState, } from 'react';
import { GetBasketballMatchById | generateQueryKey(ModuleKeys.MATCH_BASKETBALL |
| sports_match | `match-info` | `src/modules/match-info/basketball/detail/index.tsx` | `match-basketball` | GetBasketballMatchById | - |
| sports_match | `match-info` | `src/modules/match-info/football/detail/_components/historical/_components/team-battle.tsx` | `match-football` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { ComponentProps, FunctionComponent, useState } from 'react';
import { GetFootballMatchAnalysisVsV2 | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/_components/historical/_components/team-performance.tsx` | `match-football` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { ComponentProps, FunctionComponent, useState } from 'react';
import { GetFootballMatchAnalysisRecentV2 | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/_components/lineup1/_components/current-store.tsx` | `match-football` | useQuery } from '@tanstack/react-query';
import { createContext, FunctionComponent, PropsWithChildren, useContext } from 'react';
import { GetFootballMatchLineupById | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/_components/lineup1/_components/substitute-lineup.tsx` | `match-football` | useTranslations } from 'next-intl';
import { FC, FunctionComponent, ReactNode, useMemo } from 'react';
import { GetFootballMatchLineupById | - |
| sports_match | `match-info` | `src/modules/match-info/football/detail/_components/overview1/_components/trend1/trend.tsx` | `match-football` | useQuery } from '@tanstack/react-query';
import { ComponentProps, FunctionComponent, useMemo } from 'react';
import { GetFootballMatchTrendById | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/_components/page-store.tsx` | `match-football` | keepPreviousData, QueryObserverResult, useQuery } from '@tanstack/react-query';
import {
    ContextType, createContext, Dispatch, FunctionComponent, PropsWithChildren, SetStateAction, useContext, useEffect, useState, } from 'react';
import { GetFootballMatchById | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/components/Historical/components/TeamBattle/index.tsx` | `match-football` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { ComponentProps, FunctionComponent, useState } from 'react';
import { GetFootballMatchAnalysisVsV2 | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/components/Historical/components/TeamPerformance/index.tsx` | `match-football` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { ComponentProps, FunctionComponent, useState } from 'react';
import { GetFootballMatchAnalysisRecentV2 | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/components/Lineup/components/CurrentStore/index.tsx` | `match-football` | useQuery } from '@tanstack/react-query';
import { createContext, FunctionComponent, PropsWithChildren, useContext } from 'react';
import { GetFootballMatchLineupById | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/components/Lineup/components/SubstituteLineup/index.tsx` | `match-football` | useTranslations } from 'next-intl';
import { FC, FunctionComponent, ReactNode, useMemo } from 'react';
import { GetFootballMatchLineupById | - |
| sports_match | `match-info` | `src/modules/match-info/football/detail/components/Overview/components/Trend/index.tsx` | `match-football` | useQuery } from '@tanstack/react-query';
import { ComponentProps, FunctionComponent, useMemo } from 'react';
import { GetFootballMatchTrendById | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/components/PageStore/index.tsx` | `match-football` | keepPreviousData, QueryObserverResult, useQuery } from '@tanstack/react-query';
import {
    ContextType, createContext, Dispatch, FunctionComponent, PropsWithChildren, SetStateAction, useContext, useEffect, useState, } from 'react';
import { GetFootballMatchById | generateQueryKey(ModuleKeys.MATCH_FOOTBALL |
| sports_match | `match-info` | `src/modules/match-info/football/detail/index.tsx` | `match-football` | GetFootballMatchById | - |
| account_user_center | `security-center` | `src/modules/security-center/security-center.tsx` | `user` | useTranslations } from 'next-intl';
import { FunctionComponent } from 'react';
import { useEffect, useMemo, useState } from 'react';
import {
    SendUserPasswordCodeInterface, SendWalletPasswordCodeInterface, SetUserPasswordInterface, SetWalletPasswordInterface | - |
| transaction | `transaction` | `src/modules/transaction/_hooks/use-transaction-queries.ts` | `transaction` | useQuery } from '@tanstack/react-query';
import { GetMainEfficientBalanceInterface, GetTotalBetWinInterface | ['transaction' |
| account_balance | `transaction` | `src/modules/transaction/balance/balance-list.tsx` | `transaction` | useQueryClient } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FC, useCallback, useState } from 'react';
import { GetBalanceListPageInterface, PostBonusWithdrawInterface | TransactionQueryKeys.balance.all }); | TransactionQueryKeys.balance.list(currencyId |
| casino | `transaction` | `src/modules/transaction/betHistory/bet-history-filter-row.tsx` | `casino` | useQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useMemo } from 'react';
import { GetCasinoGameMerchantsInterface, GetCasinoGameTypesInterface | ['casino' |
| transaction | `transaction` | `src/modules/transaction/betHistory/bet-history-list.tsx` | `transaction-bethistory` | useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { useTimeZone, useTranslations } from 'next-intl';
import { FC, useCallback, useMemo, useState } from 'react';
import {
    BetHistoryPageParams, GetCasinoBetHistoryInterface, GetGameReportInterface, GetSportReportInterface | getAllQueryKey( | getAllQueryKey(currencyId | getCasinoQueryKey(dateRangeKey | getSportQueryKey( | getSportQueryKey(currencyId |
| transaction | `transaction` | `src/modules/transaction/transactions/transactions-page.tsx` | `transaction` | useTranslations } from 'next-intl';
import { FC } from 'react';
import { GetTransactionsListPageInterface | TransactionQueryKeys.transactions.list(currencyId |
| transaction | `transaction` | `src/modules/transaction/transactions/transactions-scroll.tsx` | `transaction` | useInfiniteQuery } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FC, useMemo } from 'react';
import { GetTransactionsListInterface | [...TransactionQueryKeys.transactions.list(currencyId |
| transaction | `transaction` | `src/modules/transaction/transferOrder/transfer-order.tsx` | `transaction` | useTranslations } from 'next-intl';
import { FC, useCallback, useMemo, useState } from 'react';
import { GetTransferOrderListInterface | ['transfer-order' |
| auth | `user` | `src/modules/user/auth/_hooks/use-phone-form.ts` | `passport` | useMutation } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useEffect, useRef, useState } from 'react';
import { useFormContext } from 'react-hook-form';
import { SendSmsCodeInterface | - |
| auth | `user` | `src/modules/user/auth/_hooks/use-signin-form.ts` | `passport` | zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import z from 'zod';
import { CheckNewUserInterface, LoginInterface, LoginType | - |
| account_user_center | `user` | `src/modules/user/kyc/home.tsx` | `user-kyc` | useTranslations } from 'next-intl';
import { FC, useEffect, useState } from 'react';
import { GetKycEnabledInterface, GetWebKycUrl | - |
| account_user_center | `user` | `src/modules/user/kyc/kyc-form.tsx` | `user-kyc` | zodResolver } from '@hookform/resolvers/zod';
import { useTranslations } from 'next-intl';
import { FC, useMemo } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { CreateKycInterface | - |
| account_user_center | `user-center` | `src/modules/user-center/affiliate/affiliate-faq.tsx` | `faq` | useQuery } from '@tanstack/react-query';
import { useLocale, useTranslations } from 'next-intl';
import { Accordion } from 'radix-ui';
import { SVGProps, useMemo, useState } from 'react';
import { GetFrontFaqListInterface | ['faq' |
| account_user_center | `user-center` | `src/modules/user-center/faq/faq.tsx` | `faq` | useQuery } from '@tanstack/react-query';
import { useLocale, useTranslations } from 'next-intl';
import { Accordion } from 'radix-ui';
import { useDeferredValue, useMemo, useState } from 'react';
import { GetFrontFaqListInterface | ['faq' |
| account_user_center | `user-center` | `src/modules/user-center/health-setting/home.tsx` | `health-setting` | useTranslations } from 'next-intl';
import { FC, useState } from 'react';
import { SetDepositLimitInterface, SetLossLimitInterface, SetRestTimeInterface | - |
| account_user_center | `user-center` | `src/modules/user-center/health-setting/use-health-setting.ts` | `health-setting` | useQuery, useQueryClient } from '@tanstack/react-query';
import { GetRGConfigInterface | healthSettingQueryKey() | healthSettingQueryKey() }); |
| account_user_center | `user-center` | `src/modules/user-center/notification/announcements.tsx` | `notification` | useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FC, useCallback, useEffect, useMemo } from 'react';
import { SystemMessageListResponse | ['announcements'] | ['unread-announcements'] }); |
| account_user_center | `user-center` | `src/modules/user-center/notification/announcements.tsx` | `notification` | DeleteSystemMessagesInterface, GetAnnouncementsInterface, ReadSystemMessagesInterface | ['announcements'] | ['unread-announcements'] }); |
| account_user_center | `user-center` | `src/modules/user-center/notification/footer.tsx` | `notification` | useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FC } from 'react';
import { DeleteAllSystemMessagesInterface, ReadAllSystemMessagesInterface | ['announcements'] }); | ['system-messages'] }); | ['unread-announcements'] }); | ['unread-messages'] }); |
| account_user_center | `user-center` | `src/modules/user-center/notification/normal-messages.tsx` | `notification` | useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslations } from 'next-intl';
import { FC, useCallback, useEffect, useMemo } from 'react';
import { SystemMessageListResponse | ['system-messages' | ['unread-messages'] }); |
| account_user_center | `user-center` | `src/modules/user-center/notification/normal-messages.tsx` | `notification` | DeleteSystemMessagesInterface, GetSystemMessagesInterface, ReadSystemMessagesInterface | ['system-messages' | ['unread-messages'] }); |
| account_user_center | `user-center` | `src/modules/user-center/notification/use-unread-messages.ts` | `notification` | useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { create } from 'zustand';
import { GetAnnouncementsInterface, GetSystemMessagesInterface | ['unread-announcements'] | ['unread-messages' |
| account_user_center | `user-center` | `src/modules/user-center/support/home.tsx` | `support` | useQuery } from '@tanstack/react-query';
import { StaticImageData } from 'next/image';
import Image from 'next/image';
import { useTranslations } from 'next-intl';
import { FC } from 'react';
import { useState } from 'react';
import { GetSupportPhoneInterface | ['support' |
| account_user_center | `user-center` | `src/modules/user-center/support/online.tsx` | `support` | useQuery } from '@tanstack/react-query';
import Image from 'next/image';
import { useTranslations } from 'next-intl';
import { GetSupportPhoneInterface | ['support' |
| account_user_center | `user-center` | `src/modules/user-center/support/support-faq.tsx` | `faq` | useQuery } from '@tanstack/react-query';
import { useLocale, useTranslations } from 'next-intl';
import { Accordion } from 'radix-ui';
import { useMemo, useState } from 'react';
import { GetFrontFaqListInterface | ['faq' |
| account_user_center | `user-center` | `src/modules/user-center/support/vip.tsx` | `support` | useQuery } from '@tanstack/react-query';
import Image from 'next/image';
import { useTranslations } from 'next-intl';
import { GetVipSupportListInterface | ['vipSupportList'] |
| platform_shell | `(global/app/components)` | `src/replay/manager.ts` | `tournament` | FetchOptions, fetcher } from '@/api/client';
import { TournamentMarkets | unknown[]): boolean => |
| platform_shell | `(global/app/components)` | `src/stores/app-info-store.ts` | `app` | transform } from 'lodash-es';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { GetMatchStatusInterface | - |
| auth | `(global/app/components)` | `src/stores/session-store.ts` | `passport` | create } from 'zustand';
/**
 * React Hook mimicking next-auth's useSession
 */
import { useShallow } from 'zustand/react/shallow';
import { CheckLoginInterface | - |
| platform_shell | `(global/app/components)` | `src/stores/session-store.ts` | `user` | GetProfileInterface | - |

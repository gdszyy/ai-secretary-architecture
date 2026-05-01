# 自动索引草稿

## App Router 路由索引

| 路由/职责 | 文件 | 关键导入 |
|---|---|---|
| `/[locale]/casino/[lobbyId]` | `src/app/[locale]/(main)/(casino)/casino/[lobbyId]/page.tsx` | `@/modules/casino/home/casino-home` |
| `/[locale]/casino/game/[gameCode]` | `src/app/[locale]/(main)/(casino)/casino/game/[gameCode]/page.tsx` | `@/api/handlers/casino`<br>`@/modules/casino/game/game-detail-page` |
| `/[locale]/casino/game/callback` | `src/app/[locale]/(main)/(casino)/casino/game/callback/page.tsx` | `@/components/loading/loading` |
| `/[locale]/casino` | `src/app/[locale]/(main)/(casino)/casino/page.tsx` | `@/api/handlers/casino` |
| `/[locale]/casino/promotions/[slug]` | `src/app/[locale]/(main)/(casino)/casino/promotions/[slug]/page.tsx` | - |
| `/[locale]/casino/promotions` | `src/app/[locale]/(main)/(casino)/casino/promotions/page.tsx` | `@/modules/marketing/promotion/list` |
| `/[locale]/(layout)` | `src/app/[locale]/(main)/(casino)/layout.tsx` | - |
| `/[locale]/(layout)` | `src/app/[locale]/(main)/(sports)/layout.tsx` | - |
| `/[locale]/leagues/[tournament_id]/(layout)` | `src/app/[locale]/(main)/(sports)/leagues/[tournament_id]/layout.tsx` | `@/modules/match/list/tournament-shell` |
| `/[locale]/leagues/[tournament_id]/outright` | `src/app/[locale]/(main)/(sports)/leagues/[tournament_id]/outright/page.tsx` | `@/api/handlers/matches`<br>`@/modules/match/outright/outright-content` |
| `/[locale]/leagues/[tournament_id]` | `src/app/[locale]/(main)/(sports)/leagues/[tournament_id]/page.tsx` | `@/api/handlers/matches`<br>`@/modules/match/list/match-list-content` |
| `/[locale]/matches/[match_id]` | `src/app/[locale]/(main)/(sports)/matches/[match_id]/page.tsx` | `@/api/handlers/match`<br>`@/modules/match/detail` |
| `/[locale]/sports/[sport_id]/(layout)` | `src/app/[locale]/(main)/(sports)/sports/[sport_id]/layout.tsx` | `@/modules/match/list` |
| `/[locale]/sports/[sport_id]` | `src/app/[locale]/(main)/(sports)/sports/[sport_id]/page.tsx` | `@/api/handlers/matches`<br>`@/modules/match/list` |
| `/[locale]/sports/live` | `src/app/[locale]/(main)/(sports)/sports/live/page.tsx` | `@/api/models/match` |
| `/[locale]/sports` | `src/app/[locale]/(main)/(sports)/sports/page.tsx` | `@/modules/home/home-page` |
| `/[locale]/sports/promotions/[slug]` | `src/app/[locale]/(main)/(sports)/sports/promotions/[slug]/page.tsx` | - |
| `/[locale]/sports/promotions` | `src/app/[locale]/(main)/(sports)/sports/promotions/page.tsx` | `@/modules/marketing/promotion/list` |
| `/[locale]/sports/rules` | `src/app/[locale]/(main)/(sports)/sports/rules/page.tsx` | `@/modules/docs/sports-rules/sports-rules-page` |
| `/[locale]/sports-live` | `src/app/[locale]/(main)/(sports)/sports-live/page.tsx` | `@/modules/home/live-page` |
| `/[locale]/account/affiliate` | `src/app/[locale]/(main)/account/affiliate/page.tsx` | `@/modules/user-center`<br>`@/modules/user-center/affiliate/affiliate-faq` |
| `/[locale]/account/announcements` | `src/app/[locale]/(main)/account/announcements/page.tsx` | `@/modules/user-center`<br>`@/modules/user-center/notification/home` |
| `/[locale]/account/deposit` | `src/app/[locale]/(main)/account/deposit/page.tsx` | - |
| `/[locale]/account/faq` | `src/app/[locale]/(main)/account/faq/page.tsx` | `@/modules/user-center`<br>`@/modules/user-center/faq` |
| `/[locale]/account/gambling-games` | `src/app/[locale]/(main)/account/gambling-games/page.tsx` | `@/modules/user-center`<br>`@/modules/user-center/health-setting` |
| `/[locale]/account/kyc` | `src/app/[locale]/(main)/account/kyc/page.tsx` | - |
| `/[locale]/account/(layout)` | `src/app/[locale]/(main)/account/layout.tsx` | - |
| `/[locale]/account/notifications` | `src/app/[locale]/(main)/account/notifications/page.tsx` | `@/modules/user-center`<br>`@/modules/user-center/notification/home` |
| `/[locale]/account` | `src/app/[locale]/(main)/account/page.tsx` | - |
| `/[locale]/account/security` | `src/app/[locale]/(main)/account/security/page.tsx` | `@/modules/security-center/security-center`<br>`@/modules/user-center` |
| `/[locale]/account/settings` | `src/app/[locale]/(main)/account/settings/page.tsx` | `@/modules/user-center` |
| `/[locale]/account/support` | `src/app/[locale]/(main)/account/support/page.tsx` | `@/modules/user-center`<br>`@/modules/user-center/support` |
| `/[locale]/account/transactions` | `src/app/[locale]/(main)/account/transactions/page.tsx` | `@/modules/transaction`<br>`@/modules/user-center` |
| `/[locale]/account/withdraw` | `src/app/[locale]/(main)/account/withdraw/page.tsx` | - |
| `/[locale]/(layout)` | `src/app/[locale]/(main)/layout.tsx` | - |
| `/[locale]/legal/aml-kyc` | `src/app/[locale]/(main)/legal/aml-kyc/page.tsx` | `@/modules/docs/legal/legal-doc-page` |
| `/[locale]/legal/(layout)` | `src/app/[locale]/(main)/legal/layout.tsx` | - |
| `/[locale]/legal/privacy` | `src/app/[locale]/(main)/legal/privacy/page.tsx` | `@/modules/docs/legal/legal-doc-page` |
| `/[locale]/legal/responsible-gaming` | `src/app/[locale]/(main)/legal/responsible-gaming/page.tsx` | `@/modules/docs/legal/legal-doc-page` |
| `/[locale]/legal/terms` | `src/app/[locale]/(main)/legal/terms/page.tsx` | `@/modules/docs/legal/legal-doc-page` |
| `/[locale]/(template)` | `src/app/[locale]/(main)/template.tsx` | - |
| `/[locale]/(error)` | `src/app/[locale]/error.tsx` | - |
| `/[locale]/(layout)` | `src/app/[locale]/layout.tsx` | `@/components/dialog/dialog-provider`<br>`@/components/timezone-synchronizer`<br>`@/constants`<br>`@/modules/bet-slip/_components/cart-cleanup-listener`<br>`@/modules/home/_components/app-shell`<br>`@/modules/home/_components/navigation-bar` |
| `/[locale]/(loading)` | `src/app/[locale]/loading.tsx` | - |
| `/[locale]/(not-found)` | `src/app/[locale]/not-found.tsx` | - |
| `/[locale]` | `src/app/[locale]/page.tsx` | - |
| `/[locale]/signin/(layout)` | `src/app/[locale]/signin/layout.tsx` | - |
| `/[locale]/signin` | `src/app/[locale]/signin/page.tsx` | `@/modules/user/auth/h5-signin` |
| `/[locale]/test` | `src/app/[locale]/test/page.tsx` | `@/modules/match-info/basketball/detail/detail`<br>`@/modules/match-info/football/detail/detail` |
| `/(global-error)` | `src/app/global-error.tsx` | - |
| `/health/(route-handler)` | `src/app/health/route.ts` | - |
| `/(layout)` | `src/app/layout.tsx` | `@/components/providers/root-providers`<br>`@/components/toast/toast-provider`<br>`@/constants` |

## API Handler 索引

| 业务域 | 文件 | 导出接口/函数 |
|---|---|---|
| `analytics` | `src/api/handlers/analytics.ts` | `ReportAnalyticsInterface` |
| `app` | `src/api/handlers/app.ts` | `GetMatchStatusInterface` |
| `cart` | `src/api/handlers/cart.ts` | `GetCartInterface`, `GetSlipSettingsInterface`, `PutCartItemInterface`, `UpdateSlipSettingsInterface` |
| `casino` | `src/api/handlers/casino.ts` | `GetCasinoGameLobbiesInterface`, `GetCasinoGameMerchantsInterface`, `GetCasinoGameTagsInterface`, `GetCasinoGameTypesInterface`, `GetCasinoGamesInterface`, `LaunchGameInterface` |
| `currency` | `src/api/handlers/currency.ts` | `GetListCurrencyInterface` |
| `deposit` | `src/api/handlers/deposit.ts` | `CreateDepositInterface`, `GetDepositInterface` |
| `faq` | `src/api/handlers/faq.ts` | `GetFrontFaqListInterface` |
| `health-setting` | `src/api/handlers/health-setting.ts` | `GetRGConfigInterface`, `SetDepositLimitInterface`, `SetLossLimitInterface`, `SetRestTimeInterface` |
| `match-basketball` | `src/api/handlers/match-basketball.ts` | `GetBasketballMatchAnalysisRecentV2`, `GetBasketballMatchAnalysisVsV2`, `GetBasketballMatchById`, `GetBasketballMatchIndexById`, `GetBasketballMatchPlayersById`, `GetBasketballMatchTrendById` |
| `match-football` | `src/api/handlers/match-football.ts` | `GetFootballMatchAnalysisRecentV2`, `GetFootballMatchAnalysisVsV2`, `GetFootballMatchById`, `GetFootballMatchIndexById`, `GetFootballMatchLineupById`, `GetFootballMatchTrendById` |
| `match` | `src/api/handlers/match.ts` | `GetMatchInterface`, `PostLocalCartInterface` |
| `matches` | `src/api/handlers/matches.ts` | `GetBreadcrumbInterface`, `GetHotMatchesInterface`, `GetMarketChipInterface`, `GetMarketTabsInterface`, `PostMatchRowBatchCountInterface`, `SearchMatchesInterface` |
| `menu` | `src/api/handlers/menu.ts` | `GetMenuCategoriesInterface`, `GetMenuHotTournamentsInterface`, `GetMenuSportsInterface`, `GetMenuTournamentsInterface`, `GetTopSportsInterface` |
| `merchant` | `src/api/handlers/merchant.ts` | `GetMerchantAggregationLimitRangeInterface` |
| `notification` | `src/api/handlers/notification.ts` | `DeleteAllSystemMessagesInterface`, `DeleteSystemMessagesInterface`, `GetAnnouncementsInterface`, `GetSystemMessagesInterface`, `ReadAllSystemMessagesInterface`, `ReadSystemMessagesInterface` |
| `order` | `src/api/handlers/order.ts` | `CreateOrderInterface`, `GetOrderListInterface` |
| `passport` | `src/api/handlers/passport.ts` | `CheckLoginInterface`, `CheckNewUserInterface`, `LoginInterface`, `LogoutInterface`, `SendSmsCodeInterface` |
| `promotion` | `src/api/handlers/promotion.ts` | `GetActivePromotionInterface`, `GetFirstRechargeDefaultStatusInterface`, `GetFirstRechargeStatusInterface`, `GetPromotionsInterface`, `ValidatePromoCodeInterface`, `isFirstRechargeCampaignActive` |
| `statscore` | `src/api/handlers/statscore.ts` | `GetStatscoreEventIdInterface` |
| `support` | `src/api/handlers/support.ts` | `GetSupportPhoneInterface`, `GetVipSupportListInterface` |
| `tournament` | `src/api/handlers/tournament.ts` | `GetOutrightMarketsInterface`, `GetTournamentMarketsInterface` |
| `transaction-bethistory` | `src/api/handlers/transaction-bethistory.ts` | `GetCasinoBetHistoryInterface`, `GetGameReportInterface`, `GetSportReportInterface` |
| `transaction` | `src/api/handlers/transaction.ts` | `GetBalanceListInterface`, `GetBalanceListPageInterface`, `GetMainEfficientBalanceInterface`, `GetTotalBetWinInterface`, `GetTransactionsListInterface`, `GetTransactionsListPageInterface`, `GetTransferOrderListInterface`, `PostBonusWithdrawInterface` |
| `transfer-instrument` | `src/api/handlers/transfer-instrument.ts` | `CreateTransferInstrumentInterface`, `DeleteTransferInstrumentInterface`, `GetListTransferInstrumentInterface`, `GetTransferInstrumentTypeInterface` |
| `user-kyc` | `src/api/handlers/user-kyc.ts` | `CreateKycInterface`, `GetKycEnabledInterface`, `GetKycTipsInterface`, `GetWebKycUrl` |
| `user` | `src/api/handlers/user.ts` | `GetProfileInterface`, `GetUserPasswordCheckInterface`, `SendUserPasswordCodeInterface`, `SendWalletPasswordCodeInterface`, `SetUserPasswordInterface`, `SetWalletPasswordInterface` |
| `wallet` | `src/api/handlers/wallet.ts` | `GetBalanceInterface` |
| `withdraw` | `src/api/handlers/withdraw.ts` | `CreateWithdrawInterface`, `GetWithdrawInterface` |

## Modules 体量索引

| 模块 | TSX 文件数 | TS 文件数 | 目录 |
|---|---:|---:|---|
| `balance` | 9 | 10 | `src/modules/balance` |
| `bet-slip` | 32 | 28 | `src/modules/bet-slip` |
| `casino` | 10 | 3 | `src/modules/casino` |
| `docs` | 2 | 0 | `src/modules/docs` |
| `home` | 13 | 5 | `src/modules/home` |
| `marketing` | 11 | 4 | `src/modules/marketing` |
| `match` | 41 | 36 | `src/modules/match` |
| `match-info` | 106 | 10 | `src/modules/match-info` |
| `security-center` | 3 | 0 | `src/modules/security-center` |
| `transaction` | 26 | 16 | `src/modules/transaction` |
| `user` | 14 | 5 | `src/modules/user` |
| `user-center` | 28 | 11 | `src/modules/user-center` |

## Components 目录索引

| 组件/目录 | 文件数 | 路径 |
|---|---:|---|
| `banner-carousel` | 1 | `src/components/banner-carousel.tsx` |
| `base-modal` | 2 | `src/components/base-modal` |
| `basketball-jersey-icon` | 1 | `src/components/basketball-jersey-icon.tsx` |
| `block-title-1` | 4 | `src/components/block-title-1` |
| `block1` | 3 | `src/components/block1` |
| `border-beam-path` | 1 | `src/components/border-beam-path.tsx` |
| `border-beam-svg` | 1 | `src/components/border-beam-svg.tsx` |
| `border-beam` | 1 | `src/components/border-beam.tsx` |
| `btn-with-countdown` | 1 | `src/components/btn-with-countdown` |
| `button` | 1 | `src/components/button` |
| `card-collapsible` | 3 | `src/components/card-collapsible` |
| `carousel-nav-controls` | 1 | `src/components/carousel-nav-controls.tsx` |
| `cascader` | 1 | `src/components/cascader` |
| `checkbox` | 1 | `src/components/checkbox` |
| `checkbox-filter` | 1 | `src/components/checkbox-filter` |
| `client-only` | 2 | `src/components/client-only` |
| `collapse-icon` | 1 | `src/components/collapse-icon.tsx` |
| `collapsible` | 1 | `src/components/collapsible` |
| `currency-input` | 1 | `src/components/currency-input` |
| `date-range-picker` | 2 | `src/components/date-range-picker` |
| `dialog` | 3 | `src/components/dialog` |
| `drawer` | 1 | `src/components/drawer` |
| `empty` | 2 | `src/components/empty` |
| `football-jersey-icon` | 1 | `src/components/football-jersey-icon.tsx` |
| `footer` | 12 | `src/components/footer` |
| `form-cascader` | 1 | `src/components/form-cascader` |
| `form-checkbox` | 1 | `src/components/form-checkbox` |
| `form-error-message` | 1 | `src/components/form-error-message` |
| `form-input` | 1 | `src/components/form-input` |
| `form-item` | 1 | `src/components/form-item` |
| `form-password` | 1 | `src/components/form-password` |
| `form-select` | 1 | `src/components/form-select` |
| `funs-select-short-cut-list` | 1 | `src/components/funs-select-short-cut-list` |
| `hot-line-icon` | 1 | `src/components/hot-line-icon.tsx` |
| `icon-button` | 1 | `src/components/icon-button.tsx` |
| `icons` | 261 | `src/components/icons` |
| `input` | 1 | `src/components/input` |
| `loading` | 1 | `src/components/loading` |
| `mobile-zoom-lock` | 1 | `src/components/mobile-zoom-lock.tsx` |
| `modal` | 1 | `src/components/modal` |
| `module-error-boundary` | 1 | `src/components/module-error-boundary.tsx` |
| `next-button-small` | 1 | `src/components/next-button-small.tsx` |
| `pagination` | 1 | `src/components/pagination.tsx` |
| `prev-button-small` | 1 | `src/components/prev-button-small.tsx` |
| `progress` | 1 | `src/components/progress.tsx` |
| `providers` | 1 | `src/components/providers` |
| `question-tooltip` | 1 | `src/components/question-tooltip.tsx` |
| `select` | 3 | `src/components/select` |
| `sidebar` | 5 | `src/components/sidebar` |
| `sticky-blur-header` | 1 | `src/components/sticky-blur-header.tsx` |
| `table` | 2 | `src/components/table` |
| `tabs` | 1 | `src/components/tabs` |
| `tanstack-provider` | 1 | `src/components/tanstack-provider` |
| `text-field` | 1 | `src/components/text-field` |
| `theme-provider` | 1 | `src/components/theme-provider` |
| `time-picker` | 4 | `src/components/time-picker` |
| `timezone-synchronizer` | 1 | `src/components/timezone-synchronizer.tsx` |
| `toast` | 4 | `src/components/toast` |
| `tooltip` | 3 | `src/components/tooltip` |
| `ui` | 1 | `src/components/ui` |

# weekly-report-builder/components-restyled/EcosystemHealthMap.tsx 函数索引

> 自动生成于 2026-04-23 | 总行数: 953 | 函数数: 10 | 语言: typescript
> **本文件由 code-indexer 脚本自动生成，严禁手动编辑。**

**巨型函数警告**: 本文件包含 1 个超过 200 行的函数，建议优先通过 `@section` 标记进行内部导航。

## 函数列表

> 定位方式：在源文件中 `grep -n "函数名"` 即可跳转，行号不在此列出（行号随代码变化而失效）。

| 函数名 | 类型 | 签名 | 备注 |
|--------|------|------|------|
| formatNumber | function | `formatNumber(n: number)` |  |
| formatChange | function | `formatChange(v?: number)` |  |
| getChangeColor | function | `getChangeColor(v?: number, inverse = false)` |  |
| EcosystemTooltip | function | `EcosystemTooltip({ tier, metricName, side }: ChartTooltipData)` |  |
| buildChartData | function | `buildChartData(tiers: TierData[])` |  |
| CustomBarLabel | function | `CustomBarLabel({ x = 0, y = 0, width = 0, height = 0, value = 0, side = 'right' }: CustomBarLab)` |  |
| BiDirectionalChart | function | `BiDirectionalChart({ tiers, metricName, label, showWarning, warningThreshold }: BiDirectionalChartP)` |  |
| TierCard | function | `TierCard({ tier, metricName, showChange }: TierCardProps)` |  |
| ConcentrationIndicator | function | `ConcentrationIndicator({ topTier, threshold, metricName }: ConcentrationIndicatorProps)` |  |
| EcosystemHealthMap | function | `EcosystemHealthMap({ data, className = '' }: EcosystemHealthMapProps)` | ⚠️ 巨型函数，见 @section 导航 |

# 已废弃脚本归档

本目录存放因架构重构而废弃的脚本，保留以供历史参考。

| 文件 | 废弃原因 | 废弃日期 |
|------|---------|---------|
| `stale_topic_followup.py` | 旧版"事事追问"逻辑产物。新架构下，常规任务不再追问，仅 `major_decision` / `risk_blocker` 在缺失致命信息时触发极简追问，原脚本的全量扫描+追问模式已不适用。 | 2026-04-20 |
| `topic_reply_tracker.py` | 旧版追问闭环逻辑产物。依赖 `stale_topic_followup.py` 写入的追问消息 ID 进行回复追踪，随上游废弃而一并废弃。 | 2026-04-20 |

> 参见流程洞察 [PI-002](../../.cursor/rules/process_insights/PI-002_topic_extraction_and_inquiry_noise_reduction.md) 了解完整的架构重构背景。

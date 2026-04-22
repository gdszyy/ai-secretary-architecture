# weekly_report_timeline 模块规范

## 模块定位

`docs/weekly_report_timeline/` 目录存放**周报模块进度时间线**功能的完整设计文档，涵盖数据模型、触发机制和 Agent 协作工作流三个维度。

## 核心设计决策

**数据来源优先级**：飞书多维表格周报（`xp-weekly-report` 技能）> 多维表格需求状态 > Meegle 进度 > 群内讨论洞察。

**触发机制**：Agent 驱动的双轨制——Manus 定时任务（每周一 06:00）自动唤醒，飞书 Bot 指令支持按需触发。通过 `multi-agent-hub` 进行任务编排。

**周期定义**：每周 ISO 周标识（如 `2026-16`）为唯一标识，`run_weekly_batch.py` 以此为参数执行。

## 文档清单

| 文件 | 内容 | 状态 |
|------|------|------|
| [`01_data_model_design.md`](../../docs/weekly_report_timeline/01_data_model_design.md) | 多源数据模型扩展、前端组件设计、实施步骤 | ✅ 已定稿 |
| [`02_trigger_design_v1.md`](../../docs/weekly_report_timeline/02_trigger_design_v1.md) | 触发机制初版（定时跑批 + 飞书 Bot 手动触发） | 📦 已归档（被 v2 取代） |
| [`03_agent_driven_trigger_design.md`](../../docs/weekly_report_timeline/03_agent_driven_trigger_design.md) | Agent 驱动触发机制（当前采用方案） | ✅ 已定稿 |

## 关键脚本映射

| 脚本 | 职责 |
|------|------|
| `scripts/run_weekly_batch.py` | 每周批处理入口，接受 `--week YYYY-WW` 参数 |
| `scripts/run_weekly_report.py` | 三源数据整合 + LLM 联合归因 + 写入 dashboard |
| `scripts/extract_weekly_insights.py` | 从飞书群聊提取当周关键话题洞察 |
| `scripts/topic_expiry_archiver.py` | 归档跨周过期话题 |

## 禁止行为

- 禁止修改 `02_trigger_design_v1.md`（已归档，仅供参考）
- 禁止在 `run_weekly_report.py` 中硬编码周标识，必须通过 `--week` 参数传入

# repo-indexer / match-pc

本目录是 `match-pc-test1.zip` 前端包在仓库内的 `/repo-indexer` 专用归档入口，用于以业务导向方式保存源文件、拆解报告、页面/模块/功能/组件/接口索引和结构化索引数据。


## 强制索引访问规则

当任务涉及 **用户体验、功能修改或前端修改** 时，Agent 必须先访问并查询本目录的前端业务索引，再开始方案设计或代码修改。该规则适用于但不限于页面结构调整、交互流程变更、组件样式修改、接口取数调整、表单/弹窗/导航/投注单/账户中心等前端相关改动。

推荐查询顺序为：`repo-indexer/match-pc/INDEX.md` → `repo-indexer/match-pc/business_oriented_index.md` → 按需进入 `repo-indexer/match-pc/frontend_breakdown_report.md`、`repo-indexer/match-pc/generated_frontend_index.md` 或 `repo-indexer/match-pc/data/*.csv`。如果变更影响路由、模块边界、功能归属、关键组件或取数逻辑，必须在同一提交中同步更新这些索引文件。

## 快速入口

| 文件 | 用途 |
|---|---|
| [`README.md`](README.md) | match-pc 前端业务索引总入口与读取路径。 |
| [`business_oriented_index.md`](business_oriented_index.md) | 强化版业务导向索引，按功能、页面、模块、API 和取数调用组织。 |
| [`frontend_breakdown_report.md`](frontend_breakdown_report.md) | 完整前端拆解报告，包含 coding 逻辑与新 patch 融入建议。 |
| [`generated_frontend_index.md`](generated_frontend_index.md) | 自动抽取的完整路由、模块、组件、接口清单。 |
| [`data/`](data/) | CSV/JSON 结构化索引数据，可用于二次分析或导入表格。 |
| [`source/match-pc-test1.zip`](source/match-pc-test1.zip) | 用户上传的原始前端包归档。 |

## 维护约定

后续如果前端包拆解结果发生变化，应优先更新本目录，并同步维护 `.cursor/rules/frontend_match_pc.md` 与根目录 `AGENTS.md` 的链接，保证 repo-indexer 入口、规则入口和全局入口一致。

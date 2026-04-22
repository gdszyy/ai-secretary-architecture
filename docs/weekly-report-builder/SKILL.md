---
name: weekly-report-builder
description: 从零搭建周报网页呈现的交互式构建流程。当用户提供周报文档或数据，并要求构建、生成、设计或搭建周报网页/看板时使用此技能。包含解析拆解、模块提炼、组件选型三个交互阶段。
---

# 周报网页构建器 (Weekly Report Builder)

本技能指导如何通过三个交互式步骤，将用户提供的原始周报文档或数据，逐步转化为结构化的 React/TypeScript 周报网页呈现。

**核心原则：** 这是一个**交互式**的构建过程。在每个阶段结束时，必须向用户展示当前阶段的成果，并等待用户确认或补充后，才能进入下一阶段。

## 阶段 1：解析与拆解 (Analysis & Breakdown)

**目标**：解析输入文档，提取核心业务逻辑，拆解业务模块，并发现框架外洞察。

1. **读取分析框架**：首先读取 `references/analysis_framework.md`，了解预设的 5 大业务模块及评估模式。
2. **执行解析**：运行 `scripts/analysis_engine.py` 对用户提供的文档进行深度解析，提取核心业务定位、商业模式闭环和北极星指标，并将内容映射到预设的业务模块中。引擎会自动识别商业模式类型（广告/订阅/电商/游戏/SaaS/双边市场/内容社区）和业务阶段（种子期→启动期→成长期→扩张期→成熟期），推荐对应的特有模块，并根据阶段矩阵标注各通用模块的适用性（required / lightweight / disabled）。
3. **数据洞察诊断**：在展示结果前，运行 `scripts/data_insight_probe.py` 对文档中的数据进行三层诊断：
   - **口径来源诊断**：检测关键指标的口径缺失、时间窗口模糊、分母不明确、口径不一致四类风险。
   - **北极星因子分解**：识别北极星指标，套用标准分解公式（如 DAU = 新用户 + 回流 + 留存 − 流失），检测各驱动因子的数据完整性，并询问用户补充缺失因子。
   - **跨模块因果链**：检测不同业务模块间的潜在因果关联（如版本发布→留存变化、RTP 异常→收入影响），生成结构化确认问题。
4. **洞察与异常检测**：运行 `scripts/insight_detector.py`。如果发现框架外的新模式、反常识数据或隐性关联，必须单独列出并暂停流程，等待用户决策。
5. **用户交互 (必须执行)**：
   - 运行 `scripts/phase1_interaction.py` 管理交互状态。
   - 向用户展示解析结果（含数据洞察诊断报告），要求用户结合提炼的内容进行补充，完善商业逻辑和业务架构。
   - **特别提醒**：要求用户额外确认里程碑模块的准确性和当前状态，以及数据洞察探针发现的口径风险和缺失因子。
   - 等待用户回复。

## 阶段 2：模块提炼与优先级划分 (Module Extraction & Prioritization)

**目标**：根据第一阶段确认的业务架构，提炼可用的周报呈现模块，并划分优先级。

1. **读取组件规范**：在用户确认第一阶段结果后，读取 `references/component_library.md`，了解首屏模块和其他模块的定义。
2. **提炼模块**：运行 `scripts/module_extractor.py`，提炼首屏模块 (P0) 和其他模块 (P1/P2)。
3. **设计导航**：运行 `scripts/navigation_designer.py`，设计从首屏模块下钻 (Drill-down) 或通过金刚区跳转到其他模块的逻辑。
4. **用户交互 (必须执行)**：
   - 运行 `scripts/phase2_interaction.py` 管理交互状态。
   - 向用户展示提炼出的呈现模块列表及优先级划分，解释每个模块的呈现意图。
   - 要求用户选定最终需要在网页中呈现的模块。
   - 如果用户调整优先级或模块列表，重新触发优先级评分，循环至用户确认。
   - 等待用户回复。

## 阶段 3：组件选型与数据绑定 (Component Selection & Data Binding)

**目标**：为用户选定的模块匹配具体的 UI 组件，明确数据需求和交互逻辑，最终生成网页代码。

1. **匹配组件**：运行 `scripts/component_recommender.py`，为每个选定的模块推荐合适的 UI 组件。
2. **用户交互 (必须执行)**：
   - 运行 `scripts/phase3_confirmation.py` 管理四要素确认流。
   - 针对每个选定的模块，向用户逐一确认以下 4 点：
     1. **数据来源**：该组件取用第一阶段提炼的哪个业务模块的信息？
     2. **呈现方法**：组件内的视觉形态是否符合预期？
     3. **回报内容**：组件内具体需要展示哪些数据字段？
     4. **下钻逻辑**：点击该组件后，跳转关联到哪个详细模块？
   - 处理异常分支（数据来源不明确、呈现方法需调整、下钻逻辑缺失）。
   - 等待用户确认所有组件的细节。
3. **生成代码**：
   - 在用户确认所有细节后，运行 `scripts/code_generator.py`。
   - 该脚本将读取 `templates/dashboard_template.tsx` 作为参考，并根据确认的组件选型、数据绑定和下钻逻辑，生成最终的 React/TypeScript 周报网页代码。
   - 最终输出完整可运行的周报网页单文件（如 `templates/weekly_report_example.tsx` 所示）。
   - 如果用户验收代码时需要修改，支持针对特定组件或样式的精准修改，循环至验收通过。

## 资源文件说明

- `references/analysis_framework.md`: 业务模块分析框架，包含 5 大通用模块、7 种商业模式特有模块（共 22 个特有模块）、业务阶段矩阵（5 阶段 × 5 通用模块适用性）和阶段强制推荐模块。
- `references/component_library.md`: 组件库规范，分为首屏组件（Hero Components）和详情展示组件（Detail Components）两大类，含完整的选型规则和数据绑定规范。
- `templates/dashboard_template.tsx`: 周报仪表盘 React 组件模板，用于最终生成网页代码。
- `templates/weekly_report_example.tsx`: 完整可运行的周报网页示例输出（含 10 个 `@section` 标记）。
- `scripts/`: 包含各阶段核心逻辑的 Python 脚本。
- `scripts/session_state.py`: 统一 SessionState 状态持久化模块（v1.1 新增）。
- `scripts/data_insight_probe.py`: 数据洞察探针模块（v1.2 新增），包含 DataSourceProbe（口径诊断）、NorthStarProbe（北极星因子分解）、CausalityProbe（跨模块因果链）三个子探针。
- `scripts/analysis_engine.py`: 业务模块分析框架引擎（v1.2 重构），集成商业模式识别、业务阶段矩阵、特有模块推荐和数据洞察探针。
- `scripts/phase3_confirmation.py`: 阶段三四要素确认流管理器（v1.3 重构），已接入 SessionState 持久化，支持断点续建。

## 版本日志 (Changelog)

### v1.3 (2026-04-22)

**P0 优化：三阶段断点续建完整闭环**

1. **`phase3_confirmation.py` 重构（v1.3）——接入 SessionState 统一持久化**
   - 移除内存字典 `self.sessions`，改用 `SessionState` 作为唯一状态源
   - `start_confirmation()` 调用 `ss.start_phase3()` 并立即 `save()`，防止对话截断丢失进度
   - `process_user_feedback()` 每次确认后调用 `ss.advance_phase3_step()` + `ss.save()`
   - 新增 `resume_session()` 方法：对话重启后调用即可从中断步骤继续
   - `finalize_phase3()` 调用 `ss.complete_phase3()` + `ss.save()`，不再另存独立 JSON
   - 异常分支 E/F/G 均已更新为通过 SessionState 持久化状态

2. **端到端三阶段断点续建闭环验证**
   - 验证内容：阶段一→阶段二→阶段三全流程均写入同一个 SessionState JSON 文件
   - 验证内容：重启 Manager 实例后，`resume_session()` 可从正确模块索引和步骤游标恢复
   - 验证内容：异常分支 E（数据来源不明确）、F（呈现方法调整）、G（暂不下钒）均正确持久化
   - 验证内容：最终 SessionState 中 `phase1/2/3` 均标记为 `completed`

### v1.2 (2026-04-22)

**模块覆盖扩充：**

1. **`analysis_framework.md` 大幅扩充**
   - 新增 7 种商业模式特有模块映射（广告变现/订阅制/电商/游戏/B2B SaaS/双边市场/内容社区），共 22 个特有模块，每个模块含关注指标和常见异常信号
   - 新增业务阶段矩阵（种子期/启动期/成长期/扩张期/成熟期），对 5 大通用模块标注 required / lightweight / disabled 三种适用性，并提供阶段建议文案
   - 新增 5 个阶段强制推荐模块（PMF 信号追踪/冷启动漏斗/渠道效率矩阵/单元经济模型/用户分层与生命周期）

2. **`component_library.md` 重构为首屏/详情双层规范**
   - 首屏组件（Hero Components）：HealthScorecard、NorthStarChart、KpiAlertList、MilestoneTimeline，含选型规则和数据绑定规范
   - 详情展示组件（Detail Components）：ModuleProgressCard、TrendLineChart、FunnelChart、HeatmapCalendar、DataTable、ComparativeBarChart，含适用场景和下钻逻辑规范

**数据洞察功能（新增）：**

3. **新增 `data_insight_probe.py` — 数据洞察探针模块**
   - `DataSourceProbe`：检测 30+ 种关键指标的口径缺失、时间窗口模糊、分母不明确、口径不一致四类风险
   - `NorthStarProbe`：识别北极星指标类型（用户规模/收入/GMV/参与度/转化率/ARR），套用标准分解公式，检测各驱动因子数据完整性
   - `CausalityProbe`：内置 6 条跨模块因果链模式（风控→收入、版本→留存、渠道→用户质量等），检测并生成结构化确认问题
   - `DataInsightProbe`：统一入口，`run_all()` 一键运行三个子探针，`get_pending_questions()` 提取所有待询问问题

4. **`analysis_engine.py` 重构**
   - 集成商业模式识别（7 种）、业务阶段识别（5 阶段）、模块适用性矩阵
   - 集成 `DataInsightProbe`，在模块映射后自动运行数据洞察诊断
   - `parse_document()` 返回结构新增 `business_model_type`、`business_stage`、`data_insight_report`、`pending_questions` 字段

5. **`phase1_interaction.py` 更新（v1.2）**
   - 新增 `run_data_insight_probe()` 方法，支持在格式化输出前独立运行探针
   - `format_analysis_result()` 新增 `include_probe_report` 参数，自动嵌入数据洞察诊断报告
   - 新增商业模式类型和业务阶段的中文展示
   - 模块列表新增适用性图标（✅ required / ⚠️ lightweight / 🚫 disabled）和类型标签

### v1.1 (2026-04-22)

**P0 优化：**

1. **新增 `session_state.py` — 统一 SessionState 持久化模块**
   - 引入 `SessionState` 数据类，支持跨阶段共享状态（phase1/phase2/phase3）
   - 支持断点续建：通过 `SessionState.load_or_new(session_id)` 恢复中断的构建流程
   - `phase1_interaction.py` 和 `phase2_interaction.py` 已集成，phase3 待下一迭代接入

2. **`component_recommender.py` 重构为 `ComponentRecommender` 类**
   - 核心逻辑封装为 `ComponentRecommender` 类，统一与其他 Manager 类的代码风格
   - 新增 `ComponentRecommender.from_library()` 工厂方法，支持注入自定义组件库（测试/扩展场景）
   - 保留所有原有模块级函数作为向后兼容包装器，不破坏现有调用方

**P1 优化：**

3. **`weekly_report_example.tsx` 添加 10 个 `@section` 标记**
   - 在每个主要章节顶部插入 `// @section <id>` 注释，提升 AI 读取大文件时的定位效率
   - 标记列表：`data-binding-notes` / `types-and-interfaces` / `mock-data` / `navigation-and-utils` / `atomic-components` / `hero-components` / `milestone-timeline` / `module-progress-cards` / `secondary-modules` / `main-dashboard-component`
   - 原有 `// Section 5: 原子组件` 锚点文本完整保留（code_generator.py 依赖该锚点）

4. **`navigation_designer.py` 循环检测从 DFS 升级为 Kahn 拓扑排序**
   - 原 DFS 仅能检测从当前入口节点可达的环，存在遗漏多节点间接环的风险
   - 新 Kahn 算法（BFS 实现）完整检测所有层级的环，并在检测到环时输出具体的循环节点列表
   - 无递归栈溢风险，适合超大导航图

### v1.0 (2026-04-15)

- 初始版本：三阶段交互式构建流程，包含解析引擎、模块提炼、组件推荐、代码生成四大核心模块。

## 函数级索引 (Function Index)

### `session_state.py`

| 函数/方法 | 行号 | 说明 |
|---|---|---|
| `SessionState.new()` | ~50 | 工厂方法：创建新会话 |
| `SessionState.load()` | ~60 | 工厂方法：从文件加载会话 |
| `SessionState.load_or_new()` | ~75 | 工厂方法：加载或新建会话 |
| `SessionState.save()` | ~90 | 持久化到 JSON 文件 |
| `SessionState.update_phase1()` | ~105 | 更新阶段一数据 |
| `SessionState.complete_phase1()` | ~115 | 标记阶段一完成 |
| `SessionState.start_phase2()` | ~125 | 初始化阶段二 |
| `SessionState.update_phase2_modules()` | ~135 | 更新阶段二模块列表 |
| `SessionState.complete_phase2()` | ~145 | 标记阶段二完成 |
| `SessionState.start_phase3()` | ~155 | 初始化阶段三 |
| `SessionState.advance_phase3_step()` | ~165 | 推进阶段三步骤游标 |
| `SessionState.complete_phase3()` | ~175 | 标记阶段三完成 |
| `SessionState.get_resume_summary()` | ~185 | 生成断点续建摘要 |

### `component_recommender.py`

| 函数/方法 | 行号 | 说明 |
|---|---|---|
| `ComponentRecommender.__init__()` | ~220 | 构造函数，支持注入自定义组件库 |
| `ComponentRecommender.from_library()` | ~235 | 工厂方法：使用自定义组件库创建实例 |
| `ComponentRecommender._normalize_module_name()` | ~250 | 内部：规范化模块名称（支持别名） |
| `ComponentRecommender._score_component()` | ~265 | 内部：计算组件匹配得分（0~1） |
| `ComponentRecommender._generate_recommendation_reason()` | ~290 | 内部：生成选型理由文本 |
| `ComponentRecommender._match_components()` | ~345 | 内部：执行组件匹配，返回内部格式 |
| `ComponentRecommender.recommend()` | ~385 | 公开：单模块推荐，返回完整 JSON |
| `ComponentRecommender.batch_recommend()` | ~460 | 公开：批量推荐 |
| `ComponentRecommender.list_modules()` | ~475 | 公开：列出所有预设模块 |
| `ComponentRecommender.list_components()` | ~485 | 公开：列出所有可用组件 |
| `build_recommendation_result()` | ~510 | 向后兼容包装器 |
| `batch_recommend()` | ~520 | 向后兼容包装器 |

### `navigation_designer.py`

| 函数/方法 | 行号 | 说明 |
|---|---|---|
| `NavigationDesigner.design_navigation()` | ~34 | 主入口：设计导航结构 |
| `NavigationDesigner._find_drill_down_targets()` | ~103 | 查找下钻目标（精确+模糊匹配） |
| `NavigationDesigner._is_default_navbar()` | ~121 | 判断是否为预设金刚区模块 |
| `NavigationDesigner._validate_hierarchy()` | ~129 | **Kahn 拓扑排序**循环检测（v1.1 升级） |
| `NavigationDesigner.to_json()` | ~182 | 格式化输出 JSON |

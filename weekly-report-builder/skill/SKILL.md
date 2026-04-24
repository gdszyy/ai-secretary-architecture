---
name: weekly-report-builder
description: 从零搭建周报网页呈现的交互式构建流程。当用户提供周报文档或数据，并要求构建、生成、设计或搭建周报网页/看板时使用此技能。包含解析拆解、模块提炼、组件选型三个交互阶段，每阶段含询问节点收集关键信息后直接加载内置资源，最大化复用内置模板与组件，节省 token。支持「快速复用通道」：当用户说「更新周报」「本周数据来了」「刷新数据」时，直接走 JSON 数据注入流程，无需重新生成代码。支持「多项目管理」：当用户提到「投后」「中台」「增长」「运营」等不同项目的周报，或要求「新建项目」「切换项目」时，走多项目通道。
---

# 周报网页构建器 (Weekly Report Builder)

三阶段交互式构建流程：**每阶段结束必须向用户展示成果并等待确认**，再进入下一阶段。

> **修改脚本前**：先读 `.cursor/rules/auto_index/INDEX.md` 定位函数，再 grep 函数名精准跳转，不要全文读取脚本。

---

## ⚡ 快速复用通道（周期性周报专用）

**适用场景**：已有上周周报，本周内容结构基本不变，只需更新数据。

> **判断标准**：用户说「更新周报」「本周数据来了」「刷新数据」→ 走此通道；首次生成或大幅改版 → 走三阶段流程。

### 步骤

1. **准备本周数据 JSON**
   - 将用户提供的周报数据填入 `templates/data_schema.json`（参照字段注释）
   - 字段说明：`grep "_comment" templates/data_schema.json`

2. **对比差异，判断是否需要微调**
   ```bash
   python scripts/weekly_diff.py \
     --prev state/weekly_data_{上周周期}.json \
     --curr templates/data_schema.json
   ```
   - 输出「变更摘要」+ 「Agent 微调指令」
   - **无结构性变更** → 直接执行步骤 3，无需 Agent 介入
   - **有结构性变更**（新增/删除模块、里程碑等）→ 按微调指令做局部修改后执行步骤 3

3. **注入数据，生成本周周报**
   ```bash
   python scripts/data_injector.py \
     --data templates/data_schema.json \
     --output output/weekly_report_{本周周期}.tsx
   ```

4. **保存本周数据供下周使用**
   ```bash
   python scripts/weekly_diff.py \
     --prev state/weekly_data_{上周周期}.json \
     --curr templates/data_schema.json \
     --save-curr
   ```

5. 向用户展示生成的周报文件，确认验收。

> **首次使用**：没有上周数据时，跳过步骤 2，直接执行步骤 3+4 建立基线。

---

## 🗂️ 多项目管理通道

**适用场景**：管理多个项目（投后/中台/增长/运营等）的周报，每个项目有独立的数据结构和模块组成。

> **判断标准**：用户提到「投后」「中台」「增长」「运营」等项目名称，或说「新建项目」「切换项目」「查看项目列表」→ 走此通道。

### 查看所有项目

```bash
python scripts/data_injector.py --list-projects
```

### 为已有项目更新周报

```bash
# 1. 编辑对应项目的 schema.json
vim projects/{project-id}/schema.json

# 2. 对比差异（可选）
python scripts/weekly_diff.py \
  --prev state/{project-id}/weekly_data_{上周周期}.json \
  --curr projects/{project-id}/schema.json

# 3. 注入数据生成周报
python scripts/data_injector.py --project {project-id}

# 4. 输出路径：output/{project-id}/weekly_report_{周期}.tsx
```

### 创建新项目

```bash
# 交互式创建（推荐）
python scripts/project_scaffold.py

# 非交互式（已知参数时）
python scripts/project_scaffold.py \
  --id my-project \
  --name "我的项目周报" \
  --type general   # 可选：general / post-investment / platform / growth / ops / pre-launch

# 查看所有项目类型
python scripts/project_scaffold.py --list-types
```

> 创建后：编辑 `projects/{id}/schema.json` 填入真实数据，再运行 `data_injector.py --project {id}` 即可生成首份周报。

### 特别说明：pre-launch 类型（上线前/研发期）

**适用场景**：多模块并行开发、功能点驱动里程碑、无业务数据的项目。

| schema 字段 | 研发期语义 | 说明 |
| :--- | :--- | :--- |
| `northStar.metric` | 整体功能完成率 | `currentValue` = 已完成功能点数/总功能点数 × 100 |
| `milestones[].version` | 所属模块 | 不是业务版本号，而是模块名称 |
| `milestones[].status` | 开发状态 | `done/active/upcoming/blocked` 四态 |
| `risks[]` | 阻塞项 | 不是业务风险，而是技术阻塞和依赖阻塞 |
| `kpiMetrics[]` | 研发过程指标 | PR 数、Bug 数、联调通过率等，而非业务 KPI |
| `extra.features[]` | 功能点清单 | 可选，供 Agent 生成功能地图组件 |

**Agent 微调层处理规则**：当用户提供的数据与 schema 不完全匹配时（如自定义功能状态、特殊排期字段），**直接在生成的 tsx 代码中局部调整对应组件的数据绑定，无需修改 schema**。参考 `projects/pre-launch/config.json` 中的 `agentHints` 字段。

### 项目目录结构

```
projects/
├── default/          ← 泛娱乐项目（内置示例）
│   ├── config.json   ← 项目元信息（名称、模块别名、sections 配置）
│   └── schema.json   ← 该项目的数据模板（每周填写）
├── post-investment/  ← 投后管理（内置）
├── platform/         ← 中台建设（内置）
└── {your-project}/   ← 用 project_scaffold.py 创建的新项目

output/{project-id}/  ← 生成的周报 tsx 文件
state/{project-id}/   ← 历史数据存档（供 weekly_diff.py 对比）
```

---

## 阶段 1：解析与拆解

**目标**：解析输入文档，提取核心业务逻辑，拆解业务模块。

1. 读取 `references/analysis_framework.md`（5 大业务模块定义）。
2. 运行 `scripts/analysis_engine.py` 解析文档，提取北极星指标并映射到业务模块。
3. 运行 `scripts/insight_detector.py`。发现框架外新模式/反常识数据时，单独列出并暂停等待用户决策。
4. **【统筹信息询问节点】** 向用户提出以下问题，等待回复后再继续：
   - ① 确认文档覆盖的业务范围/项目名是否准确（回复写入 `ctx.project`）
   - ② 是否有遗漏模块或需要补充说明的内容
   - ③ 里程碑信息是否准确，有无需要修正的节点
5. 用户确认后调用 `finalize_phase1(session_id)` 持久化至 `state/{session_id}_phase1_final.json`。

---

## 阶段 2：模块提炼与优先级划分

**目标**：提炼可用的周报呈现模块，划分优先级。

> 读取上阶段状态：`state/{session_id}_phase1_final.json`（无需上下文传递）。

### 2.1 商业模式询问

**【商业模式询问节点】** 向用户提出以下问题，等待回复后再继续：

- ① 项目类型（从内置列表选一个，写入 `ctx.projectType`）：

  | 选项 | 适用场景 |
  | :--- | :--- |
  | `general` | 通用型，适合大多数产品/业务团队 |
  | `post-investment` | 投后管理，被投企业组合跟踪 |
  | `platform` | 中台/基础设施，服务能力、API 指标 |
  | `growth` | 增长团队，获客/留存/变现漏斗 |
  | `ops` | 运营团队，活动/内容/用户运营 |
  | `pre-launch` | 上线前/研发期，功能点驱动里程碑 |

- ② 本周关注方向（写入 `ctx.focus`，每周必问，不可复用）

> `ctx.project` 已由阶段 1 写入，**不重复询问项目名**。

用户回复后，**直接加载对应内置资源（零 token）**：

```bash
# 加载项目类型配置，包含 sections / moduleAlias / agentHints
cat projects/{ctx.projectType}/config.json
cat projects/{ctx.projectType}/schema.json
```

若用户项目类型不在内置列表（兜底）：选最近似类型加载，在 `agentHints` 中标注差异字段，后续局部调整数据绑定，无需重新生成。

### 2.2 模块提炼

1. 读取 `references/component_library.md`（15 个组件注册结构）。
   - 快速定位：`grep "^### " references/component_library.md`
2. 运行 `scripts/module_extractor.py` 提炼 P0/P1/P2 模块（基于已加载的 `config.sections`）。
   - **数据完整性评估**：可视化数据模块（漏斗/趋势矩阵/气泡图等）较少时，**必须主动建议用户上传 Excel/CSV**。

### 2.3 报告模式询问

**【报告模式询问节点】** 向用户提出以下问题，等待回复后再继续：

- ① 风格偏好（写入 `ctx.style`，选一个）：
  - `data-dense`：数据密集，图表为主，适合高管/投资人
  - `narrative`：叙事型，进展描述为主，适合团队同步
  - `exec-board`：执行看板，状态卡片为主，适合日常跟进
- ② 是否需要下钻导航（写入 `ctx.drilldown`，是/否）

> 受众已由 `config.description` 携带，**不重复询问受众**。项目名已由 `ctx.project` 携带，**不重复询问**。

用户回复后，**直接映射内置风格配置（零 token）**：

```bash
# 按需 grep design_system.md 对应章节，不全文读取
grep -A 30 "^## 3\. 颜色系统" references/design_system.md
grep -A 20 "^## 6\. 字体系统" references/design_system.md
```

运行 `scripts/navigation_designer.py`，按 `ctx.drilldown` 决定是否生成首屏下钻与金刚区跳转逻辑。

### 2.4 确认模块

运行 `scripts/phase2_interaction.py` 展示模块列表及优先级，等待用户选定最终模块。用户确认后调用 `finalize_phase2(session_id)` 持久化至 `state/{session_id}_phase2_final.json`。

---

## 阶段 3：组件选型与数据绑定

**目标**：为选定模块匹配 UI 组件，确认数据绑定，生成代码。

> 读取上阶段状态：`state/{session_id}_phase2_final.json`（无需上下文传递）。

### 3.1 加载内置组件候选（零 token）

运行 `scripts/component_recommender.py`，基于 `ctx.projectType + ctx.style` **优先索引 `templates/components/` 中已有组件**，不重新生成：

| 内置组件文件 | 适用场景 |
| :--- | :--- |
| `ConversionFunnel.tsx` | 转化漏斗（growth/ops） |
| `EcosystemHealthMap.tsx` | 生态健康地图（post-investment/platform） |
| `HealthRadarChart.tsx` | 健康度雷达图（通用） |
| `MilestoneCardList.tsx` | 里程碑卡片列表（通用） |
| `NorthStarDecomposition.tsx` | 北极星拆解（通用） |
| `StageProgressBar.tsx` | 阶段进度条（pre-launch） |
| `TrendMatrixGrid.tsx` | 趋势矩阵（data-dense） |
| `UnitEconomicsCard.tsx` | 单位经济模型（growth/post-investment） |
| `UserSegmentationBubble.tsx` | 用户分层气泡图（growth/ops） |
| `MultiProjectShell.tsx` | 多项目报告壳层（platform/post-investment，项目数≥ 3） |

> **🚨 壳层组件强制规则（已升级为 Shell 注入路径）**：当 `ctx.projectType` 为 `platform` 或 `post-investment`，且项目数量 ≥ 3 时，**禁止直接生成 HTML/TSX 代码**。必须走 Shell 注入路径：
> 1. Agent 只输出 JSON 数据文件（参照 `projects/platform/shell_schema.json`）
> 2. 运行 `scripts/shell_injector.py` 渲染为完整 HTML
> 3. 相比旧方案（直接生成 1600+ 行 HTML），**节省约 80% 输出 Token**

**仅对无内置组件的模块才生成新代码**。需要创建预设组件库以外的新组件时：
- 首屏组件 → 先读 `references/hero_component_design_principles.md`
- 其他组件 → 参考 `references/component_brainstorm.md`

### 3.2 组件使用询问

**【组件使用询问节点】** 向用户提出以下问题，等待回复后再继续：

- ① 品牌色 / 设计规范约束（写入 `ctx.brand`，**必问，无法从上游推断**）
- ② 图表类型偏好（**条件问**：仅当同一模块有 ≥ 2 个内置组件可选时询问）

> 交互需求已由 `ctx.drilldown` 决定，风格已由 `ctx.style` 决定，**不重复询问**。

用户回复后，**将 `ctx.brand` patch 到色彩 Token 覆盖层（零 token）**，无需重新生成整套设计系统：

```bash
grep -A 100 "^## 附录：设计 Token JSON" references/design_system.md
# 仅覆盖 primary/accent 色值，其余 Token 保持内置默认
```

### 3.3 四要素确认

运行 `scripts/phase3_confirmation.py` 管理确认流，逐模块确认：
1. **数据来源**（含数据完整性评估）
2. **呈现方法**（视觉形态，优先从内置组件列表选取）
3. **展示字段**（具体数据字段）
4. **下钻逻辑**（跳转目标）

异常分支处理：
- **分支 E**（数据来源不明确）→ `resume_from_branch_e()` 补充后恢复
- **分支 F**（呈现方法需调整）→ `_handle_branch_f_selection()` 选备选组件或自定义，`resume_from_branch_f()` 恢复
- **分支 G**（下钻逻辑缺失）→ 标注「暂不下钻」继续

### 3.4 生成代码（⚠️ 强制走 Shell 注入路径）

> **🚨 Token 节省强制规则（违反此规则将导致 80% Token 浪费）**：
> - **当 `ctx.projectType` 为 `platform` 或 `post-investment`，且项目数量 ≥ 3 时**，**禁止直接输出 HTML/TSX 代码**。
> - **必须走 Shell 注入路径**：Agent 只输出 JSON 数据文件（约 80-120 行），由 `shell_injector.py` 渲染为完整 HTML。
> - 直接生成 HTML 的方式已被废弃，任何情况下不得绕过此路径。

#### Shell 注入路径（platform/post-investment，项目数 ≥ 3）

**步骤 1：Agent 只输出 JSON 数据文件**

参照 `projects/platform/shell_schema.json` 的字段结构，将本次周报数据填入 JSON 文件（约 80-120 行），保存至 `state/{session_id}_shell_data.json`。

```bash
# 查看 JSON Schema 字段说明
cat projects/platform/shell_schema.json
```

JSON 顶层字段说明：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `meta` | object | 报告元信息（标题、日期、Logo 文字等） |
| `summary` | object | 首页总览（副标题、Banner、统计卡、成果列表） |
| `projects` | array | 各项目详情（每个项目约 15-20 行） |
| `risks` | object | 风险总览（top3 + all 列表） |
| `plan` | object | 下周计划（表格行列表） |
| `improvements` | object | 改进措施（根因 + 行动卡） |
| `charts` | object | 图表数据（可选，不提供则自动推断） |

**步骤 2：运行注入脚本，生成完整 HTML**

```bash
python scripts/shell_injector.py \
  --data state/{session_id}_shell_data.json \
  --output output/platform/weekly_report_{period}.html
```

**步骤 3：验证输出**

```bash
# 验证占位符全部替换
python scripts/shell_injector.py \
  --data state/{session_id}_shell_data.json \
  --dry-run
```

**步骤 4：用户验收**

启动本地服务器预览，用户验收后交付 HTML 文件。如需微调，只修改 JSON 数据文件，重新运行注入脚本，无需修改 HTML 模板。

#### 通用 Shell 注入路径（所有项目类型强制使用）

> **🚨 全面升级：所有项目类型均已内置 HTML Shell 模板，任何类型禁止直接输出 HTML/TSX 代码。**

**步骤 1：Agent 只输出 JSON 数据文件**

参照对应项目类型的 shell_schema 填写数据（约 80-150 行），保存至 `state/{session_id}_shell_data.json`。

| 项目类型 | Shell 模板 | 参照 Schema |
| :--- | :--- | :--- |
| `platform` | `templates/shells/multi_project.html` | `projects/platform/shell_schema.json` |
| `post-investment` | `templates/shells/post_investment.html` | `projects/post-investment/schema.json` |
| `general` | `templates/shells/general.html` | `projects/default/schema.json` |
| `growth` | `templates/shells/growth.html` | `projects/growth-team/schema.json` |
| `pre-launch` | `templates/shells/pre_launch.html` | `projects/pre-launch/schema.json` |
| `ops` | `templates/shells/ops.html` | `projects/ops/schema.json` |

**步骤 2：运行通用渲染入口，生成完整 HTML**

```bash
# 通用入口（自动路由到对应 Shell）
python scripts/render.py \
  --data state/{session_id}_shell_data.json \
  --type {ctx.projectType} \
  --output output/{ctx.projectType}/weekly_report_{period}.html

# 查看所有支持的项目类型
python scripts/render.py --list-types

# 验证占位符全部替换（不写入文件）
python scripts/render.py \
  --data state/{session_id}_shell_data.json \
  --type {ctx.projectType} \
  --dry-run
```

**步骤 3：用户验收**

启动本地服务器预览，用户验收后交付 HTML 文件。如需微调，只修改 JSON 数据文件，重新运行渲染脚本，无需修改 HTML 模板。

> **Token 节省效果**：相比直接生成 HTML（1000-2000 行），Agent 只需输出 JSON（~80-150 行），**节省 80-90% 输出 Token**。

---

## 🛡️ 兜底调整方案

| 场景 | 处理方式 |
| :--- | :--- |
| 用户跳过任意询问节点 | 使用默认值继续（`general` 类型 + `data-dense` 风格），后续可随时补充修改 |
| 用户项目类型不在内置列表 | 选最近似类型加载，`agentHints` 标注差异字段，局部调整数据绑定 |
| 阶段 3 要求大幅改版 | 回退至阶段 2 重新选模块，保留 `phase1_final.json` 状态不重跑 |

---

## 资源索引

| 资源 | 用途 | 读取时机 |
| :--- | :--- | :--- |
| `references/analysis_framework.md` | 5 大业务模块定义 | 阶段 1 必读 |
| `references/component_library.md` | 15 个组件 + 壳层组件注册结构 | 阶段 2-3 必读 |
| `references/hero_component_design_principles.md` | 首屏组件三层交互规范 | 创建新首屏组件时必读 |
| `references/component_brainstorm.md` | 15 个组件完整设计方案 | 阶段 3 实现新组件时参考 |
| `references/design_system.md` | iOS 26 Liquid Glass 设计规范（498 行，**按需 grep**） | 阶段 3 生成代码时按需读取 |
| `.cursor/rules/auto_index/INDEX.md` | 脚本函数索引 + references 读取时机 | 修改脚本前必读 |
| `templates/dashboard_template.tsx` | 仪表盘 React 模板骨架 | 代码生成时参考 |
| `templates/weekly_report_example.tsx` | 完整可运行示例输出 | 代码生成时参考格式 |
| `templates/components/*.tsx` | 9 个内置可复用组件 | 阶段 3 优先复用，不重新生成 |
| `templates/components/MultiProjectShell.tsx` | 多项目报告壳层（侧边栏+多页面+原子组件全套） | 商业模式为 platform/post-investment 且项目数≥ 3 时优先加载 |
| `templates/shells/multi_project.html` | **platform 类型 HTML Shell 模板（带占位符，可注入）** | platform 类型阶段 3 必须使用 |
| `templates/shells/general.html` | **general 类型 HTML Shell 模板** | general 类型阶段 3 必须使用 |
| `templates/shells/growth.html` | **growth 类型 HTML Shell 模板（转化漏斗+渠道 ROI）** | growth 类型阶段 3 必须使用 |
| `templates/shells/pre_launch.html` | **pre-launch 类型 HTML Shell 模板（功能点+模块进度）** | pre-launch 类型阶段 3 必须使用 |
| `templates/shells/ops.html` | **ops 类型 HTML Shell 模板（活动+内容运营）** | ops 类型阶段 3 必须使用 |
| `templates/shells/post_investment.html` | **post-investment 类型 HTML Shell 模板（被投企业+融资动态）** | post-investment 类型阶段 3 必须使用 |
| `scripts/render.py` | **🚨 通用渲染入口：自动路由到对应 Shell，所有类型必须使用** | 阶段 3 生成代码时必须调用 |
| `scripts/shell_registry.py` | **Shell 注册表+分发器：6 种类型的渲染器实现** | render.py 内部依赖，一般无需直接读取 |
| `scripts/shell_injector.py` | **Shell 注入器：JSON → 完整 HTML（platform 类型专用）** | render.py 内部自动调用，无需直接调用 |
| `projects/platform/shell_schema.json` | **platform 类型 Shell 注入 JSON Schema（含字段注释）** | 阶段 3 输出 JSON 时参照此文件的字段结构 |
| `templates/data_schema.json` | 周报数据模板（DashboardData 结构） | 快速复用通道：每周填写此文件 |
| `scripts/data_injector.py` | 数据注入器：JSON → tsx mockData 块替换 | 快速复用通道步骤 3 |
| `scripts/weekly_diff.py` | 差异分析器：对比两周 JSON，生成微调指令 | 快速复用通道步骤 2 |
| `state/weekly_data_{period}.json` | 历史周报数据存档 | 快速复用通道步骤 2/4 |
| `state/{session_id}_shell_data.json` | Shell 注入 JSON 数据（platform 类型每次生成保存） | 阶段 3 Shell 注入路径产物，供下周快速复用 |
| `scripts/project_scaffold.py` | 新项目一键初始化（6 种类型模板） | 多项目通道：创建新项目时 |
| `projects/{id}/config.json` | 项目元信息（sections、模块别名、路径配置） | 商业模式询问后直接加载 |
| `projects/{id}/schema.json` | 项目专属数据模板（每周填写） | 商业模式询问后直接加载 |

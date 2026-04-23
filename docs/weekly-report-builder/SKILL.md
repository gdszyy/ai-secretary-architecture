---
name: weekly-report-builder
description: 从零搭建周报网页呈现的交互式构建流程。当用户提供周报文档或数据，并要求构建、生成、设计或搭建周报网页/看板时使用此技能。包含解析拆解、模块提炼、组件选型三个交互阶段。支持「快速复用通道」：当用户说「更新周报」「本周数据来了」「刷新数据」时，直接走 JSON 数据注入流程，无需重新生成代码。支持「多项目管理」：当用户提到「投后」「中台」「增长」「运营」等不同项目的周报，或要求「新建项目」「切换项目」时，走多项目通道。
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
  --type general   # 可选：general / post-investment / platform / growth / ops

# 查看所有项目类型
python scripts/project_scaffold.py --list-types
```

> 创建后：编辑 `projects/{id}/schema.json` 填入真实数据，再运行 `data_injector.py --project {id}` 即可生成首份周报。

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
4. 运行 `scripts/phase1_interaction.py` 管理交互状态，展示解析结果，**特别要求用户确认里程碑模块准确性**，等待回复。
5. 用户确认后调用 `finalize_phase1(session_id)` 持久化至 `state/{session_id}_phase1_final.json`。

---

## 阶段 2：模块提炼与优先级划分

**目标**：提炼可用的周报呈现模块，划分优先级。

> 读取上阶段状态：`state/{session_id}_phase1_final.json`（无需上下文传递）。

1. 读取 `references/component_library.md`（15 个组件注册结构）。
   - 快速定位：`grep "^### " references/component_library.md`
2. 运行 `scripts/module_extractor.py` 提炼 P0/P1/P2 模块。
   - **数据完整性评估**：可视化数据模块（漏斗/趋势矩阵/气泡图等）较少时，**必须主动建议用户上传 Excel/CSV**。
3. 运行 `scripts/navigation_designer.py` 设计首屏下钻与金刚区跳转逻辑。
4. 运行 `scripts/phase2_interaction.py` 管理交互状态，展示模块列表及优先级，等待用户选定最终模块。
5. 用户确认后调用 `finalize_phase2(session_id)` 持久化至 `state/{session_id}_phase2_final.json`。

---

## 阶段 3：组件选型与数据绑定

**目标**：为选定模块匹配 UI 组件，确认数据绑定，生成代码。

> 读取上阶段状态：`state/{session_id}_phase2_final.json`（无需上下文传递）。

### 3.1 组件匹配

运行 `scripts/component_recommender.py` 推荐组件。需要创建预设组件库以外的新组件时：
- 首屏组件 → 先读 `references/hero_component_design_principles.md`
- 其他组件 → 参考 `references/component_brainstorm.md`

### 3.2 四要素确认

运行 `scripts/phase3_confirmation.py` 管理确认流，逐模块确认：
1. **数据来源**（含数据完整性评估）
2. **呈现方法**（视觉形态）
3. **展示字段**（具体数据字段）
4. **下钻逻辑**（跳转目标）

异常分支处理：
- **分支 E**（数据来源不明确）→ `resume_from_branch_e()` 补充后恢复
- **分支 F**（呈现方法需调整）→ `_handle_branch_f_selection()` 选备选组件或自定义，`resume_from_branch_f()` 恢复
- **分支 G**（下钻逻辑缺失）→ 标注「暂不下钻」继续

### 3.3 生成代码

`references/design_system.md` 共 498 行，**按需 grep，不要全文读取**：

```bash
# 颜色 Token（最常用）
grep -A 30 "^## 3\. 颜色系统" references/design_system.md
# 毛玻璃效果
grep -A 20 "^## 12\. 视觉效果" references/design_system.md
# 字体系统
grep -A 20 "^## 6\. 字体系统" references/design_system.md
# 动效系统
grep -A 25 "^## 11\. 动效系统" references/design_system.md
# 卡片与表面层级
grep -A 15 "^## 8\. 卡片与表面层级系统" references/design_system.md
# 完整 Token JSON（仅需精确实现时）
grep -A 100 "^## 附录：设计 Token JSON" references/design_system.md
```

运行 `scripts/code_generator.py`，参考 `templates/dashboard_template.tsx`，生成最终 React/TypeScript 单文件（格式参考 `templates/weekly_report_example.tsx`）。用户验收时支持精准修改，循环至验收通过。

---

## 资源索引

| 资源 | 用途 | 读取时机 |
| :--- | :--- | :--- |
| `references/analysis_framework.md` | 5 大业务模块定义 | 阶段 1 必读 |
| `references/component_library.md` | 15 个组件注册结构 | 阶段 2-3 必读 |
| `references/hero_component_design_principles.md` | 首屏组件三层交互规范 | 创建新首屏组件时必读 |
| `references/component_brainstorm.md` | 15 个组件完整设计方案 | 阶段 3 实现新组件时参考 |
| `references/design_system.md` | iOS 26 Liquid Glass 设计规范（498 行，**按需 grep**） | 阶段 3 生成代码时按需读取 |
| `.cursor/rules/auto_index/INDEX.md` | 脚本函数索引 + references 读取时机 | 修改脚本前必读 |
| `templates/dashboard_template.tsx` | 仪表盘 React 模板骨架 | 代码生成时参考 |
| `templates/weekly_report_example.tsx` | 完整可运行示例输出 | 代码生成时参考格式 |
| `templates/data_schema.json` | 周报数据模板（DashboardData 结构） | 快速复用通道：每周填写此文件 |
| `scripts/data_injector.py` | 数据注入器：JSON → tsx mockData 块替换 | 快速复用通道步骤 3 |
| `scripts/weekly_diff.py` | 差异分析器：对比两周 JSON，生成微调指令 | 快速复用通道步骤 2 |
| `state/weekly_data_{period}.json` | 历史周报数据存档 | 快速复用通道步骤 2/4 |
| `scripts/project_scaffold.py` | 新项目一键初始化（5 种类型模板） | 多项目通道：创建新项目时 |
| `projects/{id}/config.json` | 项目元信息（sections、模块别名、路径配置） | 多项目通道：自动加载 |
| `projects/{id}/schema.json` | 项目专属数据模板（每周填写） | 多项目通道：每周更新 |

---
title: weekly-report-builder Skill 迭代交接文档
type: 迭代交接文档（Handover Document）
version: v1.1（2026-04-22）
path: docs/weekly-report-builder/HANDOVER.md
audience: 接手该 Skill 迭代的 Agent 或开发者
---

# weekly-report-builder Skill 迭代交接文档

---

## 一、快速上下文加载路径

接手迭代时，**按以下顺序依次读取**，可在最短时间内重建完整上下文：

| 优先级 | 文件路径 | 读取目的 |
| :---: | :--- | :--- |
| **1** | `skills/weekly-report-builder/SKILL.md` | AI 触发入口，三阶段工作流主文档（含版本日志与函数索引） |
| **2** | `skills/weekly-report-builder/.cursor/rules/auto_index/INDEX.md` | 大文件函数级索引汇总（涉及代码修改时必读） |
| **3** | `skills/weekly-report-builder/.cursor/rules/auto_index/scripts_code_generator_py_index.md` | 代码生成引擎函数级索引（1507 行） |
| **4** | `skills/weekly-report-builder/.cursor/rules/auto_index/scripts_component_recommender_py_index.md` | 组件推荐系统函数级索引（878 行） |
| **5** | `skills/weekly-report-builder/.cursor/rules/auto_index/templates_weekly_report_example_tsx_index.md` | 示例输出函数级索引（2169 行，含 10 个 @section 标记） |
| **6** | `skills/weekly-report-builder/.cursor/rules/auto_index/scripts_session_state_py_index.md` | SessionState 持久化模块索引（527 行，v1.1 新增） |

---

## 二、当前 Skill 现状快照（v1.1）

### 2.1 文件结构

```
skills/weekly-report-builder/
├── SKILL.md                          # AI 触发入口（三阶段工作流 + 版本日志 + 函数索引）
├── .cursor/rules/auto_index/         # 自动生成的函数级索引（严禁手动编辑）
│   ├── INDEX.md                      # 索引汇总入口
│   ├── scripts_code_generator_py_index.md
│   ├── scripts_component_recommender_py_index.md
│   ├── scripts_session_state_py_index.md
│   └── templates_weekly_report_example_tsx_index.md
├── references/
│   ├── analysis_framework.md         # 5 大业务模块评估框架（阶段 1 使用）
│   └── component_library.md          # 组件库规范与 P0/P1/P2 优先级定义（阶段 2/3 使用）
├── templates/
│   ├── dashboard_template.tsx        # React 仪表盘基础骨架（129 行）
│   └── weekly_report_example.tsx     # 完整周报示例输出（2169 行，含 10 个 @section 标记）
└── scripts/
    ├── session_state.py              # 统一 SessionState 状态持久化（527 行，v1.1 新增）
    ├── analysis_engine.py            # 阶段 1：业务模块解析引擎（131 行）
    ├── insight_detector.py           # 阶段 1：异常洞察检测，覆盖分支 A（164 行）
    ├── phase1_interaction.py         # 阶段 1：交互状态管理，覆盖分支 B/C（308 行，已集成 SessionState）
    ├── module_extractor.py           # 阶段 2：组件规范读取与动态评分（246 行）
    ├── navigation_designer.py        # 阶段 2：导航与下钻逻辑，Kahn 拓扑排序（204 行，v1.1 升级）
    ├── phase2_interaction.py         # 阶段 2：交互动态调整，覆盖分支 D（328 行，已集成 SessionState）
    ├── component_recommender.py      # 阶段 3：ComponentRecommender 类（878 行，v1.1 重构）
    ├── phase3_confirmation.py        # 阶段 3：四要素确认流，覆盖分支 E/F/G（302 行）
    └── code_generator.py             # 阶段 3：代码生成引擎，覆盖分支 H（1507 行）
```

### 2.2 核心类与入口函数

| 脚本 | 核心类 | 主要职责 |
| :--- | :--- | :--- |
| `session_state.py` | `SessionState` | 跨阶段状态持久化、断点续建（v1.1 新增） |
| `analysis_engine.py` | `AnalysisEngine` | 文档解析、模块映射、北极星指标提取 |
| `insight_detector.py` | `InsightDetector` | 框架外洞察检测、强制暂停触发 |
| `phase1_interaction.py` | `Phase1InteractionManager` | 阶段 1 状态机、里程碑确认、分支 B/C 循环（已集成 SessionState） |
| `module_extractor.py` | `ModuleExtractor` | 动态评分算法、P0/P1/P2 分级 |
| `navigation_designer.py` | `NavigationDesigner` | 导航图谱生成、**Kahn 拓扑排序**循环引用检测（v1.1 升级） |
| `phase2_interaction.py` | `Phase2InteractionManager` | 阶段 2 状态机、分支 D 循环（已集成 SessionState） |
| `component_recommender.py` | `ComponentRecommender` | 组件评分匹配、推荐理由生成（v1.1 重构为类） |
| `phase3_confirmation.py` | `Phase3ConfirmationManager` | 四要素确认流、分支 E/F/G 处理 |
| `code_generator.py` | `CodeGeneratorEngine` / `TemplateInjector` / `ComponentCodeGenerator` / `NavigationCodeGenerator` / `BranchHModificationLoop` | 模板注入、5 种组件生成、分支 H 修改循环 |

### 2.3 异常分支覆盖状态

| 分支 | 触发条件 | 覆盖脚本 | 状态 |
| :--- | :--- | :--- | :--- |
| A | 框架外洞察 | `insight_detector.py` | ✅ 已实现 |
| B | 里程碑状态有误 | `phase1_interaction.py` | ✅ 已实现 |
| C | 用户补充商业逻辑 | `phase1_interaction.py` | ✅ 已实现 |
| D | 用户调整模块优先级 | `phase2_interaction.py` | ✅ 已实现 |
| E | 数据来源不明确 | `phase3_confirmation.py` | ✅ 已实现 |
| F | 呈现方法需调整 | `phase3_confirmation.py` | ✅ 已实现 |
| G | 下钻逻辑缺失 | `phase3_confirmation.py` | ✅ 已实现 |
| H | 代码验收需修改 | `code_generator.py` → `BranchHModificationLoop` | ✅ 已实现 |

---

## 三、已知问题与技术债

### 3.1 高优先级（v1.1 已修复）

~~**问题 1：`weekly_report_example.tsx` 缺少 `@section` 标记**~~
> ✅ **v1.1 已修复**：已添加 10 个符合 code-indexer 规范的 `@section` 标记（下划线命名格式），索引脚本可正确识别所有标记。

~~**问题 2：`component_recommender.py` 未使用类封装**~~
> ✅ **v1.1 已修复**：已重构为 `ComponentRecommender` 类，保留向后兼容包装器。

### 3.2 中优先级（v1.1 已修复）

~~**问题 3：三个阶段的交互管理器缺乏统一的状态持久化机制**~~
> ✅ **v1.1 已修复**：新增 `session_state.py`，phase1/phase2 已集成。**待完成**：`phase3_confirmation.py` 尚未接入 SessionState，待下一迭代完成。

~~**问题 4：`navigation_designer.py` 的 DFS 防死循环检测未覆盖间接循环**~~
> ✅ **v1.1 已修复**：已升级为 Kahn 拓扑排序算法，完整检测所有层级循环引用，并输出具体循环节点列表。

### 3.3 低优先级（待处理）

**问题 5：`analysis_framework.md` 的 5 大框架缺少"内容与社区"模块**

当前预设框架覆盖：增长与获客、产品与活跃、商业化与变现、风险与合规、里程碑与项目管理。对于内容型或社区型产品，缺少专门的内容运营评估框架。

**修复方案**：在 `analysis_framework.md` 中新增第 6 个框架模块，并同步更新 `analysis_engine.py` 的映射逻辑。

---

## 四、迭代建议（按优先级排序）

### 4.1 近期迭代（P0，建议 v1.2 完成）

**迭代 1：`phase3_confirmation.py` 接入 SessionState**

`phase3_confirmation.py` 是唯一尚未集成 SessionState 的交互管理器。接入后，三阶段断点续建功能将完整闭环。

### 4.2 中期迭代（P1，建议 v1.2~v1.3 完成）

**迭代 2：新增"内容与社区"分析框架**（对应已知问题 5）

扩展 Skill 的适用业务类型，从游戏/社交产品扩展到内容型产品。

**迭代 3：增加多业务类型的示例输出**

当前 `weekly_report_example.tsx` 只有一个示例（游戏社交产品）。建议为电商、SaaS、内容平台各提供一个示例模板，降低 AI 在阶段 3 生成代码时的幻觉风险。

### 4.3 长期迭代（P2，规划中）

**迭代 4：数据自动化接入**

通过 API 接入 BI 系统（如 Mixpanel、Amplitude）或项目管理工具（如 Tapd、Jira），实现周报数据的自动填充，减少手动输入。

**迭代 5：历史快照自动归档**

每期周报确认后，自动生成静态 HTML 快照并存入 `config-versions/`，支持历史周报的跨期对比。

---

## 五、迭代操作规范

### 修改 SKILL.md 主文档

SKILL.md 是 AI 的执行指令，修改时需特别注意：
- 三阶段的顺序和脚本引用不得随意调整，否则会导致 AI 执行流程错乱。
- 修改后需在 SKILL.md 的"版本日志"章节中记录，并同步更新本文档。

### 修改 Python 脚本

- 修改任何脚本后，如果函数签名或类接口发生变化，必须重新运行 `code-indexer` 更新函数级索引：
  ```bash
  python3 /home/ubuntu/skills/code-indexer/scripts/generate_index.py \
    /home/ubuntu/skills/weekly-report-builder --src-dirs scripts templates
  ```
- 新增超过 200 行的函数时，必须在函数内部添加 `// @section:{snake_case_name} - {一句话中文说明}` 标记。
- **注意**：`@section` 名称只能使用字母、数字、下划线（`\w+`），不能含连字符（`-`）。

### 修改 React 模板

- 修改 `dashboard_template.tsx` 或 `weekly_report_example.tsx` 后，需同步更新对应的函数级索引（同上）。
- 新增组件类型后，必须同步更新 `references/component_library.md` 中的组件规范定义。
- `// Section 5: 原子组件` 这行文本是 `code_generator.py` 的注入锚点，**严禁删除或修改**。

### 发现新的防坑经验

在 `.cursor/rules/process_insights/` 下创建新的洞察文档（命名格式：`PI-{编号:03d}_{slug}.md`），并在 `index.md` 中注册。

---

## 六、版本变更日志

| 版本 | 日期 | 变更内容 | 作者 |
| :--- | :--- | :--- | :--- |
| v1.1 | 2026-04-22 | P0：新增 SessionState 持久化模块，phase1/phase2 已集成；ComponentRecommender 类封装重构。P1：weekly_report_example.tsx 添加 10 个 @section 标记（code-indexer 规范格式）；navigation_designer.py DFS 升级为 Kahn 拓扑排序。更新函数级索引。 | Manus AI |
| v1.0 | 2026-04-22 | 初始版本：三阶段工作流完整实现，覆盖 8 条异常分支，13 个子任务全部完成 | Manus AI |

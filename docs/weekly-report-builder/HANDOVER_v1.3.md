# weekly-report-builder Skill 交接文档 v1.3

> **交接时间**：2026-04-22
> **当前版本**：v1.3
> **交接目的**：组件扩展——将 `component_library.md` 中规范已定义但尚未在代码中实现的 9 个组件补全

---

## 一、Skill 概述

`weekly-report-builder` 是一个三阶段交互式周报网页构建 Skill，核心流程如下：

```
用户上传周报文档
      ↓
阶段一：业务架构解析（analysis_engine.py + phase1_interaction.py）
  - 识别商业模式、业务阶段、北极星指标
  - 运行数据洞察探针（口径诊断 / 北极星因子分解 / 因果链）
  - 输出模块推荐清单 + 数据诊断报告
      ↓
阶段二：模块确认（phase2_interaction.py）
  - 用户确认/调整推荐的模块列表
  - 支持增删模块、调整优先级
      ↓
阶段三：组件选型与数据绑定（phase3_confirmation.py）
  - 对每个模块逐一确认四要素：
    ① 数据来源  ② 呈现方法（UI 组件）  ③ 回报内容  ④ 下钻逻辑
  - 输出完整组件配置清单 JSON
      ↓
代码生成（code_generator.py）
  - 基于配置清单生成完整的 React/TSX 周报网页
```

---

## 二、文件结构与版本状态

### 2.1 脚本文件（`scripts/`）

| 文件 | 行数 | 函数数 | 版本 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| `session_state.py` | 527 | 22 | v1.1 新增 | 统一 SessionState 持久化，三阶段共享同一 JSON 文件 |
| `analysis_engine.py` | 579 | 12 | v1.2 重构 | 商业模式识别 + 阶段矩阵 + 特有模块推荐 + 数据洞察探针集成 |
| `data_insight_probe.py` | 790 | 33 | v1.2 新增 | 口径诊断 / 北极星因子分解 / 跨模块因果链三层探针 |
| `component_recommender.py` | 878 | 10 | v1.1 重构 | ComponentRecommender 类封装，**当前仅注册 5 个组件** |
| `phase1_interaction.py` | 400 | — | v1.1 集成 | 已接入 SessionState |
| `phase2_interaction.py` | 328 | — | v1.1 集成 | 已接入 SessionState |
| `phase3_confirmation.py` | 547 | 6 | **v1.3 重构** | 已接入 SessionState，支持断点续建

| `module_extractor.py` | 246 | — | v1.0 | 从文档中提取模块信息 |
| `navigation_designer.py` | 204 | — | v1.1 重构 | DFS 升级为 Kahn 拓扑排序，完整检测循环引用 |
| `insight_detector.py` | 164 | — | v1.0 | 洞察检测辅助模块 |
| `code_generator.py` | 1507 | 16 | v1.0 | 代码生成引擎，含 2 个巨型函数 |

### 2.2 模板文件（`templates/`）

| 文件 | 行数 | 说明 |
| :--- | :---: | :--- |
| `weekly_report_example.tsx` | 2169 | 完整可运行周报示例，含 10 个 `@section` 标记，**已实现 8 个组件** |
| `dashboard_template.tsx` | 129 | 代码生成器使用的基础模板 |

### 2.3 参考文档（`references/`）

| 文件 | 行数 | 说明 |
| :--- | :---: | :--- |
| `analysis_framework.md` | 248 | 商业模式特有模块 + 阶段矩阵（v1.2 大幅扩充） |
| `component_library.md` | 230 | **首屏/详情双层组件规范（v1.2 扩充），是组件扩展的主要参考** |

### 2.4 函数级索引（`.cursor/rules/auto_index/`）

code-indexer 已为所有大文件生成索引，共 7 个索引文件：

```
INDEX.md                                  ← 总览索引
scripts_analysis_engine_py_index.md
scripts_code_generator_py_index.md
scripts_component_recommender_py_index.md
scripts_data_insight_probe_py_index.md
scripts_phase3_confirmation_py_index.md
scripts_session_state_py_index.md
templates_weekly_report_example_tsx_index.md  ← 含 10 个 @section 标记
```

---

## 三、版本历史

| 版本 | 日期 | 主要内容 |
| :--- | :--- | :--- |
| v1.0 | 2026-04-22 | 初始三阶段交互式构建流程 |
| v1.1 | 2026-04-22 | SessionState 统一持久化 + ComponentRecommender 类封装 + @section 标记 + Kahn 拓扑排序 |
| v1.2 | 2026-04-22 | 商业模式特有模块 + 阶段矩阵 + 数据洞察探针（口径诊断/北极星分解/因果链） |
| **v1.3** | **2026-04-22** | **phase3 接入 SessionState，三阶段断点续建完整闭环** |

---

## 四、当前核心缺口：组件扩展

### 4.1 现状对比

`component_library.md` 中规范了 **14 个组件**，但代码中仅实现了 **5 个**（`component_recommender.py` 注册）和 **8 个**（`weekly_report_example.tsx` 实现）。

**`component_recommender.py` 中已注册的 5 个组件：**

| 组件 key | 组件名 | 类型 | 优先级 |
| :--- | :--- | :---: | :---: |
| `scorecard` | 评分卡组件 | 首屏 | P0 |
| `attribution_waterfall` | 归因瀑布图/树状图组件 | 首屏 | P0 |
| `timeline` | 时间轴组件 | 首屏 | P0 |
| `anomaly_alert_list` | 异常告警列表组件 | 首屏 | P0 |
| `module_progress_card` | 模块进度卡片组件 | 详情 | P1 |

**`weekly_report_example.tsx` 中已实现的 8 个 React 组件：**

| 组件函数名 | 对应模块 | @section 位置 |
| :--- | :--- | :--- |
| `HealthScorecard` | 项目健康度诊断 | `hero_components`（L936） |
| `NorthStarChart` | 北极星指标归因 | `hero_components`（L1061） |
| `KpiAlertList` | KPI 监控与数据异常 | `hero_components`（L1169） |
| `MilestoneTimeline` | 里程碑进度 | `milestone_timeline`（L1256） |
| `ModuleCardItem` | 业务模块详情 | `module_progress_cards`（L1428） |
| `ModuleCardsGrid` | 业务模块详情（容器） | `module_progress_cards`（L1584） |
| `SecondaryModules` | 风险/决策/待办/问题 | `secondary_modules`（L1617） |
| `WeeklyReportDashboard` | 主仪表盘 | `main_dashboard_component`（L1841） |

### 4.2 待扩展的 9 个组件

以下组件在 `component_library.md` 中已有完整规范，但尚未在 `component_recommender.py` 注册，也未在 `weekly_report_example.tsx` 中实现：

| 优先级 | 组件名 | 类型 | 适用模块 | 说明 |
| :---: | :--- | :---: | :--- | :--- |
| **P0** | 北极星因子分解图 | 首屏 | 北极星指标归因 | 已有 `NorthStarChart` 但仅展示趋势，缺少因子分解树状结构 |
| **P0** | 多维健康度雷达图 | 首屏 | 项目健康度诊断 | 已有 `HealthScorecard` 但缺少雷达图形态 |
| **P0** | 业务阶段进度组件 | 首屏 | 里程碑进度 | 横向阶段进度条，展示当前所处阶段 |
| **P1** | 漏斗转化组件 | 详情 | 增长/获客/转化 | 适用于广告、电商、订阅等转化漏斗 |
| **P1** | 指标趋势矩阵 | 详情 | 多指标监控 | 多指标并排折线图矩阵，适合 KPI 监控 |
| **P1** | 用户分层气泡图 | 详情 | 用户分层运营 | 气泡图展示用户价值分层分布 |
| **P1** | 创作者/供给方生态图 | 详情 | 内容/社区/平台 | 供给侧健康度展示，适合双边市场 |
| **P1** | 单元经济模型卡片 | 详情 | 商业化/变现 | LTV/CAC/ROI 等单元经济指标卡片 |
| **P2** | 口径说明浮层 | 辅助 | 所有模块 | 点击指标名称弹出口径来源说明 |

---

## 五、组件扩展任务说明

### 5.1 扩展目标

完成上述 9 个组件的完整实现，使 `component_library.md` 中规范的所有组件均可被系统推荐和生成。

### 5.2 每个组件需要完成的工作

**工作一：在 `component_recommender.py` 中注册组件**

在 `COMPONENT_LIBRARY` 字典中新增组件条目，格式参考现有 5 个组件：

```python
"component_key": {
    "name": "组件中文名",
    "name_en": "Component English Name",
    "applicable_modules": ["适用模块名（中文）", "module_key_en"],
    "data_types": ["numeric", "trend", ...],  # 参见 component_library.md
    "display_dimensions": ["multi_metric", ...],
    "interaction_types": ["drill_down", "hover_detail", ...],
    "data_requirements": [
        "字段名 (field_name: 类型说明)",
        ...
    ],
    "presentation": "视觉呈现描述（一段话）",
    "drill_down": "点击后的跳转逻辑描述",
    "priority": "P0 | P1 | P2",
    "strengths": ["优势1", "优势2", "优势3"],
    "limitations": ["局限1", "局限2"],
},
```

同时在 `MODULE_FEATURE_MAP` 中为新适用的模块添加映射（如果该模块尚未有映射）。

**工作二：在 `weekly_report_example.tsx` 中实现 React 组件**

在对应的 `@section` 区域内新增 React 函数组件，遵循以下规范：

1. **TypeScript 接口**：在 `@section:types_and_interfaces` 区域新增 Props 接口定义
2. **组件实现**：在对应的 `@section` 区域实现组件，使用 `tailwindcss` 样式
3. **Mock 数据**：在 `@section:mock_data` 区域的 `mockData` 对象中新增对应的示例数据
4. **主仪表盘集成**：在 `WeeklyReportDashboard` 组件中集成新组件（可选，视组件类型决定）

**工作三：更新 `analysis_engine.py` 中的推荐逻辑**

确保 `_recommend_components_for_module()` 方法能够为新模块推荐新组件（检查 `MODULE_COMPONENT_MAPPING` 字典是否覆盖新组件）。

**工作四：运行 code-indexer 更新索引**

```bash
cd /home/ubuntu/skills/weekly-report-builder
python3 /home/ubuntu/skills/code-indexer/scripts/generate_index.py . --src-dirs scripts templates
```

### 5.3 扩展顺序建议

建议按以下顺序扩展，优先完成 P0 组件：

1. **北极星因子分解图**（P0）——已有 `NorthStarChart` 基础，扩展因子分解树状结构
2. **多维健康度雷达图**（P0）——已有 `HealthScorecard` 基础，扩展雷达图形态
3. **漏斗转化组件**（P1）——通用性强，适用于多种商业模式
4. **指标趋势矩阵**（P1）——适用于 KPI 监控场景
5. **业务阶段进度组件**（P0）——与阶段矩阵联动
6. **单元经济模型卡片**（P1）——商业化模块必备
7. **用户分层气泡图**（P1）——用户运营模块专用
8. **创作者/供给方生态图**（P1）——内容/平台类业务专用
9. **口径说明浮层**（P2）——辅助组件，最后实现

### 5.4 关键约束

- `weekly_report_example.tsx` 中的 `// Section 5: 原子组件` 锚点**不可删除**（`code_generator.py` 依赖该锚点注入生成代码）
- 新增 `@section` 标记必须使用 `// @section:{snake_case_name} - {描述}` 格式（code-indexer 规范）
- 组件 key 命名使用 `snake_case`，与 `MODULE_FEATURE_MAP` 中的 `aliases` 保持一致
- 每个新组件必须有对应的 `data_requirements` 字段，供阶段三确认流程生成询问文案

---

## 六、断点续建机制说明

v1.3 完成了三阶段统一持久化，新 Agent 在开发和测试过程中可利用此机制：

```python
from scripts.session_state import SessionState

# 恢复已有会话
ss = SessionState.load("session_id", state_dir="./state")
print(ss.get_resume_summary())

# 查看阶段三配置结果
configs = ss.get_phase3_confirmed_configs()
```

会话文件存储路径：`./state/{session_id}_session.json`

---

## 七、测试验证方法

每个新组件完成后，运行以下验证：

```bash
# 1. component_recommender.py 单元测试
cd /home/ubuntu/skills/weekly-report-builder/scripts
python3 component_recommender.py

# 2. 端到端三阶段闭环测试（验证新组件能被正确推荐）
python3 analysis_engine.py

# 3. 更新 code-indexer 索引
cd /home/ubuntu/skills/weekly-report-builder
python3 /home/ubuntu/skills/code-indexer/scripts/generate_index.py . --src-dirs scripts templates
```

---

## 八、GitHub 仓库信息

- **仓库**：`gdszyy/ai-secretary-architecture`
- **文档目录**：`docs/weekly-report-builder/`
- **Skill 本体路径**：`/home/ubuntu/skills/weekly-report-builder/`（沙箱本地，不在 Git 追踪范围）
- **同步方式**：将 `SKILL.md` 和关键文档 `cp` 到 `docs/weekly-report-builder/` 后 `git push`
- **最新 commit**：`6d947f0`（v1.3 phase3 接入 SessionState）

---

## 九、下一迭代建议（供参考）

完成组件扩展后，建议进行以下迭代：

1. **`code_generator.py` 适配新组件**：确保生成引擎能为新组件生成正确的 TSX 代码片段
2. **组件 × 商业模式推荐矩阵完善**：在 `component_library.md` 第 4.2 节中补充新组件的商业模式推荐关系
3. **`weekly_report_example.tsx` 响应式优化**：当前示例为桌面端优先，可补充移动端适配

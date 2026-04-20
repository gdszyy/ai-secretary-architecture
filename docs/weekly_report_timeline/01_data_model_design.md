# 「周报模块进度时间线」功能设计文档 (修订版)

## 1. 需求背景与目标

当前 `kanban-v2` 的周报功能仅在右侧面板和模块详情页展示简单的纯文本列表（`weekly_updates`），数据来源单一（仅群聊摘要），且缺乏时间维度的全局切换能力。

为了提升周报的实用性和信息丰富度，本次功能设计旨在实现以下目标：
1. **多源数据整合**：以**飞书多维表格周报（XP团队周报）**为第一数据来源，结合 Meegle 进度、群内讨论内容（需对模块进度有补充和推进作用）生成综合周报。
2. **时间线分段展示**：为模块的进度分出单独的“本周”（每周二至下周二）进度段。
3. **全局与局部切换**：支持在外部（全局）整体切换周报时间段，并在模块卡片或详情中点击进度段切换查看对应周的进度情况。

## 2. 数据模型扩展设计

为了支持多源数据和按周切换，需要对现有的 `DashboardData` JSON 契约进行扩展。

### 2.1 扩展 `WeeklyUpdate` 类型

在 `kanban-v2/client/src/lib/types.ts` 中，将原有的纯文本 `update` 扩展为结构化的多源数据对象：

```typescript
export interface WeeklyUpdateSource {
  xp_weekly_report?: string;    // 飞书多维表格周报（第一数据来源，按模块提取的成员填报内容）
  bitable_summary?: string;     // 多维表格需求状态与备注
  meegle_progress?: string;     // Meegle 进度（如：完成 3 个 Story，新增 2 个 Defect）
  chat_insights?: string[];     // 群内讨论内容（对进度有补充和推进作用的关键话题）
}

export interface WeeklyUpdate {
  week: string;                 // 周标识，如 "2026-16"
  start_date: string;           // 周期开始时间（上周二）
  end_date: string;             // 周期结束时间（本周二）
  update: string;               // 综合摘要（由 AI 秘书基于多源数据生成的总结）
  sources: WeeklyUpdateSource;  // 多源数据明细
}
```

### 2.2 扩展全局周报索引

在 `DashboardData` 根节点增加全局的周报周期列表，用于支持外部整体切换：

```typescript
export interface WeeklyPeriod {
  week: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

export interface DashboardData {
  // ... 现有字段
  weekly_periods: WeeklyPeriod[]; // 全局周报周期列表，倒序排列
}
```

## 3. 数据生成与注入流程

数据生成主要在 `ai-secretary-architecture` 仓库中通过离线脚本或定时任务完成。

### 3.1 数据源采集

1. **飞书多维表格周报（核心新增）**：
   *   **来源**：飞书 Base `CyDxbUQGGa3N2NsVanMjqdjxp6e`，Table `tblVuYt2CwWgdj6g`。
   *   **采集方式**：复用 `xp-weekly-report` 技能中的 `fetch_weekly_data.py` 逻辑，提取指定日期（本周二）各成员（VoidZ, Yark, Starvia, Zoey）填写的“本周”和“下周”工作内容。
   *   **数据处理**：编写解析脚本，将成员填写的纯文本周报内容，通过 LLM 或正则匹配，映射归类到对应的功能模块（Module ID）下，作为 `xp_weekly_report` 字段的值。
2. **多维表格需求状态**：通过 `scripts/lark_bitable_client.py` 拉取 Lark 多维表格中各模块的最新状态和备注。
3. **Meegle 进度**：通过 `scripts/meegle_client.py` 拉取各模块关联的 Story 和 Defect 在本周内的状态变更记录。
4. **群内讨论内容**：复用 `scripts/extract_weekly_insights.py`，提取本周内与各模块相关的关键话题和决策。

### 3.2 AI 综合摘要生成

编写新的数据聚合脚本（如 `scripts/generate_comprehensive_weekly.py`），将上述四源数据按模块聚合，并调用 LLM 生成综合摘要：

*   **Prompt 逻辑**：输入飞书成员周报（最高优先级）、多维表格状态、Meegle 变更统计、群聊关键话题，要求 LLM 输出一段精炼的综合摘要，并保留原始数据作为 `sources` 字段。

### 3.3 数据注入

修改 `scripts/inject_weekly_updates.py`，将生成的结构化周报数据注入到 `data/dashboard_data.json` 的 `modules[].weekly_updates` 和全局 `weekly_periods` 中。

## 4. 前端交互与组件设计

在 `xpbet-frontend-components` 仓库的 `kanban-v2` 子应用中进行 UI 改造。

### 4.1 全局周报切换器 (Global Weekly Switcher)

在 `Home.tsx` 的右侧面板（`tab === "weekly"`）顶部，增加全局周切换控件：

*   **UI 表现**：一个下拉选择器或左右切换按钮，展示 `weekly_periods` 列表（如 "W16 (4/14 - 4/21)"）。
*   **交互逻辑**：默认选中 `is_current === true` 的周期。切换时，更新本地状态 `selectedWeek`，并过滤展示所有模块在该周的 `WeeklyUpdate`。

### 4.2 模块卡片进度段展示

在中央矩阵的模块卡片上，增加本周进度的微型可视化：

*   **UI 表现**：在卡片底部增加一个微型时间线或进度条，高亮显示本周（`selectedWeek`）的进度状态。
*   **交互逻辑**：点击该区域，可直接在右侧面板或弹窗中展开该模块本周的详细多源周报。

### 4.3 模块详情页时间线 (ModuleDetail.tsx)

重构 `ModuleDetail.tsx` 右侧的“周报更新”区域，将其升级为可交互的时间线：

*   **UI 表现**：以垂直时间线的形式展示历史周报。每个节点代表一周。
*   **内容层级**：
    *   **摘要层**：默认展示 AI 综合摘要（`update`）。
    *   **证据层（可展开）**：点击展开后，分块展示 `sources` 中的飞书成员周报（优先展示）、多维表格、Meegle 和群聊洞察明细。
*   **交互逻辑**：支持点击时间线节点切换高亮，并与全局 `selectedWeek` 状态联动（若通过全局状态管理）。

## 5. 实施步骤建议

1. **后端/数据层**：在 `ai-secretary-architecture` 中开发多源数据聚合脚本，**重点实现飞书周报文本到模块的映射逻辑**，更新 JSON 契约。
2. **前端/类型层**：在 `kanban-v2/client/src/lib/types.ts` 中更新接口定义。
3. **前端/UI层**：依次改造 `Home.tsx` 的右侧面板、模块卡片，以及 `ModuleDetail.tsx` 的时间线组件。
4. **联调与测试**：运行数据注入脚本，验证前端按周切换和多源数据展示的正确性。

## 6. 遵循的架构规范

*   **活文档契约**：完成代码修改后，需同步更新 `kanban-v2.md` 和 `docs/kanban_data_schema_v2.md`。
*   **大文件修改**：修改 `Home.tsx` 时，必须先查阅 `auto_index` 获取目标函数（如 `SidebarStatus`）的行号范围，避免全量读取。
*   **Single Source of Truth**：前端完全依赖 `dashboard_data.json` 渲染，不引入额外的状态同步逻辑。

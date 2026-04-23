"""
代码生成引擎 (Code Generator)
==============================
weekly-report-builder Skill 的最终出口模块（Sprint 3 - 异常分支 H）

功能：
1. 模板注入器：读取 dashboard_template.tsx，根据 phase3_confirmation.py 输出的
   组件配置清单，将真实数据结构和业务逻辑注入模板。
2. 组件代码生成器：为每个选定模块生成对应的 React 组件代码（评分卡、归因瀑布图、
   时间轴、异常告警列表、模块进度卡片），绑定正确数据接口。
3. 导航代码生成器：根据 navigation_designer.py 的导航图谱，生成下钻跳转和
   金刚区入口的交互代码。
4. 异常分支 H 的代码修改循环：支持用户验收时针对特定组件或样式的精准修改，
   循环至验收通过。
5. 最终输出完整可运行的周报网页单文件（weekly_report.tsx）。

技术栈: React + TypeScript + TailwindCSS
"""

import json
import logging
import os
import re
import copy
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("code_generator")

# ─────────────────────────────────────────────────────────────────────────────
# 常量定义
# ─────────────────────────────────────────────────────────────────────────────

# 组件类型到 Section ID 的映射
COMPONENT_TO_SECTION: Dict[str, str] = {
    # ── 原始 5 个组件（中文名） ────────────────────────────────────────────────
    "评分卡组件":       "hero",
    "归因瀑布图组件":   "hero",
    "告警列表组件":     "hero",
    "时间轴组件":       "milestone",
    "模块进度卡片组件": "modules",
    # ── 新增 9 个组件（component_key） ────────────────────────────────────────
    "north_star_decomposition":   "hero",       # 北极星因子分解图 → 首屏
    "health_radar_chart":         "hero",       # 多维健康度雷达图 → 首屏
    "stage_progress_bar":         "milestone",  # 业务阶段进度组件 → 里程碑
    "conversion_funnel":          "modules",    # 漏斗转化组件 → 业务模块
    "trend_matrix_grid":          "kpi",        # 指标趋势矩阵 → KPI 区
    "user_segmentation_bubble":   "modules",    # 用户分层气泡图 → 业务模块
    "ecosystem_health_map":       "modules",    # 创作者/供给方生态图 → 业务模块
    "unit_economics_card":        "secondary",  # 单元经济模型卡片 → 辅助信息
    "milestone_card_list":        "milestone",  # 里程碑卡片 → 里程碑
    "metric_definition_popover":  None,         # 口径说明浮层 → 全局辅助，不绑定 Section
    # ── 英文 React 组件名别名 ─────────────────────────────────────────────────
    "HealthScorecard":            "hero",
    "NorthStarChart":             "hero",
    "KpiAlertList":               "hero",
    "MilestoneTimeline":          "milestone",
    "ModuleCardsGrid":            "modules",
    "NorthStarDecomposition":     "hero",
    "HealthRadarChart":           "hero",
    "StageProgressBar":           "milestone",
    "ConversionFunnel":           "modules",
    "TrendMatrixGrid":            "kpi",
    "UserSegmentationBubble":     "modules",
    "EcosystemHealthMap":         "modules",
    "UnitEconomicsCard":          "secondary",
    "MilestoneCardList":          "milestone",
    "MetricDefinitionPopover":    None,
}

# 组件类型到 React 组件名的映射
COMPONENT_TO_REACT: Dict[str, str] = {
    # ── 原始 5 个组件 ─────────────────────────────────────────────────────────
    "评分卡组件":       "HealthScorecard",
    "归因瀑布图组件":   "NorthStarChart",
    "告警列表组件":     "KpiAlertList",
    "时间轴组件":       "MilestoneTimeline",
    "模块进度卡片组件": "ModuleCardsGrid",
    # ── 新增 9 个组件（component_key → React 组件名） ─────────────────────────
    "north_star_decomposition":   "NorthStarDecomposition",
    "health_radar_chart":         "HealthRadarChart",
    "stage_progress_bar":         "StageProgressBar",
    "conversion_funnel":          "ConversionFunnel",
    "trend_matrix_grid":          "TrendMatrixGrid",
    "user_segmentation_bubble":   "UserSegmentationBubble",
    "ecosystem_health_map":       "EcosystemHealthMap",
    "unit_economics_card":        "UnitEconomicsCard",
    "milestone_card_list":        "MilestoneCardList",
    "metric_definition_popover":  "MetricDefinitionPopover",
}

# 组件类型到数据字段的映射
COMPONENT_TO_DATA_FIELD: Dict[str, str] = {
    # ── 原始 5 个组件 ─────────────────────────────────────────────────────────
    "评分卡组件":       "healthScore",
    "归因瀑布图组件":   "northStar",
    "告警列表组件":     "kpiAlerts",
    "时间轴组件":       "milestones",
    "模块进度卡片组件": "modules",
    # ── 新增 9 个组件（component_key → mockData 字段名） ─────────────────────
    "north_star_decomposition":   "northStarDecomposition",
    "health_radar_chart":         "healthRadar",
    "stage_progress_bar":         "stageProgress",
    "conversion_funnel":          "conversionFunnel",
    "trend_matrix_grid":          "trendMatrix",
    "user_segmentation_bubble":   "userSegmentation",
    "ecosystem_health_map":       "ecosystemHealth",
    "unit_economics_card":        "unitEconomics",
    "milestone_card_list":        "milestoneCards",
    "metric_definition_popover":  "metricDefinitions",
}

# 默认模板路径（相对于本脚本所在目录）
DEFAULT_TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "templates", "dashboard_template.tsx"
)

# ─────────────────────────────────────────────────────────────────────────────
# Section 1: 模板注入器 (Template Injector)
# ─────────────────────────────────────────────────────────────────────────────

class TemplateInjector:
    """
    模板注入器

    读取 dashboard_template.tsx 基础骨架，根据 phase3_confirmation.py 输出的
    组件配置清单，将真实数据结构、项目元信息和业务逻辑注入模板。
    """

    def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH):
        self.template_path = template_path
        self._template_content: Optional[str] = None

    def load_template(self) -> str:
        """加载模板文件内容"""
        if self._template_content is not None:
            return self._template_content

        if not os.path.exists(self.template_path):
            raise FileNotFoundError(
                f"模板文件不存在: {self.template_path}\n"
                f"请确认 dashboard_template.tsx 已放置于 templates/ 目录。"
            )

        with open(self.template_path, "r", encoding="utf-8") as f:
            self._template_content = f.read()

        logger.info(f"模板文件加载成功，共 {len(self._template_content)} 字符")
        return self._template_content

    def inject_meta(
        self,
        content: str,
        project_name: str,
        report_period: str,
        version: str = "v1.0",
    ) -> str:
        """注入项目元信息（项目名称、报告周期、版本号）"""
        updated_at = datetime.now().strftime("%Y/%m/%d")

        # 替换 mockData 中的 meta 字段
        meta_pattern = r"(meta:\s*\{[^}]*projectName:\s*')[^']*('[^}]*reportPeriod:\s*')[^']*('[^}]*updatedAt:[^,]*,[^}]*version:\s*')[^']*('[^}]*\})"

        # 更精确的逐字段替换
        content = re.sub(
            r"(projectName:\s*')[^']*(')",
            rf"\g<1>{project_name}\g<2>",
            content
        )
        content = re.sub(
            r"(reportPeriod:\s*')[^']*(')",
            rf"\g<1>{report_period}\g<2>",
            content
        )
        content = re.sub(
            r"(updatedAt:[^,\n]*new Date\(\)[^,\n]*)",
            f"updatedAt: '{updated_at}'",
            content
        )
        content = re.sub(
            r"(version:\s*')[^']*(')",
            rf"\g<1>{version}\g<2>",
            content
        )

        logger.info(f"元信息注入完成: {project_name} / {report_period}")
        return content

    def inject_section_config(
        self,
        content: str,
        enabled_sections: List[str],
    ) -> str:
        """
        根据启用的 Section 列表，更新 defaultSectionConfig 中的 enabled 字段。

        :param enabled_sections: 启用的 section id 列表，如 ['hero', 'kpi', 'milestone']
        """
        all_sections = ["hero", "kpi", "milestone", "modules", "secondary", "risk", "finance", "team", "decisions"]

        for section_id in all_sections:
            is_enabled = section_id in enabled_sections
            # 匹配 { id: 'hero', ... enabled: true/false, ... }
            pattern = rf"(\{{ id: '{section_id}'[^}}]*enabled:\s*)(true|false)"
            replacement = rf"\g<1>{'true' if is_enabled else 'false'}"
            content = re.sub(pattern, replacement, content)

        logger.info(f"Section 配置注入完成，启用: {enabled_sections}")
        return content

    def inject_data_placeholder_comment(
        self,
        content: str,
        component_configs: List[Dict[str, Any]],
    ) -> str:
        """
        在 mockData 区域顶部注入数据绑定说明注释，
        便于开发者快速定位需要替换的数据字段。
        """
        comment_lines = [
            "// ─────────────────────────────────────────────────────────────────────────────",
            "// ⚠️  以下 mockData 由 weekly-report-builder 代码生成引擎自动注入",
            "// 请将各字段替换为真实业务数据，数据绑定关系如下：",
            "//",
        ]
        for cfg in component_configs:
            module_name = cfg.get("module_name", "未知模块")
            component_name = cfg.get("component_name", "未知组件")
            data_source = cfg.get("data_source", "待确认")
            display_fields = cfg.get("display_fields", "默认字段")
            comment_lines.append(
                f"//   [{module_name}] → {component_name} | 数据来源: {data_source} | 展示字段: {display_fields}"
            )
        comment_lines.append("// ─────────────────────────────────────────────────────────────────────────────")

        comment_block = "\n".join(comment_lines) + "\n"

        # 在 mockData 声明之前插入注释
        content = content.replace(
            "const mockData: DashboardData = {",
            comment_block + "const mockData: DashboardData = {"
        )

        return content

    def inject(
        self,
        component_configs: List[Dict[str, Any]],
        project_name: str = "项目周报仪表盘",
        report_period: str = "",
        version: str = "v1.0",
    ) -> str:
        """
        主入口：执行完整的模板注入流程

        :param component_configs: phase3_confirmation.py 输出的组件配置清单
        :param project_name: 项目名称
        :param report_period: 报告周期，如 "2026-W16"
        :param version: 版本号
        :return: 注入后的完整 TSX 代码字符串
        """
        if not report_period:
            # 自动生成当前周期
            now = datetime.now()
            week_num = now.isocalendar()[1]
            report_period = f"{now.year}-W{week_num:02d}"

        content = self.load_template()
        content = self.inject_meta(content, project_name, report_period, version)

        # 确定需要启用的 Section
        enabled_sections = set(["hero"])  # hero 始终启用
        for cfg in component_configs:
            comp_name = cfg.get("component_name", "")
            section_id = COMPONENT_TO_SECTION.get(comp_name)
            if section_id:
                enabled_sections.add(section_id)

        # 如果有辅助信息类组件，启用 secondary
        secondary_keywords = ["风险", "决策", "待办", "问题", "Risk", "Decision", "Todo", "Issue"]
        for cfg in component_configs:
            module_name = cfg.get("module_name", "")
            if any(kw in module_name for kw in secondary_keywords):
                enabled_sections.add("secondary")

        content = self.inject_section_config(content, list(enabled_sections))
        content = self.inject_data_placeholder_comment(content, component_configs)

        logger.info("模板注入完成")
        return content


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: 组件代码生成器 (Component Code Generator)
# ─────────────────────────────────────────────────────────────────────────────

class ComponentCodeGenerator:
    """
    组件代码生成器

    为每个选定模块生成对应的 React 组件代码片段，
    包含数据接口绑定、Props 类型定义和示例用法注释。
    """

    # 各组件的代码片段模板
    COMPONENT_SNIPPETS: Dict[str, str] = {

        "评分卡组件": '''
// ── 健康度评分卡 (HealthScorecard) ────────────────────────────────────────
// 数据来源: {data_source}
// 展示字段: {display_fields}
// 下钻逻辑: {drill_down_logic}
//
// 使用示例:
//   <HealthScorecard
//     data={{data.healthScore}}
//     onClick={{() => {drill_down_handler}}}
//     onDimensionClick={{(dim) => console.log('维度下钻:', dim)}}
//   />
//
// 数据接口 (HealthScore):
//   score: number          — 综合评分 (0-100)
//   trend: TrendDirection  — 趋势方向 ('up' | 'down' | 'stable')
//   phase: string          — 阶段描述，如"蓄力期"
//   summary: string        — 阶段简要说明
//   dimensions: Array<{{   — 各维度评分
//     name: string;
//     score: number;
//     prevScore?: number;
//     color?: string;       — Tailwind 颜色类名，如 "bg-emerald-500"
//   }}>
//   history?: Array<{{ label: string; value: number }}>  — 历史评分序列
''',

        "归因瀑布图组件": '''
// ── 北极星指标归因图 (NorthStarChart) ─────────────────────────────────────
// 数据来源: {data_source}
// 展示字段: {display_fields}
// 下钻逻辑: {drill_down_logic}
//
// 使用示例:
//   <NorthStarChart
//     data={{data.northStar}}
//     onClick={{() => {drill_down_handler}}}
//     onFactorClick={{(id, moduleId) => {drill_down_handler}}}
//   />
//
// 数据接口 (NorthStarMetric):
//   metric: string         — 指标名称，如"DAU"
//   value: number          — 当前值
//   unit?: string          — 单位，如"万"
//   change: number         — 环比变化量
//   changeRate: string     — 环比变化率，如"+5.2%"
//   trend: TrendDirection  — 变化趋势
//   target?: number        — 目标值
//   attribution: Array<{{  — 归因因素列表（按贡献绝对值降序）
//     id: string;
//     factor: string;       — 因素名称
//     contribution: number; — 贡献量（正值=正向，负值=负向）
//     moduleId?: string;    — 所属业务模块 ID（用于下钻）
//   }}>
''',

        "告警列表组件": '''
// ── KPI 告警列表 (KpiAlertList) ───────────────────────────────────────────
// 数据来源: {data_source}
// 展示字段: {display_fields}
// 下钻逻辑: {drill_down_logic}
//
// 使用示例:
//   <KpiAlertList
//     alerts={{data.kpiAlerts}}
//     onAlertClick={{(id, kpiId) => {drill_down_handler}}}
//     maxVisible={{5}}
//   />
//
// 数据接口 (KpiAlert[]):
//   id: string             — 告警 ID
//   level: AlertPriority   — 优先级 ('P0' | 'P1' | 'P2')
//   title: string          — 告警标题
//   description: string    — 详细描述
//   triggeredAt: string    — 触发时间
//   impact?: string        — 影响范围
//   status: AlertStatus    — 处理状态 ('open' | 'in_progress' | 'resolved')
//   kpiId?: string         — 关联指标 ID（用于下钻）
''',

        "时间轴组件": '''
// ── 里程碑时间轴 (MilestoneTimeline) ──────────────────────────────────────
// 数据来源: {data_source}
// 展示字段: {display_fields}
// 下钻逻辑: {drill_down_logic}
//
// 使用示例:
//   <MilestoneTimeline
//     milestones={{data.milestones}}
//     onNodeClick={{(id) => {drill_down_handler}}}
//   />
//
// 数据接口 (Milestone[]):
//   id: string                — 里程碑 ID
//   version: string           — 版本号，如"v2.0"
//   title: string             — 里程碑标题
//   date: string              — 计划/完成日期
//   status: MilestoneStatus   — 状态 ('done' | 'active' | 'upcoming')
//   description: string       — 详细描述
//   achievements: string[]    — 核心成就列表
//   nextGoals?: string[]      — 下阶段目标
//   path?: string[]           — 实现路径
//   resources?: string[]      — 资源需求
''',

        "模块进度卡片组件": '''
// ── 业务模块进度卡片网格 (ModuleCardsGrid) ────────────────────────────────
// 数据来源: {data_source}
// 展示字段: {display_fields}
// 下钻逻辑: {drill_down_logic}
//
// 使用示例:
//   <ModuleCardsGrid
//     modules={{data.modules}}
//     onModuleClick={{(id) => {drill_down_handler}}}
//     onMilestoneClick={{(moduleId, milestone) => {drill_down_handler}}}
//     onMetricClick={{(moduleId, label) => {drill_down_handler}}}
//   />
//
// 数据接口 (ModuleCard[]):
//   id: string             — 模块 ID
//   name: string           — 模块中文名
//   nameEn?: string        — 模块英文名
//   owner: string          — 负责人
//   priority: number       — 优先级 (1=最高)
//   progress: number       — 整体进度百分比 (0-100)
//   status: StatusLevel    — 状态 ('success'|'warning'|'danger'|'info'|'neutral')
//   currentFocus: string   — 当前核心工作描述
//   nextMilestone: string  — 下一里程碑名称
//   nextMilestoneDate: string — 下一里程碑计划日期
//   metrics?: Array<{{     — 核心指标列表
//     label: string; value: string; target: string;
//   }}>
//   progressHistory?: Array<{{ date: string; progress: number }}>
''',
    }

    def generate_component_snippet(self, config: Dict[str, Any]) -> str:
        """
        为单个组件配置生成代码片段注释

        :param config: phase3_confirmation.py 输出的单个组件配置
        :return: 格式化的代码片段字符串
        """
        component_name = config.get("component_name", "")
        data_source = config.get("data_source", "待确认")
        display_fields = config.get("display_fields", "默认字段")
        drill_down_logic = config.get("drill_down_logic", "暂不下钻")

        # 生成下钻处理器代码
        if drill_down_logic == "暂不下钻" or not drill_down_logic:
            drill_down_handler = "() => { /* 暂不下钻 */ }"
        else:
            # 从下钻逻辑描述中提取目标模块
            drill_down_handler = f"() => scrollToSection('{drill_down_logic}')"

        template = self.COMPONENT_SNIPPETS.get(component_name, "")
        if not template:
            # 未知组件类型，生成通用注释
            template = f"""
// ── 自定义组件: {component_name} ─────────────────────────────────────────
// 数据来源: {{data_source}}
// 展示字段: {{display_fields}}
// 下钻逻辑: {{drill_down_logic}}
// ⚠️ 此组件类型未在标准库中找到，请手动实现对应的 React 组件。
"""

        snippet = template.format(
            data_source=data_source,
            display_fields=display_fields,
            drill_down_logic=drill_down_logic,
            drill_down_handler=drill_down_handler,
        )

        return snippet

    def generate_all_snippets(
        self, component_configs: List[Dict[str, Any]]
    ) -> str:
        """
        为所有组件配置生成完整的代码片段集合

        :param component_configs: 组件配置清单列表
        :return: 合并后的代码片段字符串
        """
        snippets = []
        for cfg in component_configs:
            snippet = self.generate_component_snippet(cfg)
            snippets.append(snippet)

        header = """
// =============================================================================
// 组件数据绑定说明 (由 weekly-report-builder 代码生成引擎自动生成)
// 以下注释描述了各组件的数据接口和下钻逻辑，请按说明替换真实数据
// =============================================================================
"""
        return header + "\n".join(snippets)

    def generate_drill_down_handlers(
        self, component_configs: List[Dict[str, Any]]
    ) -> str:
        """
        生成下钻处理器函数集合（注入到主组件 Props 中）

        :param component_configs: 组件配置清单列表
        :return: 下钻处理器代码字符串
        """
        handlers = []
        seen_targets = set()

        for cfg in component_configs:
            drill_down = cfg.get("drill_down_logic", "暂不下钻")
            component_name = cfg.get("component_name", "")
            module_name = cfg.get("module_name", "")

            if drill_down == "暂不下钻" or not drill_down:
                continue

            # 避免重复生成相同目标的处理器
            target_key = f"{component_name}_{drill_down}"
            if target_key in seen_targets:
                continue
            seen_targets.add(target_key)

            # 根据组件类型生成对应的处理器
            react_comp = COMPONENT_TO_REACT.get(component_name, "Unknown")
            handler_name = f"handle{react_comp}DrillDown"

            handler_code = f"""
  // [{module_name}] 下钻处理器 → {drill_down}
  const {handler_name} = useCallback(() => {{
    // TODO: 实现跳转逻辑，目标: {drill_down}
    // 示例: navigate('/{drill_down.replace(' ', '-').lower()}');
    const targetSection = document.getElementById('section-{drill_down.split('(')[0].strip().lower().replace(' ', '-')}');
    if (targetSection) {{
      targetSection.scrollIntoView({{ behavior: 'smooth' }});
    }}
  }}, []);"""
            handlers.append(handler_code)

        if not handlers:
            return "  // 所有模块均设置为「暂不下钻」，无需生成下钻处理器\n"

        return "\n".join(handlers)


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: 导航代码生成器 (Navigation Code Generator)
# ─────────────────────────────────────────────────────────────────────────────

class NavigationCodeGenerator:
    """
    导航代码生成器

    根据 navigation_designer.py 的导航图谱，生成：
    1. 下钻跳转的交互代码（onClick 回调）
    2. 金刚区（Navbar）入口的导航菜单代码
    3. 锚点跳转辅助函数
    """

    def generate_navbar_component(
        self, navigation_graph: List[Dict[str, Any]]
    ) -> str:
        """
        生成金刚区导航菜单组件代码

        :param navigation_graph: navigation_designer.py 输出的导航图谱
        :return: React 组件代码字符串
        """
        navbar_items = [
            edge for edge in navigation_graph
            if edge.get("jump_type") == "navbar"
        ]

        if not navbar_items:
            return "// 无金刚区导航项\n"

        items_code = []
        for item in navbar_items:
            target = item.get("target_module", "")
            # 生成锚点 ID（从模块名提取）
            anchor_id = self._module_name_to_anchor(target)
            items_code.append(
                f'  {{ id: "{anchor_id}", label: "{target}", href: "#{anchor_id}" }},'
            )

        items_str = "\n".join(items_code)

        return f"""
// ── 金刚区导航菜单 (由 navigation_designer.py 图谱自动生成) ──────────────
// 导航项列表
const navbarItems = [
{items_str}
];

// 金刚区导航组件
function GlobalNavbar() {{
  return (
    <nav
      className="sticky top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700"
      aria-label="金刚区快捷导航"
    >
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-10 py-3 flex items-center gap-3 overflow-x-auto">
        <span className="text-xs font-semibold text-slate-400 shrink-0">快捷跳转</span>
        {{navbarItems.map((item) => (
          <a
            key={{item.id}}
            href={{item.href}}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors shrink-0 whitespace-nowrap"
            onClick={{(e) => {{
              e.preventDefault();
              document.getElementById(item.id)?.scrollIntoView({{ behavior: 'smooth' }});
            }}}}
          >
            {{item.label.split(' (')[0]}}
          </a>
        ))}}
      </div>
    </nav>
  );
}}
"""

    def generate_drill_down_map(
        self, navigation_graph: List[Dict[str, Any]]
    ) -> str:
        """
        生成下钻路径映射表代码

        :param navigation_graph: navigation_designer.py 输出的导航图谱
        :return: TypeScript 映射表代码字符串
        """
        drill_down_items = [
            edge for edge in navigation_graph
            if edge.get("jump_type") == "drill_down"
        ]

        if not drill_down_items:
            return "// 无下钻路径配置\nconst drillDownMap: Record<string, string> = {};\n"

        entries = []
        for item in drill_down_items:
            source = item.get("source_module", "")
            target = item.get("target_module", "")
            anchor = self._module_name_to_anchor(target)
            entries.append(f'  "{source}": "{anchor}",')

        entries_str = "\n".join(entries)

        return f"""
// ── 下钻路径映射表 (由 navigation_designer.py 图谱自动生成) ──────────────
// 格式: {{ 源模块名: 目标锚点 ID }}
const drillDownMap: Record<string, string> = {{
{entries_str}
}};

// 下钻跳转辅助函数
function drillDownTo(sourceName: string): void {{
  const targetAnchor = drillDownMap[sourceName];
  if (targetAnchor) {{
    const el = document.getElementById(targetAnchor);
    if (el) {{
      el.scrollIntoView({{ behavior: 'smooth' }});
    }} else {{
      console.warn(`[下钻跳转] 目标锚点 #${{targetAnchor}} 未找到`);
    }}
  }} else {{
    console.info(`[下钻跳转] 模块 "${{sourceName}}" 未配置下钻路径`);
  }}
}}
"""

    def generate_scroll_helper(self) -> str:
        """生成页面滚动辅助函数"""
        return """
// ── 页面滚动辅助函数 ──────────────────────────────────────────────────────
function scrollToSection(sectionId: string): void {
  const el = document.getElementById(sectionId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
"""

    def generate_navigation_code(
        self, navigation_result: Dict[str, Any]
    ) -> str:
        """
        主入口：根据完整导航图谱生成所有导航相关代码

        :param navigation_result: navigation_designer.py 的完整输出
        :return: 合并后的导航代码字符串
        """
        if navigation_result.get("status") != "success":
            logger.warning("导航图谱状态异常，将生成空导航代码")
            return "// ⚠️ 导航图谱生成失败，请检查 navigation_designer.py 输出\n"

        nav_graph = navigation_result.get("data", {}).get("navigation_graph", [])
        summary = navigation_result.get("data", {}).get("summary", "")

        code_parts = [
            f"// 导航图谱摘要: {summary}",
            self.generate_scroll_helper(),
            self.generate_drill_down_map(nav_graph),
            self.generate_navbar_component(nav_graph),
        ]

        return "\n".join(code_parts)

    @staticmethod
    def _module_name_to_anchor(module_name: str) -> str:
        """
        将模块名转换为 DOM 锚点 ID。
        支持中文模块名、英文别名和 component_key 三种输入形式。
        修复历史问题：财务情况/团队构成/决策待办等均有独立锚点，
        section-secondary 仅作为通用辅助信息区兜底。
        """
        # 提取括号前的名称，去除首尾空白
        name = module_name.split("(")[0].strip()
        # ── 完整锚点映射表 ────────────────────────────────────────────────────
        mapping = {
            # 首屏模块 (P0)
            "项目健康度诊断":        "section-health",
            "health_score":          "section-health",
            "北极星指标归因":        "section-north-star",
            "north_star_attribution": "section-north-star",
            "KPI 监控与数据异常":    "section-kpi",
            "KPI监控与数据异常":     "section-kpi",
            "kpi_monitor":           "section-kpi",
            "里程碑进度":            "section-timeline",
            "milestone_progress":    "section-timeline",
            # 其他模块 (P1/P2) — 各自独立锚点
            "业务模块详情":          "section-modules",
            "module_details":        "section-modules",
            "风险与问题登记册":      "section-risk",
            "risk_register":         "section-risk",
            "财务情况":              "section-finance",
            "financial_status":      "section-finance",
            "团队构成与动态":        "section-team",
            "team_org":              "section-team",
            "决策与待办事项":        "section-decisions",
            "decisions_todos":       "section-decisions",
            # 全局辅助
            "全局辅助":              "section-global",
            "global_auxiliary":      "section-global",
            # 通用辅助信息区（兜底）
            "辅助信息":              "section-secondary",
        }
        # 精确匹配
        if name in mapping:
            return mapping[name]
        # 模糊匹配（包含关系）
        for key, anchor in mapping.items():
            if key in name or name in key:
                return anchor
        # 最终兜底：将中文/英文名转为小写连字符格式
        anchor = re.sub(r"[^\w\s-]", "", name.lower())
        anchor = re.sub(r"\s+", "-", anchor.strip())
        return f"section-{anchor}" if anchor else "section-unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: 异常分支 H — 代码修改循环 (Branch H: Code Modification Loop)
# ─────────────────────────────────────────────────────────────────────────────

class BranchHModificationLoop:
    """
    异常分支 H：代码修改循环

    支持用户验收时针对特定组件或样式的精准修改，循环至验收通过。

    修改类型：
    - component_style: 修改组件样式（颜色、字体、间距等）
    - component_data:  修改组件数据绑定
    - section_toggle:  启用/禁用某个 Section
    - custom_code:     注入自定义代码片段
    - meta_update:     更新项目元信息
    """

    MODIFICATION_TYPES = {
        "component_style": "修改组件样式",
        "component_data":  "修改数据绑定",
        "section_toggle":  "启用/禁用 Section",
        "custom_code":     "注入自定义代码",
        "meta_update":     "更新项目元信息",
    }

    def __init__(self):
        self.modification_history: List[Dict[str, Any]] = []

    def parse_modification_request(
        self, user_request: str
    ) -> Dict[str, Any]:
        """
        解析用户的修改请求，识别修改类型和目标

        :param user_request: 用户的自然语言修改描述
        :return: 结构化的修改请求字典
        """
        request_lower = user_request.lower()

        # 识别修改类型
        mod_type = "custom_code"  # 默认

        if any(kw in request_lower for kw in ["颜色", "字体", "间距", "圆角", "样式", "color", "font", "style"]):
            mod_type = "component_style"
        elif any(kw in request_lower for kw in ["数据", "字段", "接口", "data", "field"]):
            mod_type = "component_data"
        elif any(kw in request_lower for kw in ["启用", "禁用", "隐藏", "显示", "enable", "disable", "section"]):
            mod_type = "section_toggle"
        elif any(kw in request_lower for kw in ["项目名", "周期", "版本", "project", "period", "version"]):
            mod_type = "meta_update"

        # 识别目标组件
        target_component = None
        component_keywords = {
            # 原始 5 个组件
            "评分卡": "HealthScorecard",
            "健康度": "HealthScorecard",
            "归因": "NorthStarChart",
            "北极星": "NorthStarChart",
            "告警": "KpiAlertList",
            "kpi": "KpiAlertList",
            "时间轴": "MilestoneTimeline",
            "里程碑": "MilestoneTimeline",
            "模块": "ModuleCardsGrid",
            "进度卡": "ModuleCardsGrid",
            # 新增 9 个组件
            "因子分解": "NorthStarDecomposition",
            "分解图": "NorthStarDecomposition",
            "雷达图": "HealthRadarChart",
            "阶段进度": "StageProgressBar",
            "漏斗": "ConversionFunnel",
            "趋势矩阵": "TrendMatrixGrid",
            "气泡图": "UserSegmentationBubble",
            "用户分层": "UserSegmentationBubble",
            "生态图": "EcosystemHealthMap",
            "生态": "EcosystemHealthMap",
            "单元经济": "UnitEconomicsCard",
            "ltv": "UnitEconomicsCard",
            "里程碑卡片": "MilestoneCardList",
            "口径说明": "MetricDefinitionPopover",
            "口径": "MetricDefinitionPopover",
        }
        for keyword, comp in component_keywords.items():
            if keyword in request_lower:
                target_component = comp
                break

        return {
            "modification_type": mod_type,
            "target_component": target_component,
            "raw_request": user_request,
            "timestamp": datetime.now().isoformat(),
        }

    def apply_style_modification(
        self,
        content: str,
        target_component: Optional[str],
        style_change: str,
    ) -> Tuple[str, str]:
        """
        应用样式修改

        :param content: 当前 TSX 代码内容
        :param target_component: 目标组件名
        :param style_change: 样式修改描述
        :return: (修改后的代码, 修改摘要)
        """
        # 常见样式修改映射
        style_patterns = {
            "深色主题": ("bg-slate-50 dark:bg-slate-900", "bg-slate-900"),
            "浅色主题": ("bg-slate-900", "bg-slate-50 dark:bg-slate-900"),
            "圆角更大": ("rounded-2xl", "rounded-3xl"),
            "圆角更小": ("rounded-2xl", "rounded-xl"),
            "紧凑布局": ("gap-5", "gap-3"),
            "宽松布局": ("gap-5", "gap-8"),
        }

        applied = []
        for desc, (old, new) in style_patterns.items():
            if desc in style_change:
                if target_component:
                    # 仅修改目标组件范围内的样式（简化实现：全局替换）
                    new_content = content.replace(old, new)
                    if new_content != content:
                        content = new_content
                        applied.append(f"已将 '{old}' 替换为 '{new}'")
                else:
                    new_content = content.replace(old, new)
                    if new_content != content:
                        content = new_content
                        applied.append(f"全局将 '{old}' 替换为 '{new}'")

        if not applied:
            # 无法自动应用，添加注释提示
            comment = f"\n// ⚠️ [Branch H] 待手动应用的样式修改: {style_change}\n"
            # 在文件末尾添加注释
            content = content.rstrip() + comment
            applied.append(f"已添加待处理注释: {style_change}")

        summary = "样式修改: " + "; ".join(applied)
        return content, summary

    def apply_section_toggle(
        self,
        content: str,
        section_id: str,
        enabled: bool,
    ) -> Tuple[str, str]:
        """
        启用或禁用指定 Section

        :param content: 当前 TSX 代码内容
        :param section_id: Section ID（如 'kpi', 'milestone'）
        :param enabled: True=启用, False=禁用
        :return: (修改后的代码, 修改摘要)
        """
        pattern = rf"(\{{ id: '{section_id}'[^}}]*enabled:\s*)(true|false)"
        new_value = "true" if enabled else "false"
        new_content = re.sub(pattern, rf"\g<1>{new_value}", content)

        if new_content == content:
            return content, f"未找到 Section '{section_id}'，无法修改"

        action = "启用" if enabled else "禁用"
        return new_content, f"已{action} Section '{section_id}'"

    def apply_meta_update(
        self,
        content: str,
        updates: Dict[str, str],
    ) -> Tuple[str, str]:
        """
        更新项目元信息

        :param content: 当前 TSX 代码内容
        :param updates: 要更新的字段字典，如 {'projectName': '新项目名'}
        :return: (修改后的代码, 修改摘要)
        """
        applied = []
        for field, value in updates.items():
            if field == "projectName":
                new_content = re.sub(
                    r"(projectName:\s*')[^']*(')",
                    rf"\g<1>{value}\g<2>",
                    content
                )
            elif field == "reportPeriod":
                new_content = re.sub(
                    r"(reportPeriod:\s*')[^']*(')",
                    rf"\g<1>{value}\g<2>",
                    content
                )
            elif field == "version":
                new_content = re.sub(
                    r"(version:\s*')[^']*(')",
                    rf"\g<1>{value}\g<2>",
                    content
                )
            else:
                new_content = content

            if new_content != content:
                content = new_content
                applied.append(f"{field} → {value}")

        summary = "元信息更新: " + ("; ".join(applied) if applied else "无变更")
        return content, summary

    def apply_custom_code(
        self,
        content: str,
        insertion_point: str,
        custom_code: str,
    ) -> Tuple[str, str]:
        """
        在指定位置注入自定义代码片段

        :param content: 当前 TSX 代码内容
        :param insertion_point: 插入点标识（如组件名、注释标记）
        :param custom_code: 要插入的代码
        :return: (修改后的代码, 修改摘要)
        """
        if insertion_point in content:
            content = content.replace(
                insertion_point,
                f"{custom_code}\n{insertion_point}"
            )
            return content, f"已在 '{insertion_point}' 前插入自定义代码"
        else:
            # 在文件末尾追加
            content = content.rstrip() + f"\n\n// [Branch H 自定义代码]\n{custom_code}\n"
            return content, "已在文件末尾追加自定义代码"

    def process_modification(
        self,
        content: str,
        modification_request: Dict[str, Any],
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """
        处理单次修改请求

        :param content: 当前 TSX 代码内容
        :param modification_request: parse_modification_request 的输出
        :param extra_params: 额外参数（如具体的样式值、Section ID 等）
        :return: (修改后的代码, 修改摘要)
        """
        mod_type = modification_request.get("modification_type", "custom_code")
        target = modification_request.get("target_component")
        raw_request = modification_request.get("raw_request", "")
        extra = extra_params or {}

        if mod_type == "component_style":
            content, summary = self.apply_style_modification(
                content, target, raw_request
            )
        elif mod_type == "section_toggle":
            section_id = extra.get("section_id", "")
            enabled = extra.get("enabled", True)
            content, summary = self.apply_section_toggle(content, section_id, enabled)
        elif mod_type == "meta_update":
            updates = extra.get("updates", {})
            content, summary = self.apply_meta_update(content, updates)
        elif mod_type == "custom_code":
            insertion_point = extra.get("insertion_point", "export default function WeeklyReportDashboard")
            custom_code = extra.get("custom_code", f"// TODO: {raw_request}")
            content, summary = self.apply_custom_code(content, insertion_point, custom_code)
        else:
            summary = f"未知修改类型: {mod_type}"

        # 记录修改历史
        self.modification_history.append({
            "timestamp": datetime.now().isoformat(),
            "modification_type": mod_type,
            "target_component": target,
            "summary": summary,
            "raw_request": raw_request,
        })

        logger.info(f"[Branch H] 修改完成: {summary}")
        return content, summary

    def generate_modification_report(self) -> str:
        """生成修改历史报告"""
        if not self.modification_history:
            return "暂无修改记录。"

        lines = ["# 代码修改历史 (Branch H)\n"]
        for i, record in enumerate(self.modification_history, 1):
            lines.append(
                f"{i}. [{record['timestamp'][:19]}] "
                f"**{record['modification_type']}** "
                f"→ {record['summary']}"
            )

        return "\n".join(lines)

    def run_acceptance_loop(
        self,
        initial_content: str,
        session_id: str,
        state_dir: str = "./state",
    ) -> Dict[str, Any]:
        """
        启动交互式验收循环（用于命令行交互模式）

        :param initial_content: 初始生成的 TSX 代码内容
        :param session_id: 会话 ID
        :param state_dir: 状态持久化目录
        :return: 最终验收结果
        """
        content = initial_content
        iteration = 0
        max_iterations = 20  # 防止无限循环

        print("\n" + "=" * 70)
        print("🔄 进入异常分支 H：代码验收与修改循环")
        print("=" * 70)
        print("当前已生成 weekly_report.tsx，请查看并提出修改意见。")
        print("输入 '验收通过' 或 'done' 结束循环，输入 'quit' 放弃。")
        print("=" * 70 + "\n")

        while iteration < max_iterations:
            iteration += 1
            print(f"\n[第 {iteration} 轮验收]")
            user_input = input("请输入修改意见（或 '验收通过' 结束）: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["验收通过", "done", "ok", "通过", "确认"]:
                print("\n✅ 验收通过！代码生成完成。")
                break

            if user_input.lower() in ["quit", "退出", "放弃"]:
                print("\n⚠️ 用户放弃验收，保留当前版本。")
                break

            # 解析并应用修改
            mod_request = self.parse_modification_request(user_input)
            content, summary = self.process_modification(content, mod_request)
            print(f"✓ {summary}")

            # 持久化当前版本
            if not os.path.exists(state_dir):
                os.makedirs(state_dir)
            temp_path = os.path.join(state_dir, f"{session_id}_weekly_report_v{iteration}.tsx")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  已保存当前版本至: {temp_path}")

        return {
            "status": "accepted" if iteration <= max_iterations else "max_iterations_reached",
            "content": content,
            "iterations": iteration,
            "modification_report": self.generate_modification_report(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Section 5: 主代码生成引擎 (Main Code Generator Engine)
# ─────────────────────────────────────────────────────────────────────────────

class CodeGeneratorEngine:
    """
    主代码生成引擎

    整合模板注入器、组件代码生成器、导航代码生成器和修改循环，
    提供完整的端到端代码生成流程。
    """

    def __init__(
        self,
        template_path: str = DEFAULT_TEMPLATE_PATH,
        output_dir: str = "./output",
        state_dir: str = "./state",
    ):
        self.template_injector = TemplateInjector(template_path)
        self.component_generator = ComponentCodeGenerator()
        self.navigation_generator = NavigationCodeGenerator()
        self.branch_h = BranchHModificationLoop()
        self.output_dir = output_dir
        self.state_dir = state_dir

        for d in [output_dir, state_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

    def load_phase3_config(self, config_path: str) -> List[Dict[str, Any]]:
        """
        加载 phase3_confirmation.py 输出的组件配置清单

        :param config_path: JSON 文件路径
        :return: 组件配置列表
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Phase3 配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        configs = data.get("component_configs", [])
        logger.info(f"加载 Phase3 配置: {len(configs)} 个组件")
        return configs

    def load_navigation_graph(self, nav_path: str) -> Dict[str, Any]:
        """
        加载 navigation_designer.py 输出的导航图谱

        :param nav_path: JSON 文件路径
        :return: 导航图谱字典
        """
        if not os.path.exists(nav_path):
            logger.warning(f"导航图谱文件不存在: {nav_path}，将使用空导航")
            return {"status": "success", "data": {"navigation_graph": [], "summary": "无导航配置"}}

        with open(nav_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"加载导航图谱: {data.get('data', {}).get('summary', '')}")
        return data

    def generate(
        self,
        component_configs: List[Dict[str, Any]],
        navigation_result: Optional[Dict[str, Any]] = None,
        project_name: str = "项目周报仪表盘",
        report_period: str = "",
        version: str = "v1.0",
        output_filename: str = "weekly_report.tsx",
    ) -> Dict[str, Any]:
        """
        主生成流程

        :param component_configs: Phase3 组件配置清单
        :param navigation_result: navigation_designer.py 的导航图谱
        :param project_name: 项目名称
        :param report_period: 报告周期
        :param version: 版本号
        :param output_filename: 输出文件名
        :return: 生成结果字典
        """
        logger.info("=" * 60)
        logger.info("开始代码生成流程")
        logger.info("=" * 60)

        # Step 1: 模板注入
        logger.info("Step 1: 执行模板注入...")
        content = self.template_injector.inject(
            component_configs=component_configs,
            project_name=project_name,
            report_period=report_period,
            version=version,
        )

        # Step 2: 生成组件代码片段注释
        logger.info("Step 2: 生成组件代码片段注释...")
        component_snippets = self.component_generator.generate_all_snippets(
            component_configs
        )

        # 将组件片段注释注入到文件头部（在 import 语句之后）
        import_end_marker = "import React, { useState, useCallback } from 'react';"
        if import_end_marker in content:
            content = content.replace(
                import_end_marker,
                import_end_marker + "\n" + component_snippets
            )

        # Step 3: 生成导航代码
        if navigation_result:
            logger.info("Step 3: 生成导航代码...")
            nav_code = self.navigation_generator.generate_navigation_code(
                navigation_result
            )
            # 将导航代码注入到 Section 4（工具函数）之后
            nav_marker = "// Section 5: 原子组件"
            if nav_marker in content:
                content = content.replace(
                    nav_marker,
                    nav_code + "\n" + nav_marker
                )
            else:
                # 追加到文件末尾的 export default 之前
                content = content.replace(
                    "export default function WeeklyReportDashboard",
                    nav_code + "\nexport default function WeeklyReportDashboard"
                )
        else:
            logger.info("Step 3: 跳过导航代码生成（未提供导航图谱）")

        # Step 4: 生成下钻处理器
        logger.info("Step 4: 生成下钻处理器...")
        drill_down_handlers = self.component_generator.generate_drill_down_handlers(
            component_configs
        )

        # 将下钻处理器注入到主组件内部
        dashboard_fn_marker = "  // 按 order 排序，过滤 enabled: false 的 Section"
        if dashboard_fn_marker in content:
            content = content.replace(
                dashboard_fn_marker,
                f"  // ── 下钻处理器（由代码生成引擎自动生成）──\n{drill_down_handlers}\n\n{dashboard_fn_marker}"
            )

        # Step 5: 输出文件
        logger.info("Step 5: 输出最终文件...")
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ 代码生成完成！输出路径: {output_path}")
        logger.info(f"   文件大小: {len(content):,} 字符 / {len(content.encode('utf-8')):,} 字节")

        return {
            "status": "success",
            "output_path": output_path,
            "content": content,
            "stats": {
                "total_chars": len(content),
                "total_bytes": len(content.encode("utf-8")),
                "component_count": len(component_configs),
                "nav_items": len(
                    navigation_result.get("data", {}).get("navigation_graph", [])
                ) if navigation_result else 0,
            },
        }

    def generate_from_files(
        self,
        phase3_config_path: str,
        navigation_path: Optional[str] = None,
        project_name: str = "项目周报仪表盘",
        report_period: str = "",
        version: str = "v1.0",
        output_filename: str = "weekly_report.tsx",
    ) -> Dict[str, Any]:
        """
        从文件路径加载配置并生成代码（便捷入口）

        :param phase3_config_path: Phase3 配置 JSON 文件路径
        :param navigation_path: 导航图谱 JSON 文件路径（可选）
        :param project_name: 项目名称
        :param report_period: 报告周期
        :param version: 版本号
        :param output_filename: 输出文件名
        :return: 生成结果字典
        """
        component_configs = self.load_phase3_config(phase3_config_path)
        navigation_result = None
        if navigation_path:
            navigation_result = self.load_navigation_graph(navigation_path)

        return self.generate(
            component_configs=component_configs,
            navigation_result=navigation_result,
            project_name=project_name,
            report_period=report_period,
            version=version,
            output_filename=output_filename,
        )

    def run_with_acceptance_loop(
        self,
        component_configs: List[Dict[str, Any]],
        navigation_result: Optional[Dict[str, Any]] = None,
        project_name: str = "项目周报仪表盘",
        report_period: str = "",
        version: str = "v1.0",
        session_id: str = "default",
        interactive: bool = True,
    ) -> Dict[str, Any]:
        """
        完整流程：生成代码 + 进入验收循环（异常分支 H）

        :param interactive: True=交互式命令行循环，False=直接返回生成结果
        :return: 最终验收结果
        """
        # 先生成初始代码
        gen_result = self.generate(
            component_configs=component_configs,
            navigation_result=navigation_result,
            project_name=project_name,
            report_period=report_period,
            version=version,
            output_filename="weekly_report_draft.tsx",
        )

        if gen_result["status"] != "success":
            return gen_result

        initial_content = gen_result["content"]

        if not interactive:
            # 非交互模式：直接保存最终文件
            final_path = os.path.join(self.output_dir, "weekly_report.tsx")
            with open(final_path, "w", encoding="utf-8") as f:
                f.write(initial_content)
            return {
                "status": "accepted",
                "output_path": final_path,
                "content": initial_content,
                "iterations": 0,
                "modification_report": "非交互模式，无修改记录。",
            }

        # 交互模式：进入验收循环
        acceptance_result = self.branch_h.run_acceptance_loop(
            initial_content=initial_content,
            session_id=session_id,
            state_dir=self.state_dir,
        )

        # 保存最终验收版本
        final_path = os.path.join(self.output_dir, "weekly_report.tsx")
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(acceptance_result["content"])

        acceptance_result["output_path"] = final_path
        logger.info(f"最终版本已保存至: {final_path}")

        return acceptance_result


# ─────────────────────────────────────────────────────────────────────────────
# Section 6: 命令行入口 (CLI Entry Point)
# ─────────────────────────────────────────────────────────────────────────────

def create_mock_phase3_config() -> List[Dict[str, Any]]:
    """创建用于测试的模拟 Phase3 配置"""
    return [
        {
            "module_name": "项目健康度诊断 (Health Score)",
            "component_name": "评分卡组件",
            "data_source": "来自核心业务指标库，包含增长势能、产品完成度、商业化健康、风险控制四个维度",
            "presentation_method": "大字号数值展示，配合红绿灯颜色标识，各维度进度条",
            "display_fields": "综合评分、阶段描述、各维度评分及环比变化",
            "drill_down_logic": "业务模块详情 (Module Details)",
        },
        {
            "module_name": "北极星指标归因 (North Star Attribution)",
            "component_name": "归因瀑布图组件",
            "data_source": "来自增长与获客模块，DAU 数据及各归因因素贡献量",
            "presentation_method": "横向条形归因图，正向贡献绿色，负向拖累红色",
            "display_fields": "当前 DAU 值、环比变化率、各归因因素贡献量、目标达成率",
            "drill_down_logic": "业务模块详情 (Module Details)",
        },
        {
            "module_name": "KPI 监控与数据异常 (KPI Monitor & Anomalies)",
            "component_name": "告警列表组件",
            "data_source": "来自 KPI 监控系统，包含 P0/P1/P2 三级告警",
            "presentation_method": "按优先级排序的告警列表，P0 告警带闪烁提示",
            "display_fields": "告警级别、标题、描述、触发时间、处理状态",
            "drill_down_logic": "风险与问题登记册 (Risk & Issue Register)",
        },
        {
            "module_name": "里程碑进度 (Milestone Progress)",
            "component_name": "时间轴组件",
            "data_source": "来自项目管理系统，包含各版本里程碑节点",
            "presentation_method": "水平时间轴，当前节点高亮，点击展开详情",
            "display_fields": "版本号、里程碑标题、日期、状态、核心成就",
            "drill_down_logic": "决策与待办事项 (Decisions & Todos)",
        },
        {
            "module_name": "业务模块详情 (Module Details)",
            "component_name": "模块进度卡片组件",
            "data_source": "来自各业务线周报，包含增长、产品、商业化三个模块",
            "presentation_method": "网格布局的卡片，包含进度条和核心指标",
            "display_fields": "模块名称、负责人、整体进度、当前核心工作、下一里程碑、核心指标列表",
            "drill_down_logic": "暂不下钻",
        },
    ]


def create_mock_navigation_result() -> Dict[str, Any]:
    """创建用于测试的模拟导航图谱"""
    return {
        "status": "success",
        "message": "导航结构设计完成",
        "data": {
            "navigation_graph": [
                {
                    "source_module": "项目健康度诊断 (Health Score)",
                    "target_module": "业务模块详情 (Module Details)",
                    "jump_type": "drill_down",
                    "trigger_condition": "用户点击健康度评分卡或异常指标"
                },
                {
                    "source_module": "项目健康度诊断 (Health Score)",
                    "target_module": "风险与问题登记册 (Risk & Issue Register)",
                    "jump_type": "drill_down",
                    "trigger_condition": "用户点击健康度评分卡或异常指标"
                },
                {
                    "source_module": "北极星指标归因 (North Star Attribution)",
                    "target_module": "业务模块详情 (Module Details)",
                    "jump_type": "drill_down",
                    "trigger_condition": "用户点击北极星指标或归因因素"
                },
                {
                    "source_module": "Global_Navigation_Bar",
                    "target_module": "财务情况 (Financial Status)",
                    "jump_type": "navbar",
                    "trigger_condition": "用户点击顶部/侧边金刚区导航菜单"
                },
                {
                    "source_module": "Global_Navigation_Bar",
                    "target_module": "决策与待办事项 (Decisions & Todos)",
                    "jump_type": "navbar",
                    "trigger_condition": "用户点击顶部/侧边金刚区导航菜单"
                },
            ],
            "validation": {
                "is_valid": True,
                "message": "导航层级验证通过，无循环引用"
            },
            "summary": "共生成 5 条导航路径，其中下钻 3 条，金刚区 2 条。"
        }
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="weekly-report-builder 代码生成引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用模拟数据生成示例输出
  python code_generator.py --demo

  # 从 Phase3 配置文件生成
  python code_generator.py \\
    --phase3-config ./state/session_001_phase3_final.json \\
    --nav-graph ./state/session_001_nav_graph.json \\
    --project-name "Sukie 泛娱乐项目" \\
    --report-period "2026-W16" \\
    --output weekly_report.tsx

  # 生成后进入交互式验收循环（异常分支 H）
  python code_generator.py --demo --interactive
        """
    )

    parser.add_argument("--demo", action="store_true", help="使用模拟数据生成示例输出")
    parser.add_argument("--phase3-config", type=str, help="Phase3 配置 JSON 文件路径")
    parser.add_argument("--nav-graph", type=str, help="导航图谱 JSON 文件路径")
    parser.add_argument("--project-name", type=str, default="项目周报仪表盘", help="项目名称")
    parser.add_argument("--report-period", type=str, default="", help="报告周期，如 2026-W16")
    parser.add_argument("--version", type=str, default="v1.0", help="版本号")
    parser.add_argument("--output", type=str, default="weekly_report.tsx", help="输出文件名")
    parser.add_argument("--output-dir", type=str, default="./output", help="输出目录")
    parser.add_argument("--interactive", action="store_true", help="生成后进入交互式验收循环（异常分支 H）")
    parser.add_argument("--template", type=str, default=DEFAULT_TEMPLATE_PATH, help="模板文件路径")

    args = parser.parse_args()

    # 初始化引擎
    engine = CodeGeneratorEngine(
        template_path=args.template,
        output_dir=args.output_dir,
    )

    if args.demo:
        # 演示模式：使用模拟数据
        print("🚀 演示模式：使用模拟数据生成示例输出...")
        component_configs = create_mock_phase3_config()
        navigation_result = create_mock_navigation_result()

        if args.interactive:
            result = engine.run_with_acceptance_loop(
                component_configs=component_configs,
                navigation_result=navigation_result,
                project_name=args.project_name,
                report_period=args.report_period,
                version=args.version,
                session_id="demo_session",
                interactive=True,
            )
        else:
            result = engine.generate(
                component_configs=component_configs,
                navigation_result=navigation_result,
                project_name=args.project_name,
                report_period=args.report_period,
                version=args.version,
                output_filename=args.output,
            )

    elif args.phase3_config:
        # 从文件加载配置
        print(f"📂 从配置文件生成: {args.phase3_config}")
        result = engine.generate_from_files(
            phase3_config_path=args.phase3_config,
            navigation_path=args.nav_graph,
            project_name=args.project_name,
            report_period=args.report_period,
            version=args.version,
            output_filename=args.output,
        )

    else:
        parser.print_help()
        exit(0)

    # 输出结果摘要
    print("\n" + "=" * 60)
    print("📊 生成结果摘要")
    print("=" * 60)
    print(f"状态: {result.get('status', 'unknown')}")
    print(f"输出路径: {result.get('output_path', 'N/A')}")

    stats = result.get("stats", {})
    if stats:
        print(f"文件大小: {stats.get('total_chars', 0):,} 字符")
        print(f"组件数量: {stats.get('component_count', 0)} 个")
        print(f"导航路径: {stats.get('nav_items', 0)} 条")

    if result.get("modification_report"):
        print(f"\n修改记录:\n{result['modification_report']}")

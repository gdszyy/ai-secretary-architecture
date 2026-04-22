"""
UI 组件智能推荐系统 (Component Recommender)
==========================================
根据周报模块的特性（数据类型、展示维度、交互需求），从组件库中智能推荐最合适的
UI 组件，并生成结构化的 JSON 推荐结果。

组件库包含 5 种核心组件：
  1. 评分卡组件 (Scorecard Component)
  2. 归因瀑布图/树状图组件 (Attribution Chart Component)
  3. 时间轴组件 (Timeline Component)
  4. 异常告警列表组件 (Anomaly Alert List Component)
  5. 模块进度卡片组件 (Module Progress Card Component)

用法示例：
  python component_recommender.py --module "北极星指标归因"
  python component_recommender.py --module "KPI监控与数据异常" --data-type numeric --interaction alert
  python component_recommender.py --list-modules
  python component_recommender.py --batch modules.json
"""

import json
import argparse
import sys
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# 1. 组件库定义 (Component Library Definition)
# ─────────────────────────────────────────────────────────────────────────────

COMPONENT_LIBRARY = {
    "scorecard": {
        "name": "评分卡组件",
        "name_en": "Scorecard Component",
        "applicable_modules": [
            "项目健康度诊断",
            "health_score",
            "KPI监控与数据异常",
            "kpi_monitor",
        ],
        "data_types": ["numeric", "percentage", "ratio", "score"],
        "display_dimensions": ["single_metric", "multi_metric", "comparison"],
        "interaction_types": ["drill_down", "trend_view", "alert"],
        "data_requirements": [
            "指标名称 (metric_name)",
            "当前值 (current_value)",
            "目标值 (target_value)",
            "环比变化率 (change_rate)",
            "状态标识 (status: healthy | warning | danger)",
            "迷你趋势数据 (sparkline_data, 可选)",
        ],
        "presentation": (
            "大字号数值展示，配合红绿灯颜色标识和迷你趋势图 (Sparkline)。"
            "数值进场时建议使用数字滚动动效。"
        ),
        "drill_down": "点击可跳转至该指标的历史趋势图或详细归因分析页面。",
        "priority": "P0",
        "strengths": ["直观呈现单指标健康状态", "支持多指标并排对比", "红绿灯告警一目了然"],
        "limitations": ["不适合展示因果关系", "不适合展示时序进度"],
    },
    "attribution_chart": {
        "name": "归因瀑布图/树状图组件",
        "name_en": "Attribution Chart Component",
        "applicable_modules": [
            "北极星指标归因",
            "north_star_attribution",
        ],
        "data_types": ["delta", "contribution", "breakdown"],
        "display_dimensions": ["causal", "decomposition", "waterfall"],
        "interaction_types": ["drill_down", "factor_detail"],
        "data_requirements": [
            "总指标变化量 (total_delta)",
            "各子维度名称 (dimension_names)",
            "各子维度贡献量 (contribution_values, 正向/负向)",
            "颜色映射规则 (color_mapping: positive=green, negative=red)",
        ],
        "presentation": (
            "瀑布图展示各因素对总指标增减的贡献。"
            "正向贡献使用绿色系，负向贡献使用红色系。"
        ),
        "drill_down": "点击特定子维度，跳转至该业务模块的详情页，查看具体的运营动作或产品变更。",
        "priority": "P0",
        "strengths": ["清晰呈现因果归因关系", "正负贡献一目了然", "支持多层级拆解"],
        "limitations": ["不适合展示时序进度", "不适合展示告警状态"],
    },
    "timeline": {
        "name": "时间轴组件",
        "name_en": "Timeline Component",
        "applicable_modules": [
            "里程碑进度",
            "milestone_progress",
        ],
        "data_types": ["temporal", "milestone", "progress"],
        "display_dimensions": ["chronological", "status", "sequential"],
        "interaction_types": ["node_detail", "drill_down"],
        "data_requirements": [
            "节点名称 (node_name)",
            "计划时间 (planned_date)",
            "实际时间 (actual_date, 可选)",
            "节点状态 (status: completed | in_progress | delayed | planned)",
            "关键交付物 (deliverables, 可选)",
            "阻塞问题 (blockers, 可选)",
        ],
        "presentation": (
            "垂直或水平时间轴，当前节点高亮显示。"
            "已完成节点使用绿色标识，延期节点使用红色标识。"
        ),
        "drill_down": "点击节点查看详细的资源消耗、阻塞问题或具体的交付物文档。",
        "priority": "P0",
        "strengths": ["直观呈现时序进度", "延期状态一目了然", "支持里程碑节点详情"],
        "limitations": ["不适合展示数值指标对比", "不适合展示因果归因"],
    },
    "anomaly_alert_list": {
        "name": "异常告警列表组件",
        "name_en": "Anomaly Alert List Component",
        "applicable_modules": [
            "KPI监控与数据异常",
            "kpi_monitor",
            "风险与问题登记册",
            "risk_register",
        ],
        "data_types": ["alert", "risk", "issue", "status"],
        "display_dimensions": ["priority_list", "severity", "status_tracking"],
        "interaction_types": ["alert", "drill_down", "status_update"],
        "data_requirements": [
            "异常级别 (level: P0 | P1 | P2)",
            "异常描述 (description)",
            "发生时间 (occurred_at)",
            "影响范围 (impact_scope)",
            "当前处理状态 (handling_status: open | in_progress | resolved)",
            "负责人 (owner, 可选)",
        ],
        "presentation": (
            "带颜色标识的列表，高优异常置顶并闪烁提示。"
            "不同级别的异常使用不同的颜色和图标区分。"
        ),
        "drill_down": "点击查看详细的排查报告、处理工单或相关的责任人信息。",
        "priority": "P0",
        "strengths": ["高优异常置顶告警", "多级别优先级管理", "处理状态追踪"],
        "limitations": ["不适合展示趋势数据", "不适合展示时序进度"],
    },
    "module_progress_card": {
        "name": "模块进度卡片组件",
        "name_en": "Module Progress Card Component",
        "applicable_modules": [
            "业务模块详情",
            "module_details",
        ],
        "data_types": ["progress", "summary", "action_items"],
        "display_dimensions": ["overview", "multi_module", "grid"],
        "interaction_types": ["drill_down", "hover_detail"],
        "data_requirements": [
            "模块名称 (module_name)",
            "负责人 (owner)",
            "整体进度百分比 (progress_percentage: 0-100)",
            "近期核心动作 (recent_actions, 最多3条)",
            "进度状态 (status: normal | delayed | at_risk)",
        ],
        "presentation": (
            "网格布局的卡片，包含进度条和简短文本。"
            "进度条颜色可根据状态（正常/延期/风险）动态变化。"
        ),
        "drill_down": "点击进入该模块的完整数据看板，查看更详细的子任务和指标。",
        "priority": "P1",
        "strengths": ["多模块并排概览", "进度可视化直观", "支持悬浮查看历史"],
        "limitations": ["不适合展示精确数值指标", "不适合展示告警状态"],
    },
    "north_star_decomposition": {
        "name": "北极星因子分解图",
        "name_en": "North Star Decomposition",
        "applicable_modules": [
            "北极星指标归因",
            "north_star_attribution",
        ],
        "data_types": ["delta", "contribution", "breakdown", "tree"],
        "display_dimensions": ["causal", "decomposition", "tree_structure", "hierarchical"],
        "interaction_types": ["drill_down", "hover_detail"],
        "data_requirements": [
            "北极星指标名称 (metric: string)",
            "当前总值 (value: number)",
            "单位 (unit: string, 可选)",
            "总环比变化量 (change: number)",
            "总环比变化率 (changeRate: string, 如 '+7.3%')",
            "总体趋势 (trend: 'up' | 'down' | 'stable')",
            "目标值 (target: number, 可选)",
            "因子分解树根节点 (rootNode: DecompositionNode)",
            "  └ 节点ID (id: string)",
            "  └ 因子名称 (name: string)",
            "  └ 贡献量 (contribution: number, 正向/负向)",
            "  └ 健康状态 (status: 'success' | 'warning' | 'danger' | 'info' | 'neutral')",
            "  └ 关联模块ID (moduleId: string, 可选, 用于下钻)",
            "  └ 上下文信息 (context: FactorContext, 可选)",
            "  └ 子节点列表 (children: DecompositionNode[], 可选)",
        ],
        "presentation": (
            "SVG 横向树状结构图，左侧根节点为北极星指标总变化量，向右展开为各级归因因子。"
            "节点颜色（绿/黄/红）反映健康状态，连线粗细反映该因子的权重（贡献量占比）。"
            "警戒节点（danger 状态）附加警告图标并伴随轻微呼吸动效。"
            "Hover 节点弹出浮层，显示当前值、目标差距、负责团队、洞察分析等上下文信息。"
        ),
        "drill_down": (
            "点击节点触发 onDrillDown 回调，传入节点ID和关联模块ID，"
            "由父组件决定跳转目标（如转化率节点→漏斗转化组件）。"
        ),
        "priority": "P0",
        "strengths": [
            "树状结构直观展示多层因果关系",
            "连线粗细量化各因子权重",
            "Hover 浮层提供丰富上下文，无需跳转即可获取关键信息",
            "支持多级下钻，灵活适配不同业务深度",
        ],
        "limitations": [
            "节点过多时（>10个）视觉复杂度较高",
            "不适合展示时序趋势数据",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. 模块特性映射表 (Module Feature Mapping)
# ─────────────────────────────────────────────────────────────────────────────

# 预设的模块名称 → 特性映射（支持中英文别名）
MODULE_FEATURE_MAP = {
    # 首屏模块 (P0)
    "项目健康度诊断": {
        "aliases": ["health_score", "health score", "健康度"],
        "data_types": ["numeric", "score", "percentage"],
        "display_dimensions": ["multi_metric", "comparison"],
        "interaction_types": ["drill_down", "alert"],
        "priority": "P0",
        "description": "综合评分，通常包含增长、产品、商业化、风险等维度的雷达图或评分卡。",
    },
    "北极星指标归因": {
        "aliases": ["north_star_attribution", "north star", "归因"],
        "data_types": ["delta", "contribution", "breakdown"],
        "display_dimensions": ["causal", "decomposition"],
        "interaction_types": ["drill_down", "factor_detail"],
        "priority": "P0",
        "description": "核心指标的当前值、环比/同比变化，以及导致该变化的主要因素拆解。",
    },
    "KPI监控与数据异常": {
        "aliases": ["kpi_monitor", "kpi monitor", "KPI监控", "数据异常", "anomaly"],
        "data_types": ["numeric", "alert", "status"],
        "display_dimensions": ["single_metric", "priority_list"],
        "interaction_types": ["alert", "drill_down"],
        "priority": "P0",
        "description": "关键业务指标的红绿灯状态，特别是突破阈值的异常告警。",
    },
    "里程碑进度": {
        "aliases": ["milestone_progress", "milestone", "里程碑"],
        "data_types": ["temporal", "milestone", "progress"],
        "display_dimensions": ["chronological", "sequential"],
        "interaction_types": ["node_detail", "drill_down"],
        "priority": "P0",
        "description": "当前版本的核心目标达成情况，以及下一阶段的规划。",
    },
    # 其他模块 (P1/P2)
    "业务模块详情": {
        "aliases": ["module_details", "module details", "业务模块", "模块详情"],
        "data_types": ["progress", "summary", "action_items"],
        "display_dimensions": ["overview", "grid"],
        "interaction_types": ["drill_down", "hover_detail"],
        "priority": "P1",
        "description": "各子业务线（如游戏、社交、商业化）的具体进展、核心数据和近期动作。",
    },
    "风险与问题登记册": {
        "aliases": ["risk_register", "risk register", "风险", "问题", "issue"],
        "data_types": ["alert", "risk", "issue"],
        "display_dimensions": ["priority_list", "status_tracking"],
        "interaction_types": ["alert", "status_update"],
        "priority": "P1",
        "description": "当前面临的阻塞问题、潜在风险点及应对策略。",
    },
    "团队构成与动态": {
        "aliases": ["team_org", "team", "团队"],
        "data_types": ["summary", "action_items"],
        "display_dimensions": ["overview"],
        "interaction_types": ["drill_down"],
        "priority": "P2",
        "description": "人员变动、招聘需求、团队绩效。",
    },
    "财务情况": {
        "aliases": ["financial_status", "finance", "财务"],
        "data_types": ["numeric", "ratio", "breakdown"],
        "display_dimensions": ["multi_metric", "decomposition"],
        "interaction_types": ["drill_down"],
        "priority": "P2",
        "description": "收入结构、成本支出、ROI 分析、现金流消耗。",
    },
    "决策与待办事项": {
        "aliases": ["decisions_todos", "decisions", "待办", "todo"],
        "data_types": ["summary", "action_items"],
        "display_dimensions": ["priority_list"],
        "interaction_types": ["status_update"],
        "priority": "P2",
        "description": "需要高层决策的事项列表，以及各模块的待办任务追踪。",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. 组件匹配器 (Component Matcher)
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_module_name(module_input: str) -> Optional[str]:
    """
    将用户输入的模块名称（支持中英文别名）规范化为标准模块名称。
    返回标准模块名称，若未找到则返回 None。
    """
    module_input_lower = module_input.strip().lower()
    for standard_name, features in MODULE_FEATURE_MAP.items():
        if module_input_lower == standard_name.lower():
            return standard_name
        for alias in features.get("aliases", []):
            if module_input_lower == alias.lower():
                return standard_name
    return None


def _score_component(component_key: str, module_features: dict) -> float:
    """
    计算某个组件与模块特性的匹配得分（0.0 ~ 1.0）。

    评分维度：
      - 数据类型匹配 (data_types): 权重 40%
      - 展示维度匹配 (display_dimensions): 权重 35%
      - 交互需求匹配 (interaction_types): 权重 25%
    """
    component = COMPONENT_LIBRARY[component_key]
    score = 0.0

    # 数据类型匹配
    data_type_matches = len(
        set(module_features.get("data_types", [])) &
        set(component["data_types"])
    )
    data_type_total = max(len(module_features.get("data_types", [])), 1)
    score += 0.40 * (data_type_matches / data_type_total)

    # 展示维度匹配
    display_matches = len(
        set(module_features.get("display_dimensions", [])) &
        set(component["display_dimensions"])
    )
    display_total = max(len(module_features.get("display_dimensions", [])), 1)
    score += 0.35 * (display_matches / display_total)

    # 交互需求匹配
    interaction_matches = len(
        set(module_features.get("interaction_types", [])) &
        set(component["interaction_types"])
    )
    interaction_total = max(len(module_features.get("interaction_types", [])), 1)
    score += 0.25 * (interaction_matches / interaction_total)

    return round(score, 4)


def match_components(
    module_name: str,
    data_types: Optional[list] = None,
    display_dimensions: Optional[list] = None,
    interaction_types: Optional[list] = None,
) -> dict:
    """
    组件匹配器：根据模块特性推荐最合适的 UI 组件。

    参数：
      module_name         - 模块名称（支持中英文别名）
      data_types          - 自定义数据类型列表（可覆盖预设）
      display_dimensions  - 自定义展示维度列表（可覆盖预设）
      interaction_types   - 自定义交互需求列表（可覆盖预设）

    返回：
      包含主推荐和备选方案的匹配结果字典
    """
    # 规范化模块名称
    standard_name = _normalize_module_name(module_name)
    if standard_name:
        features = MODULE_FEATURE_MAP[standard_name].copy()
    else:
        # 未知模块：使用用户传入的特性构建临时特性
        features = {
            "data_types": data_types or [],
            "display_dimensions": display_dimensions or [],
            "interaction_types": interaction_types or [],
            "priority": "P1",
            "description": f"用户自定义模块: {module_name}",
        }

    # 允许用户覆盖预设特性
    if data_types:
        features["data_types"] = data_types
    if display_dimensions:
        features["display_dimensions"] = display_dimensions
    if interaction_types:
        features["interaction_types"] = interaction_types

    # 对所有组件评分并排序
    scores = {}
    for key in COMPONENT_LIBRARY:
        scores[key] = _score_component(key, features)

    sorted_components = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 主推荐：得分最高的组件
    primary_key, primary_score = sorted_components[0]

    # 备选方案：得分第二、第三的组件（得分 > 0）
    alternatives = [
        (k, s) for k, s in sorted_components[1:]
        if s > 0
    ][:2]

    return {
        "module_name": module_name,
        "standard_module_name": standard_name or module_name,
        "module_description": features.get("description", ""),
        "module_priority": features.get("priority", "P1"),
        "primary": {
            "component_key": primary_key,
            "score": primary_score,
        },
        "alternatives": [
            {"component_key": k, "score": s}
            for k, s in alternatives
        ],
        "all_scores": {k: s for k, s in sorted_components},
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. 推荐理由生成器 (Recommendation Reason Generator)
# ─────────────────────────────────────────────────────────────────────────────

def generate_recommendation_reason(
    component_key: str,
    module_features: dict,
    is_primary: bool = True,
) -> str:
    """
    为推荐的组件生成简短的选型理由。

    参数：
      component_key   - 组件键名
      module_features - 模块特性字典
      is_primary      - 是否为主推荐（影响理由措辞）

    返回：
      选型理由字符串
    """
    component = COMPONENT_LIBRARY[component_key]
    module_data_types = set(module_features.get("data_types", []))
    module_display = set(module_features.get("display_dimensions", []))
    module_interaction = set(module_features.get("interaction_types", []))

    matched_strengths = []

    # 根据数据类型匹配生成理由
    data_type_overlap = module_data_types & set(component["data_types"])
    if data_type_overlap:
        type_reasons = {
            "numeric": "数值型数据展示",
            "percentage": "百分比指标呈现",
            "score": "综合评分展示",
            "delta": "变化量/增减分析",
            "contribution": "贡献度拆解",
            "breakdown": "多维度拆解",
            "temporal": "时序数据展示",
            "milestone": "里程碑节点追踪",
            "progress": "进度百分比展示",
            "alert": "告警状态管理",
            "risk": "风险优先级管理",
            "issue": "问题追踪",
            "summary": "摘要信息概览",
            "action_items": "行动项管理",
            "ratio": "比率/比例分析",
        }
        for dt in data_type_overlap:
            if dt in type_reasons:
                matched_strengths.append(type_reasons[dt])

    # 根据展示维度匹配生成理由
    display_overlap = module_display & set(component["display_dimensions"])
    if display_overlap:
        display_reasons = {
            "single_metric": "单指标聚焦展示",
            "multi_metric": "多指标并排对比",
            "comparison": "目标值与实际值对比",
            "causal": "因果关系可视化",
            "decomposition": "多层级分解展示",
            "waterfall": "瀑布图增减呈现",
            "chronological": "时间顺序排列",
            "sequential": "顺序节点展示",
            "priority_list": "优先级排序列表",
            "severity": "严重程度分级",
            "status_tracking": "状态追踪管理",
            "overview": "全局概览视图",
            "grid": "网格化多模块布局",
        }
        for dd in display_overlap:
            if dd in display_reasons:
                matched_strengths.append(display_reasons[dd])

    # 根据交互需求匹配生成理由
    interaction_overlap = module_interaction & set(component["interaction_types"])
    if interaction_overlap:
        interaction_reasons = {
            "drill_down": "支持下钻至详细分析",
            "trend_view": "支持历史趋势查看",
            "alert": "内置告警高亮机制",
            "factor_detail": "支持因子详情展开",
            "node_detail": "支持节点详情查看",
            "hover_detail": "支持悬浮查看历史",
            "status_update": "支持状态实时更新",
        }
        for it in interaction_overlap:
            if it in interaction_reasons:
                matched_strengths.append(interaction_reasons[it])

    # 去重并限制数量
    unique_strengths = list(dict.fromkeys(matched_strengths))[:3]

    if not unique_strengths:
        unique_strengths = component["strengths"][:2]

    prefix = "主推荐：" if is_primary else "备选方案："
    strengths_text = "、".join(unique_strengths)
    reason = (
        f"{prefix}{component['name']}（{component['name_en']}）。"
        f"该组件擅长{strengths_text}，"
        f"与本模块的核心展示需求高度匹配。"
        f"{component['presentation']}"
    )
    return reason


# ─────────────────────────────────────────────────────────────────────────────
# 5. 推荐结果构建器 (Recommendation Result Builder)
# ─────────────────────────────────────────────────────────────────────────────

def build_recommendation_result(
    module_name: str,
    data_types: Optional[list] = None,
    display_dimensions: Optional[list] = None,
    interaction_types: Optional[list] = None,
) -> dict:
    """
    为指定模块生成完整的结构化组件推荐结果（JSON 格式）。

    输出结构：
    {
      "module_name": str,
      "standard_module_name": str,
      "module_description": str,
      "module_priority": str,
      "recommendation": {
        "primary": {
          "component_name": str,
          "component_name_en": str,
          "reason": str,
          "data_requirements": list[str],
          "presentation": str,
          "drill_down": str,
          "match_score": float
        },
        "alternatives": [
          {
            "component_name": str,
            "component_name_en": str,
            "reason": str,
            "data_requirements": list[str],
            "match_score": float
          }
        ]
      },
      "confirmation_checklist": {
        "data_source": str,
        "presentation_method": str,
        "display_fields": str,
        "drill_down_logic": str
      }
    }
    """
    # 执行组件匹配
    match_result = match_components(
        module_name=module_name,
        data_types=data_types,
        display_dimensions=display_dimensions,
        interaction_types=interaction_types,
    )

    # 获取规范化后的模块特性（用于生成理由）
    standard_name = match_result["standard_module_name"]
    if standard_name in MODULE_FEATURE_MAP:
        features = MODULE_FEATURE_MAP[standard_name].copy()
    else:
        features = {
            "data_types": data_types or [],
            "display_dimensions": display_dimensions or [],
            "interaction_types": interaction_types or [],
        }
    if data_types:
        features["data_types"] = data_types
    if display_dimensions:
        features["display_dimensions"] = display_dimensions
    if interaction_types:
        features["interaction_types"] = interaction_types

    # 构建主推荐
    primary_key = match_result["primary"]["component_key"]
    primary_component = COMPONENT_LIBRARY[primary_key]
    primary_reason = generate_recommendation_reason(
        component_key=primary_key,
        module_features=features,
        is_primary=True,
    )

    primary_result = {
        "component_name": primary_component["name"],
        "component_name_en": primary_component["name_en"],
        "reason": primary_reason,
        "data_requirements": primary_component["data_requirements"],
        "presentation": primary_component["presentation"],
        "drill_down": primary_component["drill_down"],
        "match_score": match_result["primary"]["score"],
    }

    # 构建备选方案
    alternatives_result = []
    for alt in match_result["alternatives"]:
        alt_key = alt["component_key"]
        alt_component = COMPONENT_LIBRARY[alt_key]
        alt_reason = generate_recommendation_reason(
            component_key=alt_key,
            module_features=features,
            is_primary=False,
        )
        alternatives_result.append({
            "component_name": alt_component["name"],
            "component_name_en": alt_component["name_en"],
            "reason": alt_reason,
            "data_requirements": alt_component["data_requirements"],
            "match_score": alt["score"],
        })

    # 构建第三阶段交互确认清单（4要素）
    confirmation_checklist = {
        "data_source": (
            f"请确认：{match_result['module_description']}"
            f"该组件的数据从第一阶段提炼的哪个业务模块中获取？"
        ),
        "presentation_method": (
            f"请确认：{primary_component['presentation']}"
            f"是否需要调整视觉形态（如趋势图、红绿灯告警、颜色映射）？"
        ),
        "display_fields": (
            f"请确认：除默认字段外，是否需要额外展示同比/环比变化率、目标达成率等字段？"
            f"默认数据需求：{', '.join(primary_component['data_requirements'][:3])}..."
        ),
        "drill_down_logic": (
            f"请确认：{primary_component['drill_down']}"
            f"点击该组件后，期望跳转到哪个关联模块？"
        ),
    }

    return {
        "module_name": module_name,
        "standard_module_name": match_result["standard_module_name"],
        "module_description": match_result["module_description"],
        "module_priority": match_result["module_priority"],
        "recommendation": {
            "primary": primary_result,
            "alternatives": alternatives_result,
        },
        "confirmation_checklist": confirmation_checklist,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. 批量推荐接口 (Batch Recommendation Interface)
# ─────────────────────────────────────────────────────────────────────────────

def batch_recommend(modules: list) -> list:
    """
    批量为多个模块生成组件推荐结果。

    参数：
      modules - 模块配置列表，每项为：
        {
          "module_name": str,
          "data_types": list (可选),
          "display_dimensions": list (可选),
          "interaction_types": list (可选)
        }

    返回：
      推荐结果列表
    """
    results = []
    for module_config in modules:
        result = build_recommendation_result(
            module_name=module_config.get("module_name", ""),
            data_types=module_config.get("data_types"),
            display_dimensions=module_config.get("display_dimensions"),
            interaction_types=module_config.get("interaction_types"),
        )
        results.append(result)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 7. CLI 入口 (Command Line Interface)
# ─────────────────────────────────────────────────────────────────────────────

def list_modules():
    """列出所有预设模块及其优先级。"""
    print("\n📋 预设模块列表 (Preset Module List)\n")
    print(f"{'模块名称':<20} {'优先级':<8} {'别名示例'}")
    print("─" * 70)
    for name, features in MODULE_FEATURE_MAP.items():
        aliases_preview = ", ".join(features.get("aliases", [])[:2])
        print(f"{name:<20} {features['priority']:<8} {aliases_preview}")
    print()


def list_components():
    """列出所有可用组件及其适用场景。"""
    print("\n🧩 可用组件列表 (Available Components)\n")
    for key, comp in COMPONENT_LIBRARY.items():
        print(f"  [{key}] {comp['name']} ({comp['name_en']})")
        print(f"    适用场景: {', '.join(comp['applicable_modules'][:2])}")
        print(f"    优先级: {comp['priority']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="UI 组件智能推荐系统 - 为周报模块推荐最合适的 UI 组件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 为单个模块生成推荐
  python component_recommender.py --module "北极星指标归因"

  # 指定自定义特性覆盖预设
  python component_recommender.py --module "KPI监控" --data-type numeric alert --interaction alert drill_down

  # 批量推荐（从 JSON 文件读取）
  python component_recommender.py --batch modules.json

  # 列出所有预设模块
  python component_recommender.py --list-modules

  # 列出所有可用组件
  python component_recommender.py --list-components
        """,
    )
    parser.add_argument(
        "--module", "-m",
        type=str,
        help="要推荐组件的模块名称（支持中英文别名）",
    )
    parser.add_argument(
        "--data-type", "-d",
        nargs="+",
        dest="data_types",
        help="自定义数据类型（覆盖预设，可多个）",
    )
    parser.add_argument(
        "--display-dim", "-dd",
        nargs="+",
        dest="display_dimensions",
        help="自定义展示维度（覆盖预设，可多个）",
    )
    parser.add_argument(
        "--interaction", "-i",
        nargs="+",
        dest="interaction_types",
        help="自定义交互需求（覆盖预设，可多个）",
    )
    parser.add_argument(
        "--batch", "-b",
        type=str,
        help="批量推荐：从 JSON 文件读取模块列表",
    )
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="列出所有预设模块",
    )
    parser.add_argument(
        "--list-components",
        action="store_true",
        help="列出所有可用组件",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="将推荐结果输出到指定 JSON 文件",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="以格式化 JSON 输出（默认开启）",
    )

    args = parser.parse_args()

    # 处理列表命令
    if args.list_modules:
        list_modules()
        return
    if args.list_components:
        list_components()
        return

    result = None

    # 批量推荐
    if args.batch:
        try:
            with open(args.batch, "r", encoding="utf-8") as f:
                modules = json.load(f)
            result = batch_recommend(modules)
        except FileNotFoundError:
            print(f"❌ 错误：找不到文件 {args.batch}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ 错误：JSON 解析失败 - {e}", file=sys.stderr)
            sys.exit(1)

    # 单模块推荐
    elif args.module:
        result = build_recommendation_result(
            module_name=args.module,
            data_types=args.data_types,
            display_dimensions=args.display_dimensions,
            interaction_types=args.interaction_types,
        )
    else:
        parser.print_help()
        return

    # 输出结果
    indent = 2 if args.pretty else None
    json_output = json.dumps(result, ensure_ascii=False, indent=indent)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"✅ 推荐结果已保存至: {args.output}")
    else:
        print(json_output)


# ─────────────────────────────────────────────────────────────────────────────
# 8. 模块 API（供其他脚本 import 使用）
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    "COMPONENT_LIBRARY",
    "MODULE_FEATURE_MAP",
    "match_components",
    "generate_recommendation_reason",
    "build_recommendation_result",
    "batch_recommend",
]


if __name__ == "__main__":
    main()

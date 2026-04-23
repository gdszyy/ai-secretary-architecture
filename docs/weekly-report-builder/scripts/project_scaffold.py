"""
project_scaffold.py — 新项目一键初始化工具

功能：
  基于交互式问答，快速创建新项目目录（projects/{id}/），
  生成 config.json 和 schema.json，开箱即用。

用法：
  # 交互式创建（推荐）
  python scripts/project_scaffold.py

  # 非交互式（CI/脚本调用）
  python scripts/project_scaffold.py \\
      --id my-project \\
      --name "我的项目周报" \\
      --type general

  # 查看可用项目类型
  python scripts/project_scaffold.py --list-types

项目类型（--type）：
  general         通用型（默认，适合大多数产品/业务团队）
  post-investment 投后管理（被投企业组合跟踪）
  platform        中台/基础设施（服务能力、API 指标）
  growth          增长团队（获客、留存、变现漏斗）
  ops             运营团队（活动、内容、用户运营）
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKILL_ROOT   = Path(__file__).parent.parent
PROJECTS_DIR = SKILL_ROOT / "projects"

# ─── 项目类型模板 ─────────────────────────────────────────────────────────────

PROJECT_TYPES = {
    "general": {
        "label": "通用型",
        "description": "适合大多数产品/业务团队，包含健康度、北极星、模块进度等标准模块",
        "sections": [
            {"id": "hero",       "label": "首屏总览",     "required": True},
            {"id": "health",     "label": "健康度诊断",   "required": True},
            {"id": "north-star", "label": "北极星指标",   "required": True},
            {"id": "kpi",        "label": "KPI 监控",     "required": False},
            {"id": "milestones", "label": "里程碑进度",   "required": True},
            {"id": "modules",    "label": "业务模块详情", "required": True},
            {"id": "risks",      "label": "风险与决策",   "required": False},
        ],
        "module_alias": {
            "modules":             "业务模块",
            "module.name":         "模块名称",
            "module.owner":        "负责人",
            "module.progress":     "进度",
            "module.currentFocus": "本周重点",
            "module.nextMilestone":"下一里程碑",
            "module.metrics":      "核心指标",
        },
        "north_star_hint": "DAU / MAU / ARR 等核心增长指标",
        "health_dimensions": [
            {"name": "增长势能",   "color": "bg-emerald-500"},
            {"name": "产品完成度", "color": "bg-violet-500"},
            {"name": "商业化健康", "color": "bg-amber-500"},
            {"name": "风险控制",   "color": "bg-sky-500"},
        ],
        "extra_fields": None,
    },
    "post-investment": {
        "label": "投后管理",
        "description": "被投企业组合跟踪，关注 MOIC、ARR、融资进度、风险预警",
        "sections": [
            {"id": "hero",       "label": "首屏总览",       "required": True},
            {"id": "health",     "label": "组合健康度",     "required": True},
            {"id": "north-star", "label": "核心追踪指标",   "required": True},
            {"id": "kpi",        "label": "KPI 监控",       "required": False},
            {"id": "milestones", "label": "里程碑跟踪",     "required": True},
            {"id": "modules",    "label": "被投企业详情",   "required": True},
            {"id": "risks",      "label": "风险预警与决策", "required": True},
        ],
        "module_alias": {
            "modules":             "被投企业",
            "module.name":         "企业名称",
            "module.owner":        "对接 Partner",
            "module.progress":     "里程碑完成率",
            "module.currentFocus": "本周重点进展",
            "module.nextMilestone":"下一关键节点",
            "module.metrics":      "核心经营指标",
        },
        "north_star_hint": "组合加权 MOIC / 组合合并 ARR",
        "health_dimensions": [
            {"name": "增长势能",   "color": "bg-emerald-500"},
            {"name": "财务健康",   "color": "bg-violet-500"},
            {"name": "团队稳定性", "color": "bg-sky-500"},
            {"name": "风险控制",   "color": "bg-amber-500"},
        ],
        "extra_fields": {
            "portfolio": ["totalInvested", "deployed", "moic", "irr", "exitPipeline"],
            "fundingRounds": ["company", "round", "amount", "lead", "date", "status"],
        },
    },
    "platform": {
        "label": "中台/基础设施",
        "description": "服务能力周报，关注可用率、P99 延迟、接入进度、技术风险",
        "sections": [
            {"id": "hero",       "label": "首屏总览",       "required": True},
            {"id": "health",     "label": "服务健康度",     "required": True},
            {"id": "north-star", "label": "核心服务指标",   "required": True},
            {"id": "kpi",        "label": "API 告警",       "required": True},
            {"id": "milestones", "label": "基础设施里程碑", "required": True},
            {"id": "modules",    "label": "业务线接入进度", "required": True},
            {"id": "risks",      "label": "技术风险与决策", "required": True},
        ],
        "module_alias": {
            "modules":             "业务线/服务",
            "module.name":         "服务名称",
            "module.owner":        "负责人",
            "module.progress":     "接入完成度",
            "module.currentFocus": "本周进展",
            "module.nextMilestone":"下一节点",
            "module.metrics":      "服务指标",
        },
        "north_star_hint": "平台服务可用率 / 已接入业务线数",
        "health_dimensions": [
            {"name": "服务稳定性", "color": "bg-emerald-500"},
            {"name": "接入进度",   "color": "bg-violet-500"},
            {"name": "性能达标",   "color": "bg-sky-500"},
            {"name": "研发效能",   "color": "bg-amber-500"},
        ],
        "extra_fields": {
            "serviceCapacity": ["totalQps", "p99Latency", "availability", "connectedBizLines"],
            "apiMetrics": ["apiName", "callCount", "successRate", "p99", "trend"],
        },
    },
    "growth": {
        "label": "增长团队",
        "description": "获客、留存、变现漏斗，关注渠道 ROI、转化率、LTV",
        "sections": [
            {"id": "hero",       "label": "首屏总览",     "required": True},
            {"id": "health",     "label": "增长健康度",   "required": True},
            {"id": "north-star", "label": "核心增长指标", "required": True},
            {"id": "kpi",        "label": "渠道告警",     "required": False},
            {"id": "milestones", "label": "实验里程碑",   "required": True},
            {"id": "modules",    "label": "渠道/实验详情","required": True},
            {"id": "risks",      "label": "风险与决策",   "required": False},
        ],
        "module_alias": {
            "modules":             "渠道/实验",
            "module.name":         "渠道/实验名称",
            "module.owner":        "负责人",
            "module.progress":     "目标达成率",
            "module.currentFocus": "本周重点",
            "module.nextMilestone":"下一实验节点",
            "module.metrics":      "增长指标",
        },
        "north_star_hint": "DAU / 新增用户 / 付费转化率",
        "health_dimensions": [
            {"name": "获客效率",   "color": "bg-emerald-500"},
            {"name": "留存质量",   "color": "bg-violet-500"},
            {"name": "变现能力",   "color": "bg-amber-500"},
            {"name": "实验效率",   "color": "bg-sky-500"},
        ],
        "extra_fields": {
            "funnelMetrics": ["stage", "users", "conversionRate", "dropoffRate"],
            "channelROI": ["channel", "spend", "newUsers", "cac", "ltv", "roi"],
        },
    },
    "ops": {
        "label": "运营团队",
        "description": "活动、内容、用户运营，关注活动 ROI、内容消费、用户分层",
        "sections": [
            {"id": "hero",       "label": "首屏总览",     "required": True},
            {"id": "health",     "label": "运营健康度",   "required": True},
            {"id": "north-star", "label": "核心运营指标", "required": True},
            {"id": "kpi",        "label": "活动告警",     "required": False},
            {"id": "milestones", "label": "活动里程碑",   "required": True},
            {"id": "modules",    "label": "活动/内容详情","required": True},
            {"id": "risks",      "label": "风险与决策",   "required": False},
        ],
        "module_alias": {
            "modules":             "活动/内容线",
            "module.name":         "活动/内容名称",
            "module.owner":        "运营负责人",
            "module.progress":     "目标完成率",
            "module.currentFocus": "本周重点",
            "module.nextMilestone":"下一活动节点",
            "module.metrics":      "运营指标",
        },
        "north_star_hint": "DAU / 内容消费时长 / 付费用户数",
        "health_dimensions": [
            {"name": "活动效果",   "color": "bg-emerald-500"},
            {"name": "内容质量",   "color": "bg-violet-500"},
            {"name": "用户活跃",   "color": "bg-amber-500"},
            {"name": "商业转化",   "color": "bg-sky-500"},
        ],
        "extra_fields": {
            "activityMetrics": ["activityName", "participants", "conversion", "roi"],
            "contentMetrics": ["contentType", "publishCount", "avgPlayTime", "completionRate"],
        },
    },
}


# ─── 生成文件 ─────────────────────────────────────────────────────────────────

def generate_config(project_id: str, project_name: str, project_type: str, description: str) -> dict:
    """生成 config.json 内容。"""
    tpl = PROJECT_TYPES[project_type]
    config = {
        "_comment": f"项目配置文件。类型: {tpl['label']}。修改后重新运行 data_injector.py 生效。",
        "id":          project_id,
        "name":        project_name,
        "description": description or tpl["description"],
        "template":    "../../templates/weekly_report_example.tsx",
        "schema":      "schema.json",
        "mockDataVar":  "mockData",
        "mockDataType": "DashboardData",
        "sections":    tpl["sections"],
        "moduleAlias": tpl["module_alias"],
        "stateDir":    f"../../state/{project_id}",
        "outputDir":   f"../../output/{project_id}",
    }
    if tpl["extra_fields"]:
        config["extraFields"] = {
            "_comment": f"{tpl['label']}特有扩展字段，在 schema.json 中以 extra 命名空间存放",
        }
        for field_name, fields in tpl["extra_fields"].items():
            config["extraFields"][field_name] = {"fields": fields}
    return config


def generate_schema(project_id: str, project_name: str, project_type: str) -> dict:
    """生成 schema.json 内容（带完整注释和示例数据）。"""
    tpl = PROJECT_TYPES[project_type]
    dims = tpl["health_dimensions"]

    schema = {
        "_comment": f"{project_name}数据模板。每周填写此文件，运行 data_injector.py --project {project_id} 生成周报。",
        "_usage":   f"python scripts/data_injector.py --project {project_id}",
        "meta": {
            "projectName": project_name,
            "reportPeriod": "2026-W17",
            "updatedAt": "2026/04/28",
            "version": "v1.0",
        },
        "healthScore": {
            "_comment": f"整体健康度评分（0-100）。维度：{'、'.join(d['name'] for d in dims)}。",
            "overall": 75,
            "trend": "up",
            "trendValue": "+2",
            "dimensions": [
                {"name": d["name"], "score": 75, "prevScore": 73, "color": d["color"]}
                for d in dims
            ],
            "summary": f"请填写{project_name}本周整体状态摘要（1-2句话）。",
        },
        "northStar": {
            "_comment": f"核心追踪指标。建议使用：{tpl['north_star_hint']}。",
            "metric": "核心指标名称",
            "unit": "单位",
            "currentValue": 0,
            "previousValue": 0,
            "targetValue": 0,
            "trend": "up",
            "trendValue": "+0%",
            "achievementRate": 0.0,
            "factors": [
                {
                    "id": "factor-001",
                    "label": "归因因素 1",
                    "contribution": 0,
                    "trend": "up",
                    "moduleId": "module-001",
                }
            ],
            "insight": "请填写本周核心指标的关键洞察。",
        },
        "kpiAlerts": [
            {
                "id": "alert-001",
                "level": "P1",
                "title": "告警标题",
                "description": "告警描述",
                "triggeredAt": "2026-04-28",
                "impact": "影响范围",
                "status": "处理中",
                "kpiId": "kpi-001",
            }
        ],
        "kpiMetrics": [
            {
                "id": "kpi-001",
                "label": "指标名称",
                "value": "0",
                "unit": "单位",
                "target": "目标值",
                "status": "normal",
                "trend": "up",
                "trendValue": "+0%",
                "description": "指标说明",
                "historyWeekly": [0, 0, 0, 0],
            }
        ],
        "milestones": [
            {
                "id": "ms-001",
                "version": "v1.0",
                "title": "里程碑标题",
                "date": "2026-06-30",
                "status": "active",
                "description": "里程碑描述",
                "achievements": [],
            }
        ],
        "modules": [
            {
                "id": "module-001",
                "name": tpl["module_alias"].get("modules", "模块") + " 1",
                "nameEn": "Module 1",
                "owner": "负责人",
                "priority": 1,
                "progress": 50,
                "status": "normal",
                "currentFocus": "本周重点工作描述",
                "nextMilestone": "下一里程碑",
                "nextMilestoneDate": "2026-05-31",
                "metrics": [
                    {"label": "指标 1", "value": "0", "trend": "up", "trendValue": "+0%"},
                    {"label": "指标 2", "value": "0", "trend": "flat", "trendValue": "0%"},
                ],
            }
        ],
        "risks": [
            {
                "id": "risk-001",
                "title": "风险标题",
                "level": "medium",
                "description": "风险描述",
                "owner": "负责人",
                "mitigation": "缓解措施",
            }
        ],
        "decisions": [
            {
                "id": "dec-001",
                "title": "待决策事项",
                "description": "决策背景描述",
                "deadline": "2026-05-10",
                "status": "pending",
            }
        ],
        "todos": [
            {
                "id": "todo-001",
                "title": "待办事项",
                "owner": "负责人",
                "dueDate": "2026-05-05",
                "priority": "high",
                "done": False,
            }
        ],
        "issues": [
            {
                "id": "issue-001",
                "title": "当前问题",
                "description": "问题描述",
                "level": "medium",
                "moduleId": "module-001",
            }
        ],
    }

    # 添加扩展字段
    if tpl["extra_fields"]:
        extra = {"_comment": f"{tpl['label']}特有扩展字段，供 Agent 生成定制化组件时使用"}
        for field_name, fields in tpl["extra_fields"].items():
            extra[field_name] = {f: f"请填写 {f}" for f in fields}
        schema["extra"] = extra

    return schema


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def validate_project_id(pid: str) -> bool:
    """验证项目 ID 格式（小写字母、数字、连字符）。"""
    return bool(re.match(r'^[a-z0-9][a-z0-9\-]{0,30}[a-z0-9]$', pid))


def create_project(project_id: str, project_name: str, project_type: str,
                   description: str = "", force: bool = False) -> str:
    """创建项目目录和配置文件，返回项目目录路径。"""
    project_dir = PROJECTS_DIR / project_id

    if project_dir.exists() and not force:
        raise FileExistsError(
            f"项目 '{project_id}' 已存在：{project_dir}\n"
            f"使用 --force 覆盖，或选择不同的项目 ID。"
        )

    project_dir.mkdir(parents=True, exist_ok=True)

    # 生成 config.json
    config = generate_config(project_id, project_name, project_type, description)
    config_path = project_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # 生成 schema.json
    schema = generate_schema(project_id, project_name, project_type)
    schema_path = project_dir / "schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    # 创建 state 和 output 目录
    (SKILL_ROOT / "state" / project_id).mkdir(parents=True, exist_ok=True)
    (SKILL_ROOT / "output" / project_id).mkdir(parents=True, exist_ok=True)

    return str(project_dir)


def interactive_create():
    """交互式项目创建流程。"""
    print("\n🚀 weekly-report-builder 新项目初始化\n")

    # 项目 ID
    while True:
        pid = input("项目 ID（小写字母/数字/连字符，如 my-project）: ").strip()
        if not pid:
            print("  ❌ 项目 ID 不能为空")
            continue
        if not validate_project_id(pid):
            print("  ❌ 格式不正确，只允许小写字母、数字和连字符，长度 2-32")
            continue
        if (PROJECTS_DIR / pid).exists():
            overwrite = input(f"  ⚠️  项目 '{pid}' 已存在，是否覆盖？(y/N): ").strip().lower()
            if overwrite != "y":
                continue
        break

    # 项目名称
    name = input("项目名称（如「投后管理周报」）: ").strip()
    if not name:
        name = f"{pid} 周报"

    # 项目类型
    print("\n可用项目类型：")
    for tid, tpl in PROJECT_TYPES.items():
        print(f"  {tid:<20} {tpl['label']}  —  {tpl['description'][:40]}...")
    while True:
        ptype = input(f"\n项目类型（默认 general）: ").strip() or "general"
        if ptype in PROJECT_TYPES:
            break
        print(f"  ❌ 未知类型 '{ptype}'，请从上方列表中选择")

    # 描述
    desc = input("项目描述（可选，直接回车跳过）: ").strip()

    # 确认
    print(f"\n即将创建项目：")
    print(f"  ID:   {pid}")
    print(f"  名称: {name}")
    print(f"  类型: {PROJECT_TYPES[ptype]['label']}")
    if desc:
        print(f"  描述: {desc}")

    confirm = input("\n确认创建？(Y/n): ").strip().lower()
    if confirm == "n":
        print("已取消。")
        return

    force = (PROJECTS_DIR / pid).exists()
    project_dir = create_project(pid, name, ptype, desc, force=force)

    print(f"\n✅ 项目已创建：{project_dir}")
    print(f"\n下一步：")
    print(f"  1. 编辑 projects/{pid}/schema.json，填入真实数据")
    print(f"  2. 运行：python scripts/data_injector.py --project {pid}")
    print(f"  3. 查看生成的周报：output/{pid}/weekly_report_*.tsx")


def main():
    parser = argparse.ArgumentParser(
        description="新项目一键初始化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--id",          default=None, help="项目 ID")
    parser.add_argument("--name",        default=None, help="项目名称")
    parser.add_argument("--type",        default="general", choices=list(PROJECT_TYPES.keys()), help="项目类型")
    parser.add_argument("--description", default="", help="项目描述")
    parser.add_argument("--force",       action="store_true", help="覆盖已存在的项目")
    parser.add_argument("--list-types",  action="store_true", help="列出所有项目类型")
    args = parser.parse_args()

    if args.list_types:
        print(f"{'类型 ID':<20} {'标签':<12} 描述")
        print("─" * 80)
        for tid, tpl in PROJECT_TYPES.items():
            print(f"{tid:<20} {tpl['label']:<12} {tpl['description'][:45]}")
        return

    # 非交互式模式
    if args.id:
        if not validate_project_id(args.id):
            print(f"❌ 项目 ID 格式不正确：{args.id}", file=sys.stderr)
            sys.exit(1)
        name = args.name or f"{args.id} 周报"
        try:
            project_dir = create_project(args.id, name, args.type, args.description, args.force)
            print(f"✅ 项目已创建：{project_dir}")
            print(f"   下一步：编辑 projects/{args.id}/schema.json，然后运行 data_injector.py --project {args.id}")
        except FileExistsError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        return

    # 交互式模式
    interactive_create()


if __name__ == "__main__":
    main()

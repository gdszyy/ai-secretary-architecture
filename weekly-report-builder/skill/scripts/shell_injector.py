"""
shell_injector.py — HTML Shell 模板注入器（多项目周报专用）

核心理念：
  大模型只输出 ~50 行 JSON 数据，本脚本负责将 JSON 渲染为完整 HTML。
  相比旧方案（大模型直接输出 1600+ 行 HTML），Token 节省约 80%。

数据格式（JSON Schema）：
  见 projects/platform/shell_schema.json

用法：
  python scripts/shell_injector.py --data /path/to/data.json
  python scripts/shell_injector.py --data /path/to/data.json --output output/platform/report.html
  python scripts/shell_injector.py --data /path/to/data.json --dry-run   # 仅验证，不写文件

占位符说明（模板中的 {{KEY}}）：
  META_TITLE          页面 <title>
  LOGO_CHAR           侧边栏 Logo 文字（1-2字）
  REPORT_TITLE        侧边栏标题
  DATE_RANGE          日期范围
  NAV_RISK_BADGE      风险导航徽章文字
  NAV_PROJECT_LINKS   侧边栏项目导航链接 HTML
  FOOTER_TEXT         侧边栏底部文字
  HOME_SUBTITLE       首页副标题
  HOME_BANNER_HTML    首页核心结论 HTML
  HOME_STAT_CARDS     首页统计卡 HTML
  HOME_ACHIEVEMENTS   首页成果列表 HTML
  HOME_TOP_RISKS      首页风险 TOP3 HTML
  RISK_HIGH_ITEMS     风险总览高风险 HTML
  RISK_MID_ITEMS      风险总览中风险 HTML
  PLAN_SUBTITLE       下周计划副标题
  PLAN_TABLE_ROWS     下周计划表格行 HTML
  IMPROVE_ROOT_CAUSES 改进措施根因 HTML
  IMPROVE_ACTION_CARDS 改进措施行动卡 HTML
  PROJECT_PAGES       所有项目详情页 HTML
  CHART_DATA_JSON     图表数据 JSON（内联到 JS）
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

SKILL_ROOT    = Path(__file__).parent.parent
SHELL_TEMPLATE = SKILL_ROOT / "templates" / "shells" / "multi_project.html"
DEFAULT_OUTPUT_DIR = SKILL_ROOT / "output"

# ─── 颜色常量（与模板 JS 保持一致）────────────────────────────────────────────

COLOR_MAP = {
    "high":    "oklch(0.58 0.22 25 / 0.8)",
    "mid":     "oklch(0.68 0.19 55 / 0.8)",
    "low":     "oklch(0.62 0.2 160 / 0.8)",
    "normal":  "oklch(0.62 0.2 160 / 0.7)",
    "risk":    "oklch(0.68 0.19 55 / 0.7)",
    "blocked": "oklch(0.58 0.22 25 / 0.7)",
    "blue":    "oklch(0.58 0.22 255 / 0.7)",
    "muted":   "oklch(0.52 0.012 240 / 0.5)",
}

STATUS_COLOR_MAP = {
    "正常": COLOR_MAP["normal"],
    "有风险": COLOR_MAP["risk"],
    "高风险": COLOR_MAP["blocked"],
    "阻塞": COLOR_MAP["muted"],
    "延期": COLOR_MAP["risk"],
}

RISK_BADGE_CLASS = {"high": "high", "mid": "mid", "low": "low"}
RISK_BADGE_TEXT  = {"high": "高",   "mid": "中",  "low": "低"}
STATUS_TAG_CLASS = {
    "正常": "tag-done", "有风险": "tag-mid", "高风险": "tag-risk",
    "阻塞": "tag-risk",  "延期": "tag-mid",  "进行中": "tag-progress",
}
NAV_BADGE_CLASS = {
    "正常": "ok", "有风险": "mid", "高风险": "", "阻塞": "mid", "延期": "mid",
}


# ─── 数据加载与校验 ────────────────────────────────────────────────────────────

def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    required = ["meta", "summary", "projects", "risks", "plan", "improvements", "charts"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"JSON 缺少必填字段: {missing}")
    return data


# ─── HTML 片段生成器 ───────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    """HTML 转义（仅处理 & < > 引号）"""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_nav_links(projects: list) -> str:
    lines = []
    for p in projects:
        badge_class = NAV_BADGE_CLASS.get(p.get("status", ""), "")
        badge_text  = p.get("navBadge", p.get("status", ""))
        badge_html  = f'<span class="nav-badge {badge_class}">{_esc(badge_text)}</span>' if badge_text else ""
        lines.append(
            f'<a class="nav-link" onclick="showPage(\'{p["id"]}\')">'
            f'<span class="nav-icon">{p.get("icon","📋")}</span>'
            f'<span>{_esc(p["name"])}</span>'
            f'{badge_html}</a>'
        )
    return "\n      ".join(lines)


def build_stat_cards(stats: list) -> str:
    """stats: [{color, label, value, desc}]"""
    cards = []
    for s in stats:
        cards.append(
            f'<div class="stat-card">'
            f'<div class="stat-bar {s["color"]}"></div>'
            f'<div class="stat-label">{_esc(s["label"])}</div>'
            f'<div class="stat-value">{_esc(str(s["value"]))}</div>'
            f'<div class="stat-desc">{_esc(s["desc"])}</div>'
            f'</div>'
        )
    return "\n        ".join(cards)


def build_achievement_list(items: list) -> str:
    lines = []
    for item in items:
        lines.append(
            f'<li><span class="achievement-dot"></span>{item}</li>'
        )
    return "\n          ".join(lines)


def build_risk_items(risks: list) -> str:
    lines = []
    for r in risks:
        level = r.get("level", "mid")
        badge_cls  = RISK_BADGE_CLASS.get(level, "mid")
        badge_text = RISK_BADGE_TEXT.get(level, "中")
        lines.append(
            f'<div class="risk-item {badge_cls}">'
            f'<span class="risk-badge {badge_cls}">{badge_text}</span>'
            f'<div>'
            f'<div class="risk-title">{r["title"]}</div>'
            f'<div class="risk-desc">{r.get("desc","")}</div>'
            f'</div></div>'
        )
    return "\n          ".join(lines)


def build_plan_rows(rows: list) -> str:
    lines = []
    for r in rows:
        pri = r.get("priority", "mid")
        lines.append(
            f'<tr>'
            f'<td><strong>{_esc(r["project"])}</strong></td>'
            f'<td>{_esc(r["task"])}</td>'
            f'<td>{_esc(r.get("milestone",""))}</td>'
            f'<td><span class="priority-badge {pri}">{RISK_BADGE_TEXT.get(pri,"中")}</span></td>'
            f'</tr>'
        )
    return "\n            ".join(lines)


def build_root_causes(items: list) -> str:
    lines = []
    for i, rc in enumerate(items, 1):
        level = rc.get("level", "mid")
        lines.append(
            f'<div class="root-cause-card {level}">'
            f'<div class="rc-label {level}">根因 {i} · {"高优先级" if level=="high" else "中优先级"}</div>'
            f'<div class="rc-title">{rc["title"]}</div>'
            f'<div class="rc-desc">{rc.get("desc","")}</div>'
            f'</div>'
        )
    return "\n          ".join(lines)


def build_action_cards(items: list) -> str:
    lines = []
    for card in items:
        items_html = "\n".join(
            f'<li><span class="ic-dot"></span>{_esc(it)}</li>'
            for it in card.get("items", [])
        )
        lines.append(
            f'<div class="improve-card">'
            f'<div class="ic-icon">{card.get("icon","📋")}</div>'
            f'<div class="ic-title">{_esc(card["title"])}</div>'
            f'<ul class="ic-list">{items_html}</ul>'
            f'</div>'
        )
    return "\n          ".join(lines)


def build_timeline(milestones: list) -> str:
    lines = []
    for m in milestones:
        dot_class = m.get("dotClass", "upcoming")
        lines.append(
            f'<div class="timeline-item">'
            f'<div class="timeline-dot {dot_class}"></div>'
            f'<div class="timeline-date">{_esc(m["date"])}</div>'
            f'<div class="timeline-title">{_esc(m["title"])}</div>'
            f'<div class="timeline-desc">{_esc(m.get("desc",""))}</div>'
            f'</div>'
        )
    return "\n          ".join(lines)


def build_project_page(p: dict) -> str:
    """渲染单个项目详情页"""
    pid     = p["id"]
    name    = p.get("name", pid)
    icon    = p.get("icon", "📋")
    owner   = p.get("owner", "")
    phase   = p.get("phase", "")
    status  = p.get("status", "")
    progress = p.get("progress", 0)
    tag_cls = STATUS_TAG_CLASS.get(status, "tag-progress")

    # 本周进展
    this_week_items = "".join(
        f'<li><span class="detail-dot"></span>{_esc(it)}</li>'
        for it in p.get("thisWeek", [])
    )
    # 下周计划
    next_week_items = "".join(
        f'<li><span class="detail-dot"></span>{_esc(it)}</li>'
        for it in p.get("nextWeek", [])
    )
    # 里程碑
    timeline_html = build_timeline(p.get("milestones", []))
    # 风险
    risk_html = build_risk_items(p.get("risks", []))

    # 额外内容（如事故记录）
    extra_html = p.get("extraHtml", "")

    return f"""
    <!-- ══ {name} ══ -->
    <div id="{pid}" class="page">
      <div class="project-header">
        <div class="project-icon">{icon}</div>
        <div>
          <div class="project-name">{_esc(name)}</div>
          <div class="project-meta">负责人：{_esc(owner)} · 当前阶段：{_esc(phase)}</div>
        </div>
        <span class="status-tag {tag_cls}" style="margin-left: auto;">{_esc(status)}</span>
      </div>
      <div style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="font-size: 13px; color: var(--text-muted);">本周完成度</span>
          <span style="font-size: 13px; font-weight: 600; font-family: 'DM Sans';">{progress}%</span>
        </div>
        <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width: {progress}%;"></div></div>
      </div>
      <div class="section-grid">
        <div class="card">
          <div class="card-title">本周进展</div>
          <ul class="detail-list">{this_week_items}</ul>
        </div>
        <div class="card">
          <div class="card-title">下周计划</div>
          <ul class="detail-list">{next_week_items}</ul>
        </div>
      </div>
      <div class="card">
        <div class="card-title">里程碑</div>
        <div class="timeline">{timeline_html}</div>
      </div>
      <div class="card">
        <div class="card-title">风险与阻塞</div>
        <div class="risk-list">{risk_html}</div>
      </div>
      {extra_html}
    </div>"""


def build_project_pages(projects: list) -> str:
    return "\n".join(build_project_page(p) for p in projects)


# ─── 图表数据构建 ──────────────────────────────────────────────────────────────

def build_chart_data(charts: dict, projects: list) -> dict:
    """
    将 JSON 中的 charts 字段转换为模板 JS 可直接消费的格式。
    如果 charts 中已提供完整数据则直接使用，否则从 projects 自动推断。
    """
    labels = [p["id"] for p in projects]

    # 状态分布
    status_dist = charts.get("statusDist", {})
    if not status_dist:
        from collections import Counter
        cnt = Counter(p.get("status", "正常") for p in projects)
        status_dist = {
            "labels": list(cnt.keys()),
            "data":   list(cnt.values()),
        }

    # 完成度
    completion = charts.get("completion", {})
    if not completion:
        data = [p.get("progress", 0) for p in projects]
        colors = [
            COLOR_MAP["normal"] if p.get("progress", 0) >= 70
            else COLOR_MAP["risk"] if p.get("progress", 0) >= 40
            else COLOR_MAP["blocked"]
            for p in projects
        ]
        completion = {"labels": labels, "data": data, "colors": colors}

    # 风险等级
    risk_level = charts.get("riskLevel", {})
    if not risk_level:
        high_data = [1 if any(r.get("level") == "high" for r in p.get("risks", [])) else 0 for p in projects]
        mid_data  = [1 if any(r.get("level") == "mid"  for r in p.get("risks", [])) else 0 for p in projects]
        low_data  = [1 if not p.get("risks") else 0 for p in projects]
        risk_level = {"labels": labels, "high": high_data, "mid": mid_data, "low": low_data}

    # 风险雷达
    risk_radar = charts.get("riskRadar", {
        "labels": ["发布流程", "架构稳定性", "外部依赖", "人力资源", "产品管理", "技术方案"],
        "data":   [50, 50, 50, 50, 50, 50]
    })

    # 热力图
    heatmap = charts.get("heatmap", {})
    if not heatmap:
        sorted_projects = sorted(projects, key=lambda p: -p.get("riskScore", 50))
        heatmap_labels = [p["id"] for p in sorted_projects]
        heatmap_data   = [p.get("riskScore", 50) for p in sorted_projects]
        heatmap_colors = [
            COLOR_MAP["blocked"] if s >= 80
            else COLOR_MAP["risk"] if s >= 50
            else COLOR_MAP["normal"]
            for s in heatmap_data
        ]
        heatmap = {"labels": heatmap_labels, "data": heatmap_data, "colors": heatmap_colors}

    # 甘特图
    gantt = charts.get("gantt", {})
    if not gantt:
        gantt_labels   = [p["id"] for p in projects if p.get("ganttDays", 0) > 0]
        gantt_offsets  = [p.get("ganttOffset", 0) for p in projects if p.get("ganttDays", 0) > 0]
        gantt_durations= [p.get("ganttDays", 7)   for p in projects if p.get("ganttDays", 0) > 0]
        gantt_colors   = [
            COLOR_MAP["normal"] if p.get("status") == "正常"
            else COLOR_MAP["blocked"] if p.get("status") in ("高风险", "阻塞")
            else COLOR_MAP["risk"]
            for p in projects if p.get("ganttDays", 0) > 0
        ]
        gantt = {"labels": gantt_labels, "offsets": gantt_offsets, "durations": gantt_durations, "colors": gantt_colors}

    return {
        "statusDist": status_dist,
        "completion": completion,
        "riskLevel":  risk_level,
        "riskRadar":  risk_radar,
        "heatmap":    heatmap,
        "gantt":      gantt,
    }


# ─── 主注入逻辑 ────────────────────────────────────────────────────────────────

def render(data: dict, template_path: str = None) -> str:
    """将 JSON 数据渲染为完整 HTML 字符串。"""
    tpl_path = template_path or str(SHELL_TEMPLATE)
    with open(tpl_path, encoding="utf-8") as f:
        tpl = f.read()

    meta     = data["meta"]
    summary  = data["summary"]
    projects = data["projects"]
    risks    = data["risks"]
    plan     = data["plan"]
    improvements = data["improvements"]
    charts   = data["charts"]

    chart_data = build_chart_data(charts, projects)

    replacements = {
        "META_TITLE":          meta.get("title", "周报"),
        "LOGO_CHAR":           meta.get("logoChar", "中"),
        "REPORT_TITLE":        meta.get("reportTitle", "团队周报"),
        "DATE_RANGE":          meta.get("dateRange", ""),
        "NAV_RISK_BADGE":      summary.get("navRiskBadge", ""),
        "NAV_PROJECT_LINKS":   build_nav_links(projects),
        "FOOTER_TEXT":         meta.get("footerText", "内部汇报"),
        "HOME_SUBTITLE":       summary.get("subtitle", ""),
        "HOME_BANNER_HTML":    summary.get("bannerHtml", ""),
        "HOME_STAT_CARDS":     build_stat_cards(summary.get("stats", [])),
        "HOME_ACHIEVEMENTS":   build_achievement_list(summary.get("achievements", [])),
        "HOME_TOP_RISKS":      build_risk_items(risks.get("top3", [])),
        "RISK_HIGH_ITEMS":     build_risk_items([r for r in risks.get("all", []) if r.get("level") == "high"]),
        "RISK_MID_ITEMS":      build_risk_items([r for r in risks.get("all", []) if r.get("level") == "mid"]),
        "PLAN_SUBTITLE":       plan.get("subtitle", ""),
        "PLAN_TABLE_ROWS":     build_plan_rows(plan.get("rows", [])),
        "IMPROVE_ROOT_CAUSES": build_root_causes(improvements.get("rootCauses", [])),
        "IMPROVE_ACTION_CARDS":build_action_cards(improvements.get("actionCards", [])),
        "PROJECT_PAGES":       build_project_pages(projects),
        "CHART_DATA_JSON":     json.dumps(chart_data, ensure_ascii=False),
    }

    for key, value in replacements.items():
        tpl = tpl.replace("{{" + key + "}}", value)

    return tpl


def inject(data_path: str, output_path: str, dry_run: bool = False,
           template_path: str = None) -> None:
    data = load_data(data_path)
    html = render(data, template_path)

    if dry_run:
        print(f"✅ DRY RUN: 渲染成功，输出 {len(html)} 字符 / {html.count(chr(10))} 行")
        remaining = [k for k in ["{{META_TITLE}}", "{{PROJECT_PAGES}}", "{{CHART_DATA_JSON}}"] if k in html]
        if remaining:
            print(f"⚠️  未替换占位符: {remaining}")
        else:
            print("✅ 所有占位符已替换完毕")
        return

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    meta = data["meta"]
    print(f"✅ 周报已生成: {output_path}")
    print(f"   报告周期: {meta.get('dateRange','')}")
    print(f"   项目数量: {len(data['projects'])}")
    print(f"   文件大小: {len(html):,} 字符 / {html.count(chr(10))} 行")


# ─── CLI 入口 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="HTML Shell 注入器：将 JSON 数据注入多项目周报模板",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scripts/shell_injector.py --data /path/to/data.json
  python scripts/shell_injector.py --data /path/to/data.json --output output/report.html
  python scripts/shell_injector.py --data /path/to/data.json --dry-run
        """
    )
    parser.add_argument("--data",     required=True, help="JSON 数据文件路径")
    parser.add_argument("--output",   default=None,  help="输出 HTML 文件路径（默认自动推断）")
    parser.add_argument("--template", default=None,  help="HTML Shell 模板路径（默认 templates/shells/multi_project.html）")
    parser.add_argument("--dry-run",  action="store_true", help="仅验证，不写文件")
    args = parser.parse_args()

    try:
        data = load_data(args.data)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"❌ 数据加载失败: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output is None:
        period = data["meta"].get("period", datetime.now().strftime("%Y-W%V"))
        output_path = str(DEFAULT_OUTPUT_DIR / "platform" / f"weekly_report_{period}.html")
    else:
        output_path = args.output

    try:
        inject(args.data, output_path, dry_run=args.dry_run, template_path=args.template)
    except Exception as e:
        print(f"❌ 注入失败: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

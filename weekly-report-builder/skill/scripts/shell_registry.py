"""
shell_registry.py — Shell 模板注册表与分发器

核心设计：
  每种项目类型对应一个 HTML Shell 模板 + 一个渲染器类。
  render.py 作为统一入口，通过此注册表自动路由到对应渲染器。

注册表结构：
  REGISTRY[project_type] = {
    "shell":    相对于 templates/shells/ 的模板文件名
    "renderer": 渲染器类（继承自 BaseShellRenderer）
    "schema":   相对于 projects/{type}/ 的 Schema 示例文件名
    "desc":     类型描述
  }

扩展方法（新增项目类型）：
  1. 在 templates/shells/ 下创建新的 HTML Shell 模板
  2. 在 projects/{type}/ 下创建 shell_schema.json
  3. 在本文件中创建继承 BaseShellRenderer 的渲染器类
  4. 在 REGISTRY 中注册

Token 节省原理：
  大模型只输出 JSON 数据（~100-200 行），本框架负责渲染为完整 HTML。
  相比直接生成 HTML（~1000-2000 行），节省约 80-90% 输出 Token。
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Type
import json
import os

SKILL_ROOT = Path(__file__).parent.parent
SHELLS_DIR = SKILL_ROOT / "templates" / "shells"


# ─── 基类 ──────────────────────────────────────────────────────────────────────

class BaseShellRenderer:
    """
    所有 Shell 渲染器的基类。
    子类只需实现 build_replacements(data) 方法，
    返回 {占位符key: HTML字符串} 的字典。
    """

    # 子类必须声明对应的 Shell 模板文件名
    SHELL_FILE: str = ""

    def __init__(self, data: dict):
        self.data = data
        self._validate()

    def _validate(self):
        """校验必填字段，子类可覆盖"""
        required = self.required_fields()
        missing = [k for k in required if k not in self.data]
        if missing:
            raise ValueError(f"[{self.__class__.__name__}] JSON 缺少必填字段: {missing}")

    def required_fields(self) -> list:
        """子类声明必填字段列表"""
        return ["meta"]

    def build_replacements(self) -> Dict[str, str]:
        """
        子类实现：返回 {占位符key: HTML内容} 字典。
        占位符在模板中以 {{KEY}} 形式出现。
        """
        raise NotImplementedError

    def render(self, template_path: str = None) -> str:
        """将 JSON 数据注入 Shell 模板，返回完整 HTML 字符串。"""
        tpl_path = template_path or str(SHELLS_DIR / self.SHELL_FILE)
        if not Path(tpl_path).exists():
            raise FileNotFoundError(f"Shell 模板不存在: {tpl_path}")

        with open(tpl_path, encoding="utf-8") as f:
            tpl = f.read()

        replacements = self.build_replacements()
        for key, value in replacements.items():
            tpl = tpl.replace("{{" + key + "}}", str(value))

        # 检查是否有未替换的占位符
        import re
        remaining = re.findall(r'\{\{[A-Z_]+\}\}', tpl)
        if remaining:
            import warnings
            warnings.warn(f"[{self.__class__.__name__}] 未替换占位符: {set(remaining)}")

        return tpl

    # ── 通用 HTML 工具方法（所有子类共享）─────────────────────────────────────

    @staticmethod
    def _esc(s: str) -> str:
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _status_class(status: str) -> str:
        return {
            "done": "tag-done", "success": "tag-done", "正常": "tag-done",
            "active": "tag-progress", "进行中": "tag-progress", "warning": "tag-mid",
            "有风险": "tag-mid", "延期": "tag-mid",
            "danger": "tag-risk", "高风险": "tag-risk", "阻塞": "tag-risk",
            "blocked": "tag-risk", "error": "tag-risk",
        }.get(status, "tag-progress")

    @staticmethod
    def _risk_level_class(level: str) -> str:
        return {"high": "high", "mid": "mid", "low": "low"}.get(level, "mid")

    @staticmethod
    def _risk_level_text(level: str) -> str:
        return {"high": "高", "mid": "中", "low": "低"}.get(level, "中")

    def _build_risk_items(self, risks: list) -> str:
        lines = []
        for r in risks:
            lv = r.get("level", "mid")
            lines.append(
                f'<div class="risk-item {self._risk_level_class(lv)}">'
                f'<span class="risk-badge {self._risk_level_class(lv)}">{self._risk_level_text(lv)}</span>'
                f'<div><div class="risk-title">{self._esc(r.get("title",""))}</div>'
                f'<div class="risk-desc">{self._esc(r.get("desc",""))}</div></div></div>'
            )
        return "\n".join(lines)

    def _build_timeline(self, milestones: list) -> str:
        lines = []
        for m in milestones:
            dc = m.get("dotClass", "upcoming")
            lines.append(
                f'<div class="timeline-item">'
                f'<div class="timeline-dot {dc}"></div>'
                f'<div class="timeline-date">{self._esc(m.get("date",""))}</div>'
                f'<div class="timeline-title">{self._esc(m.get("title",""))}</div>'
                f'<div class="timeline-desc">{self._esc(m.get("desc",""))}</div></div>'
            )
        return "\n".join(lines)

    def _build_stat_cards(self, stats: list) -> str:
        cards = []
        for s in stats:
            cards.append(
                f'<div class="stat-card">'
                f'<div class="stat-bar {s.get("color","blue")}"></div>'
                f'<div class="stat-label">{self._esc(s.get("label",""))}</div>'
                f'<div class="stat-value">{self._esc(str(s.get("value","")))}</div>'
                f'<div class="stat-desc">{self._esc(s.get("desc",""))}</div></div>'
            )
        return "\n".join(cards)

    def _build_kpi_cards(self, metrics: list) -> str:
        cards = []
        for m in metrics:
            status = m.get("status", "normal")
            trend  = m.get("trend", "")
            trend_val = m.get("trendValue", "")
            trend_icon = "↑" if trend == "up" else "↓" if trend == "down" else "→"
            trend_cls  = "trend-up" if trend == "up" else "trend-down" if trend == "down" else "trend-flat"
            cards.append(
                f'<div class="kpi-card {status}">'
                f'<div class="kpi-label">{self._esc(m.get("label",""))}</div>'
                f'<div class="kpi-value">{self._esc(str(m.get("value","")))}'
                f'<span class="kpi-unit">{self._esc(m.get("unit",""))}</span></div>'
                f'<div class="kpi-trend {trend_cls}">{trend_icon} {self._esc(trend_val)}</div>'
                f'<div class="kpi-target">{self._esc(m.get("target",""))}</div></div>'
            )
        return "\n".join(cards)

    def _build_module_cards(self, modules: list, alias: dict = None) -> str:
        alias = alias or {}
        cards = []
        for mod in modules:
            status = mod.get("status", "active")
            tag_cls = self._status_class(status)
            progress = mod.get("progress", 0)
            metrics_html = "".join(
                f'<div class="mod-metric"><span>{self._esc(k)}</span><strong>{self._esc(str(v))}</strong></div>'
                for k, v in mod.get("metrics", {}).items()
            )
            cards.append(
                f'<div class="module-card">'
                f'<div class="mod-header">'
                f'<span class="mod-name">{self._esc(mod.get("name",""))}</span>'
                f'<span class="mod-owner">{self._esc(mod.get("owner",""))}</span>'
                f'<span class="status-tag {tag_cls}">{self._esc(status)}</span></div>'
                f'<div class="mod-progress-wrap"><div class="mod-progress-fill" style="width:{progress}%"></div></div>'
                f'<div class="mod-focus">{self._esc(mod.get("currentFocus",""))}</div>'
                f'<div class="mod-metrics">{metrics_html}</div></div>'
            )
        return "\n".join(cards)

    def _build_health_dimensions(self, dimensions: list) -> str:
        bars = []
        for d in dimensions:
            score = d.get("score", 0)
            status = d.get("status", "normal")
            color = {"success": "green", "warning": "amber", "danger": "red"}.get(status, "blue")
            bars.append(
                f'<div class="health-dim">'
                f'<div class="health-dim-header">'
                f'<span>{self._esc(d.get("name",""))}</span>'
                f'<span class="health-score {color}">{score}</span></div>'
                f'<div class="health-bar-wrap"><div class="health-bar-fill {color}" style="width:{score}%"></div></div>'
                f'<div class="health-comment">{self._esc(d.get("comment",""))}</div></div>'
            )
        return "\n".join(bars)


# ─── platform / post-investment 渲染器（已有，引用 shell_injector.py 的逻辑）──

class MultiProjectRenderer(BaseShellRenderer):
    """
    多项目周报渲染器（platform / post-investment，项目数 ≥ 3）。
    直接复用 shell_injector.py 中的 render() 函数。
    """
    SHELL_FILE = "multi_project.html"

    def required_fields(self):
        return ["meta", "summary", "projects", "risks", "plan", "improvements", "charts"]

    def build_replacements(self) -> Dict[str, str]:
        # 委托给 shell_injector.py 的完整实现
        from scripts.shell_injector import render as _render
        # 返回空字典，render() 方法被覆盖
        return {}

    def render(self, template_path: str = None) -> str:
        # 直接调用 shell_injector 的完整渲染逻辑
        import sys
        sys.path.insert(0, str(SKILL_ROOT / "scripts"))
        from shell_injector import render as _render
        return _render(self.data, template_path or str(SHELLS_DIR / self.SHELL_FILE))


# ─── general / default 渲染器 ─────────────────────────────────────────────────

class GeneralRenderer(BaseShellRenderer):
    """
    通用产品团队周报渲染器（general/default 类型）。
    包含：北极星指标、健康度、KPI 监控、里程碑、业务模块、风险。
    """
    SHELL_FILE = "general.html"

    def required_fields(self):
        return ["meta", "summary", "northStar", "healthScore", "milestones", "modules", "risks"]

    def build_replacements(self) -> Dict[str, str]:
        d = self.data
        meta        = d["meta"]
        summary     = d["summary"]
        north_star  = d["northStar"]
        health      = d["healthScore"]
        milestones  = d.get("milestones", [])
        modules     = d.get("modules", [])
        risks       = d.get("risks", [])
        kpi_metrics = d.get("kpiMetrics", [])
        kpi_alerts  = d.get("kpiAlerts", [])

        # 北极星因子
        factors_html = "".join(
            f'<div class="factor-item {f.get("direction","positive")}">'
            f'<span class="factor-name">{self._esc(f.get("name",""))}</span>'
            f'<span class="factor-value">{self._esc(str(f.get("contribution","")))} {meta.get("unit","")}</span>'
            f'<div class="factor-detail">{self._esc(f.get("detail",""))}</div></div>'
            for f in north_star.get("factors", [])
        )

        # 里程碑列表
        milestone_cards = "".join(
            f'<div class="milestone-card {m.get("status","upcoming")}">'
            f'<div class="ms-version">{self._esc(m.get("version",""))}</div>'
            f'<div class="ms-title">{self._esc(m.get("title",""))}</div>'
            f'<div class="ms-date">{self._esc(m.get("date",""))}</div>'
            f'<div class="ms-progress-wrap"><div class="ms-progress-fill" style="width:{m.get("progress",0)}%"></div></div>'
            f'<ul class="ms-achievements">{"".join(f"<li>{self._esc(a)}</li>" for a in m.get("achievements",[]))}</ul>'
            f'</div>'
            for m in milestones
        )

        # KPI 预警
        alerts_html = "".join(
            f'<div class="alert-item {a.get("level","P2").lower()}">'
            f'<span class="alert-level">{self._esc(a.get("level",""))}</span>'
            f'<div class="alert-title">{self._esc(a.get("title",""))}</div>'
            f'<div class="alert-desc">{self._esc(a.get("description",""))}</div>'
            f'<div class="alert-impact">{self._esc(a.get("impact",""))}</div></div>'
            for a in kpi_alerts
        )

        return {
            "META_TITLE":        meta.get("projectName", "周报"),
            "REPORT_TITLE":      meta.get("projectName", "项目周报"),
            "DATE_RANGE":        meta.get("reportPeriod", ""),
            "HOME_SUBTITLE":     summary.get("subtitle", ""),
            "HOME_BANNER_HTML":  summary.get("bannerHtml", ""),
            "HOME_STAT_CARDS":   self._build_stat_cards(summary.get("stats", [])),
            "NORTH_STAR_METRIC": north_star.get("metric", ""),
            "NORTH_STAR_VALUE":  str(north_star.get("currentValue", "")),
            "NORTH_STAR_UNIT":   north_star.get("unit", ""),
            "NORTH_STAR_TREND":  north_star.get("trendValue", ""),
            "NORTH_STAR_TARGET": str(north_star.get("targetValue", "")),
            "NORTH_STAR_RATE":   str(north_star.get("achievementRate", "")),
            "NORTH_STAR_INSIGHT":north_star.get("insight", ""),
            "NORTH_STAR_FACTORS":factors_html,
            "HEALTH_SCORE":      str(health.get("overall", "")),
            "HEALTH_TREND":      health.get("trendValue", ""),
            "HEALTH_SUMMARY":    health.get("summary", ""),
            "HEALTH_DIMENSIONS": self._build_health_dimensions(health.get("dimensions", [])),
            "KPI_CARDS":         self._build_kpi_cards(kpi_metrics),
            "KPI_ALERTS":        alerts_html,
            "MILESTONE_CARDS":   milestone_cards,
            "MODULE_CARDS":      self._build_module_cards(modules),
            "RISK_ITEMS":        self._build_risk_items(risks),
            "CHART_DATA_JSON":   json.dumps(d.get("charts", {}), ensure_ascii=False),
            "FOOTER_TEXT":       meta.get("footerText", "内部汇报"),
        }


# ─── growth-team 渲染器 ───────────────────────────────────────────────────────

class GrowthRenderer(BaseShellRenderer):
    """
    增长团队周报渲染器（growth-team 类型）。
    在 GeneralRenderer 基础上，新增转化漏斗、渠道 ROI、实验列表。
    """
    SHELL_FILE = "growth.html"

    def required_fields(self):
        return ["meta", "summary", "northStar", "healthScore", "milestones", "modules", "risks"]

    def build_replacements(self) -> Dict[str, str]:
        d    = self.data
        meta = d["meta"]
        extra = d.get("extra", {})

        # 转化漏斗
        funnel = extra.get("funnelMetrics", [])
        funnel_rows = "".join(
            f'<tr><td>{self._esc(f.get("stage",""))}</td>'
            f'<td>{self._esc(str(f.get("users","")))}</td>'
            f'<td>{self._esc(str(f.get("conversionRate","")))}</td>'
            f'<td class="dropoff">{self._esc(str(f.get("dropoffRate","")))}</td></tr>'
            for f in funnel
        )

        # 渠道 ROI
        channels = extra.get("channelROI", [])
        channel_rows_parts = []
        for c in channels:
            roi_raw = str(c.get("roi", 0)).replace("%", "").strip()
            try:
                roi_cls = "roi-positive" if float(roi_raw or 0) > 0 else "roi-negative"
            except ValueError:
                roi_cls = "roi-positive"
            channel_rows_parts.append(
                f'<tr><td>{self._esc(c.get("channel",""))}</td>'
                f'<td>{self._esc(str(c.get("spend","")))}</td>'
                f'<td>{self._esc(str(c.get("newUsers","")))}</td>'
                f'<td>{self._esc(str(c.get("cac","")))}</td>'
                f'<td>{self._esc(str(c.get("ltv","")))}</td>'
                f'<td class="{roi_cls}">{self._esc(str(c.get("roi","")))}</td></tr>'
            )
        channel_rows = "".join(channel_rows_parts)

        # 实验列表（modules 在 growth 类型中代表渠道/实验）
        modules = d.get("modules", [])

        # 复用 GeneralRenderer 的通用部分
        gen = GeneralRenderer.__new__(GeneralRenderer)
        gen.data = d

        return {
            **gen.build_replacements(),
            "FUNNEL_ROWS":   funnel_rows,
            "CHANNEL_ROWS":  channel_rows,
            "MODULE_CARDS":  self._build_module_cards(modules),
            "CHART_DATA_JSON": json.dumps(d.get("charts", {}), ensure_ascii=False),
        }


# ─── post-investment 渲染器 ───────────────────────────────────────────────────

class PostInvestmentRenderer(BaseShellRenderer):
    """
    投后管理周报渲染器（post-investment 类型）。
    在 MultiProjectRenderer 基础上，新增组合概览、融资动态。
    """
    SHELL_FILE = "post_investment.html"

    def required_fields(self):
        return ["meta", "summary", "portfolio", "companies", "risks", "plan"]

    def build_replacements(self) -> Dict[str, str]:
        d     = self.data
        meta  = d["meta"]
        port  = d.get("portfolio", {})
        extra = d.get("extra", {})

        # 组合概览卡
        portfolio_cards = self._build_stat_cards([
            {"color": "blue",  "label": "总投资额",     "value": port.get("totalInvested", ""),  "desc": ""},
            {"color": "green", "label": "已部署资金",   "value": port.get("deployed", ""),        "desc": ""},
            {"color": "amber", "label": "账面回报倍数", "value": port.get("moic", ""),            "desc": "IRR: " + str(port.get("irr", ""))},
            {"color": "blue",  "label": "退出管道",     "value": port.get("exitPipeline", ""),   "desc": ""},
        ])
        # 融资动态
        funding_rounds = extra.get("fundingRounds", [])
        funding_rows_parts = []
        for r in funding_rounds:
            st = r.get("status", "")
            funding_rows_parts.append(
                f'<tr><td><strong>{self._esc(r.get("company",""))}</strong></td>'
                f'<td>{self._esc(r.get("round",""))}</td>'
                f'<td>{self._esc(str(r.get("amount","")))}</td>'
                f'<td>{self._esc(r.get("lead",""))}</td>'
                f'<td>{self._esc(r.get("date",""))}</td>'
                f'<td><span class="status-tag {self._status_class(st)}">'
                f'{self._esc(st)}</span></td></tr>'
            )
        funding_rows = "".join(funding_rows_parts)
        # 被投企业列表（companies 字段，结构类似 projects）
        companies = d.get("companies", [])
        company_cards_parts = []
        for c in companies:
            cst = c.get("status", "")
            company_cards_parts.append(
                f'<div class="company-card">'
                f'<div class="co-header">'
                f'<span class="co-name">{self._esc(c.get("name",""))}</span>'
                f'<span class="co-stage">{self._esc(c.get("stage",""))}</span>'
                f'<span class="status-tag {self._status_class(cst)}">{self._esc(cst)}</span></div>'
                f'<div class="co-partner">对接 Partner：{self._esc(c.get("partner",""))}</div>'
                f'<div class="co-focus">{self._esc(c.get("currentFocus",""))}</div>'
                f'<div class="co-milestone">下一节点：{self._esc(c.get("nextMilestone",""))}</div>'
                f'<div class="co-risks">{self._build_risk_items(c.get("risks",[]))}</div></div>'
            )
        company_cards = "".join(company_cards_parts)

        return {
            "META_TITLE":       meta.get("title", "投后管理周报"),
            "REPORT_TITLE":     meta.get("reportTitle", "投后管理周报"),
            "DATE_RANGE":       meta.get("dateRange", ""),
            "HOME_SUBTITLE":    d.get("summary", {}).get("subtitle", ""),
            "HOME_BANNER_HTML": d.get("summary", {}).get("bannerHtml", ""),
            "PORTFOLIO_CARDS":  portfolio_cards,
            "FUNDING_ROWS":     funding_rows,
            "COMPANY_CARDS":    company_cards,
            "RISK_ITEMS":       self._build_risk_items(d.get("risks", {}).get("all", [])),
            "PLAN_TABLE_ROWS":  self._build_plan_rows(d.get("plan", {}).get("rows", [])),
            "CHART_DATA_JSON":  json.dumps(d.get("charts", {}), ensure_ascii=False),
            "FOOTER_TEXT":      meta.get("footerText", "内部汇报"),
        }

    def _build_plan_rows(self, rows: list) -> str:
        lines = []
        for r in rows:
            pri = r.get("priority", "mid")
            pri_text = {"high": "高", "mid": "中", "low": "低"}.get(pri, "中")
            lines.append(
                f'<tr><td><strong>{self._esc(r.get("project",""))}</strong></td>'
                f'<td>{self._esc(r.get("task",""))}</td>'
                f'<td>{self._esc(r.get("milestone",""))}</td>'
                f'<td><span class="priority-badge {pri}">{pri_text}</span></td></tr>'
            )
        return "\n".join(lines)


# ─── pre-launch 渲染器 ────────────────────────────────────────────────────────

class PreLaunchRenderer(BaseShellRenderer):
    """
    研发期项目周报渲染器（pre-launch 类型）。
    无业务数据，以功能点完成率、阻塞项、模块开发进度为核心。
    """
    SHELL_FILE = "pre_launch.html"

    def required_fields(self):
        return ["meta", "summary", "northStar", "healthScore", "milestones", "modules", "risks"]

    def build_replacements(self) -> Dict[str, str]:
        d    = self.data
        meta = d["meta"]
        ns   = d["northStar"]
        health = d["healthScore"]
        extra  = d.get("extra", {})

        features = extra.get("features", [])
        feature_rows_parts = []
        for feat in features:
            fst = feat.get("status", "")
            feature_rows_parts.append(
                f'<tr><td>{self._esc(feat.get("module",""))}</td>'
                f'<td>{self._esc(feat.get("name",""))}</td>'
                f'<td><span class="status-tag {self._status_class(fst)}">'
                f'{self._esc(fst)}</span></td>'
                f'<td>{self._esc(feat.get("owner",""))}</td>'
                f'<td>{self._esc(feat.get("eta",""))}</td></tr>'
            )
        feature_rows = "".join(feature_rows_parts)

        # 研发过程指标
        dev_metrics = extra.get("devMetrics", [])
        dev_cards = "".join(
            f'<div class="dev-metric-card">'
            f'<div class="dm-label">{self._esc(m.get("label",""))}</div>'
            f'<div class="dm-value">{self._esc(str(m.get("value","")))}</div>'
            f'<div class="dm-trend">{self._esc(m.get("trendValue",""))}</div></div>'
            for m in dev_metrics
        )

        modules = d.get("modules", [])
        module_rows_parts = []
        for m in modules:
            mst = m.get("status", "")
            module_rows_parts.append(
                f'<div class="module-row">'
                f'<div class="mr-name">{self._esc(m.get("name",""))}</div>'
                f'<div class="mr-owner">{self._esc(m.get("owner",""))}</div>'
                f'<div class="mr-progress-wrap"><div class="mr-progress-fill" style="width:{m.get("progress",0)}%"></div>'
                f'<span class="mr-progress-text">{m.get("progress",0)}%</span></div>'
                f'<div class="mr-focus">{self._esc(m.get("currentFocus",""))}</div>'
                f'<div class="mr-status"><span class="status-tag {self._status_class(mst)}">'
                f'{self._esc(mst)}</span></div></div>'
            )
        module_rows = "".join(module_rows_parts)

        return {
            "META_TITLE":        meta.get("projectName", "研发周报"),
            "REPORT_TITLE":      meta.get("projectName", "研发期项目周报"),
            "DATE_RANGE":        meta.get("reportPeriod", ""),
            "HOME_SUBTITLE":     d.get("summary", {}).get("subtitle", ""),
            "HOME_BANNER_HTML":  d.get("summary", {}).get("bannerHtml", ""),
            "HOME_STAT_CARDS":   self._build_stat_cards(d.get("summary", {}).get("stats", [])),
            "OVERALL_PROGRESS":  str(ns.get("currentValue", 0)),
            "OVERALL_TARGET":    str(ns.get("targetValue", 100)),
            "OVERALL_INSIGHT":   ns.get("insight", ""),
            "HEALTH_SCORE":      str(health.get("overall", "")),
            "HEALTH_SUMMARY":    health.get("summary", ""),
            "HEALTH_DIMENSIONS": self._build_health_dimensions(health.get("dimensions", [])),
            "MILESTONE_CARDS":   self._build_timeline(d.get("milestones", [])),
            "MODULE_ROWS":       module_rows,
            "FEATURE_ROWS":      feature_rows,
            "DEV_METRIC_CARDS":  dev_cards,
            "RISK_ITEMS":        self._build_risk_items(d.get("risks", [])),
            "CHART_DATA_JSON":   json.dumps(d.get("charts", {}), ensure_ascii=False),
            "FOOTER_TEXT":       meta.get("footerText", "内部汇报"),
        }


# ─── ops 渲染器 ───────────────────────────────────────────────────────────────

class OpsRenderer(BaseShellRenderer):
    """
    运营团队周报渲染器（ops 类型）。
    关注活动效果、内容运营、用户运营指标。
    """
    SHELL_FILE = "ops.html"

    def required_fields(self):
        return ["meta", "summary", "northStar", "healthScore", "modules", "risks"]

    def build_replacements(self) -> Dict[str, str]:
        d    = self.data
        meta = d["meta"]
        extra = d.get("extra", {})

        # 活动列表
        activities = extra.get("activities", [])
        activity_cards_parts = []
        for a in activities:
            ast = a.get("status", "")
            metrics_html = "".join(
                "<span>" + self._esc(k) + ": <strong>" + self._esc(str(v)) + "</strong></span>"
                for k, v in a.get("metrics", {}).items()
            )
            activity_cards_parts.append(
                f'<div class="activity-card">'
                f'<div class="act-name">{self._esc(a.get("name",""))}</div>'
                f'<div class="act-period">{self._esc(a.get("period",""))}</div>'
                f'<div class="act-status"><span class="status-tag {self._status_class(ast)}">'
                f'{self._esc(ast)}</span></div>'
                f'<div class="act-metrics">{metrics_html}</div>'
                f'<div class="act-insight">{self._esc(a.get("insight",""))}</div></div>'
            )
        activity_cards = "".join(activity_cards_parts)
        # 内容运营
        content_items = extra.get("contentItems", [])
        content_rows = "".join(
            f'<tr><td>{self._esc(c.get("type",""))}</td>'
            f'<td>{self._esc(str(c.get("count","")))}</td>'
            f'<td>{self._esc(str(c.get("views","")))}</td>'
            f'<td>{self._esc(str(c.get("engagement","")))}</td>'
            f'<td>{self._esc(c.get("topContent",""))}</td></tr>'
            for c in content_items
        )

        modules = d.get("modules", [])

        return {
            "META_TITLE":        meta.get("projectName", "运营周报"),
            "REPORT_TITLE":      meta.get("projectName", "运营团队周报"),
            "DATE_RANGE":        meta.get("reportPeriod", ""),
            "HOME_SUBTITLE":     d.get("summary", {}).get("subtitle", ""),
            "HOME_BANNER_HTML":  d.get("summary", {}).get("bannerHtml", ""),
            "HOME_STAT_CARDS":   self._build_stat_cards(d.get("summary", {}).get("stats", [])),
            "KPI_CARDS":         self._build_kpi_cards(d.get("kpiMetrics", [])),
            "ACTIVITY_CARDS":    activity_cards,
            "CONTENT_ROWS":      content_rows,
            "MODULE_CARDS":      self._build_module_cards(modules),
            "RISK_ITEMS":        self._build_risk_items(d.get("risks", [])),
            "CHART_DATA_JSON":   json.dumps(d.get("charts", {}), ensure_ascii=False),
            "FOOTER_TEXT":       meta.get("footerText", "内部汇报"),
        }


# ─── 注册表 ────────────────────────────────────────────────────────────────────

REGISTRY: Dict[str, Dict[str, Any]] = {
    "platform": {
        "shell":    "multi_project.html",
        "renderer": MultiProjectRenderer,
        "schema":   "shell_schema.json",
        "desc":     "中台/基础设施，多项目并行，侧边栏导航",
        "aliases":  ["platform"],
    },
    "post-investment": {
        "shell":    "post_investment.html",
        "renderer": PostInvestmentRenderer,
        "schema":   "shell_schema.json",
        "desc":     "投后管理，被投企业组合跟踪",
        "aliases":  ["post-investment", "investment"],
    },
    "general": {
        "shell":    "general.html",
        "renderer": GeneralRenderer,
        "schema":   "shell_schema.json",
        "desc":     "通用产品团队，北极星+健康度+里程碑+模块",
        "aliases":  ["general", "default"],
    },
    "growth": {
        "shell":    "growth.html",
        "renderer": GrowthRenderer,
        "schema":   "shell_schema.json",
        "desc":     "增长团队，转化漏斗+渠道ROI+实验",
        "aliases":  ["growth", "growth-team"],
    },
    "pre-launch": {
        "shell":    "pre_launch.html",
        "renderer": PreLaunchRenderer,
        "schema":   "shell_schema.json",
        "desc":     "研发期，功能点完成率+阻塞项+模块进度",
        "aliases":  ["pre-launch", "dev", "research"],
    },
    "ops": {
        "shell":    "ops.html",
        "renderer": OpsRenderer,
        "schema":   "shell_schema.json",
        "desc":     "运营团队，活动效果+内容运营+用户运营",
        "aliases":  ["ops", "operations"],
    },
}

# 别名映射（方便 render.py 做模糊匹配）
ALIAS_MAP: Dict[str, str] = {}
for _type, _cfg in REGISTRY.items():
    for _alias in _cfg.get("aliases", []):
        ALIAS_MAP[_alias] = _type


def resolve_type(project_type: str) -> str:
    """将项目类型字符串（含别名）解析为注册表中的标准 key。"""
    t = project_type.lower().strip()
    if t in REGISTRY:
        return t
    if t in ALIAS_MAP:
        return ALIAS_MAP[t]
    raise ValueError(
        f"未知项目类型: '{project_type}'。"
        f"可用类型: {list(REGISTRY.keys())}。"
        f"可用别名: {list(ALIAS_MAP.keys())}"
    )


def get_renderer(project_type: str, data: dict) -> BaseShellRenderer:
    """根据项目类型获取对应渲染器实例。"""
    resolved = resolve_type(project_type)
    renderer_cls: Type[BaseShellRenderer] = REGISTRY[resolved]["renderer"]
    return renderer_cls(data)


def list_types() -> None:
    """打印所有注册的项目类型。"""
    print("\n已注册的 Shell 渲染器：\n")
    print(f"{'类型':<20} {'Shell 模板':<25} {'描述'}")
    print("-" * 80)
    for t, cfg in REGISTRY.items():
        shell_exists = (SHELLS_DIR / cfg["shell"]).exists()
        status = "✅" if shell_exists else "⚠️ 模板待创建"
        print(f"{t:<20} {cfg['shell']:<25} {cfg['desc']} {status}")
    print()

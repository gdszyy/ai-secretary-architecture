"""
weekly_diff.py — 周报数据差异分析器

功能：
  对比上周和本周的 data_schema.json，输出：
  1. 人类可读的变更摘要（给用户确认）
  2. Agent 微调指令（精简的 JSON patch 格式，只含变更字段）
  3. 结构性变更检测（新增/删除模块、里程碑状态变化等）

用法：
  python scripts/weekly_diff.py \\
      --prev state/weekly_data_2026-W16.json \\
      --curr templates/data_schema.json

  # 只看摘要（不输出完整 patch）
  python scripts/weekly_diff.py --prev ... --curr ... --summary-only

  # 输出机器可读的 patch JSON（供 Agent 直接使用）
  python scripts/weekly_diff.py --prev ... --curr ... --patch-only

参数：
  --prev          必填，上周数据 JSON 文件路径
  --curr          必填，本周数据 JSON 文件路径
  --summary-only  只输出人类可读摘要
  --patch-only    只输出 JSON patch（机器可读）
  --save-curr     将本周数据保存到 state/ 目录（供下周使用）
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).parent.parent
STATE_DIR = SKILL_ROOT / "state"


# ─── 差异计算 ─────────────────────────────────────────────────────────────────

def deep_diff(prev: Any, curr: Any, path: str = "") -> list[dict]:
    """
    递归对比两个 JSON 结构，返回变更列表。
    每条变更格式：{"path": "...", "op": "change|add|remove", "prev": ..., "curr": ...}
    """
    changes = []

    if type(prev) != type(curr):
        changes.append({"path": path, "op": "change", "prev": prev, "curr": curr})
        return changes

    if isinstance(prev, dict):
        all_keys = set(prev.keys()) | set(curr.keys())
        for k in sorted(all_keys):
            child_path = f"{path}.{k}" if path else k
            if k not in prev:
                changes.append({"path": child_path, "op": "add", "prev": None, "curr": curr[k]})
            elif k not in curr:
                changes.append({"path": child_path, "op": "remove", "prev": prev[k], "curr": None})
            else:
                changes.extend(deep_diff(prev[k], curr[k], child_path))

    elif isinstance(prev, list):
        # 列表对比：尝试按 id 字段匹配，否则按索引
        prev_by_id = {item.get("id"): item for item in prev if isinstance(item, dict) and "id" in item}
        curr_by_id = {item.get("id"): item for item in curr if isinstance(item, dict) and "id" in item}

        if prev_by_id and curr_by_id:
            # 按 id 匹配
            all_ids = set(prev_by_id.keys()) | set(curr_by_id.keys())
            for id_val in sorted(all_ids):
                child_path = f"{path}[id={id_val}]"
                if id_val not in prev_by_id:
                    changes.append({"path": child_path, "op": "add", "prev": None, "curr": curr_by_id[id_val]})
                elif id_val not in curr_by_id:
                    changes.append({"path": child_path, "op": "remove", "prev": prev_by_id[id_val], "curr": None})
                else:
                    changes.extend(deep_diff(prev_by_id[id_val], curr_by_id[id_val], child_path))
        else:
            # 按索引对比
            for i in range(max(len(prev), len(curr))):
                child_path = f"{path}[{i}]"
                if i >= len(prev):
                    changes.append({"path": child_path, "op": "add", "prev": None, "curr": curr[i]})
                elif i >= len(curr):
                    changes.append({"path": child_path, "op": "remove", "prev": prev[i], "curr": None})
                else:
                    changes.extend(deep_diff(prev[i], curr[i], child_path))

    else:
        # 基础类型
        if prev != curr:
            changes.append({"path": path, "op": "change", "prev": prev, "curr": curr})

    return changes


# ─── 变更分类 ─────────────────────────────────────────────────────────────────

FIELD_LABELS = {
    "meta.reportPeriod":       "报告周期",
    "meta.updatedAt":          "更新时间",
    "healthScore.overall":     "健康度总分",
    "healthScore.trend":       "健康度趋势",
    "healthScore.summary":     "健康度摘要",
    "northStar.currentValue":  "北极星指标当前值",
    "northStar.trendValue":    "北极星指标变化率",
    "northStar.achievementRate": "北极星达成率",
    "northStar.insight":       "北极星洞察",
}


def classify_changes(changes: list[dict]) -> dict:
    """将变更按类别分组，便于输出摘要。"""
    groups = {
        "meta":        [],   # 元信息变更
        "health":      [],   # 健康度变更
        "north_star":  [],   # 北极星变更
        "kpi":         [],   # KPI 变更
        "milestones":  [],   # 里程碑变更（含状态变化）
        "modules":     [],   # 模块变更
        "risks":       [],   # 风险变更
        "decisions":   [],   # 决策变更
        "todos":       [],   # 待办变更
        "structural":  [],   # 结构性变更（add/remove）
    }

    for c in changes:
        path = c["path"]
        op = c["op"]

        if op in ("add", "remove"):
            groups["structural"].append(c)

        if path.startswith("meta"):
            groups["meta"].append(c)
        elif path.startswith("healthScore"):
            groups["health"].append(c)
        elif path.startswith("northStar"):
            groups["north_star"].append(c)
        elif path.startswith("kpi"):
            groups["kpi"].append(c)
        elif path.startswith("milestones"):
            groups["milestones"].append(c)
        elif path.startswith("modules"):
            groups["modules"].append(c)
        elif path.startswith("risks"):
            groups["risks"].append(c)
        elif path.startswith("decisions"):
            groups["decisions"].append(c)
        elif path.startswith("todos"):
            groups["todos"].append(c)

    return groups


# ─── 输出格式化 ───────────────────────────────────────────────────────────────

def format_value(v: Any, max_len: int = 60) -> str:
    """格式化值用于展示。"""
    if v is None:
        return "(无)"
    s = json.dumps(v, ensure_ascii=False)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def build_summary(changes: list[dict], prev_data: dict, curr_data: dict) -> str:
    """生成人类可读的变更摘要。"""
    if not changes:
        return "✅ 本周数据与上周完全相同，无需任何修改。"

    groups = classify_changes(changes)
    lines = []

    prev_period = prev_data.get("meta", {}).get("reportPeriod", "上周")
    curr_period = curr_data.get("meta", {}).get("reportPeriod", "本周")
    lines.append(f"## 周报数据变更摘要：{prev_period} → {curr_period}")
    lines.append(f"共 **{len(changes)}** 处变更\n")

    # 结构性变更（最重要）
    if groups["structural"]:
        lines.append("### ⚠️ 结构性变更（新增/删除）")
        for c in groups["structural"]:
            op_label = "新增" if c["op"] == "add" else "删除"
            lines.append(f"- [{op_label}] `{c['path']}`")
        lines.append("")

    # 健康度
    health_changes = [c for c in groups["health"] if c["op"] == "change"]
    if health_changes:
        lines.append("### 📊 健康度变更")
        for c in health_changes:
            label = FIELD_LABELS.get(c["path"], c["path"])
            lines.append(f"- **{label}**：{format_value(c['prev'])} → {format_value(c['curr'])}")
        lines.append("")

    # 北极星
    ns_changes = [c for c in groups["north_star"] if c["op"] == "change"]
    if ns_changes:
        lines.append("### 🌟 北极星指标变更")
        for c in ns_changes:
            label = FIELD_LABELS.get(c["path"], c["path"])
            lines.append(f"- **{label}**：{format_value(c['prev'])} → {format_value(c['curr'])}")
        lines.append("")

    # 里程碑状态变化（特别标注）
    ms_status_changes = [c for c in groups["milestones"] if "status" in c["path"] and c["op"] == "change"]
    if ms_status_changes:
        lines.append("### 🏁 里程碑状态变化")
        for c in ms_status_changes:
            lines.append(f"- `{c['path']}`：`{c['prev']}` → `{c['curr']}`")
        lines.append("")

    # 模块变更
    module_changes = [c for c in groups["modules"] if c["op"] == "change"]
    if module_changes:
        lines.append("### 📦 业务模块变更")
        # 按模块 id 分组
        module_groups: dict[str, list] = {}
        for c in module_changes:
            # 提取 id=xxx 部分
            import re
            m = re.search(r"id=([^\]]+)", c["path"])
            mid = m.group(1) if m else "unknown"
            module_groups.setdefault(mid, []).append(c)
        for mid, mchanges in module_groups.items():
            lines.append(f"- **{mid}** 模块：{len(mchanges)} 处变更")
            for c in mchanges[:3]:  # 只展示前 3 条
                field = c["path"].split(".")[-1]
                lines.append(f"  - `{field}`：{format_value(c['prev'])} → {format_value(c['curr'])}")
            if len(mchanges) > 3:
                lines.append(f"  - ...（还有 {len(mchanges) - 3} 处）")
        lines.append("")

    # KPI 变更
    kpi_changes = [c for c in groups["kpi"] if c["op"] == "change"]
    if kpi_changes:
        lines.append("### 📈 KPI 指标变更")
        lines.append(f"共 {len(kpi_changes)} 处 KPI 数据更新（详见 patch）")
        lines.append("")

    # 风险/决策/待办
    other_count = len(groups["risks"]) + len(groups["decisions"]) + len(groups["todos"])
    if other_count > 0:
        lines.append("### 📋 其他变更")
        if groups["risks"]:
            lines.append(f"- 风险登记册：{len(groups['risks'])} 处变更")
        if groups["decisions"]:
            lines.append(f"- 决策事项：{len(groups['decisions'])} 处变更")
        if groups["todos"]:
            lines.append(f"- 待办事项：{len(groups['todos'])} 处变更")
        lines.append("")

    return "\n".join(lines)


def build_agent_instruction(changes: list[dict], curr_data: dict) -> str:
    """
    生成给 Agent 的最小微调指令。
    只包含变更字段，Agent 只需处理这些字段，不需要重新生成整个文件。
    """
    if not changes:
        return "# 无需微调：本周数据与上周相同\n运行 data_injector.py 直接生成周报即可。"

    period = curr_data.get("meta", {}).get("reportPeriod", "本周")
    lines = [
        f"# Agent 微调指令 — {period}",
        "",
        "## 操作步骤",
        "1. 运行 `python scripts/data_injector.py --data templates/data_schema.json` 生成基础周报",
        "2. 仅针对以下**结构性变更**做局部调整（数值变更已由注入器处理，无需 Agent 介入）",
        "",
    ]

    groups = classify_changes(changes)

    # 只有结构性变更才需要 Agent 介入
    structural = groups["structural"]
    if not structural:
        lines.append("## ✅ 无结构性变更")
        lines.append("所有变更均为数值/文本更新，`data_injector.py` 已自动处理。")
        lines.append("**无需 Agent 微调，直接使用生成的 tsx 文件即可。**")
        return "\n".join(lines)

    lines.append("## ⚠️ 需要 Agent 处理的结构性变更")
    lines.append("")

    for c in structural:
        op_label = "新增" if c["op"] == "add" else "删除"
        lines.append(f"### [{op_label}] `{c['path']}`")
        if c["op"] == "add":
            lines.append(f"新增了以下数据，请在对应 UI 区域添加渲染逻辑：")
            lines.append(f"```json\n{json.dumps(c['curr'], ensure_ascii=False, indent=2)}\n```")
        else:
            lines.append(f"该数据已删除，请移除对应的 UI 渲染逻辑（或保留但置为隐藏）。")
        lines.append("")

    lines.append("## 微调范围限制")
    lines.append("- 只修改上述结构性变更涉及的组件")
    lines.append("- 不要修改样式、布局、动效等 UI 代码")
    lines.append("- 不要重新生成整个文件")

    return "\n".join(lines)


# ─── CLI 入口 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="周报数据差异分析器")
    parser.add_argument("--prev",         required=True, help="上周数据 JSON 文件路径")
    parser.add_argument("--curr",         required=True, help="本周数据 JSON 文件路径")
    parser.add_argument("--summary-only", action="store_true", help="只输出人类可读摘要")
    parser.add_argument("--patch-only",   action="store_true", help="只输出 JSON patch")
    parser.add_argument("--save-curr",    action="store_true", help="将本周数据保存到 state/ 目录")
    args = parser.parse_args()

    # 加载数据
    for path_arg, label in [(args.prev, "上周"), (args.curr, "本周")]:
        if not os.path.exists(path_arg):
            print(f"❌ {label}数据文件不存在: {path_arg}", file=sys.stderr)
            sys.exit(1)

    with open(args.prev, "r", encoding="utf-8") as f:
        prev_data = json.load(f)
    with open(args.curr, "r", encoding="utf-8") as f:
        curr_data = json.load(f)

    # 去除注释字段
    for d in [prev_data, curr_data]:
        d.pop("_comment", None)
        d.pop("_usage", None)

    # 计算差异
    changes = deep_diff(prev_data, curr_data)

    # 输出
    if args.patch_only:
        print(json.dumps(changes, ensure_ascii=False, indent=2))
    elif args.summary_only:
        print(build_summary(changes, prev_data, curr_data))
    else:
        print(build_summary(changes, prev_data, curr_data))
        print("\n" + "─" * 60 + "\n")
        print(build_agent_instruction(changes, curr_data))

    # 保存本周数据到 state/
    if args.save_curr:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        period = curr_data.get("meta", {}).get("reportPeriod", "unknown").replace("/", "-")
        save_path = STATE_DIR / f"weekly_data_{period}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(curr_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 本周数据已保存至: {save_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

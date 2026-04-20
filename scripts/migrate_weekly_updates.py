#!/usr/bin/env python3
"""
migrate_weekly_updates.py
=========================
将 dashboard_data.json 中的 weekly_updates 字段从旧格式迁移到新格式：

旧格式：
  { "week": "2026-16", "update": "..." }

新格式：
  {
    "week": "2026-16",
    "start_date": "2026-04-14",
    "end_date": "2026-04-21",
    "update": "...",
    "sources": {
      "xp_weekly_report": null,
      "bitable_summary": null,
      "meegle_progress": null,
      "chat_insights": []
    }
  }

同时在顶层添加 weekly_periods 全局周期列表。

用法：
  python3 migrate_weekly_updates.py [--dry-run]
"""
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

REPO_ROOT = Path(__file__).parent.parent
DATA_FILE = REPO_ROOT / "data" / "dashboard_data.json"

TZ_UTC8 = timezone(timedelta(hours=8))


def week_str_to_dates(week_str: str) -> tuple[str, str]:
    """
    将 "YYYY-WW" 格式的周标识转换为该周的 start_date（周二）和 end_date（下周二）。
    ISO 周从周一开始，这里将周二作为周期起点。
    """
    year, week_num = int(week_str.split("-")[0]), int(week_str.split("-")[1])
    # ISO 周一 = isoweekday 1，周二 = isoweekday 2
    monday = datetime.fromisocalendar(year, week_num, 1)
    tuesday_start = monday + timedelta(days=1)   # 本周二（周期开始）
    tuesday_end = tuesday_start + timedelta(days=7)  # 下周二（周期结束）
    return tuesday_start.strftime("%Y-%m-%d"), tuesday_end.strftime("%Y-%m-%d")


def make_label(week_str: str, start_date: str, end_date: str) -> str:
    """生成展示用标签，如 'W16 (4/14 - 4/21)'"""
    week_num = week_str.split("-")[1]
    s = datetime.strptime(start_date, "%Y-%m-%d")
    e = datetime.strptime(end_date, "%Y-%m-%d")
    return f"W{week_num} ({s.month}/{s.day} - {e.month}/{e.day})"


def get_current_week_str() -> str:
    """获取当前周的 YYYY-WW 标识"""
    now = datetime.now(TZ_UTC8)
    iso = now.isocalendar()
    return f"{iso[0]}-{iso[1]:02d}"


def migrate(dry_run: bool = False):
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    current_week = get_current_week_str()
    all_weeks: set[str] = set()

    # 迁移每个模块的 weekly_updates
    for module in data.get("modules", []):
        new_updates = []
        for wu in module.get("weekly_updates", []):
            week = wu.get("week", "")
            if not week:
                continue
            all_weeks.add(week)

            # 如果已经是新格式（有 start_date），跳过
            if "start_date" in wu:
                new_updates.append(wu)
                continue

            start_date, end_date = week_str_to_dates(week)
            new_wu = {
                "week": week,
                "start_date": start_date,
                "end_date": end_date,
                "update": wu.get("update", ""),
                "sources": {
                    "xp_weekly_report": None,
                    "bitable_summary": None,
                    "meegle_progress": None,
                    "chat_insights": []
                }
            }
            new_updates.append(new_wu)

        module["weekly_updates"] = new_updates

    # 构建全局 weekly_periods（倒序排列）
    sorted_weeks = sorted(all_weeks, reverse=True)
    weekly_periods = []
    for week in sorted_weeks:
        start_date, end_date = week_str_to_dates(week)
        weekly_periods.append({
            "week": week,
            "start_date": start_date,
            "end_date": end_date,
            "label": make_label(week, start_date, end_date),
            "is_current": (week == current_week)
        })

    data["weekly_periods"] = weekly_periods

    if dry_run:
        print("[DRY RUN] 迁移结果预览（不写入文件）：")
        print(f"  当前周: {current_week}")
        print(f"  发现的周列表: {sorted_weeks}")
        print(f"  weekly_periods: {json.dumps(weekly_periods, ensure_ascii=False, indent=2)}")
        # 打印第一个模块的第一条 weekly_update 作为示例
        if data["modules"] and data["modules"][0]["weekly_updates"]:
            print(f"  示例 weekly_update: {json.dumps(data['modules'][0]['weekly_updates'][0], ensure_ascii=False, indent=2)}")
    else:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 迁移完成：{len(sorted_weeks)} 个周期，{sum(len(m['weekly_updates']) for m in data['modules'])} 条周报记录已更新。")
        print(f"   weekly_periods 已写入顶层，当前周: {current_week}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="迁移 weekly_updates 到新数据结构")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入文件")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)

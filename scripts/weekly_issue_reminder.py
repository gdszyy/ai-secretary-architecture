"""
weekly_issue_reminder.py
========================
当周问题当周解决 — 周四集中提醒脚本

功能：
  1. 扫描 Bitable 话题表中本周新增的 risk_blocker（风险/阻塞）话题。
  2. 汇总未解决的风险项，生成结构化清单。
  3. 调用 lark-secretary 技能，在飞书群发送富文本卡片提醒。
  4. 在卡片底部附带"信息纠正入口"说明，引导 VoidZ 补充或纠正 AI 提取的信息。

触发时机：
  - 每周四 15:00（通过 Manus 定时任务触发）

用法：
  python3 weekly_issue_reminder.py              # 正式运行
  python3 weekly_issue_reminder.py --dry-run    # 预览模式，打印卡片内容但不发送
  python3 weekly_issue_reminder.py --week 2026-17  # 指定周（用于测试）
  python3 weekly_issue_reminder.py --all-intents   # 包含 major_decision/milestone_fact

设计原则：
  - 只提醒当周的 risk_blocker，不追问历史遗留问题。
  - 提醒频率：每周仅一次（周四），不在日常群聊中重复打扰。
  - 信息纠正入口：卡片底部明确告知 VoidZ 如何补充/纠正 AI 提取的信息。
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import time
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("weekly_issue_reminder")

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------
APP_ID     = os.environ.get("LARK_APP_ID",     "cli_a9d985cd40f89e1a")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "UNemS0zPnUuXhONgkuuprgdK3SrVx05T")
BASE_ID    = os.environ.get("BITABLE_BASE_ID", "CyDxbUQGGa3N2NsVanMjqdjxp6e")
TABLE_ID   = os.environ.get("BITABLE_TABLE_ID","tblKscoaGp6VwhQe")

TZ_UTC8 = timezone(timedelta(hours=8))

SKILLS_DIR   = Path("/home/ubuntu/skills")
LARK_CARD    = SKILLS_DIR / "lark-secretary" / "scripts" / "send_card.py"

# 模块名称映射（用于展示）
MODULE_LABELS = {
    "mod_data_ingestion":      "数据接入",
    "mod_ls_ts_matching":      "Lsport 赛事匹配",
    "mod_sr_ts_matching":      "SR 赛事匹配",
    "mod_sports_betting_core": "体育投注核心",
    "mod_casino":              "Casino",
    "mod_activity_platform":   "活动平台",
    "mod_ads_system":          "广告投放",
    "mod_uiux_design":         "UI/UX 设计",
    "mod_user_system":         "用户系统",
    "mod_wallet_finance":      "钱包与财务",
    "mod_platform_setting":    "平台配置",
    "mod_im_cs":               "IM 客服",
    "数据源":                  "数据源",
    "体育博彩核心":             "体育投注核心",
    "活动平台":                 "活动平台",
    "活动管理":                 "活动管理",
    "游戏模块":                 "Casino",
    "游戏（Casino）":           "Casino",
    "运营":                    "运营",
    "风控":                    "风控",
    "后台管理":                 "后台管理",
    "支付系统":                 "支付系统",
    "标签系统":                 "标签系统",
    "运营监控":                 "运营监控",
    "运营活动平台":             "运营活动平台",
}

INTENT_LABELS = {
    "major_decision": "🔵 重大决策",
    "milestone_fact": "🟢 里程碑",
    "risk_blocker":   "🔴 风险/阻塞",
}


# ---------------------------------------------------------------------------
# Lark API 工具
# ---------------------------------------------------------------------------

def get_token() -> str:
    r = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["tenant_access_token"]


def fetch_all_records(token: str) -> list[dict]:
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}
    records, page_token = [], None
    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Bitable API 错误: {data}")
        records.extend(data["data"].get("items", []))
        if not data["data"].get("has_more"):
            break
        page_token = data["data"].get("page_token")
        time.sleep(0.3)
    return records


# ---------------------------------------------------------------------------
# 周期工具
# ---------------------------------------------------------------------------

def get_current_week_str(override: Optional[str] = None) -> str:
    if override:
        return override
    now = datetime.now(TZ_UTC8)
    iso = now.isocalendar()
    return f"{iso[0]}-{iso[1]:02d}"


def parse_period_to_week(period_str: str) -> Optional[str]:
    import re
    if not period_str:
        return None
    m = re.search(r"(\d{4})-W?(\d{1,2})", period_str)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    m = re.search(r"\((\d{1,2})/(\d{1,2})~", period_str)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = datetime.now(TZ_UTC8).year
        try:
            dt = datetime(year, month, day)
            iso = dt.isocalendar()
            return f"{iso[0]}-{iso[1]:02d}"
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# 核心逻辑：提取当周未解决风险项
# ---------------------------------------------------------------------------

def fetch_current_week_issues(
    current_week: str,
    include_intents: set,
) -> list[dict]:
    """
    提取当周指定意图类型的未解决话题。
    """
    token = get_token()
    records = fetch_all_records(token)
    logger.info("共获取 %d 条记录，筛选当周（%s）话题", len(records), current_week)

    issues = []
    terminal = {"已归档(跨周)", "已解决", "已忽略"}

    for rec in records:
        fields = rec.get("fields", {})
        intent = fields.get("意图类型", "")
        status = fields.get("状态", "")
        period = fields.get("来源周期", "")

        if intent not in include_intents:
            continue
        if status in terminal:
            continue

        source_week = parse_period_to_week(period)
        if source_week != current_week:
            continue

        issues.append({
            "title":   fields.get("话题标题", "（无标题）"),
            "summary": fields.get("话题摘要", ""),
            "module":  fields.get("所属模块", "unknown"),
            "group":   fields.get("群组名称", ""),
            "intent":  intent,
            "status":  status,
        })

    logger.info("当周未解决话题：%d 条", len(issues))
    return issues


# ---------------------------------------------------------------------------
# 生成卡片内容
# ---------------------------------------------------------------------------

def build_card_body(
    issues: list[dict],
    current_week: str,
    today_str: str,
) -> str:
    """
    生成飞书卡片的 Markdown 正文。
    """
    if not issues:
        return (
            f"✅ **本周（{current_week}）暂无未解决的风险/阻塞项**，进展顺利！\n\n"
            f"如有遗漏，请直接回复此卡片补充。"
        )

    lines = [
        f"以下 **{len(issues)} 项**风险/阻塞尚未闭环，请相关负责人确认进度，争取**本周内解决**：\n",
    ]

    # 按模块分组
    from collections import defaultdict
    by_module = defaultdict(list)
    for issue in issues:
        mod = MODULE_LABELS.get(issue["module"], issue["module"])
        by_module[mod].append(issue)

    for mod, items in sorted(by_module.items()):
        lines.append(f"**【{mod}】**")
        for item in items:
            intent_label = INTENT_LABELS.get(item["intent"], item["intent"])
            lines.append(f"- {intent_label} **{item['title']}**")
            if item.get("summary"):
                # 摘要截取前 60 字
                summary = item["summary"][:60].replace("\n", " ")
                if len(item["summary"]) > 60:
                    summary += "…"
                lines.append(f"  > {summary}")
        lines.append("")

    # 信息纠正入口
    lines.append("---")
    lines.append("**📝 信息纠正 / 补充入口**")
    lines.append(
        "如果 AI 提取的信息有偏差，或有群外决策未被记录，"
        "请直接回复本卡片，格式：\n"
        "> `纠正：[话题名] 实际情况是……`\n"
        "> `补充：[新话题] 决策/进展是……`\n\n"
        "AI 秘书将在下次运行时读取并更新记录。"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 发送飞书卡片
# ---------------------------------------------------------------------------

def send_reminder(
    issues: list[dict],
    current_week: str,
    dry_run: bool = False,
) -> bool:
    today_str = datetime.now(TZ_UTC8).strftime("%m/%d")
    title = f"🚨 {current_week} 本周遗留风险项集中提醒（{today_str} 周四）"
    body  = build_card_body(issues, current_week, today_str)

    if dry_run:
        print("\n" + "="*60)
        print(f"[DRY RUN] 卡片标题：{title}")
        print("-"*60)
        print(body)
        print("="*60 + "\n")
        return True

    if not LARK_CARD.exists():
        logger.error("lark-secretary 脚本不存在: %s", LARK_CARD)
        return False

    color = "red" if issues else "green"
    result = subprocess.run(
        [
            sys.executable, str(LARK_CARD),
            "--title", title,
            "--body",  body,
            "--color", color,
        ],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        logger.info("飞书提醒发送成功")
        return True
    else:
        logger.error("飞书提醒发送失败: %s", result.stderr)
        return False


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="周四集中提醒脚本 — 当周风险/阻塞项汇总播报"
    )
    parser.add_argument("--dry-run",     action="store_true", help="预览模式，不发送飞书消息")
    parser.add_argument("--week",        type=str, default=None, help="指定周（YYYY-WW），默认当前周")
    parser.add_argument("--all-intents", action="store_true",
                        help="包含 major_decision / milestone_fact（默认仅 risk_blocker）")
    args = parser.parse_args()

    current_week = get_current_week_str(args.week)

    include_intents = {"risk_blocker"}
    if args.all_intents:
        include_intents |= {"major_decision", "milestone_fact"}

    issues = fetch_current_week_issues(current_week, include_intents)
    ok = send_reminder(issues, current_week, dry_run=args.dry_run)

    if ok:
        print(f"✅ 提醒发送成功，共 {len(issues)} 条风险项")
    else:
        print("❌ 提醒发送失败")
        sys.exit(1)


if __name__ == "__main__":
    main()

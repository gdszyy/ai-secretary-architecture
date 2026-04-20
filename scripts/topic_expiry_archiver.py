"""
topic_expiry_archiver.py
========================
当周问题当周解决 — 话题过期自动归档脚本

功能：
  1. 扫描 Bitable 话题表中所有高价值话题（major_decision / milestone_fact / risk_blocker）。
  2. 将来源周期早于当前周的记录状态更新为"已归档(跨周)"。
  3. 在追问回复字段追加备注，说明归档原因。

触发时机：
  - 每周一 02:00（通过 Manus 定时任务触发）
  - 也可在周报生成前手动触发

用法：
  python3 topic_expiry_archiver.py              # 正式运行
  python3 topic_expiry_archiver.py --dry-run    # 预览模式，不写入
  python3 topic_expiry_archiver.py --week 2026-17  # 指定"当前周"（用于测试）

设计原则：
  - 跨周的 risk_blocker / milestone_fact / major_decision 默认视为已解决或已失效。
  - routine_task 本就不追踪，无需归档。
  - 已归档/已解决/已忽略的记录不重复处理。
"""

import os
import sys
import json
import logging
import argparse
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("topic_expiry_archiver")

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------
APP_ID     = os.environ.get("LARK_APP_ID",     "cli_a9d985cd40f89e1a")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "UNemS0zPnUuXhONgkuuprgdK3SrVx05T")
BASE_ID    = os.environ.get("BITABLE_BASE_ID", "CyDxbUQGGa3N2NsVanMjqdjxp6e")
TABLE_ID   = os.environ.get("BITABLE_TABLE_ID","tblKscoaGp6VwhQe")

TZ_UTC8 = timezone(timedelta(hours=8))

# 需要参与过期归档的意图类型（高价值话题）
ARCHIVABLE_INTENTS = {"major_decision", "milestone_fact", "risk_blocker"}

# 不需要重复处理的终态状态
TERMINAL_STATUSES = {"已归档(跨周)", "已解决", "已忽略"}


# ---------------------------------------------------------------------------
# Lark API 工具
# ---------------------------------------------------------------------------

def get_token() -> str:
    """获取飞书 tenant_access_token"""
    r = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["tenant_access_token"]


def fetch_all_records(token: str) -> list[dict]:
    """获取 Bitable 话题表全量记录"""
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
        items = data["data"].get("items", [])
        records.extend(items)
        if not data["data"].get("has_more"):
            break
        page_token = data["data"].get("page_token")
        time.sleep(0.3)

    return records


def update_record(token: str, record_id: str, fields: dict) -> bool:
    """更新单条 Bitable 记录"""
    url = (
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}"
        f"/tables/{TABLE_ID}/records/{record_id}"
    )
    r = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"fields": fields},
        timeout=10,
    )
    r.raise_for_status()
    resp = r.json()
    return resp.get("code") == 0


# ---------------------------------------------------------------------------
# 周期解析工具
# ---------------------------------------------------------------------------

def get_current_week_str(override: Optional[str] = None) -> str:
    """获取当前周的 YYYY-WW 标识（可通过 override 指定）"""
    if override:
        return override
    now = datetime.now(TZ_UTC8)
    iso = now.isocalendar()
    return f"{iso[0]}-{iso[1]:02d}"


def parse_period_to_week(period_str: str) -> Optional[str]:
    """
    将 Bitable 中的"来源周期"字段解析为 YYYY-WW 格式。

    支持格式：
      - "第1周 (03/17~03/24)"  → 从日期推算 ISO 周
      - "2026-W16"             → 直接返回
      - "2026-16"              → 直接返回
    """
    if not period_str:
        return None

    # 格式 "2026-W16" 或 "2026-16"
    import re
    m = re.search(r"(\d{4})-W?(\d{1,2})", period_str)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"

    # 格式 "第N周 (MM/DD~MM/DD)" — 取起始日期推算 ISO 周
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


def week_is_before(week_a: str, week_b: str) -> bool:
    """判断 week_a 是否严格早于 week_b（格式均为 YYYY-WW）"""
    try:
        ya, wa = int(week_a.split("-")[0]), int(week_a.split("-")[1])
        yb, wb = int(week_b.split("-")[0]), int(week_b.split("-")[1])
        return (ya, wa) < (yb, wb)
    except (ValueError, IndexError):
        return False


# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def archive_expired_topics(
    current_week: str,
    dry_run: bool = False,
) -> dict:
    """
    扫描并归档所有跨周的高价值话题。

    Args:
        current_week: 当前周标识（YYYY-WW），早于此周的记录将被归档。
        dry_run: 若为 True，只打印不写入。

    Returns:
        统计字典：{"scanned": N, "archived": M, "skipped": K}
    """
    logger.info("开始话题过期归档，当前周=%s，dry_run=%s", current_week, dry_run)

    token = get_token()
    records = fetch_all_records(token)
    logger.info("共获取 %d 条记录", len(records))

    stats = {"scanned": len(records), "archived": 0, "skipped": 0, "errors": 0}
    archived_titles = []

    for rec in records:
        fields = rec.get("fields", {})
        record_id = rec["record_id"]

        intent = fields.get("意图类型", "")
        status = fields.get("状态", "")
        period = fields.get("来源周期", "")
        title  = fields.get("话题标题", "")

        # 只处理高价值意图
        if intent not in ARCHIVABLE_INTENTS:
            stats["skipped"] += 1
            continue

        # 跳过已终态的记录
        if status in TERMINAL_STATUSES:
            stats["skipped"] += 1
            continue

        # 解析来源周期
        source_week = parse_period_to_week(period)
        if not source_week:
            logger.debug("无法解析周期 '%s'，跳过记录: %s", period, title)
            stats["skipped"] += 1
            continue

        # 判断是否跨周
        if not week_is_before(source_week, current_week):
            stats["skipped"] += 1
            continue

        # 执行归档
        logger.info("  归档: [%s] %s（来源周=%s）", intent, title, source_week)
        archived_titles.append(f"[{intent}] {title}")

        if not dry_run:
            existing_reply = fields.get("追问回复") or ""
            new_reply = (
                existing_reply
                + f"\n[系统自动归档 {datetime.now(TZ_UTC8).strftime('%Y-%m-%d')}] "
                  f"跨周（来源：{period}，当前：{current_week}），默认视为已解决/失效。"
            ).strip()

            ok = update_record(token, record_id, {
                "状态": "已归档(跨周)",
                "追问回复": new_reply,
            })
            if ok:
                stats["archived"] += 1
            else:
                logger.warning("  更新失败: %s", title)
                stats["errors"] += 1
            time.sleep(0.2)  # 避免 API 限速
        else:
            stats["archived"] += 1

    logger.info(
        "归档完成 | 扫描=%d 归档=%d 跳过=%d 错误=%d",
        stats["scanned"], stats["archived"], stats["skipped"], stats["errors"],
    )
    if archived_titles:
        logger.info("归档列表：\n  " + "\n  ".join(archived_titles))

    return stats


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="话题过期自动归档脚本 — 跨周高价值话题默认视为已解决"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式，不写入 Bitable",
    )
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        help="指定当前周（格式 YYYY-WW），用于测试，默认为系统当前周",
    )
    args = parser.parse_args()

    current_week = get_current_week_str(args.week)
    stats = archive_expired_topics(current_week=current_week, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n[DRY RUN] 将归档 {stats['archived']} 条跨周话题（未实际写入）")
    else:
        print(f"\n✅ 归档完成：{stats['archived']} 条话题已更新为"已归档(跨周)"")

    sys.exit(0 if stats["errors"] == 0 else 1)


if __name__ == "__main__":
    main()

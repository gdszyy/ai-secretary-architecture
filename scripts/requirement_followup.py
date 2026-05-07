"""
requirement_followup.py
=======================
每日定时跟进任务：扫描需求池中所有「未确认 / 不完善」的需求，向提出者发起私聊
追问。可由 Manus / Railway Cron / GitHub Actions 等调度器每天触发一次。

执行流程：
  1. 从需求池表读取所有处于 草稿 / 待澄清 / 待确认 状态的记录
  2. 跳过当天已经跟进过的记录（避免每次启动重复打扰）
  3. 按提出者 open_id 聚合、生成提醒文案，私聊发送
  4. 更新 Bitable：跟进次数 +1，最后跟进时间为当前

CLI 用法：
  python scripts/requirement_followup.py            # 正常执行
  python scripts/requirement_followup.py --dry-run  # 仅打印不发消息

环境变量：
  BITABLE_BASE_ID, BITABLE_TABLE_REQUIREMENTS  需求池表
  LARK_APP_ID / LARK_APP_SECRET                飞书凭证
  REQUIREMENT_FOLLOWUP_MIN_HOURS               两次跟进最小间隔小时数（默认 20）
  REQUIREMENT_FOLLOWUP_MAX_PER_RUN             单次最多跟进多少条（默认 50）
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

# 让脚本独立运行时也能 import 同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lark_bitable_client import LarkBitableClient  # type: ignore
import lark_sdk_client as sdk  # type: ignore
import requirement_tracker as rt  # type: ignore

logger = logging.getLogger("ai_secretary.requirement_followup")


def _parse_dt(value: str) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _build_followup_message(
    requirement_id: str,
    title: str,
    completeness: int,
    missing: List[str],
    follow_up_count: int,
) -> str:
    if missing:
        missing_text = "、".join(missing[:3])
        body = (
            f"👋 跟进一下昨天聊到的需求 [{requirement_id}]：\n"
            f"标题：{title or '（暂未命名）'}\n"
            f"当前完善度：{completeness}/100，还差 {missing_text}。\n\n"
            "可以直接回我补充，或者回「取消」放弃这条。"
        )
    else:
        body = (
            f"👋 需求 [{requirement_id}] 「{title or '未命名'}」已经填齐了，\n"
            "回复「确认」即可入库；如果想继续修改，直接发新内容给我即可。"
        )
    if follow_up_count >= 3:
        body += f"\n\n（这是第 {follow_up_count + 1} 次跟进，如果暂时不打算推进，回「取消」我就不再打扰）"
    return body


def run(dry_run: bool = False) -> Dict[str, int]:
    """主入口。返回 {扫描数, 跟进数, 跳过数, 异常数}。"""
    base_id, table_id = rt._bitable_config()
    client = LarkBitableClient()
    records = client.list_records(base_id, table_id)

    min_hours = int(os.environ.get("REQUIREMENT_FOLLOWUP_MIN_HOURS", "20"))
    max_per_run = int(os.environ.get("REQUIREMENT_FOLLOWUP_MAX_PER_RUN", "50"))
    now = datetime.now(timezone.utc)

    scanned = 0
    sent = 0
    skipped = 0
    errors = 0

    for rec in records:
        scanned += 1
        if sent >= max_per_run:
            break

        fields = rec.get("fields") or {}
        status = rt._flatten_text(fields.get("状态"))
        if status not in rt.ACTIVE_STATUSES:
            continue

        last_followup = _parse_dt(rt._flatten_text(fields.get("最后跟进时间")))
        if last_followup and (now - last_followup) < timedelta(hours=min_hours):
            skipped += 1
            continue

        sender_open_id = rt._flatten_text(fields.get("提出者open_id"))
        if not sender_open_id:
            skipped += 1
            continue

        try:
            completeness = int(rt._flatten_text(fields.get("完善度")) or "0")
        except ValueError:
            completeness = 0
        missing_text = rt._flatten_text(fields.get("缺失字段"))
        missing = [s.strip() for s in missing_text.split(",") if s.strip()]
        title = rt._flatten_text(fields.get("标题"))
        req_id = rt._flatten_text(fields.get("需求ID"))
        try:
            follow_up_count = int(rt._flatten_text(fields.get("跟进次数")) or "0")
        except ValueError:
            follow_up_count = 0

        msg = _build_followup_message(
            requirement_id=req_id,
            title=title,
            completeness=completeness,
            missing=missing,
            follow_up_count=follow_up_count,
        )

        if dry_run:
            logger.info("[DRY] 将向 %s 发送：%s", sender_open_id, msg.replace("\n", " | "))
            sent += 1
            continue

        ok = sdk.send_text(sender_open_id, msg, receive_id_type="open_id")
        if not ok:
            errors += 1
            continue

        sent += 1
        try:
            client.update_record(base_id, table_id, rec.get("record_id", ""), {
                "跟进次数": follow_up_count + 1,
                "最后跟进时间": rt._now_iso(),
            })
        except Exception as e:
            logger.warning("更新跟进记录失败 req=%s: %s", req_id, e)

    summary = {"scanned": scanned, "sent": sent, "skipped": skipped, "errors": errors}
    logger.info("跟进任务完成: %s", summary)
    return summary


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="需求池每日跟进")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不发送私聊")
    args = parser.parse_args()
    summary = run(dry_run=args.dry_run)
    print("Summary:", summary)


if __name__ == "__main__":
    main()

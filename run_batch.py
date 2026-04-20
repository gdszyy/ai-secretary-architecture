"""
run_batch.py
============
AI 秘书系统 —— 每日跑批主入口

执行顺序：
  Step 1. 项目进度更新（daily_progress_updater）
          拉取各群组最近 26 小时的新消息，用 LLM 提取各模块进展，
          写入 data/dashboard_data.json 的 weekly_updates 字段，
          并将新话题写入 Bitable 话题表。

  Step 2. 话题追踪（topic_reply_tracker）
          扫描 Bitable 中已发出追问但尚未收到回复的话题，
          拉取追问消息的回复，用 LLM 判断是否有结论，
          有结论则更新「追问回复」和「状态」字段。

  Step 3. 话题收尾（stale_topic_followup）
          扫描来源周期结束日超过 7 天的未闭环话题，
          在对应群组中 @VoidZ 发送带背景摘要的追问消息，
          并将追问消息 ID 写回 Bitable（供 Step 2 下次追踪）。

用法：
  python3 run_batch.py                    # 正式跑批
  python3 run_batch.py --dry-run          # 预览模式（不发消息、不写文件）
  python3 run_batch.py --stale-threshold 7  # 自定义过期阈值（天）
  python3 run_batch.py --hours 48         # 拉取最近 48 小时消息
  python3 run_batch.py --force            # 强制重发所有过期话题

环境变量（可选）：
  LARK_APP_ID, LARK_APP_SECRET  飞书应用凭证
  STALE_THRESHOLD_DAYS          话题过期阈值（天），默认 7
  DRY_RUN                       设为 "true" 启用预览模式
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime, timezone

# 将 scripts 目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_batch")

# ---------------------------------------------------------------------------
# 步骤定义
# ---------------------------------------------------------------------------

def step_daily_progress_update(hours: int, dry_run: bool) -> dict:
    """
    Step 1: 项目进度更新
    拉取群消息 → LLM 提取进展 → 写入看板 + Bitable 话题表
    """
    logger.info("=" * 60)
    logger.info("Step 1: 项目进度更新 (hours=%d)", hours)
    logger.info("=" * 60)
    try:
        from daily_progress_updater import run as progress_run
        summary = progress_run(hours=hours, dry_run=dry_run)
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error("项目进度更新失败: %s", str(e), exc_info=True)
        return {"status": "failed", "error": str(e)}


def step_topic_reply_tracking(dry_run: bool) -> dict:
    """
    Step 2: 话题追踪
    扫描已追问话题的回复 → LLM 判断结论 → 更新 Bitable 状态
    """
    logger.info("=" * 60)
    logger.info("Step 2: 话题追踪（回复扫描）")
    logger.info("=" * 60)
    try:
        from topic_reply_tracker import run as tracker_run
        summary = tracker_run(dry_run=dry_run)
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error("话题追踪失败: %s", str(e), exc_info=True)
        return {"status": "failed", "error": str(e)}


def step_stale_topic_followup(threshold_days: int, dry_run: bool, force: bool) -> dict:
    """
    Step 3: 话题收尾跟进
    扫描过期话题 → @VoidZ 发追问消息 → 写追问消息ID 到 Bitable
    """
    logger.info("=" * 60)
    logger.info("Step 3: 话题收尾跟进 (threshold=%d天)", threshold_days)
    logger.info("=" * 60)
    try:
        from stale_topic_followup import run as followup_run
        summary = followup_run(
            threshold_days=threshold_days,
            dry_run=dry_run,
            force=force,
        )
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error("话题收尾跟进失败: %s", str(e), exc_info=True)
        return {"status": "failed", "error": str(e)}


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_all(
    stale_threshold: int = 7,
    hours: int = 26,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    start_time = datetime.now(timezone.utc)
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║           AI 秘书系统 每日跑批 开始                     ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("时间: %s", start_time.strftime("%Y-%m-%d %H:%M:%S UTC"))
    logger.info("参数: dry_run=%s, stale_threshold=%d天, hours=%d, force=%s",
                dry_run, stale_threshold, hours, force)

    results = {}

    # ── Step 1: 项目进度更新 ─────────────────────────────────────────────
    results["step1_progress"] = step_daily_progress_update(hours=hours, dry_run=dry_run)

    # ── Step 2: 话题追踪 ─────────────────────────────────────────────────
    results["step2_tracking"] = step_topic_reply_tracking(dry_run=dry_run)

    # ── Step 3: 话题收尾 ─────────────────────────────────────────────────
    results["step3_followup"] = step_stale_topic_followup(
        threshold_days=stale_threshold,
        dry_run=dry_run,
        force=force,
    )

    # ── 汇总输出 ─────────────────────────────────────────────────────────
    end_time = datetime.now(timezone.utc)
    elapsed = (end_time - start_time).total_seconds()

    logger.info("")
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║           AI 秘书系统 每日跑批 完成                     ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("耗时: %.1f 秒", elapsed)

    for step_name, result in results.items():
        status = result.get("status", "unknown")
        icon = "✅" if status == "success" else "❌"
        logger.info("%s %s: %s", icon, step_name, status)

        if status == "success":
            s = result.get("summary", {})
            if "total_messages" in s:
                logger.info(
                    "   消息=%d, 有更新群=%d, 更新模块=%d, 新话题=%d",
                    s.get("total_messages", 0),
                    s.get("groups_with_updates", 0),
                    s.get("updated_modules", 0),
                    s.get("new_topics", 0),
                )
            elif "total" in s:
                logger.info(
                    "   总计=%d, 有结论=%d, 无回复=%d",
                    s.get("total", 0),
                    s.get("concluded", 0),
                    s.get("no_reply", 0),
                )
            elif "total_stale" in s:
                logger.info(
                    "   过期话题=%d, 发送=%d, 失败=%d",
                    s.get("total_stale", 0),
                    s.get("sent_count", 0),
                    s.get("failed_count", 0),
                )
        elif status == "failed":
            logger.error("   错误: %s", result.get("error", ""))


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AI 秘书系统每日跑批主入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
步骤说明：
  Step 1  项目进度更新：拉取群消息 → LLM提取 → 写入看板 + Bitable话题表
  Step 2  话题追踪：扫描已追问话题的回复 → 判断结论 → 更新Bitable状态
  Step 3  话题收尾：过期话题 @VoidZ 追问 → 写追问消息ID到Bitable

示例：
  python3 run_batch.py                      # 正式跑批
  python3 run_batch.py --dry-run            # 预览模式
  python3 run_batch.py --stale-threshold 7  # 7天阈值
  python3 run_batch.py --hours 48           # 拉取48小时消息
  python3 run_batch.py --force              # 强制重发追问
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("DRY_RUN", "false").lower() == "true",
        help="预览模式，不实际发送消息或写入文件",
    )
    parser.add_argument(
        "--stale-threshold",
        type=int,
        default=int(os.environ.get("STALE_THRESHOLD_DAYS", "7")),
        help="话题过期阈值（天），默认 7",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=26,
        help="拉取最近 N 小时的群消息，默认 26",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重发追问，忽略已发送记录",
    )
    args = parser.parse_args()

    run_all(
        stale_threshold=args.stale_threshold,
        hours=args.hours,
        dry_run=args.dry_run,
        force=args.force,
    )


if __name__ == "__main__":
    main()

"""
run_batch.py
============
AI 秘书系统 —— 跑批主入口

功能：
  按顺序执行以下批处理步骤：
    Step 1. 话题收尾跟进（stale_topic_followup）
            扫描飞书多维表格中超过阈值天数的未闭环话题，
            在对应群组中 @VoidZ 发送带上下文的追问消息。

  （后续步骤可在此扩展，例如：
    Step 2. 群消息拉取与话题拆解（lark-group-monitor）
    Step 3. 看板数据更新（inject_weekly_updates）
    Step 4. 里程碑延期检测（enrich_global_milestones）
  ）

用法：
  # 正式跑批（默认阈值 14 天）
  python3 run_batch.py

  # 预览模式（不实际发送消息）
  python3 run_batch.py --dry-run

  # 自定义过期阈值
  python3 run_batch.py --stale-threshold 7

  # 强制重发所有过期话题（忽略已发送记录）
  python3 run_batch.py --force

环境变量（可选）：
  LARK_APP_ID, LARK_APP_SECRET  飞书应用凭证
  STALE_THRESHOLD_DAYS          话题过期阈值（天），默认 14
  DRY_RUN                       设为 "true" 启用预览模式
"""

import os
import sys
import argparse
import logging
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

def step_stale_topic_followup(threshold_days: int, dry_run: bool, force: bool) -> dict:
    """
    Step 1: 话题收尾跟进
    扫描过期话题并在群内 @VoidZ 发送追问消息。
    """
    logger.info("=" * 60)
    logger.info("Step 1: 话题收尾跟进 (threshold=%d天)", threshold_days)
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
    stale_threshold: int = 14,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """
    执行全部跑批步骤。
    """
    start_time = datetime.now(timezone.utc)
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║           AI 秘书系统 跑批开始                          ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("开始时间: %s", start_time.strftime("%Y-%m-%d %H:%M:%S UTC"))
    logger.info("参数: dry_run=%s, stale_threshold=%d天, force=%s",
                dry_run, stale_threshold, force)

    results = {}

    # ── Step 1: 话题收尾跟进 ──────────────────────────────────────────────
    results["step1_stale_followup"] = step_stale_topic_followup(
        threshold_days=stale_threshold,
        dry_run=dry_run,
        force=force,
    )

    # ── 后续步骤占位（可扩展）────────────────────────────────────────────
    # results["step2_group_monitor"] = step_group_monitor(...)
    # results["step3_inject_weekly"] = step_inject_weekly(...)
    # results["step4_milestone_check"] = step_milestone_check(...)

    # ── 汇总输出 ─────────────────────────────────────────────────────────
    end_time = datetime.now(timezone.utc)
    elapsed = (end_time - start_time).total_seconds()

    logger.info("")
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║           AI 秘书系统 跑批完成                          ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("耗时: %.1f 秒", elapsed)

    for step_name, result in results.items():
        status = result.get("status", "unknown")
        icon = "✅" if status == "success" else "❌"
        logger.info("%s %s: %s", icon, step_name, status)

        if status == "success":
            summary = result.get("summary", {})
            if "total_stale" in summary:
                logger.info(
                    "   过期话题: %d 条 | 发送: %d 条 | 失败: %d 条",
                    summary.get("total_stale", 0),
                    summary.get("sent_count", 0),
                    summary.get("failed_count", 0),
                )
        elif status == "failed":
            logger.error("   错误: %s", result.get("error", ""))


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AI 秘书系统跑批主入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 run_batch.py                    # 正式跑批（默认阈值 14 天）
  python3 run_batch.py --dry-run          # 预览模式
  python3 run_batch.py --stale-threshold 7  # 7 天阈值
  python3 run_batch.py --force            # 强制重发
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("DRY_RUN", "false").lower() == "true",
        help="预览模式，不实际发送消息",
    )
    parser.add_argument(
        "--stale-threshold",
        type=int,
        default=int(os.environ.get("STALE_THRESHOLD_DAYS", "14")),
        help="话题过期阈值（天），默认 14",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重发，忽略已发送记录",
    )
    args = parser.parse_args()

    run_all(
        stale_threshold=args.stale_threshold,
        dry_run=args.dry_run,
        force=args.force,
    )


if __name__ == "__main__":
    main()

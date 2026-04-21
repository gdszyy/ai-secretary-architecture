"""
run_daily_batch.py
==================
每日批处理入口脚本（每日 09:00 触发）

执行顺序：
  1. daily_progress_updater  — 拉取飞书群消息 → LLM 提取进展 → 写入 weekly_updates
  2. git commit & push       — 将更新后的 dashboard_data.json 推送到 GitHub
     （Railway 监听 main 分支，自动重新部署，看板即刻更新）

用法：
  python3 run_daily_batch.py              # 正式运行
  python3 run_daily_batch.py --dry-run    # 预览模式，不写入文件，不推送 git
  python3 run_daily_batch.py --hours 48   # 拉取最近 48 小时（默认 26 小时）
"""

import argparse
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_daily_batch")

REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def run_step(name: str, cmd: list, dry_run: bool = False) -> bool:
    """执行一个批处理步骤，返回是否成功。"""
    if dry_run and name != "git_push":
        logger.info("[DRY RUN] 跳过: %s", name)
        return True
    logger.info("▶ 开始: %s", name)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=False)
    if result.returncode != 0:
        logger.error("✗ 失败: %s (exit code %d)", name, result.returncode)
        return False
    logger.info("✓ 完成: %s", name)
    return True


def git_push(dry_run: bool = False) -> bool:
    """提交并推送 dashboard_data.json 到 GitHub。"""
    if dry_run:
        logger.info("[DRY RUN] 跳过 git push")
        return True

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"chore(daily): auto-update dashboard_data.json [{now_str}]"

    # 只暂存 data/dashboard_data.json，避免误提交其他文件
    subprocess.run(
        ["git", "add", "data/dashboard_data.json"],
        cwd=str(REPO_ROOT)
    )

    # 检查是否有变更
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(REPO_ROOT)
    )
    if status.returncode == 0:
        logger.info("ℹ️  dashboard_data.json 无变更，跳过 git push")
        return True

    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=str(REPO_ROOT)
    )
    result = subprocess.run(
        ["git", "push"],
        cwd=str(REPO_ROOT)
    )
    if result.returncode != 0:
        logger.error("✗ git push 失败")
        return False
    logger.info("✓ git push 成功: %s", commit_msg)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="每日批处理：群消息提取 → 写入看板 → git push",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 run_daily_batch.py                # 正式运行
  python3 run_daily_batch.py --dry-run      # 预览模式
  python3 run_daily_batch.py --hours 48     # 拉取最近 48 小时
        """
    )
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入文件，不推送 git")
    parser.add_argument("--hours", type=int, default=26, help="拉取最近 N 小时的消息（默认 26）")
    args = parser.parse_args()

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║              每日批处理 开始                             ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("dry_run=%s | hours=%d", args.dry_run, args.hours)

    steps = [
        ("daily_progress_updater", [
            sys.executable,
            str(SCRIPTS_DIR / "daily_progress_updater.py"),
            "--hours", str(args.hours),
            *(["--dry-run"] if args.dry_run else []),
        ]),
    ]

    # 周四额外执行：weekly_issue_reminder（风险项集中提醒）
    today_weekday = datetime.now().weekday()  # 0=周一, 3=周四
    if today_weekday == 3:
        logger.info("今日为周四，追加执行 weekly_issue_reminder")
        steps.append(("weekly_issue_reminder", [
            sys.executable,
            str(SCRIPTS_DIR / "weekly_issue_reminder.py"),
            *(["--dry-run"] if args.dry_run else []),
        ]))

    success = True
    for name, cmd in steps:
        if not run_step(name, cmd, dry_run=args.dry_run):
            logger.error("批处理在步骤 [%s] 中止", name)
            success = False
            break

    if success:
        git_push(dry_run=args.dry_run)

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║              每日批处理 %s                           ║", "完成 ✓" if success else "失败 ✗")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

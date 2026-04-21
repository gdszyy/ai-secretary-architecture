"""
run_weekly_batch.py
===================
每周批处理入口脚本（每周一 06:00 触发）

执行顺序：
  1. topic_expiry_archiver   — 将跨周高价值话题归档（清理噪音，保证周报数据干净）
  2. run_weekly_report       — 三源整合（飞书周报 + Meegle + 群聊）→ 生成综合摘要
                               + activity 交付活跃度 → 写入看板 → 飞书通知
  3. enrich_global_milestones — 为全局里程碑补充模块快照、检测延期
  4. git commit & push        — 将 dashboard_data.json 推送到 GitHub
     （Railway 监听 main 分支，自动重新部署，看板即刻更新）

用法：
  python3 run_weekly_batch.py              # 正式运行（汇总当前周）
  python3 run_weekly_batch.py --dry-run    # 预览模式，不写入文件，不发通知，不推送 git
  python3 run_weekly_batch.py --week 2026-16  # 指定周标识（用于补跑历史周）
  python3 run_weekly_batch.py --skip-notify   # 跳过飞书通知（仅写入数据）
"""

import argparse
import logging
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_weekly_batch")

REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def get_current_week_str() -> str:
    """返回当前 ISO 周标识，格式 YYYY-WW。"""
    today = date.today()
    iso = today.isocalendar()
    return f"{iso[0]}-{iso[1]:02d}"


def run_step(name: str, cmd: list, dry_run: bool = False, skip_dry: bool = False) -> bool:
    """执行一个批处理步骤，返回是否成功。"""
    if dry_run and skip_dry:
        logger.info("[DRY RUN] 跳过: %s", name)
        return True
    logger.info("▶ 开始: %s", name)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=False)
    if result.returncode != 0:
        logger.error("✗ 失败: %s (exit code %d)", name, result.returncode)
        return False
    logger.info("✓ 完成: %s", name)
    return True


def git_push(week_str: str, dry_run: bool = False) -> bool:
    """提交并推送 dashboard_data.json 到 GitHub。"""
    if dry_run:
        logger.info("[DRY RUN] 跳过 git push")
        return True

    commit_msg = f"chore(weekly): auto-update dashboard_data.json for week {week_str}"

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
        description="每周批处理：话题归档 → 周报生成 → 里程碑更新 → git push",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 run_weekly_batch.py                    # 正式运行（当前周）
  python3 run_weekly_batch.py --dry-run          # 预览模式
  python3 run_weekly_batch.py --week 2026-16     # 补跑指定周
  python3 run_weekly_batch.py --skip-notify      # 跳过飞书通知
        """
    )
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入文件，不发通知，不推送 git")
    parser.add_argument("--week", type=str, default=None, help="指定周标识，格式 YYYY-WW（默认当前周）")
    parser.add_argument("--skip-notify", action="store_true", help="跳过飞书通知")
    args = parser.parse_args()

    week_str = args.week or get_current_week_str()

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║              每周批处理 开始                             ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("week=%s | dry_run=%s | skip_notify=%s", week_str, args.dry_run, args.skip_notify)

    # Step 1: 话题归档（清理跨周噪音）
    step1_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "topic_expiry_archiver.py"),
        "--week", week_str,
        *(["--dry-run"] if args.dry_run else []),
    ]

    # Step 2: 周报生成（三源整合 + activity 写入）
    step2_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_weekly_report.py"),
        "--week", week_str,
        *(["--dry-run"] if args.dry_run else []),
        *(["--skip-notify"] if args.skip_notify else []),
    ]

    # Step 3: 里程碑快照更新
    step3_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "enrich_global_milestones.py"),
    ]

    steps = [
        ("topic_expiry_archiver", step1_cmd),
        ("run_weekly_report", step2_cmd),
        ("enrich_global_milestones", step3_cmd),
    ]

    success = True
    for name, cmd in steps:
        if not run_step(name, cmd, dry_run=args.dry_run, skip_dry=(name == "enrich_global_milestones")):
            logger.error("批处理在步骤 [%s] 中止", name)
            success = False
            break

    if success:
        git_push(week_str, dry_run=args.dry_run)

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║              每周批处理 %s                           ║", "完成 ✓" if success else "失败 ✗")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

"""
manual_correction.py
====================
手动信息纠正脚本

用于将 VoidZ 在对话中补充/纠正的话题内容写入 Bitable。
每次运行时，将 CORRECTIONS 列表中的条目以 upsert 方式写入：
  - 若 Bitable 中已存在同名话题（标题精确匹配），则更新该记录；
  - 若不存在，则新建记录。

用法：
  python3 scripts/manual_correction.py --dry-run   # 预览
  python3 scripts/manual_correction.py             # 正式写入

CORRECTIONS 格式说明：
  title       话题标题（用于匹配已有记录）
  intent      意图类型：major_decision / milestone_fact / risk_blocker / routine_task
  status      状态：风险/阻塞 / 进行中 / 已解决 / 已归档(跨周)
  period      来源周期（填写当前周期字符串）
  summary     话题摘要（纠正后的完整描述）
  source      信息来源（如 VoidZ补充、群聊等）

重构说明（2026-04-21）：
  核心写入逻辑已迁移至 correction_writer.py，本脚本通过 write_corrections() 调用。
  这使得飞书卡片回复触发的自动纠正（lark_correction_handler.py）可以复用相同逻辑。
"""

import os
import sys
import logging
import argparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("manual_correction")

# 确保 scripts 目录在 Python 路径中（从仓库根目录运行时需要）
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from correction_writer import write_corrections, upsert_correction

# ─────────────────────────────────────────────────────────────────────────────
# 本次纠正内容（2026-W17，VoidZ 补充）
# ─────────────────────────────────────────────────────────────────────────────
CORRECTIONS = [
    {
        "title":   "活动平台赔率限制",
        "intent":  "major_decision",
        "status":  "已解决",
        "period":  "第5周 (04/20~04/26)",
        "summary": (
            "【决策】平台统一使用相同的 Bonus 赔率限制。"
            "背景：主钱包能量分配需一视同仁，若不同活动赔率限制不一致（如1.5倍 vs 1.7倍），"
            "会导致能量分配逻辑出现漏洞，低限制主钱包能量可能被分配到高限制主钱包。"
            "决策：所有活动平台统一使用相同赔率限制，消除漏洞。"
        ),
        "source":  "VoidZ补充 2026-04-21",
    },
    {
        "title":   "多语言翻译确认",
        "intent":  "milestone_fact",
        "status":  "进行中",
        "period":  "第5周 (04/20~04/26)",
        "summary": (
            "建立多语言对照表格，用于前端翻译 JS 文件的校对。"
            "当前阻塞：@tao 需将前端翻译 JS 文件交付给 @VoidZ，目前 pending 中。"
            "后续：基于对照表格完成多语言文案人工确认，覆盖巴西/墨西哥两套数据。"
        ),
        "source":  "VoidZ补充 2026-04-21",
    },
    {
        "title":   "Casino Bonus 上线计划",
        "intent":  "milestone_fact",
        "status":  "进行中",
        "period":  "第5周 (04/20~04/26)",
        "summary": (
            "Casino Bonus 功能当前处于开发中（参考 Meegle 工作项）。"
            "各厂商调用 Casino Bonus 和 FreeSpin 的 API 已整理完成，"
            "技术团队计划下周开始调通功能。正式上线时间待确认。"
        ),
        "source":  "VoidZ补充 2026-04-21",
    },
    {
        "title":   "个人中心页面开发",
        "intent":  "major_decision",
        "status":  "进行中",
        "period":  "第5周 (04/20~04/26)",
        "summary": (
            "【设计决策更新】"
            "PC 端：个人中心从弹窗形式切换为内嵌页面，并增加侧边栏导航。"
            "移动端：个人中心页面底部可与菜单导航栏共存（不再全屏覆盖）。"
            "后端功能已完成（Bonus 订单及划转记录查询），前端功能待上线。"
        ),
        "source":  "VoidZ补充 2026-04-21",
    },
    {
        "title":   "体育数据供应商选择",
        "intent":  "risk_blocker",
        "status":  "风险/阻塞",
        "period":  "第5周 (04/20~04/26)",
        "summary": (
            "【持续风险】SR 商务不配合，计划通过新公司与 SR 对接并更换商务负责人。"
            "同时积极接触其他数据供应商，目前正在对接 Lsport。"
            "阻塞原因：大部分供应商对牌照要求较高，当前牌照申请仍在进行中，供应商态度不积极。"
            "影响：墨西哥市场上线依赖 SR 商务推进，当前处于阻塞状态。"
        ),
        "source":  "VoidZ补充 2026-04-21",
    },
    {
        "title":   "CRM 系统选型",
        "intent":  "major_decision",
        "status":  "已解决",
        "period":  "第5周 (04/20~04/26)",
        "summary": (
            "【决策】接入 Smartico。"
            "背景：集团多数项目已使用 Smartico 平台，统一接入以降低集成成本。"
            "注：此前第2周记录倾向 Optimove、第4周评估后倾向不接入 Smartico 均为过程讨论，"
            "最终决策以集团要求为准，确认接入 Smartico。"
        ),
        "source":  "VoidZ补充 2026-04-21",
    },
]
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="手动信息纠正写入 Bitable")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际写入")
    args = parser.parse_args()

    if args.dry_run:
        print(f"\n{'='*60}")
        print("[DRY RUN] 以下条目将被写入（未实际执行）：")
        for corr in CORRECTIONS:
            action = "UPDATE（已存在）" if True else "CREATE（新建）"
            print(f"  [{corr['intent']}] {corr['title']} | status={corr['status']}")
        print(f"共 {len(CORRECTIONS)} 条")
        print(f"{'='*60}\n")
        return

    result = write_corrections(CORRECTIONS)
    print(f"\n{'='*60}")
    print(f"✅ 完成：更新 {result['updated']} 条 / 新建 {result['created']} 条 / 失败 {result['errors']} 条")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

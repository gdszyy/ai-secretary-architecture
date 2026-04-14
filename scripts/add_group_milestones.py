"""
add_group_milestones.py
为每个大模块（module_groups）增加里程碑列表。
每个里程碑关联一组需求（feature IDs），进度 = 该组需求中已完成/进行中的任务比例。
延期规则：due_date < today && status != completed → overdue=True
"""
import json
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()  # 2026-04-14
DASHBOARD_JSON = Path(__file__).parent.parent / "data" / "dashboard_data.json"

# 大模块里程碑定义
# 每个里程碑关联 feature_ids（跨该大模块下各子模块的需求ID）
GROUP_MILESTONES = {
    "grp_data_engine": [
        {
            "id": "gms_de_01",
            "title": "数据源全量接入 & 匹配率 ≥95%",
            "due_date": "2026-04-18",
            "status": "in_progress",
            "feature_ids": [
                "feat_sr_data", "feat_lsport_data",
                "feat_matching_algo_v2", "feat_manual_review",
                "feat_frontend_monitor"
            ],
            "description": "Lsport/SR 两路数据源完成接入，赛程变更和赔率变更 Kafka Topic 稳定推送，SR→TS 匹配率达 95% 以上，LS→TS 联调完成。"
        },
        {
            "id": "gms_de_02",
            "title": "多语言数据 & outright 冠军盘完善",
            "due_date": "2026-04-25",
            "status": "pending",
            "feature_ids": ["feat_defend_betting"],
            "description": "西语/葡语翻译接口权限问题解决，outright league 冠军盘数据推送稳定，Defend 投注与结算验证完成。"
        }
    ],
    "grp_betting_core": [
        {
            "id": "gms_bc_01",
            "title": "体育活动 V1 验收（Sportbook Testing+投注栏优化）",
            "due_date": "2026-04-24",
            "status": "in_progress",
            "feature_ids": [
                "feat_mts_basic", "feat_sr_production",
                "feat_sportbook_testing", "feat_bet_ui_optimization"
            ],
            "description": "Sportbook Testing 完成，投注栏交互优化上线，MTS 基础投注和 SR 生产账号申请完成。"
        },
        {
            "id": "gms_bc_02",
            "title": "Cashout 平台级方案落地",
            "due_date": "2026-05-09",
            "status": "pending",
            "feature_ids": ["feat_cashout"],
            "description": "Cashout 功能完成平台级方案评估并启动开发，支持体育单关/串关提前结算。"
        }
    ],
    "grp_user_finance": [
        {
            "id": "gms_uf_01",
            "title": "全民代理上线 & 财务优化 V1.2",
            "due_date": "2026-04-28",
            "status": "in_progress",
            "feature_ids": [
                "feat_referral_agent",
                "feat_finance_v12", "feat_withdrawal_resend"
            ],
            "description": "全民代理功能整理完成并上线，财务优化 V1.2 完成，提款重送/Transfer Order 功能上线。"
        },
        {
            "id": "gms_uf_02",
            "title": "用户体系完善（KYC+标签+代理）",
            "due_date": "2026-03-31",
            "status": "completed",
            "feature_ids": [
                "feat_kyc_v11", "feat_user_tag", "feat_agent_management",
                "feat_wallet_transfer", "feat_deposit_withdraw_v11", "feat_payment_optimization"
            ],
            "description": "KYC 优化 V1.1、用户标签、代理管理、主钱包划转、充提流程优化 V1.1、代付优化全部完成。"
        }
    ],
    "grp_operations": [
        {
            "id": "gms_op_01",
            "title": "活动平台 V1 上线（VIP+通行证+排行榜）",
            "due_date": "2026-04-28",
            "status": "in_progress",
            "feature_ids": [
                "feat_activity_platform_prd", "feat_first_deposit",
                "feat_vip_activity", "feat_worldcup_pass",
                "feat_leaderboard", "feat_activity_mutex"
            ],
            "description": "VIP、通行证、留存、排行榜四类活动完成前台开发，活动互斥规则上线。"
        },
        {
            "id": "gms_op_02",
            "title": "投放系统验收（埋点/数据/展示）",
            "due_date": "2026-04-17",
            "status": "in_progress",
            "feature_ids": [
                "feat_ads_prd", "feat_pixel_spec",
                "feat_promo_report", "feat_ads_acceptance"
            ],
            "description": "投放后台 xp 技术逻辑完成，广告配置自动化实现，pixel/token 数据正常传递，埋点数据验收通过。"
        },
        {
            "id": "gms_op_03",
            "title": "Casino 游戏注单报表完成",
            "due_date": "2026-05-09",
            "status": "pending",
            "feature_ids": ["feat_bet_report"],
            "description": "游戏注单报表开发完成，支持多厂商数据汇总与导出。"
        }
    ],
    "grp_platform": [
        {
            "id": "gms_pf_01",
            "title": "平台稳定化 & H5 适配完成",
            "due_date": "2026-04-21",
            "status": "in_progress",
            "feature_ids": [
                "feat_core_ui", "feat_activity_ui", "feat_bet_card_spec",
                "feat_h5_adaptation", "feat_ad_materials",
                "feat_platform_setting", "feat_sms_smtp",
                "feat_faq", "feat_announcement"
            ],
            "description": "H5 适配完成，平台 Setting 配置、SMS/SMTP、FAQ、公告功能全部稳定，核心 UI 规范落地。"
        },
        {
            "id": "gms_pf_02",
            "title": "站内信与客服功能完善",
            "due_date": "2026-03-15",
            "status": "completed",
            "feature_ids": ["feat_im", "feat_cs"],
            "description": "站内信和站内客服功能验收完成，稳定运行。"
        }
    ]
}

def compute_overdue(milestone):
    """如果 due_date < today 且 status != completed，标记为 overdue"""
    if milestone["status"] == "completed":
        return False
    return milestone["due_date"] < TODAY

def main():
    with open(DASHBOARD_JSON) as f:
        data = json.load(f)

    # Build feature status lookup
    feature_status = {}
    for mod in data["modules"]:
        for feat in mod.get("features", []):
            feature_status[feat["id"]] = feat.get("status", "pending")

    updated = 0
    for group in data["module_groups"]:
        gid = group["id"]
        if gid not in GROUP_MILESTONES:
            continue

        milestones = []
        for ms in GROUP_MILESTONES[gid]:
            # Compute progress from linked feature_ids
            fids = ms.get("feature_ids", [])
            if fids:
                done = sum(
                    1 for fid in fids
                    if feature_status.get(fid) in ("completed", "in_progress")
                )
                ms["progress"] = round(done / len(fids) * 100)
            else:
                ms["progress"] = 0

            # Compute overdue
            ms["overdue"] = compute_overdue(ms)
            milestones.append(ms)

        group["milestones"] = milestones
        updated += 1
        print(f"  ✅ {group['name']}: {len(milestones)} 个里程碑")

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已为 {updated} 个大模块写入里程碑数据")
    print(f"已写入: {DASHBOARD_JSON}")

if __name__ == "__main__":
    main()

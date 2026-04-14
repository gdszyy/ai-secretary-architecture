"""
enrich_global_milestones.py
──────────────────────────
1. 为每个整体里程碑（milestones[]）增加 group_snapshots 字段
   描述该里程碑时间点各大模块的状态快照（用于前端点击切换矩阵视图）
2. 自动检测大模块里程碑是否延期（due_date < today && status != completed）
"""
import json
from datetime import date
from pathlib import Path

DASHBOARD_JSON = Path(__file__).parent.parent / "data" / "dashboard_data.json"
today = date.today().isoformat()

# ── 整体里程碑对应的各大模块状态快照 ──────────────────────────────
# 每个快照描述：在该里程碑时间点，各大模块的整体状态和关键进展
# status: completed / in_progress / pending / blocked
GLOBAL_MILESTONE_SNAPSHOTS = {
    # 2026-01-09 MTS 基础投注功能验收
    "2026-01-09": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "UOF 数据接入完成，SR/LS 接入进行中"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "MTS 基础投注验收完成"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "KYC、用户标签开发中"},
        {"group_id": "grp_operations",     "status": "pending",     "summary": "活动平台尚未启动"},
        {"group_id": "grp_platform",       "status": "in_progress", "summary": "核心 UI 设计进行中"},
    ],
    # 2026-01-23 KYC 优化 V1.1 完成
    "2026-01-23": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "SR 数据接入测试中"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "SR 生产账号申请中"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "KYC V1.1 完成，代理管理开发中"},
        {"group_id": "grp_operations",     "status": "pending",     "summary": "活动 PRD 准备中"},
        {"group_id": "grp_platform",       "status": "in_progress", "summary": "平台 Setting 配置开发中"},
    ],
    # 2026-02-20 站内信、站内客服功能验收
    "2026-02-20": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "SR testing 验收中，LSport MVP 搭建"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "Sportbook Testing 启动"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "主钱包划转、充提流程优化完成"},
        {"group_id": "grp_operations",     "status": "in_progress", "summary": "RG/IG 对接完成，游戏商管理上线"},
        {"group_id": "grp_platform",       "status": "in_progress", "summary": "站内信与客服验收完成"},
    ],
    # 2026-02-27 MTS 测试完成并申请 SR 生产账号
    "2026-02-27": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "SR sport testing 验收完成"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "MTS 测试完成，SR 生产账号申请中"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "代付优化完成，全民代理规划中"},
        {"group_id": "grp_operations",     "status": "in_progress", "summary": "首充活动 PRD 输出中"},
        {"group_id": "grp_platform",       "status": "in_progress", "summary": "SMS/SMTP、FAQ、公告功能完成"},
    ],
    # 2026-03-06 RG API 解析完成
    "2026-03-06": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "Trade/Defend 产品连接完成"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "投注栏交互优化完成"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "用户标签、代理管理完成"},
        {"group_id": "grp_operations",     "status": "in_progress", "summary": "RG API 解析完成，注单报表文档输出"},
        {"group_id": "grp_platform",       "status": "completed",   "summary": "站内信与客服功能完善"},
    ],
    # 2026-03-20 首充活动原型设计与 PRD 文档输出完成
    "2026-03-20": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "前端监控消息配置进行中"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "Sportbook Testing 进行中"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "全民代理开发启动"},
        {"group_id": "grp_operations",     "status": "in_progress", "summary": "首充活动 PRD 完成，VIP 活动开发中"},
        {"group_id": "grp_platform",       "status": "in_progress", "summary": "H5 适配开发中，广告素材制作"},
    ],
    # 2026-04-03 SR→TS 匹配度提升至 90%+
    "2026-04-03": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "SR→TS 匹配率 90%+，LSport 后端对接基本完成"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "Sportbook Testing 持续进行"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "全民代理 50% 完成，财务优化 V1.2 进行中"},
        {"group_id": "grp_operations",     "status": "in_progress", "summary": "VIP 活动、世界杯通行证开发中"},
        {"group_id": "grp_platform",       "status": "in_progress", "summary": "H5 适配完成，平台稳定化进行中"},
    ],
    # 2026-04-10 游戏注单报表更新完成（当前）
    "2026-04-10": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "匹配算法 V2 迭代中，人工校验流程进行中"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "Sportbook Testing 收尾，Cashout 方案评估"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "全民代理整理 50%，提款重送开发中"},
        {"group_id": "grp_operations",     "status": "in_progress", "summary": "游戏注单报表更新，投放验收进行中"},
        {"group_id": "grp_platform",       "status": "in_progress", "summary": "平台稳定化，H5 适配完成"},
    ],
    # 2026-04-17 全民代理功能整理完成（下一节点）
    "2026-04-17": [
        {"group_id": "grp_data_engine",    "status": "in_progress", "summary": "Defend 投注与结算验证待完成"},
        {"group_id": "grp_betting_core",   "status": "in_progress", "summary": "Sportbook Testing 完成，Cashout 启动"},
        {"group_id": "grp_user_finance",   "status": "in_progress", "summary": "全民代理上线，财务优化 V1.2 收尾"},
        {"group_id": "grp_operations",     "status": "in_progress", "summary": "投放功能验收完成，活动平台 V1 冲刺"},
        {"group_id": "grp_platform",       "status": "in_progress", "summary": "平台稳定化基本完成"},
    ],
}

def run():
    with open(DASHBOARD_JSON) as f:
        data = json.load(f)

    # 1. 为整体里程碑增加 group_snapshots
    for ms in data["milestones"]:
        snapshots = GLOBAL_MILESTONE_SNAPSHOTS.get(ms["date"], [])
        ms["group_snapshots"] = snapshots

    # 2. 自动检测大模块里程碑延期
    for group in data["module_groups"]:
        for gms in group.get("milestones", []):
            if gms["status"] != "completed" and gms["due_date"] < today:
                gms["overdue"] = True
            else:
                gms["overdue"] = False

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已为 {len(data['milestones'])} 个整体里程碑写入 group_snapshots")
    print(f"✅ 已自动检测大模块里程碑延期状态（today={today}）")
    for group in data["module_groups"]:
        for gms in group.get("milestones", []):
            if gms.get("overdue"):
                print(f"  ⚠ 延期: [{group['name']}] {gms['title']} (due={gms['due_date']})")

if __name__ == "__main__":
    run()

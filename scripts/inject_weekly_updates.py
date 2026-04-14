"""
inject_weekly_updates.py
将飞书群组周报（4/6~4/10，W16）的真实进展注入 dashboard_data.json 的 weekly_updates 字段
"""
import json
from pathlib import Path

DASHBOARD_JSON = Path(__file__).parent.parent / "data" / "dashboard_data.json"
WEEK_KEY = "2026-16"

# 从飞书群组周报提取的各模块本周进展
# 格式: module_id -> update text
WEEKLY_UPDATES = {
    "mod_ls_ts_matching": (
        "Kafka Topic（dev_ls_fixture_change / dev_ls_odds_change）配置完成，"
        "生产环境参数完善中，数据源部分预计4/18完成，整体联调预计4/24-25完成。"
        "WebSocket断连问题排查中，SR→TS匹配率已达95%以上。"
    ),
    "mod_sr_ts_matching": (
        "SR→TS匹配率达95%以上，数据已同步仓库，安排效果验证中。"
        "outright冠军盘数据优先接入outright league，普通outright关联方案待完善。"
        "多语言（es/pt）翻译接口权限问题排查中。"
    ),
    "mod_data_ingestion": (
        "Lsport数据源接入推进中：赛程变更和赔率变更两个Kafka Topic已确认，"
        "outright league冠军盘数据推送跟进中，多语言数据缺失问题与数据源方沟通解决。"
    ),
    "mod_activity_platform": (
        "活动平台V1：广州负责运营位前台开发，上海负责Casino Bonus及Freespin礼券配置前台适配。"
        "V2：广州负责预算管理、活动模板及活动页管理（优先级较低）。"
        "活动互斥规则文档编写中，VIP/通行证/留存/排行榜为当前优先活动。"
        "每日短会机制已建立，跟进需求进展。"
    ),
    "mod_sports_betting_core": (
        "体育活动优先级确定：新客首充→0-0退赔→Superodds→VIP。"
        "0-0退赔规则明确（仅限指定赛事，支持胜平负/让球/大小球单关），上海负责。"
        "VIP UI设计4/10验收通过，推送开发。Cashout功能决定做平台级别，方案评估中。"
    ),
    "mod_casino": (
        "游戏厂商PP对接正常，图档大小问题跟进中。"
        "Stripe对接等待Free请假结束后启动，技术由Chase协助。"
        "游戏渲染加载性能优化中（直连速度较快，VPN可接受）。"
    ),
    "mod_ads_system": (
        "投放后台存在较多问题：xp技术ch逻辑未完成，广告配置自动化未实现，"
        "pixel/token数据未传递，技术团队跟进中，争取两天内解决。"
        "数据埋点及登录记录需求（APP/H5/网页端）将与埋点一起开发。"
    ),
    "mod_uiux_design": (
        "活动页面UI优化完成（巴西/墨西哥活动图已添加，footer/登陆页关闭按钮已上线）。"
        "移动端按钮高度规范确定（首页/live/体育详情页56，outright/比赛详情页40）。"
        "Bet Slip全屏交互调整：保留返回按钮，移除底部TabBar，交互文档编写中。"
        "Tooltip统一为弹窗动画形式（从问号弹出收起）。"
    ),
    "mod_user_system": (
        "推荐好友功能：广州负责页面开发，上海负责推荐关系绑定和分享三方对接，需求整理中。"
        "数字显示格式统一为三位小数，已确认并完成调整。"
    ),
    "mod_wallet_finance": (
        "Bonus类型使用流程明确：SportBonus/CasinoBonus/Freesports/Freespin四种类型，"
        "前端UI由设计团队负责，注单报表开发已启动，后端与财务协调投注计算逻辑。"
    ),
    "mod_platform_setting": (
        "菜单改为纯树形结构（二级在一级下，三级在二级下），地区筛选接口暂缓。"
        "法务要求新增底部文案和新logo，已上线test1测试环境，移动端后续美化。"
        "文案多语言支持：西语/葡语语言包提供中，Lark文案表格维护中。"
    ),
    "mod_im_cs": (
        "弱网弹窗触发频率评估中（针对墨西哥市场网络状况）。"
        "购物车快捷金额设置已同步后端，问号tooltip统一为hover状态。"
    ),
}

def main():
    with open(DASHBOARD_JSON) as f:
        data = json.load(f)

    updated_count = 0
    for module in data["modules"]:
        mid = module["id"]
        if mid in WEEKLY_UPDATES:
            # Remove existing W16 entry if any
            module["weekly_updates"] = [
                w for w in module.get("weekly_updates", [])
                if w["week"] != WEEK_KEY
            ]
            # Prepend new W16 entry
            module["weekly_updates"].insert(0, {
                "week": WEEK_KEY,
                "update": WEEKLY_UPDATES[mid]
            })
            updated_count += 1
            print(f"  ✅ {module['name']}: 注入W16周报")

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 共更新 {updated_count} 个模块的W16周报")
    print(f"已写入: {DASHBOARD_JSON}")

if __name__ == "__main__":
    main()

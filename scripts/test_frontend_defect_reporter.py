"""
前端缺陷报送脚本测试（dry-run 模式，无需真实 Meegle Token）
运行方式：
  cd /home/ubuntu/ai-secretary-architecture/scripts
  python3 test_frontend_defect_reporter.py
"""

import json
import sys
import os

# 将 scripts 目录加入路径
sys.path.insert(0, os.path.dirname(__file__))

from frontend_defect_reporter import analyze_message, generate_inquiry_message, build_meegle_payload, COMPLETENESS_THRESHOLD

# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "name": "完整 Bug 报告（应直接报送）",
        "message": "游戏模块在测试环境发现渲染加载很慢，步骤：进入游戏列表页 → 点击任意游戏 → 等待超过 10 秒仍未加载。影响所有 H5 用户，优先级高，需要尽快修复。",
        "sender": "VoidZ",
    },
    {
        "name": "不完整 Bug 报告（缺少复现步骤和优先级）",
        "message": "游戏渲染加载较慢，VPN 连接速度可接受，直连速度较快。",
        "sender": "前端同学",
    },
    {
        "name": "仅有现象描述（缺少大量信息）",
        "message": "白屏了，页面打不开",
        "sender": "测试同学",
    },
    {
        "name": "非 Bug 消息（日常需求讨论）",
        "message": "下周要把活动中心的预算配置功能加上，大家看看排期。",
        "sender": "PM",
    },
    {
        "name": "前端 UI 样式问题（中优）",
        "message": "移动端 Bet Slip 按钮在 iOS Safari 上显示错位，底部有 8px 的间距偏差，影响所有 iOS 用户。",
        "sender": "设计师",
    },
]


def run_tests():
    print("=" * 70)
    print("前端缺陷报送脚本 - 单元测试（LLM 分析 + 话术生成）")
    print("=" * 70)

    for i, case in enumerate(TEST_CASES, 1):
        print(f"\n【测试 {i}】{case['name']}")
        print(f"  消息: {case['message'][:60]}{'...' if len(case['message']) > 60 else ''}")
        print(f"  发送者: {case['sender']}")
        print("-" * 50)

        # 执行分析
        analysis = analyze_message(case["message"], case["sender"])

        is_bug = analysis.get("is_frontend_bug", False)
        confidence = analysis.get("confidence", 0)
        score = analysis.get("completeness_score", 0)
        missing = analysis.get("missing_fields", [])
        extracted = analysis.get("extracted", {})

        print(f"  ✦ 是否为前端 Bug: {is_bug}（置信度: {confidence:.2f}）")
        print(f"  ✦ 完整度评分: {score}/100（阈值: {COMPLETENESS_THRESHOLD}）")
        print(f"  ✦ 缺失字段: {missing}")
        print(f"  ✦ 提取实体:")
        for k, v in extracted.items():
            if v:
                print(f"      {k}: {v}")

        if is_bug and confidence >= 0.6:
            if score < COMPLETENESS_THRESHOLD:
                inquiry = generate_inquiry_message(case["sender"], case["message"], analysis)
                print(f"\n  → 动作: 发送补全询问\n")
                print("  " + "\n  ".join(inquiry.split("\n")))
            else:
                payload = build_meegle_payload(analysis, case["message"])
                print(f"\n  → 动作: 直接报送至 Meegle")
                print(f"     工单标题: {payload['name']}")
                print(f"     优先级: {payload['priority']}")
                print(f"     描述预览: {payload['description'][:100]}...")
        else:
            print(f"\n  → 动作: 忽略（非前端 Bug）")

        print()

    print("=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()

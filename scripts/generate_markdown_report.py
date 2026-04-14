#!/usr/bin/env python3
"""
将 LLM 提取的 JSON 洞察结果转换为易读的 Markdown 报告，并写入仓库。
"""
import os
import json

def generate_report():
    in_path = os.path.join(os.path.dirname(__file__), '..', 'weekly_insights.json')
    with open(in_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = [
        "# 新增群组 4 周历史消息洞察报告",
        "",
        "**生成日期**: 2026-04-14",
        "**总计群组**: 8 个",
        "**分析周期**: 过去 4 周 (03/17 ~ 04/14)",
        "",
        "---",
        ""
    ]

    for chat_id, group in data.items():
        name = group["name"]
        lines.append(f"## 📋 群组：{name}")
        lines.append("")
        
        # 找出最新一周的画像作为整体画像
        latest_insight = group["weeks"]["4"]["insights"]
        profile = latest_insight.get("group_profile", "无")
        lines.append(f"**群组画像**: {profile}")
        lines.append("")

        for wk_num in range(1, 5):
            wk_str = str(wk_num)
            week_data = group["weeks"][wk_str]
            label = week_data["label"]
            msg_count = week_data["message_count"]
            insights = week_data["insights"]

            if msg_count == 0:
                lines.append(f"### {label} (0 条消息)")
                lines.append("> 本周无消息记录。")
                lines.append("")
                continue

            activity = insights.get("activity_level", "unknown")
            summary = insights.get("week_summary", "")
            lines.append(f"### {label} ({msg_count} 条消息, {activity} 活跃)")
            lines.append(f"> {summary}")
            lines.append("")

            decisions = insights.get("important_decisions", [])
            if decisions:
                lines.append("**重要决策**:")
                for d in decisions:
                    lines.append(f"- {d}")
                lines.append("")

            topics = insights.get("key_topics", [])
            if topics:
                lines.append("**关键话题**:")
                for t in topics:
                    status_icon = {
                        "resolved": "✅", "in_progress": "🔄", 
                        "pending": "⏳", "unclear": "❓"
                    }.get(t.get("status", ""), "▪️")
                    
                    lines.append(f"1. **{t.get('topic', '无标题')}** {status_icon}")
                    lines.append(f"   - **摘要**: {t.get('summary', '')}")
                    lines.append(f"   - **模块**: `{t.get('module', 'unknown')}` | **意图**: `{t.get('intent', 'unknown')}`")
                    if t.get("action_items"):
                        lines.append(f"   - **待办**:")
                        for ai in t.get("action_items"):
                            lines.append(f"     * {ai}")
                lines.append("")

        lines.append("---")
        lines.append("")

    out_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'module3_info_sources', 'new_groups_4weeks_insights.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"Markdown 报告已生成: {out_path}")

if __name__ == "__main__":
    generate_report()

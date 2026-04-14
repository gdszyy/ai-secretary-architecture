#!/usr/bin/env python3
"""
逐周 LLM 提取关键信息与话题摘要。
对每个新增群的每周消息进行话题拆解，输出结构化洞察报告。
"""
import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI()

EXTRACT_SYSTEM_PROMPT = """你是一个 AI 项目秘书，负责从群聊记录中提取关键信息。

你的任务是分析一周内的群聊消息，输出以下结构化 JSON：
{
  "group_profile": "对这个群的定性描述（一句话，如：产品与研发的需求对齐群）",
  "activity_level": "high/medium/low/silent",
  "key_topics": [
    {
      "topic": "话题标题（简洁，10字以内）",
      "summary": "话题摘要（2-4句话，说清楚讨论了什么、结论是什么）",
      "participants": ["参与者ID列表，最多3个"],
      "intent": "bug_report/feature_request/design_review/status_update/decision/question/casual_chat",
      "module": "涉及的业务模块（如：支付系统/前端/风控/设计/运营，若不明确填unknown）",
      "status": "resolved/in_progress/pending/unclear",
      "action_items": ["待办事项列表，若有的话"]
    }
  ],
  "week_summary": "本周整体情况总结（3-5句话）",
  "unresolved_count": 未解决话题数量,
  "important_decisions": ["本周做出的重要决策列表"]
}

注意：
- 消息量很大时，重点关注有实质内容的讨论，忽略纯闲聊和表情包
- 同一话题的跳跃讨论要归并为一个 topic
- participants 使用消息中的 sender_id 字段
- 若消息量极少（< 5条），key_topics 可以为空列表
- 必须输出合法 JSON，不要有任何其他文字
"""


def messages_to_text(messages, max_msgs=300):
    """将消息列表转为 LLM 可读的文本格式"""
    lines = []
    # 若消息过多，均匀采样
    if len(messages) > max_msgs:
        step = len(messages) / max_msgs
        sampled = [messages[int(i * step)] for i in range(max_msgs)]
        lines.append(f"[注意：本周共 {len(messages)} 条消息，以下为均匀采样的 {max_msgs} 条]\n")
    else:
        sampled = messages

    for m in sampled:
        text = m.get("text", "").strip()
        if not text or text in ("[表情包]", "[sticker]"):
            continue
        lines.append(f"[{m['time']}] {m['sender_id']}: {text}")

    return "\n".join(lines)


def extract_weekly_insights(group_name, week_label, messages):
    """对单个群单周的消息进行 LLM 提取"""
    if not messages:
        return {
            "group_profile": "消息量为零，无法分析",
            "activity_level": "silent",
            "key_topics": [],
            "week_summary": "本周无消息记录。",
            "unresolved_count": 0,
            "important_decisions": []
        }

    msg_text = messages_to_text(messages)

    user_prompt = f"""群组名称：{group_name}
时间范围：{week_label}
消息总数：{len(messages)} 条

以下是本周的群聊记录：

{msg_text}

请提取关键信息并输出 JSON。"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
        max_tokens=2000
    )

    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e), "raw": response.choices[0].message.content}


if __name__ == "__main__":
    # 加载历史消息
    history_path = os.path.join(os.path.dirname(__file__), '..', 'history_4weeks.json')
    with open(history_path, 'r', encoding='utf-8') as f:
        history = json.load(f)

    all_insights = {}
    total_groups = len(history)
    total_weeks = 4

    print(f"开始逐周提取，共 {total_groups} 个群 × {total_weeks} 周\n")

    for g_idx, (chat_id, group_data) in enumerate(history.items(), 1):
        name = group_data["name"]
        print(f"[{g_idx}/{total_groups}] 处理群：{name}")
        group_insights = {"name": name, "chat_id": chat_id, "weeks": {}}

        for wk_num in range(1, 5):
            wk_str = str(wk_num)
            week_data = group_data["weeks"].get(wk_str, {})
            week_label = week_data.get("label", f"第{wk_num}周")
            messages = week_data.get("messages", [])
            msg_count = len(messages)

            print(f"  第{wk_num}周 ({msg_count} 条消息) ... ", end="", flush=True)

            insights = extract_weekly_insights(name, week_label, messages)
            group_insights["weeks"][wk_str] = {
                "label": week_label,
                "message_count": msg_count,
                "insights": insights
            }

            topics_count = len(insights.get("key_topics", []))
            activity = insights.get("activity_level", "?")
            print(f"完成 [{activity}活跃, {topics_count}个话题]")

        all_insights[chat_id] = group_insights
        print()

    # 保存结果
    out_path = os.path.join(os.path.dirname(__file__), '..', 'weekly_insights.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_insights, f, ensure_ascii=False, indent=2)

    print(f"✅ 所有洞察已保存至 weekly_insights.json")

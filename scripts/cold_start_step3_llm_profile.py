#!/usr/bin/env python3
"""
冷启动 Step 3：使用 LLM 分析每个群的画像，输出结构化报告
"""
import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI()  # 使用环境中预配置的 OPENAI_API_KEY

SYSTEM_PROMPT = """你是一个项目管理 AI 秘书，正在对一个新加入的 Lark 群组进行"冷启动探索"分析。
你的任务是根据提供的群聊消息样本，输出一份结构化的群组画像报告。

请严格按照以下 JSON 格式输出，不要输出任何其他内容：
{
  "group_category": "研发群|产品群|运维群|管理群|闲聊群|测试群|其他",
  "activity_level": "高活跃|中活跃|低活跃|沉默",
  "peak_hours": "描述活跃时间段，如'工作日白天'，若无法判断则填'未知'",
  "key_participants": ["发言最多或最关键的用户 open_id 列表，最多3个"],
  "business_relevance": "与业务模块的关联描述，如'主要讨论支付和风控模块'，若无法判断则填'未知'",
  "suggested_sync_interval_minutes": 60,
  "priority_score": 50,
  "summary": "一句话总结这个群的用途和价值"
}

priority_score 范围 0-100，越高越重要，建议值：
- 研发/产品核心群：70-90
- 运维报警群：80-95
- 闲聊/测试群：10-30
- 沉默群：5-15

suggested_sync_interval_minutes 建议值：
- 高活跃且重要：30
- 中活跃：60
- 低活跃：240
- 沉默：1440
"""

def analyze_group(group_name: str, messages: list) -> dict:
    # 构建消息摘要（只取文本类型，最多 30 条）
    text_msgs = [m for m in messages if m["type"] == "text" and m["text"].strip()][:30]
    
    if not text_msgs:
        # 没有文本消息，基于消息类型分布做基础判断
        type_counts = {}
        for m in messages:
            type_counts[m["type"]] = type_counts.get(m["type"], 0) + 1
        msg_summary = f"群内共 {len(messages)} 条消息，类型分布：{json.dumps(type_counts, ensure_ascii=False)}"
    else:
        lines = []
        for m in text_msgs:
            lines.append(f"[{m['sender'][:8]}]: {m['text'][:100]}")
        msg_summary = "\n".join(lines)
    
    user_prompt = f"""群组名称：{group_name}
消息样本（共 {len(messages)} 条，以下为文本消息摘要）：

{msg_summary}

请分析该群组画像并输出 JSON 报告。"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result

if __name__ == "__main__":
    print("=== Lark 冷启动 Step 3：LLM 群组画像分析 ===\n")
    
    msgs_path = os.path.join(os.path.dirname(__file__), '..', 'cold_start_messages.json')
    with open(msgs_path, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    profiles = {}
    
    for chat_id, info in all_data.items():
        name = info["name"]
        messages = info["messages"]
        print(f"🤖 正在分析群「{name}」({len(messages)} 条消息)...")
        
        profile = analyze_group(name, messages)
        profile["chat_id"] = chat_id
        profile["group_name"] = name
        profile["latest_message_id"] = info.get("latest_message_id", "")
        profile["cold_start_count"] = 1  # 第一次冷启动
        profiles[chat_id] = profile
        
        print(f"  分类: {profile.get('group_category')}  活跃度: {profile.get('activity_level')}")
        print(f"  优先级: {profile.get('priority_score')}  建议间隔: {profile.get('suggested_sync_interval_minutes')} 分钟")
        print(f"  摘要: {profile.get('summary')}\n")
    
    out_path = os.path.join(os.path.dirname(__file__), '..', 'cold_start_profiles.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    
    print(f"📄 群组画像已保存至 cold_start_profiles.json")

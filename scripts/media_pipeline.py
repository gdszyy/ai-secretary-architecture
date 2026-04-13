#!/usr/bin/env python3
"""
富媒体处理流水线 (MediaPipeline)

将 ParseEvaluator（评估是否值得解析）和 MediaParser（实际解析）串联。
在 Step2 消息拉取后，对每条包含富媒体的消息调用此流水线。

流程：
  消息 → 识别富媒体类型 → ParseEvaluator 评估 → 若值得解析 → MediaParser 解析 → 返回结构化结果
"""

import os
import json
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from media_parse_evaluator import evaluate_before_parse, ParseDecision
from media_parser import parse_media

# ──────────────────────────────────────────────
# 消息富媒体识别
# ──────────────────────────────────────────────

def extract_media_items(message: dict) -> list[dict]:
    """
    从一条 Lark 消息中提取所有富媒体项。
    返回格式：[{"media_type": "image|url|file", "content_hint": "...", "meta": {...}}]
    """
    items = []
    msg_type = message.get("type", "")
    text = message.get("text", "")
    raw_body = message.get("raw_body", "")

    # 1. 消息类型本身是图片
    if msg_type == "image":
        try:
            body = json.loads(raw_body) if raw_body else {}
            image_key = body.get("image_key", "")
        except Exception:
            image_key = ""
        items.append({
            "media_type": "image",
            "content_hint": f"image:{image_key}",
            "meta": {"image_key": image_key, "message_id": message.get("msg_id", "")}
        })

    # 2. 消息类型是文件
    elif msg_type == "file":
        try:
            body = json.loads(raw_body) if raw_body else {}
            file_name = body.get("file_name", "attachment")
            file_key = body.get("file_key", "")
        except Exception:
            file_name, file_key = "attachment", ""
        items.append({
            "media_type": "file",
            "content_hint": file_name,
            "meta": {"file_key": file_key, "message_id": message.get("msg_id", "")}
        })

    # 3. 文本消息中包含 URL
    if msg_type == "text" and text:
        urls = re.findall(r'https?://[^\s\u3000\u300c\u300d\uff08\uff09\u3001\u3002]+', text)
        for url in urls:
            items.append({
                "media_type": "url",
                "content_hint": url,
                "meta": {}
            })

    return items


# ──────────────────────────────────────────────
# 主流水线
# ──────────────────────────────────────────────

def process_message_media(
    message: dict,
    surrounding_messages: list[dict],
    project_context: Optional[dict] = None,
    current_thread_topic: Optional[str] = None,
) -> list[dict]:
    """
    对一条消息中的所有富媒体项执行"评估 → 解析"流水线。

    Returns:
        list of {
            "media_type": str,
            "content_hint": str,
            "decision": dict,       # ParseDecision 的字典形式
            "parse_result": str,    # 解析结果（若跳过则为 None）
        }
    """
    media_items = extract_media_items(message)
    if not media_items:
        return []

    results = []
    for item in media_items:
        media_type = item["media_type"]
        content_hint = item["content_hint"]
        meta = item["meta"]

        # Step 1: 评估
        decision = evaluate_before_parse(
            media_type=media_type,
            content_hint=content_hint,
            surrounding_messages=surrounding_messages,
            project_context=project_context,
            current_thread_topic=current_thread_topic,
        )

        parse_result = None
        if decision.should_parse:
            # Step 2: 解析
            parse_result = parse_media(
                media_type=media_type,
                content_hint=content_hint,
                parse_goal=decision.parse_goal,
                stop_condition=decision.stop_condition,
                message_id=meta.get("message_id"),
                image_key=meta.get("image_key"),
            )

        results.append({
            "media_type": media_type,
            "content_hint": content_hint,
            "decision": decision.to_dict(),
            "parse_result": parse_result,
        })

    return results


# ──────────────────────────────────────────────
# 集成测试：对真实群消息跑流水线
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 富媒体处理流水线集成测试 ===\n")

    # 加载 Step2 拉取的真实消息
    msgs_path = os.path.join(os.path.dirname(__file__), '..', 'cold_start_messages.json')
    with open(msgs_path, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    total_media = 0
    total_parsed = 0
    total_skipped = 0

    for chat_id, info in all_data.items():
        messages = info["messages"]
        name = info["name"]
        print(f"📋 群「{name}」共 {len(messages)} 条消息")

        for i, msg in enumerate(messages):
            # 取前后各 2 条作为上下文
            surrounding = messages[max(0, i-2): i] + messages[i+1: i+3]

            results = process_message_media(
                message=msg,
                surrounding_messages=surrounding,
                current_thread_topic=None,
            )

            for r in results:
                total_media += 1
                d = r["decision"]
                icon = "✅" if d["should_parse"] else "⏭️ "
                print(f"  [{icon}] [{r['media_type']}] {r['content_hint'][:60]}")
                print(f"       评分: {d['relevance_score']}/100  目标: {d['parse_goal'][:50]}")
                if d["should_parse"] and r["parse_result"]:
                    total_parsed += 1
                    print(f"       解析结果: {r['parse_result'][:100]}...")
                elif d["skip_reason"]:
                    total_skipped += 1
                    print(f"       跳过原因: {d['skip_reason'][:60]}")
                print()

    print(f"📊 统计：共发现 {total_media} 个富媒体项，解析 {total_parsed} 个，跳过 {total_skipped} 个")

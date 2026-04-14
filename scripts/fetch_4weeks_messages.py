#!/usr/bin/env python3
"""
拉取新增群组的 4 周历史消息，按周分段存储。
从最早一周（第1周）开始，到最近一周（第4周）。
"""
import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

LARK_APP_ID = os.environ["LARK_APP_ID"]
LARK_APP_SECRET = os.environ["LARK_APP_SECRET"]


def get_token():
    resp = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
    )
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]


def ts_to_str(ts_ms):
    """毫秒时间戳转可读字符串"""
    return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')


def extract_text(msg):
    """从消息中提取可读文本"""
    msg_type = msg.get("msg_type", "")
    body_str = msg.get("body", {}).get("content", "")
    try:
        body = json.loads(body_str)
    except Exception:
        return body_str or "[无内容]"

    if msg_type == "text":
        return body.get("text", "").strip()
    elif msg_type == "image":
        return f"[图片: {body.get('image_key', '')}]"
    elif msg_type == "file":
        return f"[文件: {body.get('file_name', '')}]"
    elif msg_type == "post":
        # 富文本，提取所有文本节点
        texts = []
        for line in body.get("content", []):
            for node in line:
                if node.get("tag") == "text":
                    texts.append(node.get("text", ""))
                elif node.get("tag") == "a":
                    texts.append(f"[链接:{node.get('href','')}]")
                elif node.get("tag") == "at":
                    texts.append(f"@{node.get('user_name','')}")
        return " ".join(texts).strip()
    elif msg_type == "sticker":
        return "[表情包]"
    else:
        return f"[{msg_type}]"


def fetch_messages_in_range(token, chat_id, start_ts_ms, end_ts_ms, max_msgs=500):
    """
    拉取指定时间范围内的消息。
    Lark API 按 page_token 翻页，消息按时间倒序返回，需要反转。
    """
    messages = []
    page_token = None
    # 转为秒级时间戳字符串（Lark API 要求）
    start_s = str(int(start_ts_ms // 1000))
    end_s = str(int(end_ts_ms // 1000))

    while True:
        params = {
            "container_id_type": "chat",
            "container_id": chat_id,
            "start_time": start_s,
            "end_time": end_s,
            "page_size": 50,
            "sort_type": "ByCreateTimeAsc",
        }
        if page_token:
            params["page_token"] = page_token

        resp = requests.get(
            "https://open.larksuite.com/open-apis/im/v1/messages",
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )
        data = resp.json()
        code = data.get("code", -1)

        if code == 230050:
            return messages, "HISTORY_RESTRICTED"
        if code != 0:
            err_msg = data.get("msg", "unknown")
            return messages, f"ERROR:{code}:{err_msg}"

        items = data.get("data", {}).get("items", [])
        for item in items:
            text = extract_text(item)
            sender_id = item.get("sender", {}).get("id", "?")[:12]
            create_time = item.get("create_time", "0")
            messages.append({
                "msg_id": item.get("message_id", ""),
                "sender_id": sender_id,
                "time": ts_to_str(create_time),
                "ts_ms": int(create_time),
                "type": item.get("msg_type", ""),
                "text": text,
            })

        has_more = data.get("data", {}).get("has_more", False)
        page_token = data.get("data", {}).get("page_token")
        if not has_more or len(messages) >= max_msgs:
            break
        time.sleep(0.3)  # 避免限流

    return messages, "OK"


if __name__ == "__main__":
    # 加载新增群列表
    group_list_path = os.path.join(os.path.dirname(__file__), '..', 'group_list.json')
    with open(group_list_path, 'r', encoding='utf-8') as f:
        group_data = json.load(f)
    new_groups = group_data["new_groups"]

    # 计算 4 周的时间分段（从 4 周前到现在，按周切分）
    now = datetime.now(tz=timezone.utc)
    weeks = []
    for i in range(4, 0, -1):  # 第1周最早，第4周最近
        week_end = now - timedelta(weeks=i - 1)
        week_start = now - timedelta(weeks=i)
        weeks.append({
            "week_num": 5 - i,  # 1=最早, 4=最近
            "label": f"第{5-i}周 ({week_start.strftime('%m/%d')}~{week_end.strftime('%m/%d')})",
            "start_ms": int(week_start.timestamp() * 1000),
            "end_ms": int(week_end.timestamp() * 1000),
        })

    print(f"时间范围：{weeks[0]['label']} → {weeks[-1]['label']}\n")

    token = get_token()
    all_results = {}

    for group in new_groups:
        chat_id = group["chat_id"]
        name = group.get("name", chat_id)
        print(f"\n{'='*60}")
        print(f"📋 群组：{name}")
        group_result = {"name": name, "chat_id": chat_id, "weeks": {}}

        for week in weeks:
            wk = week["week_num"]
            msgs, status = fetch_messages_in_range(
                token, chat_id,
                week["start_ms"], week["end_ms"]
            )
            print(f"  {week['label']}: {len(msgs)} 条消息  [{status}]")
            group_result["weeks"][str(wk)] = {
                "label": week["label"],
                "start_ms": week["start_ms"],
                "end_ms": week["end_ms"],
                "status": status,
                "message_count": len(msgs),
                "messages": msgs
            }
            time.sleep(0.5)

        all_results[chat_id] = group_result

    # 保存结果
    out_path = os.path.join(os.path.dirname(__file__), '..', 'history_4weeks.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n\n✅ 所有群历史消息已保存至 history_4weeks.json")

    # 统计摘要
    print("\n📊 统计摘要：")
    for chat_id, r in all_results.items():
        total = sum(w["message_count"] for w in r["weeks"].values())
        print(f"  {r['name']}: 共 {total} 条消息")

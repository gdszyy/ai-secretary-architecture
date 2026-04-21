#!/usr/bin/env python3
"""
逐周 LLM 提取关键信息与话题摘要。

提供两种使用方式：
1. 函数调用接口（供 run_weekly_report.py 实时调用）：
   from scripts.extract_weekly_insights import get_weekly_insights_for_modules
   insights = get_weekly_insights_for_modules("2026-16")

2. CLI 离线批量分析（读取本地 history_4weeks.json）：
   python3 extract_weekly_insights.py
"""
import os
import sys
import json
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

client = OpenAI()

# ---------------------------------------------------------------------------
# 飞书 API 配置（复用 daily_progress_updater.py 的凭据）
# ---------------------------------------------------------------------------

APP_ID     = os.environ.get("LARK_APP_ID",     "cli_a9d985cd40f89e1a")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "UNemS0zPnUuXhONgkuuprgdK3SrVx05T")

# 群组列表（chat_id → 群名），与 daily_progress_updater.py 保持一致
CHAT_GROUPS = {
    "oc_ba6f8baec0bd9566ed885d98cd3b8614": "XP产品设计",
    "oc_aba6f4b7f76c8bd6e72db298aa54b53c": "产运群",
    "oc_bfa55e46c000eb3943c2c07b989121f3": "小组长",
    "oc_266b6b295f4fb6e6ef5579ea372c7c1c": "设计稿优化对接",
    "oc_7f1872531b4664eadd4ba991cf485567": "GoToBet项目沟通群",
    "oc_bb4eb1c864720348de517027069de5a2": "风控运营合作",
    "oc_5b35ab3e1d6a407701c64df5a853c3df": "上线前前端优化需求",
    "oc_405bc9126a5ec41b5f77dd429e1731cb": "Lsport数据源",
}

# 模块 ID → 模块名（与 run_weekly_report.py 的 MODULE_NAMES 对齐）
MODULE_MAP = {
    "mod_data_ingestion":      "数据接入（Lsport/SR 数据源）",
    "mod_ls_ts_matching":      "Lsport-TS 赛事匹配",
    "mod_sr_ts_matching":      "SR-TS 赛事匹配",
    "mod_sports_betting_core": "体育投注核心（赔率/注单/结算）",
    "mod_casino":              "Casino 游戏平台",
    "mod_activity_platform":   "活动平台（Bonus/礼券/VIP）",
    "mod_ads_system":          "广告投放系统",
    "mod_uiux_design":         "UI/UX 设计",
    "mod_user_system":         "用户系统（注册/推荐/账户）",
    "mod_wallet_finance":      "钱包与财务（充值/提现/报表）",
    "mod_platform_setting":    "平台配置（菜单/多语言/法务）",
    "mod_im_cs":               "IM 客服系统",
}

API_INTERVAL = 0.5

# ---------------------------------------------------------------------------
# 飞书 API 工具（复用 daily_progress_updater.py 的实现）
# ---------------------------------------------------------------------------

_token_cache: Dict = {"token": None, "expires_at": 0}


def get_token() -> str:
    """获取飞书 tenant_access_token，带本地缓存"""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]
    r = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expires_at"] = now + data.get("expire", 7200) - 300
    return _token_cache["token"]


def lark_get(url: str, params: dict = None) -> dict:
    headers = {"Authorization": f"Bearer {get_token()}"}
    r = requests.get(url, headers=headers, params=params or {}, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_recent_messages(
    chat_id: str,
    start_ts_s: int,
    end_ts_s: int,
    max_msgs: int = 500,
) -> List[Dict]:
    """
    拉取指定时间范围内的群消息（复用 daily_progress_updater.py 的实现）。

    Args:
        chat_id: 飞书群组 ID
        start_ts_s: 起始时间戳（秒）
        end_ts_s: 结束时间戳（秒）
        max_msgs: 最大消息数量

    Returns:
        消息列表（飞书原始格式）
    """
    url = "https://open.larksuite.com/open-apis/im/v1/messages"
    messages = []
    page_token = None

    while len(messages) < max_msgs:
        params = {
            "container_id_type": "chat",
            "container_id": chat_id,
            "start_time": str(start_ts_s),
            "end_time": str(end_ts_s),
            "page_size": 50,
            "sort_type": "ByCreateTimeAsc",
        }
        if page_token:
            params["page_token"] = page_token

        try:
            data = lark_get(url, params)
            code = data.get("code", -1)
            if code == 230050:
                logger.warning("群 %s 历史消息受限（超过30天）", chat_id)
                break
            if code != 0:
                logger.warning("拉取消息失败: chat=%s, code=%s", chat_id, code)
                break

            items = data.get("data", {}).get("items", [])
            messages.extend(items)

            if not data.get("data", {}).get("has_more"):
                break
            page_token = data.get("data", {}).get("page_token")
            time.sleep(API_INTERVAL)
        except Exception as e:
            logger.error("拉取消息异常: %s", str(e))
            break

    return messages


def _normalize_messages(raw_messages: List[Dict]) -> List[Dict]:
    """
    将飞书原始消息格式转换为 extract_weekly_insights 期望的简化格式：
    { time, sender_id, text }
    """
    import re
    import json as _json
    result = []
    for m in raw_messages:
        msg_type = m.get("msg_type", "")
        body_str = m.get("body", {}).get("content", "")
        try:
            body = _json.loads(body_str)
        except Exception:
            body = {}

        if msg_type == "text":
            text = body.get("text", "")
            text = re.sub(r"<at[^>]*>[^<]*</at>", "@someone", text)
            text = text.strip()
        elif msg_type == "post":
            texts = []
            for line in body.get("content", []):
                for node in line:
                    if node.get("tag") == "text":
                        texts.append(node.get("text", ""))
                    elif node.get("tag") == "at":
                        texts.append(f"@{node.get('user_name', '')}")
            text = " ".join(texts).strip()
        else:
            text = ""

        if not text:
            continue

        ts_raw = m.get("create_time", "0")
        try:
            ts_s = int(ts_raw)
            time_str = datetime.fromtimestamp(ts_s, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        except Exception:
            time_str = ts_raw

        sender_id = m.get("sender", {}).get("id", "unknown")

        result.append({
            "time": time_str,
            "sender_id": sender_id,
            "text": text,
        })
    return result


def _week_str_to_timestamps(week_str: str):
    """
    将 YYYY-WW 格式的周标识转换为该周二 00:00 到下周二 00:00 的时间戳（秒）。
    与 run_weekly_report.py 的 week_str_to_dates 保持一致（以周二为边界）。

    Returns:
        (start_ts_s, end_ts_s): 起止时间戳（秒，UTC）
    """
    year, week_num = int(week_str.split("-")[0]), int(week_str.split("-")[1])
    monday = datetime.fromisocalendar(year, week_num, 1)
    tuesday_start = monday + timedelta(days=1)  # 周二 00:00
    tuesday_end = tuesday_start + timedelta(days=7)  # 下周二 00:00

    # 转为 UTC 时间戳（假设日期为 UTC+8，转为 UTC）
    tz_utc8 = timezone(timedelta(hours=8))
    start_dt = datetime(tuesday_start.year, tuesday_start.month, tuesday_start.day,
                        0, 0, 0, tzinfo=tz_utc8)
    end_dt = datetime(tuesday_end.year, tuesday_end.month, tuesday_end.day,
                      0, 0, 0, tzinfo=tz_utc8)

    return int(start_dt.timestamp()), int(end_dt.timestamp())


# ---------------------------------------------------------------------------
# LLM 洞察提取（原有逻辑，用于离线批量分析）
# ---------------------------------------------------------------------------

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

# 用于 get_weekly_insights_for_modules 的模块归因 Prompt
MODULE_INSIGHTS_SYSTEM_PROMPT = """你是一个 AI 项目秘书，负责从群聊记录中提取对模块进度有推进作用的关键话题。

群组名称：{group_name}
已知模块列表：
{module_list}

请分析本周群聊消息，提取与各模块相关的关键洞察，输出以下 JSON：
{{
  "module_insights": {{
    "mod_xxx": ["话题摘要1（1-2句话，说清楚决策/进展/风险）", "话题摘要2", ...],
    ...
  }}
}}

要求：
- 只输出有实质内容的模块（决策、里程碑、风险/阻塞等高价值事实）
- 每条洞察简洁精炼（1-2句话），保留关键信息
- 忽略常规日常闲聊、纯表情包、无实质内容的消息
- 群名（{group_name}）是重要的领域边界上下文，请据此判断消息归属
- 必须输出合法 JSON，不要有其他文字
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
    """对单个群单周的消息进行 LLM 提取（供离线批量分析使用）"""
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


# ---------------------------------------------------------------------------
# 新增：实时拉取接口（供 run_weekly_report.py 调用）
# ---------------------------------------------------------------------------

def get_weekly_insights_for_modules(week_str: str) -> Dict[str, List[str]]:
    """
    实时拉取指定周的群消息，并通过 LLM 提取各模块的关键洞察。

    本函数复用 daily_progress_updater.py 中的消息拉取逻辑（get_token /
    fetch_recent_messages），对 CHAT_GROUPS 中所有群组拉取指定周的消息，
    然后调用 LLM 归因到具体模块，返回结构化的模块洞察字典。

    Args:
        week_str: 周标识，格式为 "YYYY-WW"，例如 "2026-16"

    Returns:
        模块洞察字典，格式为：
        {
            "mod_data_ingestion": ["话题摘要1", "话题摘要2"],
            "mod_uiux_design": ["话题摘要1"],
            ...
        }
        若某模块无相关洞察，则不出现在字典中。
        若拉取或提取失败，返回空字典 {}。
    """
    logger.info("get_weekly_insights_for_modules: 开始拉取 %s 周的群聊洞察", week_str)

    try:
        start_ts_s, end_ts_s = _week_str_to_timestamps(week_str)
    except Exception as e:
        logger.error("week_str 解析失败: %s, 错误: %s", week_str, e)
        return {}

    week_label = week_str
    module_list_str = "\n".join(f"- {mid}: {name}" for mid, name in MODULE_MAP.items())

    # 汇总所有群组的模块洞察
    merged_insights: Dict[str, List[str]] = {}

    for chat_id, group_name in CHAT_GROUPS.items():
        logger.info("  拉取群 [%s] 消息...", group_name)

        try:
            raw_messages = fetch_recent_messages(chat_id, start_ts_s, end_ts_s)
        except Exception as e:
            logger.warning("  群 [%s] 消息拉取失败: %s，跳过", group_name, e)
            continue

        if not raw_messages:
            logger.info("  群 [%s] 本周无消息，跳过", group_name)
            continue

        # 转换为简化格式并生成文本
        normalized = _normalize_messages(raw_messages)
        if not normalized:
            logger.info("  群 [%s] 无有效文本消息，跳过", group_name)
            continue

        msg_text = messages_to_text(normalized)
        logger.info("  群 [%s] 共 %d 条有效消息，开始 LLM 提取...", group_name, len(normalized))

        user_prompt = f"""群组名称：{group_name}
时间范围：{week_label}
消息总数：{len(normalized)} 条

以下是本周的群聊记录：

{msg_text}

请提取各模块的关键洞察并输出 JSON。"""

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": MODULE_INSIGHTS_SYSTEM_PROMPT.format(
                            group_name=group_name,
                            module_list=module_list_str,
                        )
                    },
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            result = json.loads(response.choices[0].message.content)
            group_insights = result.get("module_insights", {})

            # 合并到总字典
            for mod_id, insights_list in group_insights.items():
                if mod_id in MODULE_MAP and insights_list:
                    merged_insights.setdefault(mod_id, []).extend(insights_list)

            logger.info("  群 [%s] 提取完成，涉及 %d 个模块", group_name, len(group_insights))

        except Exception as e:
            logger.warning("  群 [%s] LLM 提取失败: %s，跳过", group_name, e)
            continue

        time.sleep(API_INTERVAL)

    logger.info(
        "get_weekly_insights_for_modules 完成：%s 周，共 %d 个模块有洞察",
        week_str, len(merged_insights)
    )
    return merged_insights


# ---------------------------------------------------------------------------
# CLI 入口（离线批量分析，向后兼容）
# ---------------------------------------------------------------------------

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

"""
多对话分离算法实现 (Thread Separator)
======================================
功能：
  1. 接收一批群聊消息（含 id / sender / time / content / reply_to 字段）。
  2. 第一阶段：基于规则与实体的初步聚类（时间窗口切分 + @提及图谱 + 实体匹配）。
  3. 第二阶段：调用 LLM 对初步聚类结果进行深度上下文分离，输出标准 ThreadEvent 列表。
  4. 过滤低置信度线程（confidence < 0.8），标记为 Needs_Human_Review。
  5. 过滤无效线程（intent 为 casual_chat / other），仅保留高价值线程。

环境变量要求（在 .env 中配置）：
  - DASHSCOPE_API_KEY: 通义千问 API Key（阿里云百炼平台获取）
  - QWEN_MODEL: (可选) 模型名称，默认 qwen-plus

数据结构：
  输入消息格式：
    {
      "id": "m1",
      "sender": "Alice",
      "time": "2026-04-16T10:00:00Z",  # ISO 8601，可选
      "content": "支付网关在回调时报了500错误...",
      "reply_to": "m0"  # 可选，被回复的消息 ID
    }

  输出 ThreadEvent 格式：
    {
      "thread_id": "t_20260416_1001",
      "topic": "支付网关签名验证失败导致500错误",
      "participants": ["Alice", "Charlie"],
      "messages": [{"id": "m1", "content": "..."}],
      "intent": "bug_report",
      "confidence": 0.98,
      "cross_thread_messages": [],
      "extracted_entities": {"module": "支付网关", "error_code": "500"},
      "created_at": "2026-04-16T10:05:00Z",
      "needs_review": false
    }

用法示例：
  python3 thread_separator.py --input messages.json --output threads.json
  python3 thread_separator.py --demo  # 运行内置演示场景
"""

import os
import sys
import json
import argparse
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from openai import OpenAI

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("thread_separator")

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# LLM 配置
_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_QWEN_DEFAULT_MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")

# 时间窗口：超过此间隔（分钟）视为新 Session
SESSION_GAP_MINUTES = 30

# 置信度阈值：低于此值标记为 Needs_Human_Review
CONFIDENCE_THRESHOLD = 0.8

# 无效意图类型（过滤掉，不推入缓冲池）
INVALID_INTENTS = {"casual_chat", "other"}

# 项目实体关键词库（模块名、功能名等）
# 实际部署时应从 project_context.json 动态加载
PROJECT_ENTITY_KEYWORDS = [
    # 模块名
    "支付", "用户系统", "活动中心", "游戏", "购物车", "菜单", "Bet Slip",
    "登录", "注册", "搜索", "推荐", "通知", "消息", "钱包", "提现", "充值",
    "报表", "数据", "权限", "配置", "网关", "接口", "缓存", "数据库",
    # 技术术语
    "500", "404", "OOM", "crash", "崩溃", "白屏", "闪退", "超时",
    "Redis", "MySQL", "PostgreSQL", "Nginx", "Docker", "K8s",
    # 业务术语
    "EPAY", "微信支付", "支付宝", "iOS", "Android", "H5", "Web",
]

# ---------------------------------------------------------------------------
# LLM 调用封装
# ---------------------------------------------------------------------------

def call_llm(system_prompt: str, user_content: str, model: str = None) -> str:
    """调用通义千问 LLM，返回纯文本响应。"""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "缺少 DASHSCOPE_API_KEY 环境变量。\n"
            "请前往 https://bailian.console.aliyun.com/ 创建 API Key 并配置。"
        )
    client = OpenAI(api_key=api_key, base_url=_QWEN_BASE_URL)
    model = model or _QWEN_DEFAULT_MODEL
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,  # 低温度保证输出稳定性
    )
    return resp.choices[0].message.content.strip()


def parse_llm_json(raw: str) -> dict:
    """解析 LLM 返回的 JSON，处理 markdown 代码块包裹的情况。"""
    if "```" in raw:
        # 提取 ```json ... ``` 或 ``` ... ``` 中的内容
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if match:
            raw = match.group(1)
    return json.loads(raw.strip())


# ---------------------------------------------------------------------------
# 第一阶段：基于规则与实体的初步聚类
# ---------------------------------------------------------------------------

def parse_time(time_str: Optional[str]) -> Optional[datetime]:
    """解析 ISO 8601 时间字符串，返回 datetime 对象。"""
    if not time_str:
        return None
    try:
        # 支持带 Z 的 UTC 时间
        return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_entities(content: str) -> List[str]:
    """从消息内容中提取项目实体关键词。"""
    found = []
    content_lower = content.lower()
    for keyword in PROJECT_ENTITY_KEYWORDS:
        if keyword.lower() in content_lower:
            found.append(keyword)
    return found


def build_mention_graph(messages: List[Dict]) -> Dict[str, List[str]]:
    """
    构建消息间的关联图。
    返回 {message_id: [related_message_ids]} 的邻接表。
    """
    graph = defaultdict(list)
    for msg in messages:
        msg_id = msg["id"]
        # 显式 reply_to 关系
        if msg.get("reply_to"):
            graph[msg_id].append(msg["reply_to"])
            graph[msg["reply_to"]].append(msg_id)
        # @提及关系（简单匹配：@发送者名字）
        content = msg.get("content", "")
        for other_msg in messages:
            if other_msg["id"] == msg_id:
                continue
            sender = other_msg.get("sender", "")
            if sender and f"@{sender}" in content:
                graph[msg_id].append(other_msg["id"])
    return graph


def split_by_time_window(
    messages: List[Dict], gap_minutes: int = SESSION_GAP_MINUTES
) -> List[List[Dict]]:
    """
    按时间窗口将消息切分为多个 Session。
    若消息无时间戳，则视为单一 Session。
    """
    if not messages:
        return []

    # 检查是否有时间戳
    has_time = any(msg.get("time") for msg in messages)
    if not has_time:
        return [messages]

    sessions = []
    current_session = [messages[0]]
    gap = timedelta(minutes=gap_minutes)

    for msg in messages[1:]:
        prev_time = parse_time(current_session[-1].get("time"))
        curr_time = parse_time(msg.get("time"))

        if prev_time and curr_time and (curr_time - prev_time) > gap:
            sessions.append(current_session)
            current_session = [msg]
        else:
            current_session.append(msg)

    if current_session:
        sessions.append(current_session)

    return sessions


def preprocess_messages(messages: List[Dict]) -> Dict:
    """
    第一阶段预处理：提取实体、构建关联图，生成初步聚类线索。
    返回包含预处理信息的上下文字典，供第二阶段 LLM 使用。
    """
    entity_map = {}  # {message_id: [entities]}
    for msg in messages:
        entities = extract_entities(msg.get("content", ""))
        if entities:
            entity_map[msg["id"]] = entities

    mention_graph = build_mention_graph(messages)

    # 生成初步聚类线索（相同实体的消息倾向于同一 Thread）
    entity_groups = defaultdict(list)  # {entity: [message_ids]}
    for msg_id, entities in entity_map.items():
        for entity in entities:
            entity_groups[entity].append(msg_id)

    return {
        "entity_map": entity_map,
        "mention_graph": dict(mention_graph),
        "entity_groups": dict(entity_groups),
    }


# ---------------------------------------------------------------------------
# 第二阶段：基于 LLM 的深度上下文分离
# ---------------------------------------------------------------------------

THREAD_SEPARATION_SYSTEM_PROMPT = """
你是一个专门用于处理群聊消息并进行对话分离（Thread Separation）的AI助手。
你的任务是将给定的一组混杂的群聊消息，分离成若干个独立的话题线程（Thread）。

【输入格式】
一段群聊消息列表，每条消息包含 id, sender, time（可选）, content, reply_to（可选）。
以及第一阶段预处理提供的实体聚类线索（entity_groups）和消息关联图（mention_graph）。

【任务要求】
1. 仔细阅读所有消息，理解其上下文和@引用关系。
2. 识别出群聊中同时进行的几个独立讨论话题（Thread）。
3. 将每条消息分配到对应的话题线程中。
   - 若一条消息同时涉及多个话题（跨线程消息），请将其分配到最主要的话题，并在 cross_thread_messages 字段中标注其 ID。
4. 提取每个线程的核心意图和相关实体（如模块、参与者）。
5. 评估每个线程的置信度（0-1）。

【意图类型枚举】
- bug_report: Bug 报告或故障排查
- feature_request: 新功能需求讨论
- feature_discussion: 功能方案讨论（尚未形成明确需求）
- progress_update: 进度同步或状态确认
- status_check: 状态查询
- decision_record: 决策记录
- risk_escalation: 风险上报
- memo: 备忘或提醒
- casual_chat: 日常闲聊（无业务价值）
- other: 其他

【处理规则】
1. 实体聚类：优先参考 entity_groups 中的实体聚类线索进行初步关联。
2. 上下文连贯性：考虑时间先后顺序、reply_to 关系和 @提及关系。
3. 话题漂移：如果一个对话从Bug修复明显转变为讨论全新的需求，应拆分为两个关联的Thread。
4. 单条消息多意图：如果一条消息同时回复了多个话题，尽量将其归入主要话题，或在两个Thread中都包含该消息ID（允许消息重叠）。
5. 孤立消息：如果某条消息无法归入任何已识别的Thread，单独创建一个Thread，intent 设为 other。

【输出格式】
严格输出以下 JSON 格式，不要包含任何其他说明文字：

{
  "threads": [
    {
      "thread_id": "t1",
      "topic": "话题的简短描述（15字以内）",
      "participants": ["参与者1", "参与者2"],
      "message_ids": ["m1", "m3", "m5"],
      "intent": "bug_report",
      "confidence": 0.97,
      "cross_thread_messages": [],
      "extracted_entities": {
        "module": "模块名称",
        "error_code": "错误码（如有）",
        "keywords": ["关键词1", "关键词2"]
      }
    }
  ]
}

【Few-shot 示例】
输入消息:
[
  {"id": "m1", "sender": "Alice", "content": "服务器宕机了，日志报OOM。"},
  {"id": "m2", "sender": "Bob", "content": "明天的会议几点开始？"},
  {"id": "m3", "sender": "Charlie", "content": "@Alice 我看一下，是哪台服务器？"},
  {"id": "m4", "sender": "Alice", "content": "@Charlie 是prod-01，刚重启了但还是报错。"},
  {"id": "m5", "sender": "Dave", "content": "@Bob 下午2点，会议室A。"}
]

输出:
{
  "threads": [
    {
      "thread_id": "t1",
      "topic": "服务器OOM故障排查",
      "participants": ["Alice", "Charlie"],
      "message_ids": ["m1", "m3", "m4"],
      "intent": "bug_report",
      "confidence": 0.97,
      "cross_thread_messages": [],
      "extracted_entities": {"module": "服务器", "error_code": "OOM", "keywords": ["prod-01"]}
    },
    {
      "thread_id": "t2",
      "topic": "会议时间确认",
      "participants": ["Bob", "Dave"],
      "message_ids": ["m2", "m5"],
      "intent": "memo",
      "confidence": 0.95,
      "cross_thread_messages": [],
      "extracted_entities": {"module": null, "error_code": null, "keywords": ["会议室A"]}
    }
  ]
}
"""


def separate_threads_with_llm(
    messages: List[Dict],
    preprocess_ctx: Dict,
) -> List[Dict]:
    """
    调用 LLM 进行第二阶段对话分离。
    返回原始的 threads 列表（含 message_ids，未展开为完整消息对象）。
    """
    # 构建 LLM 输入
    user_content = json.dumps(
        {
            "messages": messages,
            "entity_groups": preprocess_ctx.get("entity_groups", {}),
            "mention_graph": preprocess_ctx.get("mention_graph", {}),
        },
        ensure_ascii=False,
        indent=2,
    )

    logger.info("调用 LLM 进行对话分离，消息数量: %d", len(messages))
    raw = call_llm(THREAD_SEPARATION_SYSTEM_PROMPT, user_content)

    try:
        result = parse_llm_json(raw)
        threads = result.get("threads", [])
        logger.info("LLM 识别出 %d 个线程", len(threads))
        return threads
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("LLM 返回了非预期内容: %s\n原始内容: %s", e, raw)
        return []


# ---------------------------------------------------------------------------
# 结果后处理：构建标准 ThreadEvent
# ---------------------------------------------------------------------------

def build_thread_events(
    raw_threads: List[Dict],
    messages: List[Dict],
    session_index: int = 0,
) -> List[Dict]:
    """
    将 LLM 返回的原始 threads 转换为标准 ThreadEvent 格式。
    - 展开 message_ids 为完整消息对象
    - 添加 needs_review 标记
    - 添加 created_at 时间戳
    """
    # 构建消息 ID 到消息对象的映射
    msg_map = {msg["id"]: msg for msg in messages}

    thread_events = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for i, thread in enumerate(raw_threads):
        message_ids = thread.get("message_ids", [])
        full_messages = [
            {"id": mid, "content": msg_map[mid].get("content", "")}
            for mid in message_ids
            if mid in msg_map
        ]

        confidence = thread.get("confidence", 0.0)
        intent = thread.get("intent", "other")

        thread_event = {
            "thread_id": f"t_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{session_index * 100 + i + 1:04d}",
            "topic": thread.get("topic", ""),
            "participants": thread.get("participants", []),
            "messages": full_messages,
            "intent": intent,
            "confidence": confidence,
            "cross_thread_messages": thread.get("cross_thread_messages", []),
            "extracted_entities": thread.get("extracted_entities", {}),
            "created_at": now_str,
            "needs_review": confidence < CONFIDENCE_THRESHOLD,
        }
        thread_events.append(thread_event)

    return thread_events


def filter_thread_events(thread_events: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    过滤 ThreadEvent 列表：
    - 返回 (high_value_threads, review_pending_threads)
    - high_value_threads: confidence >= 0.8 且 intent 不在 INVALID_INTENTS 中
    - review_pending_threads: confidence < 0.8 的线程（需人工审核）
    """
    high_value = []
    review_pending = []

    for event in thread_events:
        if event.get("needs_review"):
            review_pending.append(event)
        elif event.get("intent") in INVALID_INTENTS:
            logger.info("过滤无效线程: thread_id=%s, intent=%s", event["thread_id"], event["intent"])
        else:
            high_value.append(event)

    return high_value, review_pending


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def separate(
    messages: List[Dict],
    session_gap_minutes: int = SESSION_GAP_MINUTES,
) -> Dict:
    """
    主处理函数：接收一批群聊消息，执行完整的多对话分离流程。

    Args:
        messages: 群聊消息列表，每条消息包含 id/sender/content，可选 time/reply_to。
        session_gap_minutes: 时间窗口间隔（分钟），超过此间隔视为新 Session。

    Returns:
        结构化结果字典：
          - high_value_threads: 高价值线程列表（可直接推入信息缓冲池）
          - review_pending_threads: 待人工审核线程列表
          - stats: 统计信息
    """
    if not messages:
        return {"high_value_threads": [], "review_pending_threads": [], "stats": {}}

    # 第一步：按时间窗口切分 Session
    sessions = split_by_time_window(messages, gap_minutes=session_gap_minutes)
    logger.info("消息切分为 %d 个 Session", len(sessions))

    all_thread_events = []

    for session_idx, session_msgs in enumerate(sessions):
        logger.info("处理 Session %d，消息数量: %d", session_idx + 1, len(session_msgs))

        # 第二步：第一阶段预处理（实体提取 + 关联图构建）
        preprocess_ctx = preprocess_messages(session_msgs)

        # 第三步：第二阶段 LLM 分离
        raw_threads = separate_threads_with_llm(session_msgs, preprocess_ctx)

        # 第四步：构建标准 ThreadEvent
        thread_events = build_thread_events(raw_threads, session_msgs, session_idx)
        all_thread_events.extend(thread_events)

    # 第五步：过滤
    high_value, review_pending = filter_thread_events(all_thread_events)

    stats = {
        "total_messages": len(messages),
        "total_sessions": len(sessions),
        "total_threads": len(all_thread_events),
        "high_value_threads": len(high_value),
        "review_pending_threads": len(review_pending),
        "filtered_threads": len(all_thread_events) - len(high_value) - len(review_pending),
    }

    logger.info(
        "分离完成: 总线程=%d, 高价值=%d, 待审核=%d, 已过滤=%d",
        stats["total_threads"],
        stats["high_value_threads"],
        stats["review_pending_threads"],
        stats["filtered_threads"],
    )

    return {
        "high_value_threads": high_value,
        "review_pending_threads": review_pending,
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# 内置演示场景
# ---------------------------------------------------------------------------

DEMO_MESSAGES = [
    {
        "id": "m1",
        "sender": "Alice",
        "time": "2026-04-16T10:00:00Z",
        "content": "支付网关在回调时报了500错误，签名验证一直失败",
        "reply_to": None,
    },
    {
        "id": "m2",
        "sender": "Bob",
        "time": "2026-04-16T10:01:00Z",
        "content": "登录页面的按钮颜色和设计稿不一致，需要改一下",
        "reply_to": None,
    },
    {
        "id": "m3",
        "sender": "Charlie",
        "time": "2026-04-16T10:02:00Z",
        "content": "@Alice 我在沙箱环境也复现了，是HMAC-SHA256的密钥配置问题",
        "reply_to": "m1",
    },
    {
        "id": "m4",
        "sender": "Dave",
        "time": "2026-04-16T10:03:00Z",
        "content": "@Bob 按钮颜色我来改，是哪个页面？",
        "reply_to": "m2",
    },
    {
        "id": "m5",
        "sender": "Alice",
        "time": "2026-04-16T10:04:00Z",
        "content": "@Charlie 对，生产环境的密钥没有同步更新，我现在去修",
        "reply_to": "m3",
    },
    {
        "id": "m6",
        "sender": "Bob",
        "time": "2026-04-16T10:05:00Z",
        "content": "@Dave 是登录页面，主按钮应该是 #FF6B35 但现在是 #FF5722",
        "reply_to": "m4",
    },
]


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="多对话分离工具：将混杂群聊消息分离为独立话题线程"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="输入消息 JSON 文件路径（包含消息列表）",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出结果 JSON 文件路径（默认输出到 stdout）",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="运行内置演示场景（双线程混杂：支付Bug + UI调整）",
    )
    parser.add_argument(
        "--session-gap",
        type=int,
        default=SESSION_GAP_MINUTES,
        help=f"时间窗口间隔（分钟），默认 {SESSION_GAP_MINUTES}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="跳过 LLM 调用，仅输出预处理结果（用于测试）",
    )

    args = parser.parse_args()

    # 加载消息
    if args.demo:
        messages = DEMO_MESSAGES
        logger.info("使用内置演示场景，共 %d 条消息", len(messages))
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 支持直接传入列表或包含 messages 字段的对象
            messages = data if isinstance(data, list) else data.get("messages", [])
        logger.info("从文件加载 %d 条消息: %s", len(messages), args.input)
    else:
        # 从 stdin 读取
        try:
            data = json.load(sys.stdin)
            messages = data if isinstance(data, list) else data.get("messages", [])
        except json.JSONDecodeError:
            parser.error("请通过 --input 指定输入文件，或通过 stdin 传入 JSON 格式的消息列表")
            return

    if args.dry_run:
        # 仅输出预处理结果
        sessions = split_by_time_window(messages, args.session_gap)
        result = {
            "sessions": [
                {
                    "session_index": i,
                    "message_count": len(s),
                    "preprocess": preprocess_messages(s),
                }
                for i, s in enumerate(sessions)
            ]
        }
    else:
        result = separate(messages, session_gap_minutes=args.session_gap)

    # 输出结果
    output_str = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        logger.info("结果已写入: %s", args.output)
    else:
        print(output_str)


if __name__ == "__main__":
    main()

"""
lark_qa_handler.py
==================
AI 秘书问答系统 — 核心处理器

功能：
  - 检测飞书消息中是否 @了机器人（或 p2p 私聊）
  - 通过 LLM 解析问题意图，路由到对应信息源
  - 从 Bitable / Meegle 获取数据并生成自然语言回答
  - 调用 qa_cache 进行缓存匹配和日志记录

信息源路由：
  route:bitable_topics      → 待跟进话题表（话题进度、状态）
  route:bitable_features    → 功能表（功能验收状态）
  route:bitable_modules     → 模块表（模块整体状态）
  route:meegle_defects      → Meegle 缺陷表
  route:meegle_tasks        → Meegle 任务表
  route:meegle_requirements → Meegle 需求表
  route:multi               → 多源联合查询（问题跨多个信息源）

触发条件：
  - 群聊中消息的 mentions 字段包含机器人的 open_id
  - p2p 私聊消息（chat_type == "p2p"）

环境变量：
  LARK_APP_ID, LARK_APP_SECRET   飞书应用凭证
  BITABLE_BASE_ID                Bitable 应用 Token
  BITABLE_TABLE_ID               待跟进话题表 ID
  BITABLE_TABLE_FEATURES         功能表 ID（默认 tblLzX7wqGWFr9KP）
  BITABLE_TABLE_MODULES          模块表 ID（默认 tblaDW4D2hQS2xCw）
  BITABLE_TABLE_MEEGLE_DEFECTS   Meegle 缺陷表 ID（默认 tblLmzknrXtzhGFc）
  BITABLE_TABLE_MEEGLE_TASKS     Meegle 任务表 ID（默认 tblzyH3DKSz9IAG9）
  BITABLE_TABLE_MEEGLE_REQS      Meegle 需求表 ID（默认 tblO4wA2agKU1ZSP）
  DASHSCOPE_API_KEY              通义千问 API Key
  QWEN_MODEL                     模型名称（默认 qwen-plus）
"""

import os
import json
import logging
import re
from typing import Optional, Dict, List, Any

from openai import OpenAI

logger = logging.getLogger("ai_secretary.qa_handler")

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")

# Bitable 表 ID 配置（带默认值）
_BASE_ID = os.environ.get("BITABLE_BASE_ID", "CyDxbUQGGa3N2NsVanMjqdjxp6e")
_TABLE_TOPICS    = os.environ.get("BITABLE_TABLE_ID",             "tblKscoaGp6VwhQe")
_TABLE_FEATURES  = os.environ.get("BITABLE_TABLE_FEATURES",       "tblLzX7wqGWFr9KP")
_TABLE_MODULES   = os.environ.get("BITABLE_TABLE_MODULES",        "tblaDW4D2hQS2xCw")
_TABLE_M_DEFECTS = os.environ.get("BITABLE_TABLE_MEEGLE_DEFECTS", "tblLmzknrXtzhGFc")
_TABLE_M_TASKS   = os.environ.get("BITABLE_TABLE_MEEGLE_TASKS",   "tblzyH3DKSz9IAG9")
_TABLE_M_REQS    = os.environ.get("BITABLE_TABLE_MEEGLE_REQS",    "tblO4wA2agKU1ZSP")

# 路由名称 → 表 ID 映射
ROUTE_TABLE_MAP = {
    "route:bitable_topics":      _TABLE_TOPICS,
    "route:bitable_features":    _TABLE_FEATURES,
    "route:bitable_modules":     _TABLE_MODULES,
    "route:meegle_defects":      _TABLE_M_DEFECTS,
    "route:meegle_tasks":        _TABLE_M_TASKS,
    "route:meegle_requirements": _TABLE_M_REQS,
}

# 路由名称 → 中文描述
ROUTE_LABEL = {
    "route:bitable_topics":      "待跟进话题",
    "route:bitable_features":    "功能表",
    "route:bitable_modules":     "模块表",
    "route:meegle_defects":      "Meegle 缺陷",
    "route:meegle_tasks":        "Meegle 任务",
    "route:meegle_requirements": "Meegle 需求",
    "route:multi":               "多源联合",
    "route:unknown":             "未知",
}

# ---------------------------------------------------------------------------
# LLM 客户端（单例）
# ---------------------------------------------------------------------------
_llm_client: Optional[OpenAI] = None

def _get_llm_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "缺少 DASHSCOPE_API_KEY 环境变量。\n"
                "请前往 https://bailian.console.aliyun.com/ 创建 API Key 并配置。"
            )
        _llm_client = OpenAI(api_key=api_key, base_url=_QWEN_BASE_URL)
    return _llm_client


# ---------------------------------------------------------------------------
# Bitable 数据获取
# ---------------------------------------------------------------------------
def _get_bitable_token() -> str:
    """获取飞书 tenant_access_token。"""
    import requests as _requests
    app_id = os.environ.get("LARK_APP_ID", "cli_a9d985cd40f89e1a")
    app_secret = os.environ.get("LARK_APP_SECRET", "")
    resp = _requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    return resp.json().get("tenant_access_token", "")


def _fetch_bitable_records(table_id: str, max_records: int = 200) -> List[Dict]:
    """从 Bitable 指定表拉取全量记录（最多 max_records 条）。"""
    import requests as _requests
    token = _get_bitable_token()
    if not token:
        logger.error("获取飞书 token 失败，无法查询 Bitable")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    base_url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{_BASE_ID}/tables/{table_id}/records"
    all_records: List[Dict] = []
    page_token = ""

    while len(all_records) < max_records:
        params: Dict[str, Any] = {"page_size": min(100, max_records - len(all_records))}
        if page_token:
            params["page_token"] = page_token
        try:
            resp = _requests.get(base_url, headers=headers, params=params, timeout=15)
            data = resp.json()
            items = data.get("data", {}).get("items", [])
            all_records.extend(items)
            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data.get("data", {}).get("page_token", "")
        except Exception as e:
            logger.error("拉取 Bitable 记录失败 table=%s: %s", table_id, e)
            break

    return all_records


def _records_to_text(records: List[Dict], key_fields: List[str]) -> str:
    """将 Bitable 记录转换为 LLM 可读的文本摘要。"""
    lines = []
    for i, rec in enumerate(records, 1):
        fields = rec.get("fields", {})
        parts = []
        for k in key_fields:
            v = fields.get(k, "")
            if isinstance(v, list):
                # 飞书文本字段有时返回 [{"text": "..."}] 格式
                v = "".join(seg.get("text", "") if isinstance(seg, dict) else str(seg) for seg in v)
            if v:
                parts.append(f"{k}={v}")
        if parts:
            lines.append(f"{i}. " + " | ".join(parts))
    return "\n".join(lines) if lines else "（无数据）"


# ---------------------------------------------------------------------------
# 意图路由解析
# ---------------------------------------------------------------------------
_ROUTE_SYSTEM_PROMPT = """你是 AI 秘书的意图路由器。根据用户问题，判断应该查询哪些信息源，并提取关键词。

可选信息源：
- route:bitable_topics      → 话题进度、风险阻塞、决策、里程碑、项目整体状态
- route:bitable_features    → 功能验收、功能状态、功能上线、功能开发进度
- route:bitable_modules     → 模块整体状态、模块负责人、模块优先级
- route:meegle_defects      → 缺陷/Bug 数量、缺陷状态、缺陷优先级
- route:meegle_tasks        → 任务完成情况、任务工时、任务进度
- route:meegle_requirements → 需求状态、需求计划、需求关联
- route:multi               → 问题需要跨多个信息源联合回答

返回 JSON 格式（不要 markdown 代码块）：
{
  "routes": ["route:xxx", ...],
  "keywords": ["关键词1", "关键词2"],
  "summary": "一句话描述问题意图"
}

规则：
- routes 最多 3 个，按相关性排序
- keywords 用于在数据中精确筛选，提取模块名/功能名/需求名等实体词
- 如果问题非常宽泛（如"项目整体情况"），routes 填 ["route:multi"]
"""

def _parse_intent(question: str) -> Dict:
    """
    用 LLM 解析问题意图，返回路由和关键词。
    返回格式：{"routes": [...], "keywords": [...], "summary": "..."}
    """
    try:
        client = _get_llm_client()
        resp = client.chat.completions.create(
            model=_QWEN_MODEL,
            messages=[
                {"role": "system", "content": _ROUTE_SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.1,
            max_tokens=256,
        )
        raw = resp.choices[0].message.content.strip()
        # 去掉可能的 markdown 代码块
        raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        result = json.loads(raw)
        return result
    except Exception as e:
        logger.warning("意图解析失败: %s，使用默认路由", e)
        return {
            "routes": ["route:bitable_topics"],
            "keywords": [],
            "summary": question[:50],
        }


# ---------------------------------------------------------------------------
# 各信息源数据获取
# ---------------------------------------------------------------------------

def _fetch_topics_data(keywords: List[str]) -> str:
    """从待跟进话题表获取相关记录。"""
    records = _fetch_bitable_records(_TABLE_TOPICS, max_records=200)
    if keywords:
        # 按关键词过滤
        filtered = []
        for rec in records:
            fields = rec.get("fields", {})
            text_blob = " ".join(str(v) for v in fields.values()).lower()
            if any(kw.lower() in text_blob for kw in keywords):
                filtered.append(rec)
        records = filtered or records[:20]  # 无匹配时取前 20 条
    else:
        records = records[:20]

    return _records_to_text(records, ["话题标题", "意图类型", "状态", "话题摘要", "来源周期"])


def _fetch_features_data(keywords: List[str]) -> str:
    """从功能表获取相关记录。"""
    records = _fetch_bitable_records(_TABLE_FEATURES, max_records=200)
    if keywords:
        filtered = []
        for rec in records:
            fields = rec.get("fields", {})
            text_blob = " ".join(str(v) for v in fields.values()).lower()
            if any(kw.lower() in text_blob for kw in keywords):
                filtered.append(rec)
        records = filtered or records[:20]
    else:
        records = records[:20]

    return _records_to_text(records, ["功能名称", "状态", "阶段", "所属模块", "功能优先级", "负责人"])


def _fetch_modules_data(keywords: List[str]) -> str:
    """从模块表获取相关记录。"""
    records = _fetch_bitable_records(_TABLE_MODULES, max_records=100)
    if keywords:
        filtered = []
        for rec in records:
            fields = rec.get("fields", {})
            text_blob = " ".join(str(v) for v in fields.values()).lower()
            if any(kw.lower() in text_blob for kw in keywords):
                filtered.append(rec)
        records = filtered or records
    return _records_to_text(records, ["模块名称", "状态", "优先级", "负责人", "模块说明"])


def _fetch_meegle_defects_data(keywords: List[str]) -> str:
    """从 Meegle 缺陷表获取相关记录。"""
    records = _fetch_bitable_records(_TABLE_M_DEFECTS, max_records=200)
    # 过滤已归档
    records = [r for r in records if not r.get("fields", {}).get("是否归档")]
    if keywords:
        filtered = []
        for rec in records:
            fields = rec.get("fields", {})
            text_blob = " ".join(str(v) for v in fields.values()).lower()
            if any(kw.lower() in text_blob for kw in keywords):
                filtered.append(rec)
        records = filtered or records[:20]
    else:
        records = records[:20]
    return _records_to_text(records, ["标题", "状态", "优先级", "负责人", "业务线"])


def _fetch_meegle_tasks_data(keywords: List[str]) -> str:
    """从 Meegle 任务表获取相关记录。"""
    records = _fetch_bitable_records(_TABLE_M_TASKS, max_records=200)
    records = [r for r in records if not r.get("fields", {}).get("是否归档")]
    if keywords:
        filtered = []
        for rec in records:
            fields = rec.get("fields", {})
            text_blob = " ".join(str(v) for v in fields.values()).lower()
            if any(kw.lower() in text_blob for kw in keywords):
                filtered.append(rec)
        records = filtered or records[:20]
    else:
        records = records[:20]
    return _records_to_text(records, ["标题", "状态", "负责人", "计划结束", "实际完成"])


def _fetch_meegle_reqs_data(keywords: List[str]) -> str:
    """从 Meegle 需求表获取相关记录。"""
    records = _fetch_bitable_records(_TABLE_M_REQS, max_records=200)
    records = [r for r in records if not r.get("fields", {}).get("是否归档")]
    if keywords:
        filtered = []
        for rec in records:
            fields = rec.get("fields", {})
            text_blob = " ".join(str(v) for v in fields.values()).lower()
            if any(kw.lower() in text_blob for kw in keywords):
                filtered.append(rec)
        records = filtered or records[:20]
    else:
        records = records[:20]
    return _records_to_text(records, ["标题", "状态", "优先级", "负责人", "计划结束"])


# 路由 → 数据获取函数映射
_ROUTE_FETCHER = {
    "route:bitable_topics":      _fetch_topics_data,
    "route:bitable_features":    _fetch_features_data,
    "route:bitable_modules":     _fetch_modules_data,
    "route:meegle_defects":      _fetch_meegle_defects_data,
    "route:meegle_tasks":        _fetch_meegle_tasks_data,
    "route:meegle_requirements": _fetch_meegle_reqs_data,
}


# ---------------------------------------------------------------------------
# 回答生成
# ---------------------------------------------------------------------------

_ANSWER_SYSTEM_PROMPT = """你是 AI 秘书，负责根据项目数据回答团队成员的问题。

规则：
1. 直接回答问题，不要废话
2. 如果数据中有明确答案，给出具体数字/状态/负责人
3. 如果数据不足以回答，说明"当前数据暂无相关记录"
4. 回答用中文，简洁清晰，适合飞书群聊
5. 重要信息用 【】 标注，如 【风险/阻塞】【已完成】【进行中】
6. 回答末尾注明数据来源（信息源名称），格式：📊 数据来源：xxx
"""

def _generate_answer(question: str, context_data: Dict[str, str], intent_summary: str) -> str:
    """
    根据问题和从各信息源获取的数据，用 LLM 生成自然语言回答。

    Args:
        question: 用户原始问题
        context_data: {路由名: 数据文本} 字典
        intent_summary: 意图摘要

    Returns:
        生成的回答文本
    """
    # 构建上下文
    context_parts = []
    for route, data_text in context_data.items():
        label = ROUTE_LABEL.get(route, route)
        context_parts.append(f"【{label}】\n{data_text}")
    context = "\n\n".join(context_parts)

    user_prompt = f"问题：{question}\n\n项目数据：\n{context}"

    try:
        client = _get_llm_client()
        resp = client.chat.completions.create(
            model=_QWEN_MODEL,
            messages=[
                {"role": "system", "content": _ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error("回答生成失败: %s", e)
        return f"抱歉，生成回答时出现错误：{e}"


# ---------------------------------------------------------------------------
# @机器人 检测
# ---------------------------------------------------------------------------

def is_at_bot(msg_info: Dict) -> bool:
    """
    判断消息是否 @了机器人，或是 p2p 私聊消息。

    飞书消息 content 中 @机器人 会在文本中出现 @_user_1 或 mentions 字段中包含机器人 open_id。
    同时支持 p2p 私聊（chat_type == "p2p"）。
    """
    # p2p 私聊直接触发
    if msg_info.get("chat_type") == "p2p":
        return True

    # 检查 raw_message 中的 mentions 字段
    raw_message = msg_info.get("raw_message", {})
    mentions = raw_message.get("mentions", [])
    bot_app_id = os.environ.get("LARK_APP_ID", "cli_a9d985cd40f89e1a")

    for mention in mentions:
        # mentions 中的 id 字段包含 open_id
        mention_id = mention.get("id", {})
        if isinstance(mention_id, dict):
            open_id = mention_id.get("open_id", "")
        else:
            open_id = str(mention_id)
        # 飞书机器人的 open_id 通常以 ou_ 开头，也可能通过 app_id 匹配
        if open_id and (open_id == _get_bot_open_id() or "all" in open_id.lower()):
            return True

    # 兜底：检查文本中是否有 @机器人 的 key（@_user_1 等占位符）
    text = msg_info.get("text", "")
    if "@_user_" in text or "@AI秘书" in text or "@ai秘书" in text:
        return True

    return False


_bot_open_id_cache: str = ""

def _get_bot_open_id() -> str:
    """获取机器人自身的 open_id（缓存）。"""
    global _bot_open_id_cache
    if _bot_open_id_cache:
        return _bot_open_id_cache
    try:
        import requests as _requests
        app_id = os.environ.get("LARK_APP_ID", "cli_a9d985cd40f89e1a")
        app_secret = os.environ.get("LARK_APP_SECRET", "")
        token_resp = _requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret}, timeout=10,
        )
        token = token_resp.json().get("tenant_access_token", "")
        if token:
            bot_resp = _requests.get(
                "https://open.feishu.cn/open-apis/bot/v3/info",
                headers={"Authorization": f"Bearer {token}"}, timeout=10,
            )
            bot_data = bot_resp.json()
            _bot_open_id_cache = bot_data.get("bot", {}).get("open_id", "")
    except Exception as e:
        logger.warning("获取机器人 open_id 失败: %s", e)
    return _bot_open_id_cache


def _clean_question(text: str) -> str:
    """
    清理问题文本：去除 @机器人 占位符，提取纯问题内容。
    飞书消息中 @机器人 在文本里表现为 @_user_1 等占位符。
    """
    # 去除 @_user_xxx 占位符
    text = re.sub(r"@_user_\d+", "", text)
    # 去除 @AI秘书 等直接 @ 文本
    text = re.sub(r"@AI秘书|@ai秘书|@机器人", "", text, flags=re.IGNORECASE)
    return text.strip()


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def handle_qa(msg_info: Dict) -> Dict:
    """
    处理问答请求。

    Args:
        msg_info: 从 extract_message_from_event 提取的消息信息字典

    Returns:
        {
          "handled": bool,          # 是否处理了（False 表示不是 @机器人 消息）
          "answer": str,            # 生成的回答文本
          "routes": List[str],      # 实际使用的路由列表
          "keywords": List[str],    # 提取的关键词
          "from_cache": bool,       # 是否命中缓存
          "cache_record_id": str,   # 缓存记录 ID（用于后续更新）
          "question_clean": str,    # 清理后的问题文本
        }
    """
    # 1. 检测是否 @机器人
    if not is_at_bot(msg_info):
        return {"handled": False, "answer": "", "routes": [], "keywords": [], "from_cache": False, "cache_record_id": "", "question_clean": ""}

    # 2. 清理问题文本
    raw_text = msg_info.get("text", "")
    question = _clean_question(raw_text)
    if not question:
        return {
            "handled": True,
            "answer": "你好！请问有什么可以帮你查询的？例如：\n• 某个模块的验收进度如何？\n• CRM 相关的 Meegle 需求状态？\n• 当前有哪些风险阻塞？",
            "routes": [],
            "keywords": [],
            "from_cache": False,
            "cache_record_id": "",
            "question_clean": "",
        }

    logger.info("收到问答请求: question=%s", question[:80])

    # 3. 处理刷新指令
    if question.strip() in ("刷新", "refresh", "刷新缓存"):
        try:
            from qa_cache import invalidate_cache
            invalidate_cache()
        except Exception:
            pass
        return {
            "handled": True,
            "answer": "缓存已清空，下次查询将获取最新数据。",
            "routes": [],
            "keywords": [],
            "from_cache": False,
            "cache_record_id": "",
            "question_clean": question,
        }

    # 4. 查询缓存（延迟导入避免循环依赖）
    try:
        from qa_cache import find_similar_cache
        cache_hit = find_similar_cache(question)
    except Exception as e:
        logger.warning("缓存查询失败: %s", e)
        cache_hit = None

    if cache_hit:
        logger.info("命中缓存: record_id=%s similarity=%.2f", cache_hit.get("record_id"), cache_hit.get("similarity", 0))
        cached_answer = cache_hit.get("answer", "")
        cached_routes = cache_hit.get("routes", [])
        route_labels = [ROUTE_LABEL.get(r, r) for r in cached_routes]
        # 在回答末尾注明来自缓存
        answer_with_note = (
            f"{cached_answer}\n\n"
            f"_(以上为缓存回答，基于相似问题「{cache_hit.get('question', '')}」，"
            f"如需最新数据请发送「刷新」)_"
        )
        return {
            "handled": True,
            "answer": answer_with_note,
            "routes": cached_routes,
            "keywords": cache_hit.get("keywords", []),
            "from_cache": True,
            "cache_record_id": cache_hit.get("record_id", ""),
            "question_clean": question,
        }

    # 4. LLM 意图路由解析
    intent = _parse_intent(question)
    routes = intent.get("routes", ["route:bitable_topics"])
    keywords = intent.get("keywords", [])
    intent_summary = intent.get("summary", question[:50])
    logger.info("意图解析: routes=%s keywords=%s", routes, keywords)

    # route:multi 展开为所有主要路由
    if "route:multi" in routes:
        routes = ["route:bitable_topics", "route:bitable_features", "route:bitable_modules"]

    # 5. 从各信息源获取数据
    context_data: Dict[str, str] = {}
    for route in routes:
        fetcher = _ROUTE_FETCHER.get(route)
        if fetcher:
            try:
                data_text = fetcher(keywords)
                context_data[route] = data_text
                logger.info("路由 %s 获取到 %d 字符数据", route, len(data_text))
            except Exception as e:
                logger.error("路由 %s 数据获取失败: %s", route, e)
                context_data[route] = f"（数据获取失败：{e}）"

    # 6. 生成回答
    answer = _generate_answer(question, context_data, intent_summary)

    # 7. 写入缓存日志（异步，失败不影响主流程）
    try:
        from qa_cache import save_qa_log
        save_qa_log(
            question=question,
            answer=answer,
            routes=routes,
            keywords=keywords,
            from_cache=False,
        )
    except Exception as e:
        logger.warning("写入问答日志失败: %s", e)

    return {
        "handled": True,
        "answer": answer,
        "routes": routes,
        "keywords": keywords,
        "from_cache": False,
        "cache_record_id": "",
        "question_clean": question,
    }

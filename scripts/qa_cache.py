"""
qa_cache.py
===========
AI 秘书问答系统 — 缓存与日志模块

功能：
  1. 将每次问答（问题、回答、路由、关键词）持久化到 Bitable「问答日志」表
  2. 新问题到来时，通过 LLM Embedding 计算语义相似度，匹配历史相似问题
  3. 相似度超过阈值时直接返回缓存回答，并标记命中缓存
  4. 缓存有效期：默认 24 小时（可通过 QA_CACHE_TTL_HOURS 配置）

Bitable 表结构（问答日志，tblwhuGWDRPpAyPp）：
  问题        文本
  回答        文本
  路由        文本（JSON 序列化的 List[str]）
  关键词      文本（逗号分隔）
  命中缓存    复选框
  问题时间    日期时间
  发问人      文本
  消息ID      文本
  问题向量    文本（JSON 序列化的 List[float]，用于相似度计算）

环境变量：
  BITABLE_BASE_ID            Bitable 应用 Token
  BITABLE_TABLE_QA_LOG       问答日志表 ID（默认 tblwhuGWDRPpAyPp）
  QA_CACHE_TTL_HOURS         缓存有效期小时数（默认 24）
  QA_SIMILARITY_THRESHOLD    相似度阈值 0~1（默认 0.85）
  DASHSCOPE_API_KEY          通义千问 API Key（用于 Embedding）
"""

import os
import json
import logging
import time
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger("ai_secretary.qa_cache")

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
_BASE_ID          = os.environ.get("BITABLE_BASE_ID", "CyDxbUQGGa3N2NsVanMjqdjxp6e")
_TABLE_QA_LOG     = os.environ.get("BITABLE_TABLE_QA_LOG", "tblwhuGWDRPpAyPp")
_CACHE_TTL_HOURS  = int(os.environ.get("QA_CACHE_TTL_HOURS", "24"))
_SIM_THRESHOLD    = float(os.environ.get("QA_SIMILARITY_THRESHOLD", "0.85"))

# Embedding 模型（通义千问兼容 OpenAI Embeddings API）
_EMBED_MODEL      = "text-embedding-v3"
_QWEN_BASE_URL    = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 内存缓存：避免每次都从 Bitable 拉取全量记录
# 格式：[{"record_id": ..., "question": ..., "answer": ..., "routes": [...], "keywords": [...], "vector": [...], "created_at": float}, ...]
_memory_cache: List[Dict] = []
_cache_loaded_at: float = 0.0
_MEMORY_REFRESH_SECONDS = 300  # 5 分钟刷新一次内存缓存


# ---------------------------------------------------------------------------
# Embedding 计算
# ---------------------------------------------------------------------------
def _get_embedding(text: str) -> List[float]:
    """
    调用通义千问 Embedding API 获取文本向量。
    失败时返回空列表（降级为关键词匹配）。
    """
    try:
        from openai import OpenAI
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            return []
        client = OpenAI(api_key=api_key, base_url=_QWEN_BASE_URL)
        resp = client.embeddings.create(model=_EMBED_MODEL, input=text)
        return resp.data[0].embedding
    except Exception as e:
        logger.warning("Embedding 计算失败: %s，降级为关键词匹配", e)
        return []


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """计算两个向量的余弦相似度。"""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _keyword_similarity(q1: str, q2: str) -> float:
    """
    基于关键词重叠的简单相似度（Jaccard）。
    作为 Embedding 失败时的降级方案。
    """
    words1 = set(q1.lower().replace("？", "").replace("?", "").split())
    words2 = set(q2.lower().replace("？", "").replace("?", "").split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# Bitable 操作
# ---------------------------------------------------------------------------
def _get_token() -> str:
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


def _load_cache_from_bitable() -> List[Dict]:
    """
    从 Bitable 问答日志表加载近期记录到内存缓存。
    只加载 TTL 有效期内的记录。
    """
    import requests as _requests
    token = _get_token()
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{_BASE_ID}/tables/{_TABLE_QA_LOG}/records"
    cutoff_ts = (datetime.now(timezone.utc) - timedelta(hours=_CACHE_TTL_HOURS)).timestamp() * 1000

    all_records: List[Dict] = []
    page_token = ""

    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        try:
            resp = _requests.get(url, headers=headers, params=params, timeout=15)
            data = resp.json()
            items = data.get("data", {}).get("items", [])
            for item in items:
                fields = item.get("fields", {})
                # 过滤 TTL 外的记录
                created_ts = fields.get("问题时间", 0)
                if isinstance(created_ts, (int, float)) and created_ts < cutoff_ts:
                    continue
                # 解析向量
                vector_str = fields.get("问题向量", "")
                if isinstance(vector_str, list):
                    vector_str = "".join(
                        seg.get("text", "") if isinstance(seg, dict) else str(seg)
                        for seg in vector_str
                    )
                try:
                    vector = json.loads(vector_str) if vector_str else []
                except Exception:
                    vector = []
                # 解析路由
                routes_str = fields.get("路由", "")
                if isinstance(routes_str, list):
                    routes_str = "".join(
                        seg.get("text", "") if isinstance(seg, dict) else str(seg)
                        for seg in routes_str
                    )
                try:
                    routes = json.loads(routes_str) if routes_str else []
                except Exception:
                    routes = []
                # 解析问题文本
                question_raw = fields.get("问题", "")
                if isinstance(question_raw, list):
                    question_raw = "".join(
                        seg.get("text", "") if isinstance(seg, dict) else str(seg)
                        for seg in question_raw
                    )
                # 解析回答文本
                answer_raw = fields.get("回答", "")
                if isinstance(answer_raw, list):
                    answer_raw = "".join(
                        seg.get("text", "") if isinstance(seg, dict) else str(seg)
                        for seg in answer_raw
                    )
                all_records.append({
                    "record_id": item.get("record_id", ""),
                    "question": question_raw,
                    "answer": answer_raw,
                    "routes": routes,
                    "keywords": (fields.get("关键词") or "").split(",") if (fields.get("关键词") or "").strip() else [],
                    "vector": vector,
                    "created_at": created_ts,
                })
            if not data.get("data", {}).get("has_more", False):
                break
            page_token = data.get("data", {}).get("page_token", "")
        except Exception as e:
            logger.error("加载问答缓存失败: %s", e)
            break

    logger.info("从 Bitable 加载了 %d 条问答缓存记录", len(all_records))
    return all_records


def _ensure_cache_loaded():
    """确保内存缓存是最新的（超过刷新间隔则重新加载）。"""
    global _memory_cache, _cache_loaded_at
    if time.time() - _cache_loaded_at > _MEMORY_REFRESH_SECONDS:
        _memory_cache = _load_cache_from_bitable()
        _cache_loaded_at = time.time()


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------

def find_similar_cache(question: str) -> Optional[Dict]:
    """
    在历史问答缓存中查找语义相似的问题。

    Args:
        question: 当前用户问题（已清理）

    Returns:
        命中时返回 {"record_id": ..., "question": ..., "answer": ..., "routes": [...], "keywords": [...], "similarity": float}
        未命中时返回 None
    """
    _ensure_cache_loaded()
    if not _memory_cache:
        return None

    # 计算当前问题的 Embedding
    current_vector = _get_embedding(question)

    best_match = None
    best_score = 0.0

    for record in _memory_cache:
        cached_vector = record.get("vector", [])
        cached_question = record.get("question", "")

        if current_vector and cached_vector:
            score = _cosine_similarity(current_vector, cached_vector)
        else:
            # 降级：关键词相似度
            score = _keyword_similarity(question, cached_question)

        if score > best_score:
            best_score = score
            best_match = record

    if best_score >= _SIM_THRESHOLD and best_match:
        logger.info(
            "缓存命中: similarity=%.3f question='%s' cached='%s'",
            best_score, question[:40], best_match.get("question", "")[:40],
        )
        return {**best_match, "similarity": best_score}

    logger.debug("缓存未命中: best_score=%.3f threshold=%.2f", best_score, _SIM_THRESHOLD)
    return None


def save_qa_log(
    question: str,
    answer: str,
    routes: List[str],
    keywords: List[str],
    from_cache: bool = False,
    sender_name: str = "",
    message_id: str = "",
) -> Optional[str]:
    """
    将问答记录持久化到 Bitable 问答日志表，并更新内存缓存。

    Returns:
        新建记录的 record_id，失败时返回 None
    """
    import requests as _requests

    token = _get_token()
    if not token:
        logger.error("获取飞书 token 失败，无法写入问答日志")
        return None

    # 计算问题向量（用于后续缓存匹配）
    vector = _get_embedding(question) if not from_cache else []
    vector_str = json.dumps(vector, ensure_ascii=False) if vector else ""

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    fields = {
        "问题": question[:2000],  # Bitable 文本字段限制
        "回答": answer[:5000],
        "路由": json.dumps(routes, ensure_ascii=False),
        "关键词": ",".join(keywords),
        "命中缓存": from_cache,
        "问题时间": now_ms,
        "发问人": sender_name,
        "消息ID": message_id,
        "问题向量": vector_str[:5000],  # 向量文本可能较长，截断保护
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{_BASE_ID}/tables/{_TABLE_QA_LOG}/records"

    try:
        resp = _requests.post(url, headers=headers, json={"fields": fields}, timeout=15)
        data = resp.json()
        if data.get("code") == 0:
            record_id = data.get("data", {}).get("record", {}).get("record_id", "")
            logger.info("问答日志已写入: record_id=%s question=%s", record_id, question[:40])
            # 同步更新内存缓存
            if vector:
                _memory_cache.append({
                    "record_id": record_id,
                    "question": question,
                    "answer": answer,
                    "routes": routes,
                    "keywords": keywords,
                    "vector": vector,
                    "created_at": now_ms,
                })
            return record_id
        else:
            logger.error("写入问答日志失败: code=%s msg=%s", data.get("code"), data.get("msg"))
            return None
    except Exception as e:
        logger.error("写入问答日志异常: %s", e)
        return None


def invalidate_cache():
    """强制清空内存缓存，下次查询时重新从 Bitable 加载。"""
    global _memory_cache, _cache_loaded_at
    _memory_cache = []
    _cache_loaded_at = 0.0
    logger.info("问答缓存已清空")

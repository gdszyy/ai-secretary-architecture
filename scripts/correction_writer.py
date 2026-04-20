"""
correction_writer.py
====================
信息纠正写入模块（可被其他脚本导入调用）

从 manual_correction.py 提取的核心 Bitable 写入逻辑，封装为可复用模块。
支持：
  - upsert_correction(title, intent, summary, source, status, period)
    → 若 Bitable 中已存在同名话题，则更新；否则新建。
  - write_corrections(corrections_list)
    → 批量写入（兼容 manual_correction.py 的 CORRECTIONS 格式）

被以下脚本调用：
  - scripts/manual_correction.py（手动脚本触发）
  - main.py 中的 correction 处理器（飞书卡片回复自动触发）
"""

import os
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("correction_writer")

# ---------------------------------------------------------------------------
# 配置常量（优先读取环境变量，回退到硬编码默认值）
# ---------------------------------------------------------------------------
APP_ID     = os.environ.get("LARK_APP_ID",     "cli_a9d985cd40f89e1a")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "UNemS0zPnUuXhONgkuuprgdK3SrVx05T")
BASE_ID    = os.environ.get("BITABLE_BASE_ID", "CyDxbUQGGa3N2NsVanMjqdjxp6e")
TABLE_ID   = os.environ.get("BITABLE_TABLE_ID","tblKscoaGp6VwhQe")

TZ_UTC8 = timezone(timedelta(hours=8))

# 意图类型简写 → 完整值映射
INTENT_ALIAS = {
    "决策":   "major_decision",
    "里程碑": "milestone_fact",
    "风险":   "risk_blocker",
    "任务":   "routine_task",
}

VALID_INTENTS = {"major_decision", "milestone_fact", "risk_blocker", "routine_task"}

# ---------------------------------------------------------------------------
# Lark API 基础工具
# ---------------------------------------------------------------------------

def get_token() -> str:
    """获取飞书 tenant_access_token"""
    r = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {data.get('msg')}")
    return data["tenant_access_token"]


def fetch_all_records(token: str) -> list:
    """拉取 Bitable 话题表所有记录"""
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}
    records, page_token = [], None
    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()["data"]
        records.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
        time.sleep(0.2)
    return records


def _update_record(token: str, record_id: str, fields: dict) -> bool:
    """更新 Bitable 中的一条记录"""
    url = (
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}"
        f"/tables/{TABLE_ID}/records/{record_id}"
    )
    r = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"fields": fields},
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("code") == 0


def _create_record(token: str, fields: dict) -> bool:
    """在 Bitable 中新建一条记录"""
    url = (
        f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}"
        f"/tables/{TABLE_ID}/records"
    )
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"fields": fields},
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("code") == 0


# ---------------------------------------------------------------------------
# 核心公开接口
# ---------------------------------------------------------------------------

def normalize_intent(intent: str) -> str:
    """
    将意图类型简写转换为完整值。
    如果已是完整值则直接返回；无法识别则返回 'routine_task'。
    """
    if intent in VALID_INTENTS:
        return intent
    normalized = INTENT_ALIAS.get(intent)
    if normalized:
        return normalized
    logger.warning("未知意图类型 '%s'，回退为 routine_task", intent)
    return "routine_task"


def get_current_period() -> str:
    """返回当前周期字符串，格式：第N周 (MM/DD~MM/DD)"""
    now = datetime.now(TZ_UTC8)
    # 计算当前是今年第几周（ISO 周一为起始）
    week_num = now.isocalendar()[1]
    # 本周一和周日
    monday = now - timedelta(days=now.weekday())
    sunday = monday + timedelta(days=6)
    return f"第{week_num}周 ({monday.strftime('%m/%d')}~{sunday.strftime('%m/%d')})"


def upsert_correction(
    title: str,
    summary: str,
    intent: str = "major_decision",
    source: str = "VoidZ飞书卡片回复",
    status: Optional[str] = None,
    period: Optional[str] = None,
) -> dict:
    """
    以 upsert 方式将纠正信息写入 Bitable。

    参数：
        title   : 话题标题（用于精确匹配已有记录）
        summary : 纠正后的完整描述
        intent  : 意图类型（支持简写，如"决策"→"major_decision"）
        source  : 信息来源标注
        status  : 状态（可选，默认根据 intent 推断）
        period  : 来源周期（可选，默认为当前周）

    返回：
        {
            "action": "update" | "create",
            "title": str,
            "success": bool,
            "error": str | None,
        }
    """
    intent = normalize_intent(intent)
    period = period or get_current_period()

    # 根据意图推断默认状态
    if status is None:
        status = "风险/阻塞" if intent == "risk_blocker" else "进行中"

    source_note = f"{source} {datetime.now(TZ_UTC8).strftime('%Y-%m-%d')}"
    fields = {
        "话题标题": title,
        "意图类型": intent,
        "状态":     status,
        "来源周期": period,
        "话题摘要": summary,
        "追问回复": f"[飞书卡片纠正 {source_note}]\n{summary}",
    }

    try:
        token = get_token()
        existing = fetch_all_records(token)
        title_to_id = {
            rec["fields"].get("话题标题", ""): rec["record_id"]
            for rec in existing
            if rec["fields"].get("话题标题")
        }

        if title in title_to_id:
            record_id = title_to_id[title]
            ok = _update_record(token, record_id, fields)
            action = "update"
            logger.info("[UPDATE] %s | intent=%s status=%s ok=%s", title, intent, status, ok)
        else:
            ok = _create_record(token, fields)
            action = "create"
            logger.info("[CREATE] %s | intent=%s status=%s ok=%s", title, intent, status, ok)

        return {"action": action, "title": title, "success": ok, "error": None}

    except Exception as e:
        logger.error("写入 Bitable 失败 [%s]: %s", title, e)
        return {"action": "unknown", "title": title, "success": False, "error": str(e)}


def write_corrections(corrections: list) -> dict:
    """
    批量写入纠正条目，兼容 manual_correction.py 的 CORRECTIONS 格式。

    参数：
        corrections: 列表，每项包含 title, intent, summary, [status], [period], [source]

    返回：
        {"created": int, "updated": int, "errors": int}
    """
    created, updated, errors = 0, 0, 0
    for corr in corrections:
        result = upsert_correction(
            title=corr["title"],
            summary=corr["summary"],
            intent=corr.get("intent", "major_decision"),
            source=corr.get("source", "VoidZ手动纠正"),
            status=corr.get("status"),
            period=corr.get("period"),
        )
        if result["success"]:
            if result["action"] == "create":
                created += 1
            else:
                updated += 1
        else:
            errors += 1
        time.sleep(0.2)  # 避免触发 API 限流

    logger.info("批量写入完成：新建 %d / 更新 %d / 失败 %d", created, updated, errors)
    return {"created": created, "updated": updated, "errors": errors}

"""
migrate_intent_field.py
=======================
存量意图字段迁移脚本

将 Bitable 话题表中旧意图值映射到新五类意图体系：
  旧值                → 新值
  ─────────────────────────────────────────────────
  decision_record     → major_decision
  risk_escalation     → risk_blocker
  progress_update     → milestone_fact
  status_update       → milestone_fact
  feature_request     → routine_task
  feature_discussion  → routine_task
  bug_report          → routine_task
  design_review       → routine_task
  memo                → routine_task
  casual_chat         → (跳过，保持原样或已过滤)
  other               → (跳过)

同时将旧状态值映射到新状态体系：
  旧值        → 新值
  ─────────────────────────────────────────────────
  已完成      → 已解决
  跟进中      → 风险/阻塞（仅 risk_blocker 类型）
  待跟进      → 风险/阻塞（仅 risk_blocker 类型）
  已忽略      → 已忽略（保持不变）
  已解决      → 已解决（保持不变）

用法：
  python3 migrate_intent_field.py --dry-run   # 预览
  python3 migrate_intent_field.py             # 正式执行
"""

import os, sys, time, logging, argparse, requests
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate_intent")

APP_ID     = os.environ.get("LARK_APP_ID",     "cli_a9d985cd40f89e1a")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "UNemS0zPnUuXhONgkuuprgdK3SrVx05T")
BASE_ID    = os.environ.get("BITABLE_BASE_ID", "CyDxbUQGGa3N2NsVanMjqdjxp6e")
TABLE_ID   = os.environ.get("BITABLE_TABLE_ID","tblKscoaGp6VwhQe")

# 旧意图 → 新意图
INTENT_MAP = {
    "decision_record":    "major_decision",
    "risk_escalation":    "risk_blocker",
    "progress_update":    "milestone_fact",
    "status_update":      "milestone_fact",
    "feature_request":    "routine_task",
    "feature_discussion": "routine_task",
    "bug_report":         "routine_task",
    "design_review":      "routine_task",
    "memo":               "routine_task",
}

# 旧状态 → 新状态（仅当状态需要更新时）
STATUS_MAP = {
    "已完成": "已解决",
    # 跟进中/待跟进 → 只有 risk_blocker 才映射为"风险/阻塞"，其余保持
}

# 已是新意图值，不需要迁移
NEW_INTENTS = {"major_decision", "milestone_fact", "risk_blocker", "routine_task", "personal_followup"}

def get_token():
    r = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10
    )
    r.raise_for_status()
    return r.json()["tenant_access_token"]

def fetch_all(token):
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

def update_record(token, record_id, fields):
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records/{record_id}"
    r = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"fields": fields}, timeout=10
    )
    r.raise_for_status()
    return r.json().get("code") == 0

def llm_reclassify_risk(records_to_check: list[dict], dry_run: bool) -> int:
    """
    对已映射为 milestone_fact / routine_task 的记录做二次 LLM 校验，
    将其中真正的风险/阻塞项重新分类为 risk_blocker。
    返回实际修正的条数。
    """
    from openai import OpenAI
    import json

    if not records_to_check:
        return 0

    client = OpenAI()
    token = get_token()

    # 构建批量判断输入
    items_text = ""
    for i, rec in enumerate(records_to_check):
        f = rec["fields"]
        items_text += f"{i}: 标题={f.get('话题标题','')!r} 摘要={f.get('话题摘要','')[:80]!r}\n"

    prompt = f"""以下是项目群聊话题列表，请判断每条是否属于「风险/阻塞」（risk_blocker）类型。

判断标准：
- 外部依赖阻塞（商务不配合、第三方延迟、牌照问题）
- 技术故障影响功能可用性（WebSocket断线、数据缺失、服务异常）
- 功能缺口影响上线计划（未实现的关键功能、排期待定）
- 人员/资源不足导致项目风险

不属于 risk_blocker：常规需求、UI调整、会议安排、设计评审、已解决的问题。

{items_text}

输出 JSON 数组，只包含应该是 risk_blocker 的索引号（从 0 开始）。
示例：[0, 3, 7]
只输出 JSON，不要其他说明。"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        risk_indices = json.loads(raw)
    except Exception as e:
        logger.warning("二次分类 LLM 调用失败: %s", e)
        return 0

    corrected = 0
    for idx in risk_indices:
        if idx >= len(records_to_check):
            continue
        rec = records_to_check[idx]
        f = rec["fields"]
        title = f.get("话题标题", "")
        logger.info("  修正为 risk_blocker: %s", title)
        if not dry_run:
            ok = update_record(token, rec["record_id"], {
                "意图类型": "risk_blocker",
                "状态": "风险/阻塞",
            })
            if ok:
                corrected += 1
            time.sleep(0.15)
        else:
            corrected += 1

    logger.info("二次修正完成：%d 条记录更新为 risk_blocker", corrected)
    return corrected


def main():
    parser = argparse.ArgumentParser(description="存量意图字段迁移")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-llm", action="store_true", help="跳过 LLM 二次修正")
    args = parser.parse_args()

    token = get_token()
    records = fetch_all(token)
    logger.info("共获取 %d 条记录", len(records))

    stats = Counter()
    migration_log = []

    for rec in records:
        fields = rec["fields"]
        rid = rec["record_id"]
        old_intent = fields.get("意图类型", "")
        old_status  = fields.get("状态", "")
        title = fields.get("话题标题", "")

        # 已是新意图，跳过
        if old_intent in NEW_INTENTS:
            stats["already_new"] += 1
            continue

        # 无法映射的意图（casual_chat / other / 空）
        if old_intent not in INTENT_MAP:
            stats["unmappable"] += 1
            logger.debug("跳过无法映射的意图: %r — %s", old_intent, title)
            continue

        new_intent = INTENT_MAP[old_intent]

        # 计算新状态
        new_status = None
        if old_status == "已完成":
            new_status = "已解决"
        elif old_status in ("跟进中", "待跟进") and new_intent == "risk_blocker":
            new_status = "风险/阻塞"
        # 其余状态保持不变

        update_fields = {"意图类型": new_intent}
        if new_status and new_status != old_status:
            update_fields["状态"] = new_status

        migration_log.append({
            "title": title,
            "old_intent": old_intent,
            "new_intent": new_intent,
            "old_status": old_status,
            "new_status": new_status or old_status,
        })

        logger.info("  迁移: %r  %s→%s  状态:%s→%s",
                    title[:30], old_intent, new_intent, old_status, new_status or "(不变)")

        if not args.dry_run:
            ok = update_record(token, rid, update_fields)
            if ok:
                stats["migrated"] += 1
            else:
                stats["errors"] += 1
                logger.warning("更新失败: %s", title)
            time.sleep(0.15)
        else:
            stats["migrated"] += 1

    logger.info(
        "迁移完成 | 已迁移=%d 已是新值=%d 无法映射=%d 错误=%d",
        stats["migrated"], stats["already_new"], stats["unmappable"], stats["errors"]
    )

    # Step 2: LLM 二次修正 — 将被误判的风险项修正为 risk_blocker
    corrected = 0
    if not args.skip_llm and migration_log:
        # 只对非终态的 milestone_fact / routine_task 做二次校验
        terminal = {"已解决", "已忽略", "已归档(跨周)"}
        candidates = [
            rec for rec in records
            if rec["fields"].get("意图类型") in INTENT_MAP
            and rec["fields"].get("状态") not in terminal
        ]
        logger.info("Step 2: LLM 二次修正，候选记录 %d 条", len(candidates))
        corrected = llm_reclassify_risk(candidates, dry_run=args.dry_run)

    # 打印迁移汇总
    print(f"\n{'='*60}")
    if args.dry_run:
        print(f"[DRY RUN] 将迁移 {stats['migrated']} 条记录（未实际写入）")
        print(f"[DRY RUN] 其中 {corrected} 条将被修正为 risk_blocker")
    else:
        print(f"✅ 迁移完成：{stats['migrated']} 条记录已更新")
        print(f"✅ 二次修正：{corrected} 条记录更新为 risk_blocker")
    print(f"{'='*60}")

    # 按新意图分类统计
    from collections import defaultdict
    by_new = defaultdict(list)
    for m in migration_log:
        by_new[m["new_intent"]].append(m["title"])
    for intent, titles in sorted(by_new.items()):
        print(f"\n  [{intent}] {len(titles)} 条")
        for t in titles[:5]:
            print(f"    - {t[:50]}")
        if len(titles) > 5:
            print(f"    ... 共 {len(titles)} 条")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
parse_to_dashboard_json.py
--------------------------
从 archive/tasks_history/ 下的 Markdown 文档中，
利用 LLM 提取结构化数据并生成 dashboard_data.json。

用法:
    python3 scripts/parse_to_dashboard_json.py

输出:
    data/dashboard_data.json
"""

import os
import json
import re
from pathlib import Path
from openai import OpenAI

# ── 路径配置 ──────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
ARCHIVE_DIR = REPO_ROOT / "archive" / "tasks_history"
OUTPUT_DIR = REPO_ROOT / "data"
OUTPUT_FILE = OUTPUT_DIR / "dashboard_data.json"

# ── 要解析的文档列表（按优先级排序，越靠前权重越高）─────────────
SOURCE_FILES = [
    "xp_team_history_progress_report.md",
    "lark_group_weekly_report_0406_0410.md",
]

# ── LLM 客户端 ────────────────────────────────────────────────
client = OpenAI()  # 使用环境变量中的 OPENAI_API_KEY 和 base_url


def read_markdown(filename: str) -> str:
    path = ARCHIVE_DIR / filename
    if not path.exists():
        print(f"[WARN] 文件不存在，跳过: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def extract_dashboard_data(combined_text: str) -> dict:
    """调用 LLM 从合并文本中提取结构化看板数据"""
    system_prompt = """你是一名专业的项目数据分析师。
你的任务是从给定的项目周报和历史进度文档中，提取结构化的看板数据。
请严格按照指定的 JSON Schema 输出，不要输出任何额外的解释文字。
只输出合法的 JSON 对象。"""

    user_prompt = f"""请从以下项目文档中提取看板数据，输出符合下面 Schema 的 JSON：

## JSON Schema 要求

{{
  "last_updated": "ISO8601日期字符串",
  "project_name": "项目名称",
  "kpi_metrics": {{
    "health_score": {{
      "value": "0-100的整数，综合评估项目健康度",
      "trend_monthly": [
        {{"month": "YYYY-MM", "score": 整数, "label": "简短标签"}}
      ],
      "details": {{
        "bug_rate": "low|medium|high",
        "delay_rate": "low|medium|high",
        "team_velocity": "low|medium|high"
      }}
    }},
    "risk_alerts": {{
      "count": "当前活跃风险数量",
      "threshold": 5,
      "trend_weekly": [
        {{"week": "YYYY-WW", "count": 整数}}
      ],
      "items": [
        {{"level": "High|Medium|Low", "module": "模块名", "desc": "风险描述"}}
      ]
    }},
    "stage_version": {{
      "current": "当前版本号如V1.2",
      "history": [
        {{"version": "版本号", "date": "YYYY-MM-DD", "desc": "版本说明"}}
      ]
    }},
    "growth_engine": {{
      "active_modules": "正在进行中的模块数量",
      "completed_modules": "已完成的模块数量",
      "trend_weekly": [
        {{"week": "YYYY-WW", "active": 整数, "completed": 整数}}
      ]
    }}
  }},
  "milestones": [
    {{
      "date": "YYYY-MM-DD",
      "title": "里程碑标题",
      "owner": "负责人",
      "status": "completed|in_progress|pending",
      "is_current": "是否为当前阶段（布尔值）"
    }}
  ],
  "modules": [
    {{
      "id": "唯一标识符如mod_xxx",
      "name": "模块名称",
      "priority": "P0|P1|P2",
      "status": "completed|in_progress|pending|blocked",
      "progress_percentage": "0-100整数",
      "owner": "负责人",
      "current_summary": "当前状态一句话摘要",
      "next_milestone": "下一个里程碑描述",
      "history_timeline": [
        {{"date": "YYYY-MM-DD", "event": "事件描述"}}
      ],
      "risks": [
        {{"level": "High|Medium|Low", "desc": "风险描述"}}
      ],
      "weekly_updates": [
        {{"week": "YYYY-WW", "update": "本周更新摘要"}}
      ]
    }}
  ]
}}

## 优先级判断规则
- P0：核心数据链路、体育博彩核心功能、正在阻塞其他模块的
- P1：运营活动、用户系统、钱包财务等核心产品功能
- P2：UI/UX优化、平台系统管理、投放系统等支撑性功能

## 待解析的文档内容

{combined_text[:12000]}

请直接输出 JSON，不要有任何前缀或后缀文字。"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=4000,
    )

    raw = response.choices[0].message.content.strip()

    # 清理可能的 markdown 代码块包装
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


def merge_weekly_updates(base_data: dict, weekly_text: str) -> dict:
    """将周报中的最新动态合并进模块数据"""
    system_prompt = """你是一名项目数据分析师。
请将飞书周报中的最新动态，合并更新到已有的看板JSON数据中。
只更新 modules 中对应模块的 weekly_updates 字段，以及 kpi_metrics.risk_alerts.items。
不要改变其他字段的结构。只输出合法的 JSON 对象。"""

    user_prompt = f"""## 现有看板数据（部分）
{json.dumps({"modules": base_data.get("modules", [])[:5]}, ensure_ascii=False, indent=2)}

## 本周飞书群组周报
{weekly_text[:6000]}

请输出更新后的完整 JSON（保持原有结构，只补充 weekly_updates 和风险项）。
直接输出 JSON，不要有任何前缀或后缀。"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        merged = json.loads(raw)
        if "modules" in merged:
            base_data["modules"] = merged["modules"]
    except json.JSONDecodeError as e:
        print(f"[WARN] 周报合并解析失败，跳过: {e}")

    return base_data


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("📖 读取历史进度文档...")
    history_text = read_markdown(SOURCE_FILES[0])
    weekly_text = read_markdown(SOURCE_FILES[1])

    if not history_text:
        print("[ERROR] 历史进度文档为空，退出")
        return

    print("🤖 调用 LLM 提取结构化数据（历史进度文档）...")
    dashboard_data = extract_dashboard_data(history_text)

    if weekly_text:
        print("🔄 合并飞书周报最新动态...")
        dashboard_data = merge_weekly_updates(dashboard_data, weekly_text)

    # 写入输出文件
    OUTPUT_FILE.write_text(
        json.dumps(dashboard_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 数据已写入: {OUTPUT_FILE}")
    print(f"   模块数量: {len(dashboard_data.get('modules', []))}")
    print(f"   里程碑数量: {len(dashboard_data.get('milestones', []))}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
run_weekly_report.py
====================
周报汇总主脚本 —— Agent 驱动的多源数据聚合入口

功能：
  1. 从飞书多维表格（xp-weekly-report 技能）提取本周各成员周报
  2. 通过 LLM 将成员周报内容归因到具体模块（Module ID）
  3. 从 meegle_client.py 获取各模块 Meegle 进度（Story/Defect 变更）
  4. 从 extract_weekly_insights.py 获取群聊洞察（对模块进度有推进作用的关键话题）
  5. 调用 LLM 生成各模块的综合摘要
  6. 将结果注入 dashboard_data.json 并更新 weekly_periods
  7. 通过 lark-secretary 向飞书群发送富文本卡片通知

用法：
  python3 run_weekly_report.py                    # 正式运行（当前周）
  python3 run_weekly_report.py --week 2026-16     # 指定周
  python3 run_weekly_report.py --dry-run          # 预览模式，不写入文件
  python3 run_weekly_report.py --skip-notify      # 跳过飞书通知

触发方式：
  - Manus 定时任务（每周二 14:00）自动唤醒 Agent 执行
  - 飞书 Bot 指令（@AI秘书 生成本周周报）手动触发
"""
import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from openai import OpenAI

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_weekly_report")

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
REPO_ROOT      = Path(__file__).parent.parent
DATA_DIR       = REPO_ROOT / "data"
DASHBOARD_FILE = DATA_DIR / "dashboard_data.json"
SKILLS_DIR     = Path("/home/ubuntu/skills")
XP_WEEKLY_SCRIPT = SKILLS_DIR / "xp-weekly-report" / "scripts" / "fetch_weekly_data.py"
WEEKLY_DATA_FILE = Path("/home/ubuntu/weekly_report_data.json")
LARK_SECRETARY   = SKILLS_DIR / "lark-secretary" / "scripts" / "send_card.py"

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------
TZ_UTC8 = timezone(timedelta(hours=8))
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")

# 模块 ID → 模块名称映射（用于 LLM 归因提示词）
MODULE_NAMES = {
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


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def get_current_week_str() -> str:
    """获取当前周的 YYYY-WW 标识"""
    now = datetime.now(TZ_UTC8)
    iso = now.isocalendar()
    return f"{iso[0]}-{iso[1]:02d}"


def week_str_to_dates(week_str: str) -> tuple[str, str]:
    """将 YYYY-WW 转换为 start_date（周二）和 end_date（下周二）"""
    year, week_num = int(week_str.split("-")[0]), int(week_str.split("-")[1])
    monday = datetime.fromisocalendar(year, week_num, 1)
    tuesday_start = monday + timedelta(days=1)
    tuesday_end = tuesday_start + timedelta(days=7)
    return tuesday_start.strftime("%Y-%m-%d"), tuesday_end.strftime("%Y-%m-%d")


def make_label(week_str: str, start_date: str, end_date: str) -> str:
    """生成展示用标签，如 'W16 (4/14 - 4/21)'"""
    week_num = week_str.split("-")[1]
    s = datetime.strptime(start_date, "%Y-%m-%d")
    e = datetime.strptime(end_date, "%Y-%m-%d")
    return f"W{week_num} ({s.month}/{s.day} - {e.month}/{e.day})"


def get_week_tuesday_date(week_str: str) -> str:
    """获取该周的周二日期（用于调用飞书周报脚本）"""
    start_date, _ = week_str_to_dates(week_str)
    return start_date.replace("-", "/")


# ---------------------------------------------------------------------------
# Step 1: 提取飞书多维表格周报
# ---------------------------------------------------------------------------

def fetch_xp_weekly_report(week_str: str) -> dict:
    """
    调用 xp-weekly-report 技能的 fetch_weekly_data.py 脚本，
    提取指定周的飞书多维表格周报数据。
    返回: { "VoidZ": {"content": "...", "status": "..."}, ... }
    """
    tuesday_date = get_week_tuesday_date(week_str)
    logger.info("Step 1: 提取飞书周报，日期=%s", tuesday_date)

    result = subprocess.run(
        [sys.executable, str(XP_WEEKLY_SCRIPT), tuesday_date],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.warning("飞书周报提取失败: %s", result.stderr)
        return {}

    if not WEEKLY_DATA_FILE.exists():
        logger.warning("周报数据文件不存在: %s", WEEKLY_DATA_FILE)
        return {}

    with open(WEEKLY_DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("records", {})
    logger.info("飞书周报提取完成，共 %d 人", len(records))

    # 检查未填写成员，记录日志（实际通知由 Agent 在飞书群内发送）
    for name, info in records.items():
        if not info.get("content"):
            logger.warning("⚠️  %s 本周周报未填写，需要 Agent 在群内 @ 催促", name)

    return records


# ---------------------------------------------------------------------------
# Step 2: LLM 归因 — 将成员周报内容映射到模块
# ---------------------------------------------------------------------------

def attribute_reports_to_modules(
    records: dict,
    client: OpenAI
) -> dict[str, str]:
    """
    使用 LLM 将成员周报的自由文本内容归因到具体的 Module ID。
    返回: { "mod_xxx": "归因后的综合描述", ... }
    """
    if not records:
        logger.info("Step 2: 无飞书周报数据，跳过归因")
        return {}

    logger.info("Step 2: LLM 归因飞书周报到模块...")

    # 构建输入文本
    report_text = ""
    for name, info in records.items():
        content = info.get("content", "")
        if content:
            report_text += f"\n【{name}】\n{content}\n"

    module_list = "\n".join([f"- {mid}: {name}" for mid, name in MODULE_NAMES.items()])

    prompt = f"""你是一个项目管理助手。以下是 XP 团队本周各成员的周报内容：

{report_text}

请将上述内容按照以下模块进行归因分类，提取与每个模块相关的工作内容：

{module_list}

要求：
1. 只输出有实质内容的模块，没有相关内容的模块不要输出
2. 每个模块的内容要简洁精炼，保留关键进展和数字
3. 输出格式为 JSON，key 为模块 ID，value 为该模块的综合描述字符串
4. 只输出 JSON，不要有其他说明文字

示例输出格式：
{{
  "mod_data_ingestion": "Kafka Topic 配置完成，多语言问题跟进中...",
  "mod_uiux_design": "活动页面 UI 优化完成，移动端规范确定..."
}}"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        # 提取 JSON 部分
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        logger.info("归因完成，涉及 %d 个模块", len(result))
        return result
    except Exception as e:
        logger.error("LLM 归因失败: %s", e)
        return {}


# ---------------------------------------------------------------------------
# Step 3: 获取 Meegle 进度（占位，待 meegle_client.py 支持按周查询）
# ---------------------------------------------------------------------------

def fetch_meegle_progress(week_str: str) -> dict[str, str]:
    """
    从 meegle_client.py 获取各模块本周 Story/Defect 变更统计。
    返回: { "mod_xxx": "完成 3 个 Story，新增 2 个 Defect", ... }
    """
    logger.info("Step 3: 获取 Meegle 进度")
    from scripts.meegle_client import MeegleClient
    
    try:
        client = MeegleClient()
    except ValueError as e:
        logger.warning(f"MeegleClient 初始化失败: {e}")
        return {}

    start_date, end_date = week_str_to_dates(week_str)
    result = {}
    
    for mid, mname in MODULE_NAMES.items():
        # 提取模块名称的简写作为标签，例如 "用户系统（注册/推荐/账户）" -> "用户系统"
        label = mname.split("（")[0].strip()
        
        try:
            stats = client.list_work_items_by_week(
                module_label=label,
                week_start=start_date,
                week_end=end_date
            )
            
            completed = stats.get("completed_stories", 0)
            new_defects = stats.get("new_defects", 0)
            
            if completed == 0 and new_defects == 0:
                result[mid] = "本周无 Story 变更，新增 0 个 Defect"
            else:
                result[mid] = f"本周完成 {completed} 个 Story，新增 {new_defects} 个 Defect"
                
        except Exception as e:
            logger.error(f"获取模块 {mid} 的 Meegle 进度失败: {e}")
            result[mid] = "本周无 Story 变更，新增 0 个 Defect"
            
    return result


# ---------------------------------------------------------------------------
# Step 4: 获取群聊洞察
# ---------------------------------------------------------------------------

def fetch_chat_insights(week_str: str) -> dict[str, list[str]]:
    """
    实时拉取指定周的群聊消息，提取对模块进度有推进作用的关键话题。

    直接调用 extract_weekly_insights.get_weekly_insights_for_modules(week_str)，
    不再通过 subprocess 调用脚本，避免接口断层。

    返回: { "mod_xxx": ["话题1", "话题2"], ... }
    """
    logger.info("Step 4: 获取群聊洞察（直接函数调用）")

    # 将 scripts 目录加入 sys.path，确保可以直接导入
    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from extract_weekly_insights import get_weekly_insights_for_modules
        data = get_weekly_insights_for_modules(week_str)
        logger.info("群聊洞察提取完成，涉及 %d 个模块", len(data))
        return data
    except Exception as e:
        logger.warning("群聊洞察提取失败: %s", e)
    return {}


# ---------------------------------------------------------------------------
# Step 5: LLM 生成综合摘要
# ---------------------------------------------------------------------------

def generate_comprehensive_summary(
    module_id: str,
    module_name: str,
    xp_report: Optional[str],
    meegle_progress: Optional[str],
    chat_insights: list[str],
    client: OpenAI
) -> str:
    """
    基于多源数据，为单个模块生成高质量的综合摘要。
    """
    parts = []
    if xp_report:
        parts.append(f"【飞书周报】{xp_report}")
    if meegle_progress:
        parts.append(f"【Meegle进度】{meegle_progress}")
    if chat_insights:
        parts.append(f"【群聊洞察】" + "；".join(chat_insights))

    if not parts:
        return ""

    combined = "\n".join(parts)
    prompt = f"""你是一个项目管理助手。以下是「{module_name}」模块本周的多源进展数据：

{combined}

请基于以上信息，生成一段简洁、专业的本周进展摘要（2-4句话），要求：
1. 突出核心进展和关键节点
2. 保留重要的数字和状态信息
3. 如有阻塞或风险，明确指出
4. 语言简洁，不要重复信息
5. 只输出摘要文本，不要有其他说明"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("模块 %s 摘要生成失败: %s", module_id, e)
        # 降级：直接拼接原始数据
        return combined


# ---------------------------------------------------------------------------
# Step 5.5: 计算模块本周进度增量百分比
# ---------------------------------------------------------------------------

def calculate_weekly_progress(
    module_id: str,
    module_name: str,
    xp_report: Optional[str],
    meegle_progress: Optional[str],
    chat_insights: list[str],
    summary: str,
    client: OpenAI
) -> int:
    """
    基于三源加权算法，自动计算模块本周进度增量百分比（0-20 整数）。

    算法设计（三源加权，总分 clamp 到 [0, 20]）：

    1. Meegle Story 完成数（定量基准，权重 60%）：
       - 从 meegle_progress 文本中解析 completed_stories 数量
         （格式："本周完成 N 个 Story，新增 M 个 Defect"）
       - 每完成 1 个 Story 贡献 4%，上限 12%
       - 新增 Defect 超过 3 个时扣 1%（质量风险惩罚）

    2. 飞书周报内容质量（定性修正，权重 25%）：
       - 用 LLM 对 xp_report 文本打 0-4 分：
         0=无内容, 1=简单提及, 2=有具体进展, 3=有里程碑, 4=有上线/交付
       - 分数映射：0→0%, 1→2%, 2→5%, 3→7%, 4→10%

    3. 群聊洞察质量（补充修正，权重 15%）：
       - 有 1 条以上相关洞察：+2%
       - 有 3 条以上相关洞察：+3%（上限 +5%）
       - 洞察中含有「上线」「完成」「交付」等关键词：额外 +2%

    4. 最终 LLM 一致性校验：
       - 将三源分数合计（clamp 到 [0, 20]）和综合摘要文本一起传给 LLM
       - LLM 判断数字与摘要描述是否一致，输出最终 score（整数，0-20）

    Args:
        module_id:       模块 ID（如 "mod_casino"）
        module_name:     模块名称（如 "Casino 游戏平台"）
        xp_report:       飞书周报文本（可为 None）
        meegle_progress: Meegle 进度文本（格式："本周完成 N 个 Story，新增 M 个 Defect"）
        chat_insights:   群聊洞察列表（可为空列表）
        summary:         generate_comprehensive_summary() 生成的综合摘要文本
        client:          OpenAI 客户端实例

    Returns:
        0-20 之间的整数，表示本周进度增量百分比。任何异常情况返回 0。
    """
    import re

    try:
        # ----------------------------------------------------------------
        # 源 1：Meegle Story 完成数（定量基准）
        # ----------------------------------------------------------------
        meegle_score = 0
        completed_stories = 0
        new_defects = 0

        if meegle_progress:
            # 解析格式："本周完成 N 个 Story，新增 M 个 Defect"
            story_match = re.search(r'本周完成\s*(\d+)\s*个\s*Story', meegle_progress)
            defect_match = re.search(r'新增\s*(\d+)\s*个\s*Defect', meegle_progress)
            if story_match:
                completed_stories = int(story_match.group(1))
            if defect_match:
                new_defects = int(defect_match.group(1))

        # 每完成 1 个 Story 贡献 4%，上限 12%
        meegle_score = min(completed_stories * 4, 12)
        # 新增 Defect 超过 3 个时扣 1%
        if new_defects > 3:
            meegle_score = max(0, meegle_score - 1)

        # ----------------------------------------------------------------
        # 源 2：飞书周报内容质量（定性修正，LLM 打分）
        # ----------------------------------------------------------------
        xp_score = 0
        xp_score_map = {0: 0, 1: 2, 2: 5, 3: 7, 4: 10}

        if xp_report and xp_report.strip():
            xp_prompt = f"""请对以下飞书周报文本的内容质量打分（0-4分）：

文本：
{xp_report}

评分标准：
0 = 无内容或"本周无进展"
1 = 简单提及工作，无具体产出
2 = 有具体进展描述（如"完成了X功能开发"）
3 = 有明确里程碑达成（如"完成联调"、"提测"）
4 = 有上线/交付/验收等最终产出

请只输出一个 0-4 之间的整数，不要有其他说明。"""
            try:
                xp_resp = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{"role": "user", "content": xp_prompt}],
                    temperature=0.0,
                )
                raw_score = xp_resp.choices[0].message.content.strip()
                llm_xp_score = int(re.search(r'[0-4]', raw_score).group())
                xp_score = xp_score_map.get(llm_xp_score, 0)
            except Exception as e:
                logger.warning("模块 %s 飞书周报 LLM 打分失败: %s", module_id, e)
                xp_score = 0

        # ----------------------------------------------------------------
        # 源 3：群聊洞察质量（补充修正）
        # ----------------------------------------------------------------
        chat_score = 0
        if chat_insights:
            insight_count = len(chat_insights)
            if insight_count >= 3:
                chat_score = 3
            elif insight_count >= 1:
                chat_score = 2

            # 洞察中含有关键词时额外加分（上限 +5%）
            keyword_bonus = 0
            keywords = ["上线", "完成", "交付"]
            combined_insights = "；".join(chat_insights)
            if any(kw in combined_insights for kw in keywords):
                keyword_bonus = 2
            chat_score = min(chat_score + keyword_bonus, 5)

        # ----------------------------------------------------------------
        # 三源合计（clamp 到 [0, 20]）
        # ----------------------------------------------------------------
        raw_total = min(max(meegle_score + xp_score + chat_score, 0), 20)

        # ----------------------------------------------------------------
        # 最终 LLM 一致性校验
        # ----------------------------------------------------------------
        final_score = raw_total
        if summary and summary.strip():
            consistency_prompt = f"""你是一个项目进度评估助手。

模块「{module_name}」本周综合摘要如下：
{summary}

基于三源数据（Meegle Story 完成数、飞书周报质量、群聊洞察）的初步评分为：{raw_total}%（满分 20%）。

请判断：这个分数与摘要描述是否一致？
- 如果摘要说"本周无进展"或类似表述，但分数较高，请调低分数到 0-2
- 如果摘要描述了明确的上线/交付成果，但分数偏低，可适当调高
- 如果基本一致，保持原分数

请只输出一个 0-20 之间的整数作为最终分数，不要有其他说明。"""
            try:
                consistency_resp = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{"role": "user", "content": consistency_prompt}],
                    temperature=0.0,
                )
                raw_final = consistency_resp.choices[0].message.content.strip()
                match = re.search(r'\b([0-9]|1[0-9]|20)\b', raw_final)
                if match:
                    final_score = int(match.group())
                    final_score = min(max(final_score, 0), 20)
            except Exception as e:
                logger.warning("模块 %s LLM 一致性校验失败: %s，使用三源合计分数 %d", module_id, e, raw_total)
                final_score = raw_total

        logger.info(
            "  📊 %s: meegle=%d%% xp=%d%% chat=%d%% raw=%d%% final=%d%%",
            module_name, meegle_score, xp_score, chat_score, raw_total, final_score
        )
        return final_score

    except Exception as e:
        logger.error("模块 %s calculate_weekly_progress 异常: %s", module_id, e)
        return 0


# ---------------------------------------------------------------------------
# Step 6: 注入 dashboard_data.json
# ---------------------------------------------------------------------------

def inject_to_dashboard(
    week_str: str,
    module_updates: dict,  # { module_id: { "update": str, "sources": dict } }
    dry_run: bool = False
):
    """
    将生成的周报数据注入 dashboard_data.json，并更新 weekly_periods。
    """
    logger.info("Step 6: 注入 dashboard_data.json，week=%s", week_str)

    with open(DASHBOARD_FILE, encoding="utf-8") as f:
        data = json.load(f)

    start_date, end_date = week_str_to_dates(week_str)
    current_week = get_current_week_str()
    updated_count = 0

    for module in data.get("modules", []):
        mid = module["id"]
        if mid not in module_updates:
            continue

        update_data = module_updates[mid]
        new_entry = {
            "week": week_str,
            "start_date": start_date,
            "end_date": end_date,
            "update": update_data.get("update", ""),
            "sources": update_data.get("sources", {}),
        }
        if "activity" in update_data:
            new_entry["activity"] = update_data["activity"]

        # 移除同周旧数据，插入新数据到最前
        module["weekly_updates"] = [
            w for w in module.get("weekly_updates", [])
            if w.get("week") != week_str
        ]
        module["weekly_updates"].insert(0, new_entry)

        # 同步更新 weekly_progress_percentage 字段（覆盖旧値）
        if "weekly_progress_percentage" in update_data:
            module["weekly_progress_percentage"] = update_data["weekly_progress_percentage"]
            logger.info(
                "  📊 %s: weekly_progress_percentage=%d%%",
                module.get("name", mid),
                update_data["weekly_progress_percentage"]
            )

        updated_count += 1
        logger.info("  \u2705 %s: 周报已更新", module.get("name", mid))

    # 更新 weekly_periods
    existing_periods = {p["week"]: p for p in data.get("weekly_periods", [])}
    existing_periods[week_str] = {
        "week": week_str,
        "start_date": start_date,
        "end_date": end_date,
        "label": make_label(week_str, start_date, end_date),
        "is_current": (week_str == current_week)
    }
    # 同步更新其他周的 is_current
    for w, p in existing_periods.items():
        p["is_current"] = (w == current_week)
    data["weekly_periods"] = sorted(
        existing_periods.values(), key=lambda x: x["week"], reverse=True
    )
    data["last_updated"] = datetime.now(TZ_UTC8).strftime("%Y-%m-%d %H:%M:%S")

    if dry_run:
        logger.info("[DRY RUN] 不写入文件，共 %d 个模块待更新", updated_count)
        return updated_count

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("✅ 注入完成，共更新 %d 个模块", updated_count)
    return updated_count


# ---------------------------------------------------------------------------
# Step 7: 飞书通知
# ---------------------------------------------------------------------------

def send_lark_notification(week_str: str, updated_count: int, dry_run: bool = False):
    """通过 lark-secretary 向飞书群发送周报完成通知（含信息纠正入口）"""
    if dry_run:
        logger.info("[DRY RUN] 跳过飞书通知")
        return

    label = make_label(week_str, *week_str_to_dates(week_str))
    body = (
        f"**{label} 周报已生成完毕**\n\n"
        f"本次共更新 **{updated_count}** 个模块的进度数据，"
        f"数据来源：飞书多维表格周报 + Meegle 进度 + 群聊洞察。\n\n"
        f"请前往看板查看各模块本周详细进展。\n\n"
        f"---\n"
        f"**📝 信息纠正 / 补充入口**\n"
        f"如果 AI 提取的话题信息有偏差，或有群外决策/进展未被记录，"
        f"请直接回复本卡片，格式：\n"
        f"> `纠正：[话题名] 实际情况是……`\n"
        f"> `补充：[新话题] 决策/进展是……`\n\n"
        f"AI 秘书将在下次运行时读取并更新记录。"
    )

    if not LARK_SECRETARY.exists():
        logger.warning("lark-secretary 脚本不存在，跳过通知")
        return

    result = subprocess.run(
        [
            sys.executable, str(LARK_SECRETARY),
            "--title", f"✅ {label} 周报已更新",
            "--body", body,
            "--color", "green"
        ],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        logger.info("飞书通知发送成功")
    else:
        logger.warning("飞书通知发送失败: %s", result.stderr)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run(week_str: str, dry_run: bool = False, skip_notify: bool = False):
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║           周报汇总主流程 开始                           ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("周期: %s | dry_run=%s", week_str, dry_run)

    client = OpenAI()

    # Step 1: 飞书周报
    xp_records = fetch_xp_weekly_report(week_str)

    # Step 2: LLM 归因
    attributed = attribute_reports_to_modules(xp_records, client)

    # Step 3: Meegle 进度
    meegle_data = fetch_meegle_progress(week_str)

    # Step 4: 群聊洞察
    chat_data = fetch_chat_insights(week_str)

    # Step 5: 为每个模块生成综合摘要
    logger.info("Step 5: 生成各模块综合摘要...")
    module_updates = {}
    all_module_ids = set(attributed) | set(meegle_data) | set(chat_data)

    for mid in all_module_ids:
        module_name = MODULE_NAMES.get(mid, mid)
        xp_report = attributed.get(mid)
        meegle_progress = meegle_data.get(mid)
        insights = chat_data.get(mid, [])

        summary = generate_comprehensive_summary(
            mid, module_name, xp_report, meegle_progress, insights, client
        )
        if summary:
            # Step 5.5: 采集本周交付活跃度数据（客观事实，不依赖估算）
            completed_stories = 0
            new_defects = 0
            resolved_defects = 0
            if meegle_progress:
                import re as _re
                m_story = _re.search(r'完成\s*(\d+)\s*个\s*Story', meegle_progress)
                m_new_def = _re.search(r'新增\s*(\d+)\s*个\s*Defect', meegle_progress)
                m_res_def = _re.search(r'解决\s*(\d+)\s*个\s*Defect', meegle_progress)
                if m_story: completed_stories = int(m_story.group(1))
                if m_new_def: new_defects = int(m_new_def.group(1))
                if m_res_def: resolved_defects = int(m_res_def.group(1))
            chat_insight_count = len(insights) if insights else 0
            activity = {
                "completed_stories": completed_stories,
                "new_defects": new_defects,
                "resolved_defects": resolved_defects,
                "chat_insight_count": chat_insight_count,
            }

            module_updates[mid] = {
                "update": summary,
                "activity": activity,
                "sources": {
                    "xp_weekly_report": xp_report,
                    "bitable_summary": None,  # 待 bitable 接口扩展后填充
                    "meegle_progress": meegle_progress,
                    "chat_insights": insights
                }
            }
            logger.info(
                "  \u2705 %s: 摘要生成完成，activity=story:%d def+%d/-%d insight:%d",
                module_name, completed_stories, new_defects, resolved_defects, chat_insight_count
            )

    logger.info("共生成 %d 个模块的综合摘要", len(module_updates))

    # Step 6: 注入数据
    updated_count = inject_to_dashboard(week_str, module_updates, dry_run=dry_run)

    # Step 7: 飞书通知
    if not skip_notify:
        send_lark_notification(week_str, updated_count, dry_run=dry_run)

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║           周报汇总主流程 完成                           ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    return {"status": "success", "week": week_str, "updated_modules": updated_count}


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="周报汇总主脚本 — Agent 驱动的多源数据聚合",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 run_weekly_report.py                    # 汇总当前周
  python3 run_weekly_report.py --week 2026-16     # 汇总指定周
  python3 run_weekly_report.py --dry-run          # 预览模式
  python3 run_weekly_report.py --skip-notify      # 跳过飞书通知
        """
    )
    parser.add_argument(
        "--week",
        default=None,
        help="指定周标识，格式 YYYY-WW（默认为当前周）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("DRY_RUN", "false").lower() == "true",
        help="预览模式，不写入文件，不发送通知"
    )
    parser.add_argument(
        "--skip-notify",
        action="store_true",
        help="跳过飞书通知"
    )
    args = parser.parse_args()

    week_str = args.week or get_current_week_str()
    result = run(week_str=week_str, dry_run=args.dry_run, skip_notify=args.skip_notify)
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

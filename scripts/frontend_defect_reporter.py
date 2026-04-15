"""
前端缺陷自动报送脚本 (Frontend Defect Reporter)
=================================================
功能：
  1. 接收来自前端相关群聊的消息（可通过 stdin/参数/调用方传入）。
  2. 使用 LLM 进行意图识别，判断是否为前端 Bug Report。
  3. 若信息不完整（completeness_score < 80），生成补全询问话术。
  4. 信息完整后，自动调用 Meegle API 创建 Defect 工单。
  5. 返回结构化结果（工单 ID、链接、询问话术等）。

环境变量要求（在 .env 中配置）：
  - DASHSCOPE_API_KEY: 通义千问 API Key（阿里云百炼平台获取）
  - QWEN_MODEL: (可选) 模型名称，默认 qwen-plus（可选 qwen-turbo / qwen-max）
  - MEEGLE_TOKEN: Meegle Personal Access Token
  - MEEGLE_PROJECT_KEY: 前端缺陷对应的 Meegle 项目 Key（如 frontend_opt）
  - MEEGLE_BASE_URL: (可选) Meegle API 基础 URL

用法示例：
  python3 frontend_defect_reporter.py --message "游戏渲染加载很慢，直连快但VPN慢" --sender "VoidZ"
  python3 frontend_defect_reporter.py --json-file sample_message.json
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from openai import OpenAI  # 通义千问兼容 OpenAI SDK，无需额外安装
from meegle_client import MeegleClient

# 通义千问 API 配置（阿里云百炼平台，兼容 OpenAI 接口规范）
_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_QWEN_DEFAULT_MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("frontend_defect_reporter")

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 完整度达标阈值
COMPLETENESS_THRESHOLD = 80

# 前端相关群组关键词（用于快速过滤非前端消息）
FRONTEND_GROUP_KEYWORDS = [
    "前端", "frontend", "UI", "H5", "移动端", "web", "页面", "渲染",
    "样式", "交互", "组件", "上线前前端优化", "设计稿"
]

# Bug 相关关键词（辅助意图识别）
BUG_SIGNAL_KEYWORDS = [
    "bug", "问题", "报错", "错误", "失败", "异常", "崩溃", "卡死",
    "加载慢", "加载失败", "显示不对", "白屏", "闪退", "不生效", "没反应"
]

# 优先级映射（中文 → Meegle 枚举）
PRIORITY_MAP = {
    "阻塞": "Blocker",
    "阻碍": "Blocker",
    "blocker": "Blocker",
    "高": "High",
    "high": "High",
    "紧急": "High",
    "中": "Medium",
    "medium": "Medium",
    "普通": "Medium",
    "低": "Low",
    "low": "Low",
}

# ---------------------------------------------------------------------------
# LLM 调用封装
# ---------------------------------------------------------------------------

def call_llm(system_prompt: str, user_content: str, model: str = None) -> str:
    """
    调用通义千问 LLM，返回纯文本响应。
    使用阿里云百炼平台的 OpenAI 兼容接口，只需替换 base_url 和 api_key。
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "缺少 DASHSCOPE_API_KEY 环境变量。\n"
            "请前往 https://bailian.console.aliyun.com/ 创建 API Key 并配置。"
        )
    client = OpenAI(
        api_key=api_key,
        base_url=_QWEN_BASE_URL,
    )
    model = model or _QWEN_DEFAULT_MODEL
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# 核心分析：意图识别 + 实体提取 + 完整度评分
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM_PROMPT = """
你是一个专业的项目管理 AI 秘书，负责分析前端技术群聊消息，判断是否为前端 Bug 报告，并提取关键信息。

请严格按照以下 JSON 格式输出，不要包含任何其他说明文字：

{
  "is_frontend_bug": true/false,
  "confidence": 0.0-1.0,
  "extracted": {
    "module_name": "模块名称（如：游戏模块、购物车模块、菜单模块），无法判断则为 null",
    "description": "Bug 现象的简洁描述（1-2句话），无法提取则为 null",
    "reproduce_steps": "复现步骤或环境信息，无法提取则为 null",
    "priority": "优先级（High/Medium/Low/Blocker），无法判断则为 null",
    "impact": "影响范围（如：所有用户、iOS端、墨西哥地区），无法提取则为 null",
    "reporter": "发现者/报告人姓名，无法提取则为 null",
    "assignee_hint": "消息中被@或提到的可能负责人，无法提取则为 null"
  },
  "completeness_score": 0-100,
  "missing_fields": ["缺失的字段名列表，如 reproduce_steps、priority"],
  "suggested_title": "建议的 Meegle 工单标题（格式：[模块] 现象描述）"
}

完整度评分规则（满分 100）：
- 基础分 40：包含明确的 Bug 现象描述（description 不为 null）
- 模块归属 20：module_name 不为 null
- 复现步骤 15：reproduce_steps 不为 null
- 优先级 15：priority 不为 null
- 影响范围 10：impact 不为 null

注意：
- 若 is_frontend_bug 为 false，其余字段可以为空。
- confidence 表示你对"这是前端 Bug"判断的置信度。
"""


def analyze_message(message_text: str, sender: str = "") -> Dict:
    """
    使用 LLM 分析消息，返回结构化的分析结果。
    """
    user_content = f"发送者: {sender}\n消息内容: {message_text}"
    raw = call_llm(ANALYSIS_SYSTEM_PROMPT, user_content)

    # 尝试解析 JSON
    try:
        # 处理 LLM 可能包裹在 ```json ... ``` 中的情况
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        logger.error("LLM 返回了非 JSON 内容: %s\n原始内容: %s", e, raw)
        result = {
            "is_frontend_bug": False,
            "confidence": 0.0,
            "extracted": {},
            "completeness_score": 0,
            "missing_fields": [],
            "suggested_title": "",
        }

    return result


# ---------------------------------------------------------------------------
# 补全询问话术生成
# ---------------------------------------------------------------------------

def generate_inquiry_message(
    sender: str,
    original_message: str,
    analysis: Dict,
) -> str:
    """
    根据缺失字段生成询问话术。
    """
    missing = analysis.get("missing_fields", [])
    extracted = analysis.get("extracted", {})
    description = extracted.get("description") or original_message[:50]

    field_questions = {
        "reproduce_steps": "**复现步骤/环境**：(如：测试环境还是生产环境？具体操作路径？机型/浏览器？)",
        "priority": "**优先级**：(如：High 紧急阻塞测试 / Medium 影响体验 / Low 轻微问题)",
        "impact": "**影响范围**：(如：所有用户、iOS 端、特定地区？)",
        "module_name": "**所属模块**：(如：游戏模块、购物车、菜单、Bet Slip？)",
    }

    questions_list = []
    for i, field in enumerate(missing, start=1):
        if field in field_questions:
            questions_list.append(f"{i}. {field_questions[field]}")

    if not questions_list:
        return ""

    questions_str = "\n".join(questions_list)
    sender_mention = f"@{sender} " if sender else ""

    return (
        f"{sender_mention}**[紧急确认] 关于前端 Bug 报送**\n"
        f"收到您反馈的「{description}」。"
        f"为了在 Meegle 自动创建缺陷工单，请补充以下信息：\n\n"
        f"{questions_str}\n\n"
        f"请直接回复，我将自动为您建档。"
    )


# ---------------------------------------------------------------------------
# Meegle 工单创建
# ---------------------------------------------------------------------------

def build_meegle_payload(analysis: Dict, original_message: str) -> Dict:
    """
    将 LLM 分析结果转换为 Meegle API 所需的字段。
    """
    extracted = analysis.get("extracted", {})

    # 标题
    title = analysis.get("suggested_title") or (
        f"[前端] {extracted.get('description', original_message[:40])}"
    )

    # 描述（Markdown 格式）
    desc_parts = [f"**现象描述**\n{extracted.get('description', original_message)}"]
    if extracted.get("reproduce_steps"):
        desc_parts.append(f"\n**复现步骤/环境**\n{extracted['reproduce_steps']}")
    if extracted.get("impact"):
        desc_parts.append(f"\n**影响范围**\n{extracted['impact']}")
    if extracted.get("reporter"):
        desc_parts.append(f"\n**报告人**\n{extracted['reporter']}")
    desc_parts.append(f"\n---\n*由 AI 秘书自动创建于 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    description = "\n".join(desc_parts)

    # 优先级映射
    raw_priority = (extracted.get("priority") or "Medium").lower()
    priority = PRIORITY_MAP.get(raw_priority, "Medium")

    return {
        "name": title,
        "description": description,
        "priority": priority,
        "assignee_hint": extracted.get("assignee_hint"),
    }


def dispatch_to_meegle(
    meegle: MeegleClient,
    payload: Dict,
    project_key: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """
    调用 Meegle API 创建 Defect 工单。
    返回 (success, work_item_id, work_item_url)。
    """
    assignee_hint = payload.pop("assignee_hint", None)
    assignee_user_key = None

    # 尝试通过邮箱匹配 Meegle 用户
    if assignee_hint:
        # 若 assignee_hint 是邮箱格式则直接查询
        if "@" in assignee_hint and "." in assignee_hint:
            assignee_user_key = meegle.query_user_by_email(assignee_hint)
        else:
            logger.info("assignee_hint '%s' 不是邮箱格式，跳过用户匹配", assignee_hint)

    try:
        result = meegle.create_work_item(
            project_key=project_key,
            work_item_type_key="defect",
            name=payload["name"],
            description=payload["description"],
            priority=payload["priority"],
            assignee_user_key=assignee_user_key,
        )
        work_item_id = result.get("work_item_id", "")
        # 构建访问链接（格式依据 Meegle 实际 URL 规则）
        base_url = os.environ.get("MEEGLE_WEB_URL", "https://project.feishu.cn")
        proj = project_key or meegle.project_key
        work_item_url = f"{base_url}/{proj}/defect/{work_item_id}"
        return True, work_item_id, work_item_url
    except Exception as exc:
        logger.error("Meegle 工单创建失败: %s", exc)
        return False, "", str(exc)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def process_message(
    message_text: str,
    sender: str = "",
    project_key: Optional[str] = None,
    dry_run: bool = False,
) -> Dict:
    """
    主处理函数：接收一条消息，执行完整的分析→询问→报送流程。

    Args:
        message_text: 群聊消息原文。
        sender: 消息发送者姓名（用于 @提及）。
        project_key: Meegle 项目 Key，不传则使用环境变量。
        dry_run: 若为 True，则跳过实际的 Meegle API 调用（用于测试）。

    Returns:
        结构化结果字典，包含以下字段：
          - action: 'dispatched' | 'inquiry_needed' | 'not_bug' | 'error'
          - analysis: LLM 分析结果
          - inquiry_message: 需要发送的询问话术（action == 'inquiry_needed' 时有值）
          - work_item_id: Meegle 工单 ID（action == 'dispatched' 时有值）
          - work_item_url: Meegle 工单链接（action == 'dispatched' 时有值）
          - notify_message: 需要在群聊中发送的通知（action == 'dispatched' 时有值）
    """
    logger.info("开始处理消息: sender=%s, length=%d", sender, len(message_text))

    # Step 1: LLM 意图分析
    analysis = analyze_message(message_text, sender)
    logger.info(
        "分析结果: is_frontend_bug=%s, confidence=%.2f, completeness=%d",
        analysis.get("is_frontend_bug"),
        analysis.get("confidence", 0),
        analysis.get("completeness_score", 0),
    )

    # Step 2: 非前端 Bug，直接返回
    if not analysis.get("is_frontend_bug") or analysis.get("confidence", 0) < 0.6:
        return {
            "action": "not_bug",
            "analysis": analysis,
            "inquiry_message": None,
            "work_item_id": None,
            "work_item_url": None,
            "notify_message": None,
        }

    # Step 3: 完整度不足，生成询问话术
    score = analysis.get("completeness_score", 0)
    if score < COMPLETENESS_THRESHOLD:
        inquiry = generate_inquiry_message(sender, message_text, analysis)
        logger.info("信息不完整（score=%d），生成询问话术", score)
        return {
            "action": "inquiry_needed",
            "analysis": analysis,
            "inquiry_message": inquiry,
            "work_item_id": None,
            "work_item_url": None,
            "notify_message": None,
        }

    # Step 4: 信息完整，构建 Meegle Payload
    payload = build_meegle_payload(analysis, message_text)
    logger.info("信息完整（score=%d），准备报送至 Meegle: %s", score, payload["name"])

    if dry_run:
        logger.info("[DRY RUN] 跳过 Meegle API 调用")
        return {
            "action": "dispatched",
            "analysis": analysis,
            "inquiry_message": None,
            "work_item_id": "DRY_RUN_ID",
            "work_item_url": "https://project.feishu.cn/dry-run",
            "notify_message": f"✅ [DRY RUN] 模拟创建 Meegle 工单：{payload['name']}",
        }

    # Step 5: 调用 Meegle API
    meegle = MeegleClient(project_key=project_key)
    success, work_item_id, work_item_url = dispatch_to_meegle(
        meegle, payload, project_key=project_key
    )

    if success:
        extracted = analysis.get("extracted", {})
        assignee_str = extracted.get("assignee_hint") or "待分配"
        notify_message = (
            f"✅ **已成功在 Meegle 创建 Bug 工单**\n"
            f"**ID**: {work_item_id}\n"
            f"**标题**: {payload['name']}\n"
            f"**优先级**: {payload['priority']}\n"
            f"**指派给**: {assignee_str}\n"
            f"**链接**: {work_item_url}"
        )
        return {
            "action": "dispatched",
            "analysis": analysis,
            "inquiry_message": None,
            "work_item_id": work_item_id,
            "work_item_url": work_item_url,
            "notify_message": notify_message,
        }
    else:
        return {
            "action": "error",
            "analysis": analysis,
            "inquiry_message": None,
            "work_item_id": None,
            "work_item_url": work_item_url,  # 此时存储的是错误信息
            "notify_message": f"⚠️ 创建 Meegle 工单失败，请稍后重试或手动创建。\n错误详情：{work_item_url}",
        }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="前端缺陷自动报送工具：分析群聊消息并在 Meegle 创建 Defect 工单"
    )
    parser.add_argument("--message", "-m", type=str, help="消息原文")
    parser.add_argument("--sender", "-s", type=str, default="", help="消息发送者姓名")
    parser.add_argument("--project-key", "-p", type=str, default=None, help="Meegle 项目 Key")
    parser.add_argument(
        "--json-file", "-f", type=str, default=None,
        help="从 JSON 文件读取消息（格式：{message, sender, project_key}）"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="测试模式：跳过实际的 Meegle API 调用"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="将结果输出到指定 JSON 文件"
    )
    args = parser.parse_args()

    # 读取消息
    if args.json_file:
        with open(args.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        message_text = data.get("message", "")
        sender = data.get("sender", args.sender)
        project_key = data.get("project_key", args.project_key)
    elif args.message:
        message_text = args.message
        sender = args.sender
        project_key = args.project_key
    else:
        print("错误：请通过 --message 或 --json-file 提供消息内容。")
        parser.print_help()
        sys.exit(1)

    # 执行处理
    result = process_message(
        message_text=message_text,
        sender=sender,
        project_key=project_key,
        dry_run=args.dry_run,
    )

    # 输出结果
    print("\n" + "=" * 60)
    print(f"处理结果: {result['action'].upper()}")
    print("=" * 60)

    if result["action"] == "not_bug":
        print("该消息未被识别为前端 Bug，无需处理。")
        print(f"LLM 置信度: {result['analysis'].get('confidence', 0):.2f}")

    elif result["action"] == "inquiry_needed":
        print("信息不完整，需要发送以下询问话术：\n")
        print(result["inquiry_message"])
        print(f"\n完整度评分: {result['analysis'].get('completeness_score', 0)}/100")
        print(f"缺失字段: {result['analysis'].get('missing_fields', [])}")

    elif result["action"] == "dispatched":
        print(result["notify_message"])

    elif result["action"] == "error":
        print(result["notify_message"])

    # 保存到文件
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")

    return result


if __name__ == "__main__":
    main()

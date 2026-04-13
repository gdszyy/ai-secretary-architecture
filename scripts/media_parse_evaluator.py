#!/usr/bin/env python3
"""
富媒体解析前评估器 (MediaParseEvaluator)

在对图片、链接、文档执行实际解析之前，先评估：
  1. 信息获取目标 (parse_goal)      — 解析这个内容最重要要拿到什么
  2. 解析价值评分 (relevance_score) — 当前项目/话题语境下，解析它有多大意义
  3. 停止解析逻辑 (stop_condition)  — 何时可以提前停止，避免浪费 Token/时间

评估结果决定是否进入实际解析流程。
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI()

# ──────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────

@dataclass
class ParseDecision:
    """解析决策结果"""
    should_parse: bool          # 是否值得解析
    parse_goal: str             # 信息获取目标（最重要拿到什么）
    relevance_score: int        # 解析价值评分 0-100
    stop_condition: str         # 停止解析的条件描述
    skip_reason: Optional[str]  # 若不解析，原因是什么
    media_type: str             # image | url | file
    content_hint: str           # 内容摘要线索（来自消息上下文）

    def to_dict(self):
        return asdict(self)


# ──────────────────────────────────────────────
# 评估器核心
# ──────────────────────────────────────────────

EVALUATOR_SYSTEM_PROMPT = """你是一个 AI 项目秘书的"解析成本控制器"。

你的职责是：在对富媒体内容（图片/链接/文档）执行实际解析之前，
根据当前的项目上下文和话题语境，评估解析这个内容是否值得，以及解析的目标是什么。

请严格按照以下 JSON 格式输出，不要输出任何其他内容：
{
  "should_parse": true 或 false,
  "parse_goal": "解析这个内容最重要要获取的信息，一句话描述，如'确认设计稿是否包含支付页面的改动'",
  "relevance_score": 0-100的整数,
  "stop_condition": "何时可以停止解析，如'一旦找到支付相关的截图或文字说明即可停止'，或'全文扫描完毕'",
  "skip_reason": "若 should_parse=false，说明原因；否则填 null"
}

relevance_score 评分标准：
- 90-100：内容直接包含项目关键决策、Bug 截图、需求变更
- 70-89：内容与当前讨论话题高度相关
- 40-69：内容可能有参考价值，但不紧迫
- 10-39：内容与项目关联度低，如外部新闻、无关链接
- 0-9：完全无关，如表情包、广告

should_parse 决策逻辑：
- relevance_score >= 60 且 media_type 为 image/file：建议解析
- relevance_score >= 50 且 media_type 为 url：建议解析
- relevance_score < 40：跳过解析，记录 skip_reason
- 若消息上下文明确说明内容无关（如"随便看看"、"没事"）：直接跳过
"""

def evaluate_before_parse(
    media_type: str,          # "image" | "url" | "file"
    content_hint: str,        # 内容线索：URL、文件名、图片描述等
    surrounding_messages: list[dict],  # 该消息前后 3-5 条的对话上下文
    project_context: Optional[dict] = None,  # 当前项目模块信息
    current_thread_topic: Optional[str] = None,  # 当前话题主题
) -> ParseDecision:
    """
    在解析富媒体内容之前，先评估是否值得解析。

    Args:
        media_type: 媒体类型 image/url/file
        content_hint: 内容线索（URL、文件名、图片 alt 等）
        surrounding_messages: 该消息前后的对话上下文列表
        project_context: 项目模块信息（可选）
        current_thread_topic: 当前话题主题（可选）

    Returns:
        ParseDecision 对象
    """
    # 构建上下文描述
    ctx_lines = []
    for m in surrounding_messages[-5:]:  # 最多取最近 5 条
        sender = m.get("sender", "?")[:8]
        text = m.get("text", "[非文本]")[:80]
        ctx_lines.append(f"  [{sender}]: {text}")
    ctx_str = "\n".join(ctx_lines) if ctx_lines else "  (无上下文)"

    project_str = ""
    if project_context:
        modules = project_context.get("modules", [])
        project_str = f"\n当前项目模块：{', '.join(modules[:8])}"

    thread_str = f"\n当前话题：{current_thread_topic}" if current_thread_topic else ""

    user_prompt = f"""需要评估是否解析以下富媒体内容：

媒体类型：{media_type}
内容线索：{content_hint}
{project_str}{thread_str}

该消息前后的对话上下文：
{ctx_str}

请评估解析价值并输出 JSON 决策。"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return ParseDecision(
        should_parse=result.get("should_parse", False),
        parse_goal=result.get("parse_goal", ""),
        relevance_score=result.get("relevance_score", 0),
        stop_condition=result.get("stop_condition", ""),
        skip_reason=result.get("skip_reason"),
        media_type=media_type,
        content_hint=content_hint
    )


# ──────────────────────────────────────────────
# 快速测试
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 解析前评估器测试 ===\n")

    test_cases = [
        {
            "label": "案例1：支付 Bug 截图",
            "media_type": "image",
            "content_hint": "screenshot_payment_error.png",
            "surrounding_messages": [
                {"sender": "ou_abc123", "text": "支付那边又报错了，看截图"},
                {"sender": "ou_def456", "text": "什么错误？"},
            ],
            "current_thread_topic": "支付网关报错排查",
        },
        {
            "label": "案例2：无关外部链接",
            "media_type": "url",
            "content_hint": "https://www.zhihu.com/question/12345",
            "surrounding_messages": [
                {"sender": "ou_abc123", "text": "哈哈这个问题有意思，随便看看"},
            ],
            "current_thread_topic": None,
        },
        {
            "label": "案例3：飞书 Wiki 文档",
            "media_type": "url",
            "content_hint": "https://kjpp4yydjn38.jp.larksuite.com/wiki/L22zwRQV3iC3Bfkhp0Ajb76qp2e",
            "surrounding_messages": [
                {"sender": "ou_abc123", "text": "新的需求文档在这里，大家看一下"},
                {"sender": "ou_def456", "text": "好的"},
            ],
            "current_thread_topic": "新功能需求评审",
            "project_context": {"modules": ["用户系统", "支付网关", "风控系统", "活动页面"]},
        },
        {
            "label": "案例4：设计稿文件",
            "media_type": "file",
            "content_hint": "活动页面_v3_最终版.fig",
            "surrounding_messages": [
                {"sender": "ou_abc123", "text": "设计稿更新了，主要改了活动页的按钮颜色"},
                {"sender": "ou_def456", "text": "好，我看看"},
            ],
            "current_thread_topic": "活动页面设计评审",
            "project_context": {"modules": ["活动页面", "用户系统"]},
        },
    ]

    for case in test_cases:
        print(f"--- {case['label']} ---")
        decision = evaluate_before_parse(
            media_type=case["media_type"],
            content_hint=case["content_hint"],
            surrounding_messages=case["surrounding_messages"],
            project_context=case.get("project_context"),
            current_thread_topic=case.get("current_thread_topic"),
        )
        icon = "✅ 解析" if decision.should_parse else "⏭️  跳过"
        print(f"  决策: {icon}  评分: {decision.relevance_score}/100")
        print(f"  目标: {decision.parse_goal}")
        print(f"  停止条件: {decision.stop_condition}")
        if decision.skip_reason:
            print(f"  跳过原因: {decision.skip_reason}")
        print()

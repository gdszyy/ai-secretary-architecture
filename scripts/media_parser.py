#!/usr/bin/env python3
"""
富媒体内容解析器 (MediaParser)

在 ParseEvaluator 决定"值得解析"后，执行实际的内容提取。
支持三类媒体：
  - image  : 调用 Vision LLM 理解图片内容
  - url    : 抓取网页文本 / 识别 Lark 文档并调用 Lark Doc API
  - file   : 下载 Lark 文件后按类型处理（PDF/图片/文档）

每次解析都携带 parse_goal 和 stop_condition，引导 LLM 聚焦提取。
"""

import os
import re
import json
import base64
import requests
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI()
LARK_APP_ID = os.environ.get("LARK_APP_ID")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET")

# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def _get_lark_token() -> str:
    resp = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
    )
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]


def _is_lark_doc_url(url: str) -> bool:
    """判断是否是飞书 Wiki / Doc 链接"""
    return bool(re.search(r'larksuite\.com/(wiki|docx|docs)/', url) or
                re.search(r'feishu\.cn/(wiki|docx|docs)/', url))


def _extract_lark_doc_token(url: str) -> Optional[str]:
    """从飞书文档 URL 中提取 document token"""
    m = re.search(r'/(wiki|docx|docs)/([A-Za-z0-9]+)', url)
    return m.group(2) if m else None


def _fetch_lark_doc_content(doc_token: str, doc_type: str = "wiki") -> str:
    """通过 Lark API 获取文档纯文本内容"""
    token = _get_lark_token()
    headers = {"Authorization": f"Bearer {token}"}

    if doc_type == "wiki":
        # 先获取 wiki node 的 obj_token
        resp = requests.get(
            f"https://open.larksuite.com/open-apis/wiki/v2/spaces/get_node",
            headers=headers,
            params={"token": doc_token}
        )
        if resp.status_code == 200 and resp.json().get("code") == 0:
            obj_token = resp.json()["data"]["node"]["obj_token"]
            obj_type = resp.json()["data"]["node"]["obj_type"]
            if obj_type == "doc":
                doc_token = obj_token
                doc_type = "docx"

    # 获取 docx 内容块
    resp = requests.get(
        f"https://open.larksuite.com/open-apis/docx/v1/documents/{doc_token}/raw_content",
        headers=headers
    )
    if resp.status_code == 200 and resp.json().get("code") == 0:
        return resp.json().get("data", {}).get("content", "")
    return f"[无法获取文档内容，状态码: {resp.status_code}]"


def _fetch_webpage_text(url: str, max_chars: int = 3000) -> str:
    """抓取网页并提取纯文本（简单版）"""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.texts = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ('script', 'style', 'nav', 'footer'):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ('script', 'style', 'nav', 'footer'):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip and data.strip():
                    self.texts.append(data.strip())

        parser = TextExtractor()
        parser.feed(resp.text)
        text = ' '.join(parser.texts)
        return text[:max_chars]
    except Exception as e:
        return f"[网页抓取失败: {e}]"


def _download_lark_image(message_id: str, image_key: str) -> Optional[bytes]:
    """从 Lark 下载图片字节流"""
    token = _get_lark_token()
    resp = requests.get(
        f"https://open.larksuite.com/open-apis/im/v1/messages/{message_id}/resources/{image_key}",
        headers={"Authorization": f"Bearer {token}"},
        params={"type": "image"}
    )
    if resp.status_code == 200:
        return resp.content
    return None


# ──────────────────────────────────────────────
# 核心解析函数
# ──────────────────────────────────────────────

def parse_image(
    image_bytes: bytes,
    parse_goal: str,
    stop_condition: str,
) -> str:
    """使用 Vision LLM 解析图片内容"""
    b64 = base64.b64encode(image_bytes).decode()
    
    system_prompt = f"""你是一个项目管理 AI 秘书，正在分析一张群聊中分享的图片。

信息获取目标：{parse_goal}
停止条件：{stop_condition}

请聚焦于目标，提取最关键的信息。若图片与目标无关，直接说明。
输出格式：一段简洁的文字描述，不超过 200 字。"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": system_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


def parse_url(
    url: str,
    parse_goal: str,
    stop_condition: str,
) -> str:
    """解析 URL 内容：飞书文档走 API，普通网页走抓取"""
    if _is_lark_doc_url(url):
        doc_token = _extract_lark_doc_token(url)
        doc_type = "wiki" if "/wiki/" in url else "docx"
        raw_content = _fetch_lark_doc_content(doc_token, doc_type)
        source_label = "飞书文档内容"
    else:
        raw_content = _fetch_webpage_text(url)
        source_label = "网页内容"

    if not raw_content or raw_content.startswith("["):
        return raw_content  # 返回错误信息

    # 用 LLM 按目标提炼
    system_prompt = f"""你是一个项目管理 AI 秘书，正在分析群聊中分享的{source_label}。

信息获取目标：{parse_goal}
停止条件：{stop_condition}

请从以下内容中，聚焦提取与目标最相关的信息，输出不超过 300 字的摘要。"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"内容（前 3000 字）：\n\n{raw_content[:3000]}"}
        ],
        max_tokens=400
    )
    return response.choices[0].message.content.strip()


def parse_file(
    file_name: str,
    file_bytes: Optional[bytes],
    parse_goal: str,
    stop_condition: str,
) -> str:
    """解析文件内容：图片文件走 Vision，PDF/文本走文字提取"""
    if file_bytes is None:
        return f"[文件 {file_name} 下载失败，无法解析]"

    ext = file_name.lower().rsplit('.', 1)[-1] if '.' in file_name else ''

    if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'):
        return parse_image(file_bytes, parse_goal, stop_condition)

    if ext == 'pdf':
        try:
            import io
            from pdfminer.high_level import extract_text_to_fp
            from pdfminer.layout import LAParams
            output = io.StringIO()
            extract_text_to_fp(io.BytesIO(file_bytes), output, laparams=LAParams())
            text = output.getvalue()[:3000]
        except Exception as e:
            text = f"[PDF 解析失败: {e}]"
        return _summarize_text(text, parse_goal, stop_condition, "PDF 文件")

    # 尝试按 UTF-8 文本处理
    try:
        text = file_bytes.decode('utf-8', errors='ignore')[:3000]
        return _summarize_text(text, parse_goal, stop_condition, f"{ext.upper()} 文件")
    except Exception:
        return f"[文件类型 .{ext} 暂不支持解析]"


def _summarize_text(text: str, parse_goal: str, stop_condition: str, source_label: str) -> str:
    """通用文本摘要提炼"""
    system_prompt = f"""你是一个项目管理 AI 秘书，正在分析群聊中分享的{source_label}。

信息获取目标：{parse_goal}
停止条件：{stop_condition}

请从以下内容中，聚焦提取与目标最相关的信息，输出不超过 300 字的摘要。"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        max_tokens=400
    )
    return response.choices[0].message.content.strip()


# ──────────────────────────────────────────────
# 统一入口
# ──────────────────────────────────────────────

def parse_media(
    media_type: str,
    content_hint: str,
    parse_goal: str,
    stop_condition: str,
    message_id: Optional[str] = None,
    image_key: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
) -> str:
    """
    统一富媒体解析入口（在 ParseEvaluator 决定解析后调用）

    Args:
        media_type: "image" | "url" | "file"
        content_hint: URL 或文件名
        parse_goal: 来自 ParseDecision.parse_goal
        stop_condition: 来自 ParseDecision.stop_condition
        message_id: Lark 消息 ID（下载图片时需要）
        image_key: Lark 图片 key（下载图片时需要）
        file_bytes: 已下载的文件字节（可选）

    Returns:
        解析结果文本
    """
    if media_type == "image":
        if image_key and message_id:
            img_bytes = _download_lark_image(message_id, image_key)
        elif file_bytes:
            img_bytes = file_bytes
        else:
            return "[图片无法获取：缺少 message_id 或 image_key]"
        return parse_image(img_bytes, parse_goal, stop_condition)

    elif media_type == "url":
        return parse_url(content_hint, parse_goal, stop_condition)

    elif media_type == "file":
        return parse_file(content_hint, file_bytes, parse_goal, stop_condition)

    return f"[未知媒体类型: {media_type}]"


# ──────────────────────────────────────────────
# 快速测试
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 富媒体解析器测试 ===\n")

    # 测试 URL 解析（飞书 Wiki 链接）
    test_url = "https://kjpp4yydjn38.jp.larksuite.com/wiki/L22zwRQV3iC3Bfkhp0Ajb76qp2e"
    print(f"--- 测试 URL 解析 ---")
    print(f"URL: {test_url}")
    result = parse_url(
        url=test_url,
        parse_goal="了解这份文档的主要内容和关键信息点",
        stop_condition="获取文档的核心结构和主要章节后即可停止"
    )
    print(f"解析结果：\n{result}\n")

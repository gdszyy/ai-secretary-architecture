# Lark 机器人与飞书妙记接入指导手册

**作者**: Manus AI
**日期**: 2026-04-10
**关联文档**: [`info_source_master_plan.md`](./info_source_master_plan.md), [`prereq_data_assessment.md`](./prereq_data_assessment.md)

---

## 概述

本文档是 AI Management 项目秘书系统中两个最核心信息来源——**Lark 群聊机器人**和**飞书妙记**——的完整接入操作指南。文档按照"先决条件 → 创建应用 → 配置权限 → 代码实现 → 验证测试"的顺序组织，可直接作为开发人员的操作手册使用。

---

## 第一部分：Lark 群聊机器人接入

### 1.1 先决条件

在开始之前，需要确认以下条件已满足：

| 条件 | 说明 | 负责人 |
| :--- | :--- | :--- |
| 飞书企业管理员权限 | 需要在飞书开放平台创建企业自建应用 | IT 管理员 |
| 服务器公网地址（或内网穿透） | 飞书事件推送需要一个可访问的 HTTPS 回调地址 | 后端开发 |
| Python 3.9+ 环境 | 运行接收服务 | 后端开发 |

### 1.2 在飞书开放平台创建企业自建应用

**Step 1**：访问 [Lark 开放平台](https://open.larksuite.com/app)，使用企业管理员账号登录，点击"创建企业自建应用"。

**Step 2**：填写应用基本信息：
- **应用名称**：`AI 项目秘书`
- **应用描述**：`XPBET 项目管理 AI 秘书，负责自动采集群聊信息并更新看板`
- **应用图标**：可选

**Step 3**：创建成功后，进入应用详情页，记录以下凭证（后续写入 `.env`）：

```
App ID:     cli_xxxxxxxxxxxxxxxx
App Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 1.3 申请必要权限

进入应用详情页 → **权限管理** → 搜索并开通以下权限：

| 权限标识 | 权限名称 | 用途 | 敏感级别 |
| :--- | :--- | :--- | :--- |
| `im:message` | 获取与发送单聊、群组消息 | 接收和回复消息 | 普通 |
| `im:message.group_msg` | 获取群组中所有消息 | **全量监听群聊**（核心权限） | **敏感** |
| `im:message:send_as_bot` | 以应用身份发送消息 | 机器人追问和通知 | 普通 |
| `im:chat` | 获取群组信息 | 读取群 ID 和成员列表 | 普通 |

> **重要提示**：`im:message.group_msg` 属于敏感权限，需要在飞书管理后台由管理员审批。审批通过前，机器人只能接收 `@AI秘书` 的消息，无法全量监听。**请优先启动此权限的审批流程**，审批周期通常为 1-3 个工作日。

### 1.4 配置事件订阅（Webhook 接收）

进入应用详情页 → **事件与回调** → **添加事件**，订阅以下事件：

| 事件标识 | 触发时机 |
| :--- | :--- |
| `im.message.receive_v1` | 机器人收到消息时（包含 @机器人 和群消息） |
| `im.chat.member.bot.added_v1` | 机器人被拉入群时（用于自动注册群 ID 到白名单） |

**配置回调地址**：

```
请求 URL: https://your-server.com/webhook/lark/event
加密策略: AES 加密（推荐）
验证 Token: 在页面生成后记录，写入 .env 的 LARK_VERIFICATION_TOKEN
```

> 如果暂无公网服务器，可使用 [ngrok](https://ngrok.com/) 或 [cpolar](https://www.cpolar.com/) 进行内网穿透，用于本地开发测试。

### 1.5 将机器人添加到目标群组

进入应用详情页 → **应用功能** → **机器人** → 启用机器人功能。

然后在飞书客户端中，将机器人添加到需要监听的项目群：
1. 打开目标群聊 → 点击右上角"群设置"
2. 选择"群机器人" → "添加机器人" → 搜索 `AI 项目秘书`
3. 添加成功后，机器人会自动触发 `im.chat.member.bot.added_v1` 事件，系统可借此自动将该群 ID 注册到路由白名单

### 1.6 代码实现：消息接收服务

以下是基于 Python + Flask 的最小可运行接收服务示例：

```python
# lark_bot_receiver.py
import os
import json
import hashlib
import hmac
from flask import Flask, request, jsonify

app = Flask(__name__)

LARK_VERIFICATION_TOKEN = os.getenv("LARK_VERIFICATION_TOKEN")
LARK_APP_ID = os.getenv("LARK_APP_ID")

def verify_signature(timestamp: str, nonce: str, body: str, signature: str) -> bool:
    """验证飞书事件签名"""
    content = timestamp + nonce + LARK_VERIFICATION_TOKEN + body
    computed = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed, signature)

@app.route("/webhook/lark/event", methods=["POST"])
def lark_event():
    # 1. 获取请求头中的签名信息
    timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
    nonce = request.headers.get("X-Lark-Request-Nonce", "")
    signature = request.headers.get("X-Lark-Signature", "")
    body = request.get_data(as_text=True)

    # 2. 验证签名（防止伪造请求）
    if not verify_signature(timestamp, nonce, body, signature):
        return jsonify({"code": 403, "msg": "Invalid signature"}), 403

    data = json.loads(body)

    # 3. 处理 URL 验证挑战（首次配置时飞书会发送 challenge）
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # 4. 处理消息事件
    event_type = data.get("header", {}).get("event_type", "")
    if event_type == "im.message.receive_v1":
        event = data.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})

        chat_id = message.get("chat_id")          # 群 ID
        msg_id = message.get("message_id")        # 消息 ID（用于去重）
        msg_type = message.get("message_type")    # text / image / file
        sender_id = sender.get("sender_id", {}).get("open_id")

        # 仅处理文本消息
        if msg_type == "text":
            content = json.loads(message.get("content", "{}"))
            text = content.get("text", "").strip()

            # 5. 推送到信息缓冲区（调用 Buffer API）
            push_to_buffer(
                source_type="lark",
                source_message_id=msg_id,
                chat_id=chat_id,
                sender_id=sender_id,
                raw_content=text
            )

    return jsonify({"code": 0})


def push_to_buffer(source_type, source_message_id, chat_id, sender_id, raw_content):
    """将消息推送到信息缓冲区"""
    import requests
    BUFFER_API_URL = os.getenv("BUFFER_API_URL", "http://localhost:8000")
    payload = {
        "source_type": source_type,
        "source_message_id": source_message_id,
        "metadata": {
            "chat_id": chat_id,
            "sender_id": sender_id
        },
        "raw_content": raw_content
    }
    try:
        resp = requests.post(f"{BUFFER_API_URL}/buffer/items", json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to push to buffer: {e}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

**启动服务**：

```bash
# 安装依赖
pip install flask requests

# 配置环境变量
export LARK_APP_ID=cli_xxxxxxxxxxxxxxxx
export LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export LARK_VERIFICATION_TOKEN=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
export BUFFER_API_URL=http://localhost:8000

# 启动
python lark_bot_receiver.py
```

### 1.7 主动拉取历史消息（冷启动补偿）

当服务重启或断线重连后，需要拉取期间遗漏的历史消息：

```python
# lark_history_puller.py
import os
import requests

LARK_APP_ID = os.getenv("LARK_APP_ID")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET")

def get_tenant_access_token() -> str:
    """获取 Tenant Access Token"""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    })
    return resp.json()["tenant_access_token"]

def pull_chat_history(chat_id: str, start_time: str, end_time: str):
    """
    拉取指定群组在时间范围内的历史消息
    :param chat_id: 群组 ID
    :param start_time: 开始时间戳（秒），如 "1712800000"
    :param end_time:   结束时间戳（秒），如 "1712886400"
    """
    token = get_tenant_access_token()
    url = "https://open.larksuite.com/open-apis/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "container_id_type": "chat",
        "container_id": chat_id,
        "start_time": start_time,
        "end_time": end_time,
        "page_size": 50
    }
    messages = []
    while True:
        resp = requests.get(url, headers=headers, params=params).json()
        items = resp.get("data", {}).get("items", [])
        messages.extend(items)
        page_token = resp.get("data", {}).get("page_token")
        if not page_token:
            break
        params["page_token"] = page_token
    return messages
```

### 1.8 验证测试

完成配置后，按以下步骤验证：

1. 在目标群聊中发送任意文本消息
2. 检查服务日志，确认收到 `im.message.receive_v1` 事件
3. 检查缓冲区 API，确认消息已被推入（`GET /buffer/items?source_type=lark`）
4. 在群聊中 `@AI秘书` 发送消息，确认机器人能够回复

---

## 第二部分：飞书妙记接入

### 2.1 可行性说明与方案选择

飞书妙记（Minutes）的开放程度目前存在限制，需根据实际情况选择接入方案：

| 方案 | 适用条件 | 优点 | 缺点 |
| :--- | :--- | :--- | :--- |
| **方案 A：官方 API（推荐）** | 飞书企业版，且开放平台已开放妙记 API | 自动化程度高，实时性好 | 需确认 API 可用性 |
| **方案 B：手动触发导出** | 任何版本 | 无需额外权限 | 依赖人工操作 |
| **方案 C：RPA 自动化** | 有稳定的桌面环境 | 可完全自动化 | 维护成本高，稳定性差 |

**当前建议**：优先尝试方案 A，若 API 不可用则采用方案 B 作为过渡，同时评估方案 C 的可行性。

### 2.2 方案 A：通过飞书开放平台 API 读取妙记

#### 2.2.1 申请妙记相关权限

在飞书开放平台的应用权限管理中，申请以下权限：

| 权限标识 | 权限名称 | 说明 |
| :--- | :--- | :--- |
| `minutes:minute:readonly` | 读取妙记信息 | 获取妙记基本信息和转录文本 |
| `drive:drive:readonly` | 以应用身份读取云文档 | 妙记存储在飞书云盘中，需要此权限 |

#### 2.2.2 获取妙记列表与转录文本

```python
# feishu_minutes_reader.py
import os
import requests

def get_tenant_access_token() -> str:
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": os.getenv("LARK_APP_ID"),
        "app_secret": os.getenv("LARK_APP_SECRET")
    })
    return resp.json()["tenant_access_token"]

def list_minutes(page_size: int = 20) -> list:
    """
    获取最近的妙记列表
    注意：此 API 端点需在飞书开放平台确认是否已开放
    """
    token = get_tenant_access_token()
    url = f"https://open.larksuite.com/open-apis/minutes/v1/minutes/{minute_token}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": page_size}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        print(f"[WARN] Minutes API not available: {resp.status_code} - {resp.text}")
        return []
    return resp.json().get("data", {}).get("minutes", [])

def get_minute_transcript(minute_token: str) -> str:
    """
    获取指定妙记的转录文本
    :param minute_token: 妙记的唯一标识
    """
    token = get_tenant_access_token()
    url = f"https://open.larksuite.com/open-apis/minutes/v1/minutes/{minute_token}/transcript"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return ""
    paragraphs = resp.json().get("data", {}).get("transcript", {}).get("paragraphs", [])
    # 将段落拼接为纯文本
    lines = []
    for para in paragraphs:
        speaker = para.get("speaker_info", {}).get("user", {}).get("name", "未知")
        words = "".join([w.get("word", "") for w in para.get("words", [])])
        if words.strip():
            lines.append(f"[{speaker}]: {words.strip()}")
    return "\n".join(lines)

def process_new_minutes(whitelist_keywords: list = None):
    """
    定时轮询新妙记并推送到缓冲区
    :param whitelist_keywords: 仅处理标题包含这些关键词的妙记（隐私保护）
    """
    minutes = list_minutes()
    for minute in minutes:
        title = minute.get("topic", "")
        minute_token = minute.get("minute_token", "")

        # 白名单过滤（隐私保护：只处理项目相关会议）
        if whitelist_keywords:
            if not any(kw in title for kw in whitelist_keywords):
                print(f"[SKIP] 非白名单会议，跳过: {title}")
                continue

        transcript = get_minute_transcript(minute_token)
        if not transcript:
            continue

        # 推送到缓冲区
        push_minutes_to_buffer(
            minute_token=minute_token,
            title=title,
            transcript=transcript
        )

def push_minutes_to_buffer(minute_token: str, title: str, transcript: str):
    """将妙记转录文本推送到信息缓冲区"""
    import requests as req
    BUFFER_API_URL = os.getenv("BUFFER_API_URL", "http://localhost:8000")
    payload = {
        "source_type": "meeting_notes",
        "source_message_id": f"minutes:{minute_token}",
        "metadata": {"meeting_title": title},
        "raw_content": transcript
    }
    try:
        resp = req.post(f"{BUFFER_API_URL}/buffer/items", json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[OK] 妙记已推送到缓冲区: {title}")
    except Exception as e:
        print(f"[ERROR] 推送失败: {e}")

if __name__ == "__main__":
    # 仅处理包含以下关键词的会议妙记（隐私白名单）
    ALLOWED_KEYWORDS = ["XPBET", "项目周会", "需求评审", "技术方案", "复盘"]
    process_new_minutes(whitelist_keywords=ALLOWED_KEYWORDS)
```

**配置定时轮询**（每小时检查一次新妙记）：

```bash
# 添加到 crontab
0 * * * * /usr/bin/python3 /path/to/feishu_minutes_reader.py >> /var/log/minutes_reader.log 2>&1
```

### 2.3 方案 B：手动触发导出（过渡方案）

在 API 不可用的情况下，PM 可通过以下流程手动将妙记内容推送到缓冲区：

**Step 1**：会议结束后，在飞书妙记中点击"导出" → "导出为文本"，得到 `.txt` 文件。

**Step 2**：将文件上传到 AI 秘书的处理接口：

```bash
curl -X POST http://your-server.com/buffer/items/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@meeting_transcript.txt" \
  -F "source_type=meeting_notes" \
  -F "metadata={\"meeting_title\": \"XPBET 需求评审 2026-04-10\"}"
```

或者，PM 直接在 Lark 群聊中 `@AI秘书` 并附上妙记链接：

```
@AI秘书 请处理这次会议的妙记：https://xpbet.feishu.cn/minutes/xxxxxxxx
```

AI 秘书收到指令后，调用 `GET /minutes/{token}` 接口自动拉取内容。

### 2.4 缓冲区对妙记的处理逻辑

妙记内容进入缓冲区后，LLM 会按以下流程处理：

```
原始转录文本
    ↓
1. 发言人识别与分段（按说话人切分段落）
    ↓
2. 意图识别（提取 Action Items、决策结论、风险点）
    ↓
3. 实体提取（责任人、截止时间、关联模块）
    ↓
4. 完整度评分（明确动作+40, 责任人+30, 时间点+30）
    ↓
5. 生成"待确认"摘要，发送给 PM 在 Lark 中确认
    ↓
6. PM 确认后，推送至 Lark 多维表格或 Meegle
```

**LLM Prompt 模板（妙记专用）**：

```
你是 XPBET 项目的 AI 秘书，正在处理一段会议转录文本。

请从以下转录文本中提取所有明确的"行动项（Action Items）"，每个行动项必须包含：
1. 具体动作（做什么）
2. 责任人（谁来做）
3. 截止时间（什么时候完成）
4. 关联模块（属于哪个业务模块）

如果某个字段无法从文本中确定，请标记为 "待确认"。

会议标题：{meeting_title}
转录文本：
{transcript}

请以 JSON 数组格式输出，每个元素包含字段：action, owner, deadline, module, completeness_score。
```

### 2.5 隐私保护配置

在 `routing_config.yaml` 中配置妙记白名单，严格限制可处理的会议范围：

```yaml
sources:
  meeting_notes:
    enabled: true
    # 仅处理标题包含以下关键词的妙记
    title_whitelist_keywords:
      - "XPBET"
      - "项目周会"
      - "需求评审"
      - "技术方案评审"
      - "复盘"
    # 明确排除的敏感会议关键词
    title_blacklist_keywords:
      - "薪酬"
      - "绩效"
      - "HR"
      - "融资"
    # 是否允许全局搜索所有妙记（强烈建议保持 false）
    allow_global_search: false
```

---

## 第三部分：环境变量汇总

将以下内容写入项目根目录的 `.env` 文件（**禁止提交到 Git**，已在 `.gitignore` 中排除）：

```env
# ===== Lark Bot 配置 =====
LARK_APP_ID=cli_xxxxxxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LARK_VERIFICATION_TOKEN=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
# 事件加密密钥（如开启 AES 加密）
LARK_ENCRYPT_KEY=zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz

# ===== 信息缓冲区服务地址 =====
BUFFER_API_URL=http://localhost:8000

# ===== Meegle 配置（参考） =====
MEEGLE_API_TOKEN=mt_xxxxxxxxxxxxxxxxxxxx
MEEGLE_WEBHOOK_SECRET=wh_sec_xxxxxxxxxxxxxxxx
```

---

## 第四部分：常见问题排查

| 问题现象 | 可能原因 | 解决方案 |
| :--- | :--- | :--- |
| 机器人收不到群消息 | `im:message.group_msg` 权限未审批通过 | 联系飞书管理员加速审批；临时方案：只处理 @机器人 的消息 |
| Webhook 回调地址验证失败 | 服务未启动或地址不可访问 | 检查服务状态；使用 ngrok 测试本地环境 |
| 签名验证失败 | `LARK_VERIFICATION_TOKEN` 配置错误 | 在飞书开放平台重新复制 Verification Token |
| 妙记 API 返回 404 | 该 API 端点尚未对外开放 | 切换为方案 B（手动导出）或联系飞书商务申请内测资格 |
| 消息重复处理 | Webhook 重试机制触发 | 确认去重表（`processed_messages`）已正常运行 |

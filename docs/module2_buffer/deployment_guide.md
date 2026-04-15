# AI 秘书系统部署方案评估与上线指南

**作者**: Manus AI
**日期**: 2026-04-15
**所属模块**: 模块二 (信息缓冲池)

---

## 1. 部署需求分析

要让前端缺陷报送功能（以及整个 AI 秘书系统）“上线跑通”，我们需要从目前的“本地脚本手动运行”模式，转变为“云端 24 小时在线”的自动化服务。

基于仓库现状，系统的核心运行特征如下：
1. **触发机制**: 目前是基于 Python 脚本主动拉取（如 `cold_start_step2_fetch_messages.py`），未来如果要实现“即时拦截”，必须转型为**监听 Lark Webhook**（被动接收事件）。
2. **运行环境**: Python 3.x，依赖 `requests`, `openai` 等基础库。
3. **状态存储**: 目前无数据库依赖（全靠变量和 Bitable 存储），但如果要做长会话上下文合并，可能需要轻量级缓存（如 Redis）或持久化数据库（PostgreSQL/MySQL）。
4. **外部通信**: 需要访问外网调用 OpenAI API、Lark API 和 Meegle API。

## 2. 部署方案评估：Railway vs 其他

针对上述需求，我们对比几种主流的部署方案：

| 特性 / 平台 | Railway (推荐) | Vercel | AWS / 阿里云 EC2 | GitHub Actions |
| :--- | :--- | :--- | :--- | :--- |
| **适用场景** | Web 服务、定时任务、数据库 | 前端托管、无状态 Serverless | 重型后端、高定制化环境 | 纯定时批处理任务 |
| **Webhook 支持** | **完美支持** (常驻进程) | 支持 (冷启动可能超时) | 完美支持 | **不支持** (无法暴露端口) |
| **部署难度** | **极低** (连接 GitHub 即署) | 极低 | 较高 (需自己配 Nginx/SSL) | 低 |
| **状态存储** | **一键创建 Redis/PG** | 需配置外部服务 | 自己搭建 | 无 |
| **成本预估** | $5/月 (按使用量计费) | 免费额度较高 | 固定机器成本较高 | 免费 |

### 结论：为什么 Railway 是最适合的方案？
如果您希望实现**真正的实时群聊拦截**，系统必须暴露一个公网 URL 来接收 Lark 的 Webhook 事件推送。
- GitHub Actions 只能做定时拉取（如每 10 分钟一次），无法做到“秒级拦截”。
- Vercel 虽然能接收 Webhook，但 Serverless 函数有执行时间限制（通常 10-60 秒），如果 LLM 意图识别和 Meegle API 调用耗时较长，容易导致请求超时。
- **Railway 提供常驻容器（Docker/Nixpacks），且自带公网域名，支持一键附加 Redis（用于记录对话上下文），是当前轻量级 AI Agent 项目最完美的上线选择。**

---

## 3. Railway 上线实操指南

要将现有的脚本改造并在 Railway 上线，需要遵循以下三个阶段：

### 阶段一：代码改造 (适配 Webhook)
目前仓库里只有离线跑的脚本，我们需要加一个极简的 Web 框架（如 FastAPI 或 Flask）来接收 Lark 事件。

1. **安装依赖**: `pip install fastapi uvicorn`
2. **编写 `main.py`**:
```python
from fastapi import FastAPI, Request
from scripts.frontend_defect_reporter import process_message

app = FastAPI()

@app.post("/lark/webhook")
async def lark_webhook(request: Request):
    payload = await request.json()
    # 1. 验证 Lark 签名 (Challenge)
    if "challenge" in payload:
        return {"challenge": payload["challenge"]}
    
    # 2. 提取消息内容
    # 假设解析出了 text 和 sender
    text = payload.get("event", {}).get("message", {}).get("content", "")
    sender = "某人" # 从 payload 提取
    
    # 3. 调用缺陷报送逻辑
    result = process_message(text, sender)
    
    # 4. 根据 result["action"] 调用 Lark API 将询问话术发回群里
    # ...
    
    return {"status": "ok"}
```

### 阶段二：配置 Railway 部署环境
1. **添加 `requirements.txt`**:
   在仓库根目录创建，写入：
   ```text
   fastapi==0.104.1
   uvicorn==0.24.0
   requests==2.31.0
   openai==1.3.5
   python-dotenv==1.0.0
   ```
2. **添加 `Procfile`**:
   在仓库根目录创建，告诉 Railway 如何启动服务：
   ```text
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### 阶段三：在 Railway 平台操作
1. 登录 [Railway.app](https://railway.app/)，点击 **New Project** -> **Deploy from GitHub repo**。
2. 选择 `gdszyy/ai-secretary-architecture` 仓库。
3. 进入 **Variables** 标签页，配置必须的环境变量：
   - `OPENAI_API_KEY`
   - `MEEGLE_TOKEN`
   - `MEEGLE_PROJECT_KEY`
   - `LARK_APP_ID` 和 `LARK_APP_SECRET`
4. 部署成功后，在 **Settings** -> **Networking** 中点击 **Generate Domain**，获取公网 URL（如 `ai-sec-production.up.railway.app`）。

### 阶段四：飞书开放平台配置
1. 登录飞书开发者后台，进入您的应用。
2. 切换到 **事件订阅** 页面。
3. 将请求网址配置为 Railway 域名：`https://ai-sec-production.up.railway.app/lark/webhook`。
4. 订阅 **接收消息 (im.message.receive_v1)** 事件。
5. 发布应用新版本。

## 4. 总结
要让机器人“实时拦截”对话，**Railway 确实是最佳路径**。它免去了服务器运维的痛苦，又能提供稳定的常驻进程。您只需要在当前仓库基础上加一个 `main.py` 作为 Webhook 入口，即可顺滑上线。

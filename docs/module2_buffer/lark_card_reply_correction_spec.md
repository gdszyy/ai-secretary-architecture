# 飞书卡片回复自动触发信息纠正 — 需求规格

**状态**：待开发（需申请飞书权限）  
**优先级**：P1（信息纠正闭环的关键缺口）  
**提出人**：VoidZ  
**记录时间**：2026-04-21  

---

## 背景

当前信息纠正机制为**手动脚本触发**：VoidZ 将纠正内容告知 Manus，由 Manus 整理后执行 `scripts/manual_correction.py` 写入 Bitable。

这个流程存在以下缺口：

1. **依赖 Manus 在线**：VoidZ 在飞书群里看到周报卡片时，无法直接回复触发纠正，必须切换到 Manus 对话。
2. **纠正不及时**：群聊中的实时补充信息无法在当下被捕获，容易遗忘。
3. **缺少可追溯记录**：纠正内容散落在对话中，没有统一的纠正日志。

---

## 目标

实现以下闭环：

```
VoidZ 在飞书群回复周报卡片
  → 飞书机器人收到消息事件
  → 解析纠正指令（格式：纠正：[话题名] 实际情况是……）
  → 调用 manual_correction.py 逻辑写入 Bitable
  → 回复确认消息
```

---

## 触发格式设计

回复飞书卡片时，支持以下两种指令：

### 纠正已有话题
```
纠正：[话题名] 实际情况是……
```
示例：
```
纠正：CRM系统选型 实际情况是集团要求接入Smartico，最终决策为接入Smartico，非Optimove。
```

### 补充新话题
```
补充：[话题名] [意图类型] 内容是……
```
示例：
```
补充：活动平台赔率限制 决策 平台统一使用相同Bonus赔率限制，避免主钱包能量分配漏洞。
```

意图类型简写映射：
| 简写 | 完整值 |
|---|---|
| 决策 | major_decision |
| 里程碑 | milestone_fact |
| 风险 | risk_blocker |
| 任务 | routine_task |

---

## 技术实现方案

### 组件一：飞书事件订阅服务（新增）

**文件**：`scripts/lark_webhook_server.py`  
**类型**：FastAPI 服务，监听飞书消息事件  
**部署**：需要公网可访问的地址（或内网穿透）

核心逻辑：
```python
@app.post("/lark/event")
async def handle_event(request: Request):
    body = await request.json()
    # 1. 验证飞书签名
    # 2. 解析消息内容
    # 3. 匹配纠正/补充指令
    # 4. 调用 correction_writer.write(title, intent, summary)
    # 5. 回复确认消息
```

### 组件二：纠正写入器（复用现有逻辑）

从 `manual_correction.py` 中提取 `update_record` / `create_record` 逻辑，封装为可被 webhook 调用的函数模块 `scripts/correction_writer.py`。

### 组件三：LLM 意图解析（新增）

当用户回复格式不严格时，用 LLM 解析意图类型和话题标题：
```python
def parse_correction_message(text: str) -> dict:
    # 调用 gpt-4.1-mini 解析
    # 返回 {"action": "update/create", "title": ..., "intent": ..., "summary": ...}
```

---

## 所需飞书权限

详见交接文档 `docs/handover/lark_card_reply_correction_handover.md`

---

## 验收标准

1. VoidZ 在飞书群回复周报卡片 `纠正：CRM系统选型 实际情况是接入Smartico`，30 秒内 Bitable 对应记录被更新，飞书收到确认回复。
2. 格式不严格时（如直接描述），LLM 能正确解析并写入，置信度低时询问确认。
3. 非 VoidZ 发送的消息不触发写入（权限控制）。

---

## 依赖项

- 飞书机器人消息订阅权限（见交接文档）
- 公网服务部署（或飞书内网穿透方案）
- `correction_writer.py` 模块化重构（约 2 小时工作量）
- `lark_webhook_server.py` 新增（约 4 小时工作量）

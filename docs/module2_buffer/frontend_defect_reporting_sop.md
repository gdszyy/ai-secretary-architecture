# 前端缺陷自动报送 SOP 与数据流设计

**作者**: Manus AI
**日期**: 2026-04-15
**所属模块**: 模块二 (信息缓冲池)

---

## 1. 概述

为了提升前端缺陷（Bug）的响应速度，减少项目经理在收集问题细节和创建 Meegle 工单上的时间消耗，本设计规范定义了 AI 秘书拦截群聊对话并自动报送前端缺陷至 Meegle 的标准作业程序（SOP）和底层数据流。

该流程依托于信息缓冲池（Information Buffer）的“暂存-询问-派发”机制，结合 Meegle API 实现闭环。

## 2. 数据流与架构设计

整个报送流程分为三个核心阶段：识别与缓冲、补全与拦截、派发与同步。

### 2.1 识别与缓冲阶段
1. **消息接收**: AI 秘书通过 WebSocket 或 API 拉取（如 `scripts/cold_start_step2_fetch_messages.py`）获取前端相关群组（如“上线前前端优化需求”、“小组长”）的消息流。
2. **意图解析**: LLM 对消息进行意图分类，若识别为 `Bug Report`，则进入前端缺陷处理分支。
3. **实体提取**: 尝试提取关键实体：`module_name`（模块）、`description`（现象）、`reproduce_steps`（复现步骤）、`priority`（优先级）、`impact`（影响范围）。
4. **完整度评分**: 根据提取的实体计算 `completeness_score`。若缺少复现步骤或优先级，评分通常低于 80，状态标记为 `asking`。

### 2.2 补全与拦截阶段
1. **触发询问**: 若状态为 `asking`，AI 秘书在原群聊中通过 `@发送者` 发起即时询问（Immediate Inquiry），要求补充缺失字段。
2. **信息合并**: 用户回复后，系统将新消息与原 Buffer Item 合并，重新提取实体并评分。
3. **状态跃迁**: 当所有必填字段（现象、步骤、优先级）齐全，评分达到 80 以上，状态变更为 `ready`，准备派发。

### 2.3 派发与同步阶段 (Dispatcher)
1. **映射转换**: 调度器将 Buffer Item 的实体映射为 Meegle API 所需的 JSON 格式。
   - 提取的模块名映射到 Meegle 的 `project_id`。
   - 提取的人员（如被@的开发）映射到 Meegle 的 `user_key`。
2. **API 调用**: 调用 Meegle 的 `POST /projects/{project_id}/work_items` 接口，创建类型为 `defect` 的工作项。
3. **状态回传**: 创建成功后，获取 `work_item_id`，在原群聊中回复确认信息，并将状态更新为 `dispatched`。

## 3. 核心交互 SOP

### 3.1 触发条件
- **目标群组**: “上线前前端优化需求”、“小组长”等前端强相关群组。
- **触发意图**: `Bug Report` 或 `Risk Escalation`。

### 3.2 拦截询问话术模板
当 AI 秘书检测到前端 Bug 且信息不全时，将使用以下模板主动拦截：

> **[紧急确认] 关于前端 Bug 报送**
> 收到您反馈的“[提取的现象摘要]”。为了在 Meegle 创建缺陷工单，请补充以下信息：
> 1. **复现步骤**：(如：测试环境还是生产环境？具体操作路径？)
> 2. **优先级**：(如：High/Medium/Low，是否阻碍测试？)
> 
> 请直接回复，我将自动为您建档。

### 3.3 报送成功通知模板
> ✅ **已成功在 Meegle 创建 Bug 工单**
> **ID**: [DEF-XXXX]
> **标题**: [自动生成的标题]
> **优先级**: [提取的优先级]
> **指派给**: [@提取的责任人 或 待分配]
> **链接**: [Meegle 访问链接]

## 4. 数据字典与 API 映射

### 4.1 Meegle API Payload 示例
```json
{
  "project_id": "prj_frontend_opt",
  "work_item_type_key": "defect",
  "name": "[前端] 游戏渲染加载较慢",
  "description": "**现象**: 游戏渲染加载较慢\n**复现步骤**: 在测试环境直连时速度较快，VPN 连接时加载缓慢...\n**影响范围**: 墨西哥地区用户",
  "priority": "High",
  "assignee": "usr_voidz_01"
}
```

### 4.2 映射表维护要求
系统必须在 `project_context.json` 或环境变量中维护以下映射：
- `LARK_GROUP_ID` -> `MEEGLE_PROJECT_ID`
- `LARK_USER_ID` -> `MEEGLE_USER_KEY`
- `LARK_PRIORITY_TEXT` (如“高”、“阻碍”) -> `MEEGLE_PRIORITY_ENUM` (如 `High`, `Blocker`)

## 5. 异常处理
- **API 失败**: 若调用 Meegle API 失败（如鉴权错误），AI 秘书应在群聊中提示：“⚠️ 创建 Meegle 工单失败，请稍后重试或手动创建。”并将错误日志记录到系统。
- **超时未补充**: 若发起询问后 1 小时内无回复，再次发送强提醒；若 24 小时无回复，将该 Bug 降级为普通备忘，不再主动打扰。

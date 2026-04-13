# Lark 应用权限验证要点

> 记录时间：2026-04-13
> 应用 App ID：`cli_a9d985cd40f89e1a`（复用自 `lark-md-import` 技能）

---

## 1. 所有所需权限均已具备，无需重新申请

经过实际 API 调用验证，该应用已具备 AI 项目秘书接入所需的全部权限：

| 权限标识 | 用途 | 状态 |
| :--- | :--- | :--- |
| `im:message` | 接收/发送消息 | ✅ 已开通 |
| `im:message:send_as_bot` | 机器人发送消息 | ✅ 已开通 |
| `im:chat` | 获取群组信息 | ✅ 已开通 |
| `im:message.group_msg` | **全量监听群聊（敏感权限）** | ✅ 已开通 |
| `drive:drive:readonly` | 读取云文档 | ✅ 已开通 |
| `minutes:minutes:readonly` | 读取飞书妙记 | ✅ 已开通 |

---

## 2. 妙记 API 关键说明

### 2.1 没有"列表"接口
飞书妙记 API **没有获取全部妙记列表的接口**，必须提供具体的 `minute_token` 才能查询。

### 2.2 正确的 API 端点（使用 larksuite.com 域名）

```
# 获取妙记基础信息
GET https://open.larksuite.com/open-apis/minutes/v1/minutes/{minute_token}

# 获取妙记文字转录
GET https://open.larksuite.com/open-apis/minutes/v1/minutes/{minute_token}/transcript
```

### 2.3 如何获取 minute_token
从妙记 URL 末尾提取，例如：
```
https://xpbet.larksuite.com/minutes/obcnq3b9jl72l83w4f14xxxx
                                      ↑ 这一段即为 minute_token
```

### 2.4 错误码区分
- `code=2091002 resource not found`：token 无效或妙记不存在，**权限正常**
- `code=2091005 permission deny`：权限未开通

---

## 3. 妙记接入方案（降级为 URL 触发）

由于没有列表接口，采用以下方案：

**PM 在 Lark 群聊中 @机器人 并粘贴妙记链接** → 机器人从 URL 中提取 `minute_token` → 调用 API 拉取转录文本 → 推送到信息缓冲区。

长期可考虑订阅日历事件（`calendar.event.changed_v1`），从会议结束事件中自动获取妙记链接。

---

## 4. 所有 API 调用使用 larksuite.com 域名

本应用注册在 Lark（国际版）而非飞书（国内版），所有 API 调用必须使用：
- **正确**：`https://open.larksuite.com/open-apis/...`
- **错误**：`https://open.feishu.cn/open-apis/...`

开发者后台地址：`https://open.larksuite.com/app`

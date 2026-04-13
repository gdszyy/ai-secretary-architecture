---
description: "模块二：信息缓冲池机制、意图识别与防堆积策略的设计规范"
globs: ["docs/module2_buffer/**"]
---

# 模块二：信息缓冲池规范 (Buffer Module)

## 1. 模块职责

信息缓冲池模块是 AI 项目秘书系统的**核心处理层**，负责接收 PM 的碎片化信息输入，利用大语言模型（LLM）进行意图识别、实体提取和完整度评分，并在信息达标后将其派发到对应的工作区（Lark 或 Meegle）。

## 2. 核心状态机

缓冲区中的每条信息条目遵循以下状态机：

```
pending → asking → ready → dispatched
                 ↘ expired (防堆积降级)
```

| 状态 | 含义 | 触发条件 |
| :--- | :--- | :--- |
| `pending` | 刚接收，等待处理 | 新信息进入缓冲区 |
| `asking` | 正在向 PM 追问补充信息 | 完整度评分 < 80 |
| `ready` | 信息完整，等待派发 | 完整度评分 ≥ 80 |
| `dispatched` | 已成功派发到工作区 | 调度器确认写入成功 |
| `expired` | 超时降级归档 | 24h 无响应降级，72h 强制归档 |

## 3. 意图分类标准

LLM 对输入信息进行六大类意图分类：

| 意图类型 | 目标工作区 | 示例 |
| :--- | :--- | :--- |
| `Feature Request` | Lark 功能表 | "下周要把活动中心的预算配置功能加上" |
| `Bug Report` | GitHub Issue / Meegle Defect | "支付系统挂了，iOS端微信支付必现" |
| `Status Update` | Lark 功能表（更新状态） | "用户系统今日已完成注册流程优化" |
| `Memo` | Lark 备忘视图 + 定时提醒 | "备忘：明天下午提醒我跟进EPAY路由" |
| `Query` | 直接回复（不写入工作区） | "查询用户系统最新进度" |
| `Unclear` | 触发追问 | "那个东西搞一下" |

## 4. 防堆积策略

为防止缓冲区信息无限积压，系统执行以下降级策略：

| 时间阈值 | 动作 |
| :--- | :--- |
| 24 小时无响应 | 状态降级为 `expired`，发送提醒 |
| 72 小时无响应 | 强制归档，移出活跃队列 |
| 活跃条目 > 50 条 | 触发批量合并，按模块聚合 |

## 5. 详细设计文档

本模块的完整设计文档位于 `docs/module2_buffer/` 目录下：

| 文档 | 说明 |
| :--- | :--- |
| `info_buffer_design.md` | 缓冲池核心架构设计 |
| `secretary_module2_sop.md` | 缓冲池模块的标准作业程序 |
| `buffer_anti_accumulation_sop.md` | 防堆积策略的详细 SOP |
| `buffer_to_workspace_flow.md` | 缓冲区到工作区的派发流程 |
| `info_lifecycle_flow.md` | 信息生命周期流程图 |
| `inquiry_strategy.md` | 主动询问策略与话术模板 |
| `thread_separation_algorithm.md` | 话题分离算法设计 |
| `prereq_data_assessment.md` | 前置数据评估报告 |

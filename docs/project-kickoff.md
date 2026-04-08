# XPBET 全球站功能地图管理系统 — 项目启动报告

**项目 ID**: prj-575e0b65-dc5  
**项目负责人 Agent**: agt-82507997-ca4 (project_manager / resident)  
**Git 文档库**: gdszyy/project-management-ai-secretary  
**启动时间**: 2026-03-26  

---

## 项目背景

本项目旨在将 XPBET 全球站的功能地图（PDF 思维导图形式）升级为一套**数据驱动的数字化管理引擎**，核心架构为：

> **飞书多维表格（数据层）→ 自研前端 React + AntV G6（可视化层）→ 飞书云文档（执行层）**

---

## 数据基础

从飞书多维表格（BASE_ID: CyDxbUQGGa3N2NsVanMjqdjxp6e）读取的现有数据：

| 表格 | 记录数 | 关键字段 |
| :--- | :--- | :--- |
| 模块表 | 21 条 | 优先级、分类、模块名称、模块说明、状态、负责人 |
| 功能表 | 114 条 | 功能名称、功能说明、所属模块、文档链接、状态、功能优先级、迭代版本、阶段 |

---

## 已分派任务

| 任务 ID | 任务标题 | 优先级 | 状态 | Manus 对话 |
| :--- | :--- | :--- | :--- | :--- |
| tsk-9103d528-937 | 多维表格数据结构设计 | High | pending | [打开](https://manus.im/app/QYYc6PtknXgn8QWJtxoQcj) |
| tsk-f7cc10f7-0df | 前端可视化架构设计（AntV G6 + React） | High | pending | [打开](https://manus.im/app/aoMEKbbhNMCbvCYJm62SXy) |
| tsk-f33ad9af-54f | 飞书三层体系打通方案设计 | Medium | pending | [打开](https://manus.im/app/dNodNELFUcgjQ3n4gbawXR) |

---

## 任务依赖关系

```
tsk-9103d528-937 (数据结构设计)
        ↓
tsk-f7cc10f7-0df (前端架构设计)
        ↓
tsk-f33ad9af-54f (飞书三层打通)
        ↓
   [前端开发实现]
```

---

## 下一步行动

1. 等待三个子任务的 Agent 完成工作并提交到 Git 仓库。
2. 项目负责人对每个任务进行验收（review-task）。
3. 根据设计文档，启动前端开发实现阶段。

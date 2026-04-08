# XPBET 功能地图管理系统 — 飞书 Wiki 文档索引

> **文档版本**: v2.0
> **最后更新**: 2026-03-27（使用 Markdown 导入重建完整版）
> **任务 ID**: tsk-1afd825f-eab

---

## 文档中心子页面索引 (完整版)

| 编号 | 页面标题 | 飞书 Wiki 链接 | 内容状态 | 核心内容 |
| :--- | :--- | :--- | :--- | :--- |
| 00 | 项目概览 | [00. 项目概览 (完整版)](https://kjpp4yydjn38.jp.larksuite.com/wiki/JveuwwqhOiHMCYkm48Hj7r8Zpae) | ✅ 完整 | 项目背景、三层架构说明、技术选型决策摘要 |
| 01 | 第一层 - 前端可视化 | [01. 第一层 - 前端可视化 (完整版)](https://kjpp4yydjn38.jp.larksuite.com/wiki/DtvjwJVYGiwsxzk5gYija8Cqpkb) | ✅ 完整 | 架构设计摘要（G6 v5）、组件说明、部署指南 |
| 02 | 第二层 - 多维表格 | [02. 第二层 - 多维表格 (完整版)](https://kjpp4yydjn38.jp.larksuite.com/wiki/QmT3weJcDiqudSkZpPxjkwdrpIg) | ✅ 完整 | 双表结构设计（模块表+功能表）、ER 关系、字段规范 |
| 03 | 第三层 - 云文档体系 | [03. 第三层 - 云文档体系 (完整版)](https://kjpp4yydjn38.jp.larksuite.com/wiki/EdCgwrU0HiUTV8kqM5AjfKLdpff) | ✅ 完整 | 使用手册摘要、PRD 模板建议（5节标准结构）、Markdown 导入规范 |
| 04 | 数据结构规范 | [04. 数据结构规范 (完整版)](https://kjpp4yydjn38.jp.larksuite.com/wiki/R1RIw7xL8iwRXUkho0Bj2QEapEd) | ✅ 完整 | 4层树状结构说明、JSON格式规范、颜色映射规范 |
| 05 | 开发进度看板 | [05. 开发进度看板 (完整版)](https://kjpp4yydjn38.jp.larksuite.com/wiki/TLyfwfhk7iSXcYkAMaejvwxQp0b) | ✅ 完整 | 已完成任务清单（6项）、待启动任务（3项） |

---

## 已有飞书 Wiki 页面（前序任务产出）

| 页面标题 | 飞书 Wiki 链接 | 来源任务 |
| :--- | :--- | :--- |
| XPBET 功能地图管理体系使用手册 | [使用手册](https://kjpp4yydjn38.jp.larksuite.com/wiki/FPl1wrV3piGgsnkzl57j3WfJptC) | tsk-f33ad9af-54f |

---

## Git 仓库文档清单

| 文档路径 | 描述 | 关联 Wiki 页面 |
| :--- | :--- | :--- |
| `docs/project-kickoff.md` | 项目启动报告 | 00. 项目概览 |
| `tasks/tsk-9103d528-937/deliverables/xpbet_data_structure_design_v2.md` | 数据结构设计方案 v2.0 | 04. 数据结构规范 |
| `tasks/tsk-f7cc10f7-0df/deliverables/frontend_architecture_design.md` | 前端可视化架构设计方案 | 01. 第一层 - 前端可视化 |
| `tasks/tsk-f33ad9af-54f/deliverables/xpbet_function_map_manual.md` | 三层体系打通使用手册 | 03. 第三层 - 云文档体系 |
| `tasks/tsk-c87fc05b-5af/deliverables/xpbet_bitable_structure_design.md` | 第二层多维表格结构设计方案 v1.0 | 02. 第二层 - 多维表格 |
| `tasks/tsk-6cafe603-a9f/deliverables/frontend_implementation.md` | 前端实现文档（G6 v5） | 01. 第一层 - 前端可视化 |
| `tasks/tsk-1afd825f-eab/deliverables/wiki_index.md` | 本文档（Wiki 索引） | Wiki 首页 |

---

## 三层架构文档体系说明

| 层级 | 定位 | 技术实现 | 文档状态 |
| :--- | :--- | :--- | :--- |
| **第一层（全局查看）** | 提供全局视角的业务大图 | React 19 + AntV G6 v5 | ✅ 已完成（架构设计 + 实现代码） |
| **第二层（调整细分功能）** | 核心数据管理与状态流转 | 飞书多维表格 | ✅ 已完成（新版结构设计文档） |
| **第三层（新增细节执行）** | 详细需求说明与技术方案 | 飞书云文档（Markdown 导入） | ✅ 已完成（使用手册 + PRD 规范） |

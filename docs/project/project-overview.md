# Lark Docs Interactive Code Widget 项目概览

## 项目目标
在 Lark 云文档中开发一个完整的 Docs Add-on，实现可交互的代码编辑与渲染组件（Interactive Code Widget）。

## 技术栈
- **框架**：Lark Docs Add-on（@lark-opdev/cli）+ React + TypeScript
- **代码编辑器**：CodeMirror 6（支持 HTML/CSS/JS 语法高亮）
- **沙箱渲染**：iframe + srcdoc（优先）/ postMessage 外部渲染服务（兜底）
- **数据存储**：Doc Data (Record API) 存储代码内容；Interactive Data (Interaction API) 存储 viewMode
- **构建工具**：Webpack（Lark CLI 默认）

## 核心功能需求
1. **三态流转**：初始态（Empty State）→ 编辑态（Edit Mode）→ 阅读态（View/Render Mode）
2. **代码编辑**：HTML/CSS/JS 三个 Tab，CodeMirror 6 语法高亮，实时预览
3. **沙箱渲染**：iframe 安全隔离执行用户代码，sandbox="allow-scripts" 属性
4. **数据持久化**：Record API setRecord/getRecord，支持 undo/redo 和历史记录
5. **协同编辑**：onRecordChange 监听，多用户实时同步
6. **安全防护**：XSS 隔离，禁止 allow-same-origin 和 allow-top-navigation

## 参考文档
- Lark Docs Add-on 快速开发指南：https://open.larksuite.com/document/uAjLw4CM/uYjL24iN/docs-add-on/03-cloud-document-widget-quick-development-guide/03-cloud-document-widget-quick-developme
- Lark Docs Add-on 数据存储：https://open.larksuite.com/document/uAjLw4CM/uYjL24iN/docs-add-on/04-cloud-doc-block-data-storage/04-cloud-doc-block-data-storage
- Lark Docs Add-on 介绍：https://open.larksuite.com/document/uAjLw4CM/uYjL24iN/docs-add-on/docs-add-on-introduction

## 项目 ID
prj-fcbce203-388

## 协调者 Agent ID
agt-48ee8791-43c

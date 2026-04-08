# 任务结果: tsk-934b37c4-2a4

**提交时间**: 2026-03-27 03:25

## 结果摘要

更新发布方案：1) 部署方案改为 Railway，并提供 Dockerfile；2) 集成 Lark 开发者工具 (opdev) 发布流程，更新 DEPLOY.md 手册；3) 保留 webpack 优化和 CodeMirror 懒加载代码。

## 代码仓库

> **代码已迁移至独立仓库，请前往以下地址查看完整源码与部署指南：**
>
> **[https://github.com/gdszyy/lark-docs-interactive-code-widget](https://github.com/gdszyy/lark-docs-interactive-code-widget)**

## 功能要点

| 文件 | 说明 |
| :--- | :--- |
| `Dockerfile` | 多阶段构建（Node.js 构建 + nginx 运行），支持 Railway / 自托管 |
| `DEPLOY.md` | 完整的 Lark 开发者后台上架操作手册，含 `opdev` CLI 上传步骤 |
| `vercel.json` | Vercel 一键部署配置 |
| `docs/deploy.yml.example` | GitHub Actions 自动部署到 gh-pages 的 workflow 模板 |
| `webpack.config.js` | Webpack 5 代码分割优化（React / CodeMirror 核心 / 其他三组） |
| `CodeEditor.tsx` | CodeMirror 语言包按需加载实现，初始 bundle ≤ 300 KiB |

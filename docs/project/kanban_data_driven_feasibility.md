# 看板数据驱动方案可行性评估

**版本**: 1.0  
**日期**: 2026-04-14  
**作者**: Manus AI  

---

## 1. 目标定义

目标是实现以下链路：

> **AI Secretary 修改 `dashboard_data.json` → 看板前端自动反映最新内容**

前端代码不需要任何改动，所有业务状态（模块进度、里程碑、周报、文档链接）均通过 JSON 数据文件驱动。

---

## 2. 现状评估

### 2.1 已实现的部分

当前架构已满足「数据驱动前端」的核心约束：

| 层级 | 现状 | 说明 |
|------|------|------|
| 前端渲染 | ✅ 完全数据驱动 | `useDashboardData.ts` 在运行时 `fetch('/dashboard_data.json')`，所有组件纯函数渲染 |
| 数据契约 | ✅ TypeScript 类型定义完整 | `lib/types.ts` 定义了 `DashboardData`、`Module`、`ModuleGroup`、`Milestone` 等全部类型 |
| 脚本工具链 | ✅ 5 个维护脚本已落库 | `ai-secretary-architecture/scripts/` 下覆盖全量重建、Bitable 同步、周报注入、里程碑更新 |
| 数据仓库 | ✅ 双副本同步 | `ai-secretary-architecture/data/dashboard_data.json`（主库）↔ `kanban-v2/client/public/dashboard_data.json`（前端读取副本）|

### 2.2 当前缺口

| 缺口 | 描述 | 影响 |
|------|------|------|
| **同步步骤需手动触发** | 每次更新数据后需手动运行 `cp` 命令将主库副本同步到前端 | 容易遗漏，不够自动化 |
| **前端读取的是静态文件** | 部署后前端 `fetch` 的是构建时打包进去的 JSON，不是实时的 | 需要重新部署才能更新内容 |
| **无数据校验层** | 脚本写入 JSON 后没有 Schema 校验，格式错误会导致前端白屏 | 稳定性风险 |

---

## 3. 方案对比

### 方案 A：静态 JSON + CDN（推荐，当前路径）

**机制**：AI Secretary 更新 JSON → 上传到 CDN/S3 → 前端 `fetch` CDN URL

```
ai-secretary 修改 JSON
        ↓
  运行同步脚本（自动）
        ↓
  上传到 CDN（manus-upload-file --webdev）
        ↓
  前端 fetch CDN URL（无需重新部署）
        ↓
  看板实时更新
```

**优点**：
- 前端代码零改动，完全解耦
- 更新延迟 < 1 分钟（上传即生效）
- 无需后端服务，成本极低

**缺点**：
- 需要 CDN URL 固定（或前端配置可变的数据源 URL）
- 多人同时修改 JSON 有冲突风险

**可行性**：✅ **高**，当前架构直接支持，只需将 `fetch('/dashboard_data.json')` 改为 `fetch(import.meta.env.VITE_DATA_URL || '/dashboard_data.json')`，即可在不改动代码的前提下切换数据源。

---

### 方案 B：飞书 Bitable 实时 API

**机制**：AI Secretary 写入飞书 Bitable → 前端直接调用 Bitable API 读取

```
ai-secretary 写入 Bitable
        ↓
  前端 fetch Bitable API（实时）
        ↓
  看板实时更新
```

**优点**：
- 真正实时，无需任何同步步骤
- Bitable 天然支持多人协作编辑
- 可在飞书内直接查看/修改数据

**缺点**：
- 前端需要处理 Bitable API 认证（token 管理）
- Bitable 字段结构与当前 JSON Schema 差异较大，需要转换层
- API 有频率限制，高并发场景需缓存

**可行性**：⚠️ **中**，技术上可行，但需要额外开发 API 适配层，且 Bitable 的表结构需要与 `dashboard_data.json` Schema 严格对齐。

---

### 方案 C：Git 触发自动部署（最完整）

**机制**：AI Secretary 提交 JSON 到 GitHub → GitHub Actions 自动同步到前端 CDN

```
ai-secretary git push dashboard_data.json
        ↓
  GitHub Actions 触发
        ↓
  自动上传到 CDN / 重新部署前端
        ↓
  看板自动更新
```

**优点**：
- 完全自动化，无需任何手动步骤
- Git 提供完整的变更历史和回滚能力
- 与现有 `ai-secretary-architecture` 仓库天然集成

**缺点**：
- 需要配置 GitHub Actions（一次性工作）
- 部署时间 2-5 分钟

**可行性**：✅ **高**，是三个方案中最完整的，适合作为长期目标。

---

## 4. 推荐落地路径

### 阶段一（当前，立即可用）

维持现有架构，AI Secretary 更新数据后手动运行同步脚本：

```bash
# 1. 在 ai-secretary-architecture 中更新数据
python3 scripts/inject_weekly_updates.py

# 2. 同步到前端（一条命令）
cp data/dashboard_data.json ../xpbet-frontend-components/kanban-v2/client/public/
cd ../xpbet-frontend-components && git add kanban-v2/client/public/dashboard_data.json && git commit -m "data: update dashboard $(date +%Y-%m-%d)" && git push
```

**改进点**：将上述两步合并为一个 `make update-dashboard` 或 `scripts/deploy_dashboard.sh` 脚本。

### 阶段二（短期，1-2 周）

将 `dashboard_data.json` 上传到 CDN，前端通过环境变量读取 CDN URL，实现「更新数据无需重新部署」：

1. 在 `useDashboardData.ts` 中将数据源改为 `import.meta.env.VITE_DATA_URL || '/dashboard_data.json'`
2. 在 Manus 项目 Secrets 中配置 `VITE_DATA_URL` 指向 CDN 地址
3. AI Secretary 每次更新后运行 `manus-upload-file --webdev data/dashboard_data.json`，获取新 CDN URL 并更新 Secret

### 阶段三（中期，可选）

配置 GitHub Actions：监听 `ai-secretary-architecture` 仓库的 `data/dashboard_data.json` 变更，自动触发 `xpbet-frontend-components` 的重新部署。

---

## 5. 数据维护规范

为确保 AI Secretary 能够可靠地维护数据，以下字段已设计为**机器可写**：

| 字段路径 | 更新频率 | 维护脚本 |
|----------|----------|----------|
| `modules[].progress_percentage` | 每周 | `parse_to_dashboard_json.py` |
| `modules[].status` | 每周 | `parse_to_dashboard_json.py` |
| `modules[].weekly_updates[]` | 每周二 | `inject_weekly_updates.py` |
| `modules[].features[].docs[]` | 按需 | `sync_bitable_docs.py` |
| `module_groups[].milestones[].progress` | 每周 | `add_group_milestones.py` |
| `module_groups[].milestones[].overdue` | 每周（自动检测） | `add_group_milestones.py` |
| `milestones[].group_snapshots[]` | 每个里程碑节点 | `enrich_global_milestones.py` |
| `kpi_metrics` | 每周 | 手动或扩展脚本 |

**不应由脚本自动修改的字段**（需人工确认）：
- `milestones[].status`（里程碑完成状态，需 PM 确认）
- `modules[].features[].workflow`（需求评审状态，需评审会确认）
- `module_groups[].milestones[].title`（里程碑标题，需 PM 定义）

---

## 6. 结论

**当前方案（方案 A 阶段一）可行性高**，前端已完全数据驱动，AI Secretary 只需维护一个 JSON 文件即可更新看板所有内容。主要待完善的是「数据更新→前端生效」的自动化程度，可按阶段逐步提升。

核心约束已满足：**前端代码不需要任何改动，所有业务状态通过 JSON 数据驱动**。

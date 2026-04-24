# Shell 注入框架改造说明

## 改造背景

**问题**：`weekly-report-builder` 技能在阶段三生成周报时，大模型直接输出完整 HTML/TSX 代码（1000-2000 行），导致约 80% 的输出 Token 浪费在静态模板代码上，而非真正的业务数据。

**根因**：技能规范中虽然提到了 `MultiProjectShell.tsx` 组件，但缺乏强制约束机制，大模型倾向于直接生成代码而非复用模板。

---

## 改造方案

### 核心思路：「JSON → HTML Shell」分离架构

```
旧方案：大模型 → 1600+ 行 HTML（含 CSS + JS + 数据）
新方案：大模型 → 80-150 行 JSON 数据 → render.py → 完整 HTML
```

### 新增文件

| 文件 | 行数 | 作用 |
| :--- | :--- | :--- |
| `templates/shells/multi_project.html` | 438 | platform 类型 HTML Shell 模板（含 20 个占位符） |
| `templates/shells/general.html` | 287 | general 类型 HTML Shell 模板 |
| `templates/shells/growth.html` | 225 | growth 类型 HTML Shell 模板（转化漏斗+渠道 ROI） |
| `templates/shells/pre_launch.html` | 255 | pre-launch 类型 HTML Shell 模板（功能点+模块进度） |
| `templates/shells/ops.html` | 216 | ops 类型 HTML Shell 模板（活动+内容运营） |
| `templates/shells/post_investment.html` | 206 | post-investment 类型 HTML Shell 模板 |
| `scripts/render.py` | 223 | 通用渲染入口（自动路由到对应 Shell） |
| `scripts/shell_registry.py` | 703 | Shell 注册表 + 6 种类型渲染器实现 |
| `scripts/shell_injector.py` | 487 | platform 类型专用注入器（已有） |

---

## 使用方法

### 基本用法

```bash
# 渲染任意类型的周报（自动路由）
python scripts/render.py \
  --data state/{session_id}_shell_data.json \
  --type {projectType} \
  --output output/{projectType}/weekly_report_{period}.html

# 查看所有支持的类型
python scripts/render.py --list-types

# 验证数据（不写入文件）
python scripts/render.py \
  --data state/{session_id}_shell_data.json \
  --type {projectType} \
  --dry-run
```

### 支持的项目类型

| 类型 | Shell 模板 | 适用场景 |
| :--- | :--- | :--- |
| `platform` | `multi_project.html` | 中台/基础设施，多项目并行 |
| `post-investment` | `post_investment.html` | 投后管理，被投企业组合 |
| `general` | `general.html` | 通用产品团队 |
| `growth` | `growth.html` | 增长团队，转化漏斗+渠道 ROI |
| `pre-launch` | `pre_launch.html` | 研发期，功能点驱动里程碑 |
| `ops` | `ops.html` | 运营团队，活动+内容运营 |

---

## Token 节省效果

| 指标 | 旧方案（直接生成 HTML） | 新方案（JSON 注入） | 节省 |
| :--- | :--- | :--- | :--- |
| Agent 输出行数（首次） | 1,600+ 行 | ~150 行 JSON | **-90%** |
| Agent 输出行数（更新） | 1,600+ 行 | ~150 行 JSON | **-90%** |
| HTML 模板维护成本 | 每次重新生成 | 一次写入，永久复用 | ✅ |

---

## 架构图

```
用户提供周报数据
       ↓
  大模型解析数据
  只输出 JSON (~150行)
       ↓
  render.py (通用入口)
       ↓
  shell_registry.py (类型路由)
  ├── platform → shell_injector.py → multi_project.html
  ├── general → GeneralRenderer → general.html
  ├── growth → GrowthRenderer → growth.html
  ├── pre-launch → PreLaunchRenderer → pre_launch.html
  ├── ops → OpsRenderer → ops.html
  └── post-investment → PostInvestmentRenderer → post_investment.html
       ↓
  完整 HTML 文件（60-80KB）
```

---

## 改造日期

2026-04-24

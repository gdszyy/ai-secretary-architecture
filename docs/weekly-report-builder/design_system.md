# Sukie Project Dashboard — 设计规范文档

> **Token 节省提示**：本文件 498 行，**按需 grep 而非全文读取**。常用命令：
> ```bash
> grep -A 50 "^## 3\." references/design_system.md   # 颜色系统（主色/背景/文字/边框）
> grep -A 30 "^## 4\." references/design_system.md   # 功能色（状态色/KPI色）
> grep -A 30 "^## 6\." references/design_system.md   # 字体系统（字号/字重/行高）
> grep -A 20 "^## 8\." references/design_system.md   # 卡片层级（Level 1/2/3 毛玻璃）
> grep -A 15 "^## 9\." references/design_system.md   # 圆角系统
> grep -A 15 "^## 10\." references/design_system.md  # 阴影系统
> grep -A 30 "^## 11\." references/design_system.md  # 动效系统
> grep -A 20 "^## 12\." references/design_system.md  # 毛玻璃效果（backdrop-blur/高光线）
> grep -A 100 "^## 附录" references/design_system.md  # 完整 Token JSON
> ```
> 章节速查：§1视觉层级 | §2对比度 | §3颜色 | §4功能色 | §5按钮 | §6字体 | §7间距 | §8卡片 | §9圆角 | §10阴影 | §11动效 | §12视觉效果 | §13图标 | §14图像 | 附录Token JSON

**版本：** 1.0
**主题：** Light（浅色主题，默认）/ Dark（深色主题，可切换）
**视觉风格：** iOS 26 Liquid Glass — 毛玻璃折射、自适应光晕、分层透明
**行业分类：** 项目管理 / 数据看板 / 内部工具
**设计语言来源：** Apple iOS 26 设计系统

> 本文档由 `design-spec-extractor` 技能从 Sukie Dashboard 源码（`client/src/index.css` + 组件层）提取生成，覆盖 14 个维度的生产级设计 Token 系统。所有颜色值采用 OKLCH 色彩空间（Tailwind CSS v4 标准）。

---

## 1. 视觉层级与业务逻辑

本看板的视觉层级服务于**项目信息的快速扫描与下钻**，而非传统 SaaS 的转化漏斗。首屏"项目全景"模块承担 P0 注意力引导，KPI 指标卡片承担 P1 数据消费，模块进度与里程碑时间轴承担 P2 决策支撑，次要模块（团队/财务/风险等）承担 P3 背景信息。

| 焦点层级 | 引导方式 | 代表元素 |
|---------|---------|---------|
| P0 主焦点 | 大面积毛玻璃卡片 + 彩色仪表盘 + 动态波纹 | 项目健康度仪表盘、四信号格 |
| P1 关键信息 | 3xl 粗体数字 + 状态色顶部边框 + sparkline | KPI 指标卡片（DAU / D1留存 / 付费率等）|
| P2 次要操作 | 中等字重 + 中性色 + 悬浮交互 | 里程碑节点、模块进度条、折叠面板 |
| P3 背景信息 | 最小字号 + 最低对比度 | 次要模块（团队/财务/风险/待办）|

**CTA 视觉处理：** 主操作按钮采用 iOS 26 毛玻璃药丸形态，带顶部高光线（`0 1px 0 0 white/60 inset`）；状态徽章采用彩色半透明背景 + 同色系边框，形成"染色玻璃"效果。

**业务逻辑强调（按视觉权重排序）：**

1. 项目健康度评分（仪表盘 + 月度趋势）
2. 核心增长指标（DAU、D1/D7 留存）
3. 风险预警（RTP 双重异常，红色高亮）
4. 当前阶段进展（里程碑时间轴，当前节点高亮）
5. 模块优先级排序（P1-P6 标签 + 进度条）

---

## 2. 对比度系统

| 场景 | 估算 WCAG 比值 | 合规等级 |
|------|--------------|---------|
| 主文本 / 页面背景（浅色）| ~14:1 | AAA |
| 次要文本 / 页面背景（浅色）| ~7:1 | AA |
| 静音文本 / 页面背景（浅色）| ~3.5:1 | AA Large |
| 白色文本 / 主品牌色（蓝紫）| ~5:1 | AA |
| 卡片 / 页面背景（浅色）| 视觉分离约 ~1.5:1（依赖毛玻璃层次，非纯色对比）| 依赖效果 |
| 悬浮弹出层 / 卡片背景 | ~1.3:1（透明度差异 + 阴影区分）| 依赖效果 |
| 按钮文字 / 按钮填充色 | ~5:1 | AA |

**边框可见性：** 浅色模式下边框使用 `oklch(0 0 0 / 0.08)`（极淡黑色），主要依赖毛玻璃顶部高光线（`oklch(1 0 0 / 0.55)`）作为视觉边界，而非传统描边。深色模式下边框为 `oklch(1 0 0 / 0.1)`（极淡白色）。

**焦点指示器：** 全局使用 `outline-ring/50`，焦点环颜色为主品牌蓝 `oklch(0.58 0.22 255 / 0.4)`，圆角与容器一致。

---

## 3. 颜色系统

### 3.1 主品牌色

| Token | OKLCH | 近似 HEX | 用途 |
|-------|-------|---------|------|
| `primary.default`（浅色）| `oklch(0.58 0.22 255)` | `#3b82f6` | 默认状态、主按钮、焦点环 |
| `primary.default`（深色）| `oklch(0.68 0.20 255)` | `#60a5fa` | 深色模式主色 |
| `primary.hover` | `oklch(0.52 0.22 255)` | `#2563eb` | 悬浮状态 |
| `primary.press` | `oklch(0.46 0.22 255)` | `#1d4ed8` | 按下状态 |
| `primary.light` | `oklch(0.58 0.22 255 / 0.12)` | `#3b82f6/12%` | 背景色调、徽章底色 |
| `accent`（紫色）| `oklch(0.62 0.22 280)` | `#7c3aed` | Logo 渐变起点、高亮强调 |
| `accentSecondary` | `oklch(0.58 0.24 310)` | `#9333ea` | Logo 渐变终点 |

### 3.2 背景层级

| Token | OKLCH（浅色）| OKLCH（深色）| 用途 |
|-------|------------|------------|------|
| `background.base` | `oklch(0.975 0.003 240)` | `oklch(0.11 0.008 240)` | 页面/Body 背景（带固定网
格渐变）|
| `background.surface`（卡片）| `oklch(1 0 0 / 0.72)` | `oklch(1 0 0 / 0.07)` | 毛玻璃卡片、面板 |
| `background.elevated`（弹出）| `oklch(1 0 0 / 0.88)` | `oklch(0.16 0.008 240 / 0.92)` | Popover、下拉菜单 |
| `background.overlay` | `oklch(0 0 0 / 0.4)` | `oklch(0 0 0 / 0.6)` | 模态遮罩层 |
| `background.sunken`（输入框）| `oklch(0 0 0 / 0.06)` | `oklch(1 0 0 / 0.08)` | 输入框、内嵌区域 |

**背景网格渐变（固定定位）：**

浅色模式使用三个椭圆径向渐变叠加，分别在左上角（蓝色 `oklch(0.88 0.06 255 / 0.35)`）、右下角（紫色 `oklch(0.88 0.06 295 / 0.25)`）、右上角（青色 `oklch(0.92 0.04 200 / 0.2)`），营造自然的环境光晕效果。深色模式对应位置使用低明度版本（L 值约 0.4-0.45）。

### 3.3 文字颜色

| Token | OKLCH（浅色）| OKLCH（深色）| 用途 |
|-------|------------|------------|------|
| `text.primary` | `oklch(0.12 0.008 240)` | `oklch(0.95 0.005 240)` | 主体文字 |
| `text.secondary` | `oklch(0.35 0.01 240)` | `oklch(0.75 0.008 240)` | 辅助文字 |
| `text.muted` | `oklch(0.52 0.012 240)` | `oklch(0.60 0.012 240)` | 占位符、元数据 |
| `text.inverse` | `oklch(1 0 0)` | `oklch(0.12 0.008 240)` | 深色背景上的文字 |
| `text.onPrimary` | `oklch(1 0 0)` | `oklch(0.1 0.005 240)` | 主品牌色上的文字 |

### 3.4 边框颜色

| Token | OKLCH（浅色）| OKLCH（深色）| 用途 |
|-------|------------|------------|------|
| `border.default` | `oklch(0 0 0 / 0.08)` | `oklch(1 0 0 / 0.10)` | 标准边框 |
| `border.strong` | `oklch(0 0 0 / 0.16)` | `oklch(1 0 0 / 0.20)` | 强调边框 |
| `border.subtle`（毛玻璃高光）| `oklch(1 0 0 / 0.55)` | `oklch(1 0 0 / 0.18)` | 毛玻璃顶部高光线 |
| `border.focus` | `oklch(0.58 0.22 255 / 0.4)` | `oklch(0.68 0.20 255 / 0.4)` | 焦点环 |

---

## 4. 功能色系统

| 语义 | 默认色（OKLCH）| 背景色调 | 文字色（浅色模式）| 文字色（深色模式）|
|------|--------------|---------|----------------|----------------|
| **Success 成功** | `oklch(0.62 0.2 160)` | `/0.10` | `oklch(0.38 0.18 160)` | `oklch(0.72 0.18 160)` |
| **Error 错误** | `oklch(0.58 0.22 25)` | `/0.10` | `oklch(0.42 0.22 20)` | `oklch(0.70 0.22 20)` |
| **Warning 警告** | `oklch(0.68 0.19 55)` | `/0.10` | `oklch(0.42 0.18 55)` | `oklch(0.78 0.17 55)` |
| **Info 信息** | `oklch(0.58 0.22 255)` | `/0.10` | `oklch(0.38 0.18 220)` | `oklch(0.68 0.18 200)` |
| **Neutral 中性** | `oklch(0.52 0.012 240)` | `/0.08` | `oklch(0.35 0.01 240)` | `oklch(0.60 0.012 240)` |

**KPI 状态色系（专用）：**

| 状态 | 标签 | 颜色（深色）| 颜色（浅色覆盖）|
|------|------|-----------|--------------|
| `success` | 健康 | `emerald-400` `#34d399` | `oklch(0.38 0.18 160)` |
| `warning` | 待优化 | `amber-400` `#fbbf24` | `oklch(0.42 0.18 55)` |
| `danger` | 风险 | `red-400` `#f87171` | `oklch(0.42 0.22 20)` |
| `info` | 增长中 | `sky-400` `#38bdf8` | `oklch(0.38 0.18 220)` |
| `purple` | 进行中 | `violet-400` `#a78bfa` | `oklch(0.38 0.20 290)` |

**徽章颜色变体：** 优先级标签（P1 红/P2 橙/P3 蓝/P4-6 灰）、模块状态（开发中蓝/评审中紫/风险预警红/规划中灰/已完成绿）。

**状态指示器：** 活跃状态使用 `animate-pulse` 脉冲圆点（`w-1.5 h-1.5 rounded-full`）；风险状态使用 `pulse-danger` 自定义动画（更快频率）；里程碑当前节点使用 `ring-4 ring-violet-500/25` 光晕环。

---

## 5. 按钮系统

### 5.1 按钮变体

| 变体 | 背景 | 文字色 | 边框 | 圆角 | 内边距 | 特殊效果 |
|------|------|------|------|------|------|---------|
| **Primary**（主操作）| `oklch(0.58 0.22 255)` 蓝 | 白 | 无 | `rounded-xl` (12px) | `px-4 py-2` | 悬浮 scale-105 + shadow |
| **Glass Pill**（导航/徽章）| `var(--glass)` 毛玻璃 | 前景色 | `var(--glass-border)` 高光 | `rounded-full` | `px-3 py-1.5` | 顶部高光线 inset |
| **Glass Subtle**（图标按钮）| `var(--surface-2)` | 静音色 | `var(--border)` | `rounded-full` | `w-9 h-9` | 悬浮 scale-105，按下 scale-95 |
| **Ghost / Outline**（次要）| 透明 | 前景色 | `var(--border)` | `rounded-xl` | `px-3 py-1.5` | 悬浮 border-blue-400/40 |
| **Destructive**（危险操作）| `oklch(0.58 0.22 25)` 红 | 白 | 无 | `rounded-xl` | `px-4 py-2` | — |
| **Icon Only**（里程碑节点）| 状态色 | 白 | 状态色 2px | `rounded-full` | `w-11 h-11` | 悬浮 scale-110，active ring 光晕 |

**悬浮效果：** 卡片类按钮使用 `-translate-y-1 + shadow-xl`；图标按钮使用 `scale-105`；所有过渡时长 `200-300ms ease`。

**按下效果：** `scale-95 active:scale-95`，持续 `150ms`。

**加载状态：** 使用 Lucide `Loader2` 图标 + `animate-spin`，按钮禁用并降低透明度。

**图标按钮样式：** 圆形（`rounded-full`），尺寸 `w-9 h-9`，毛玻璃背景，图标居中。

### 5.2 尺寸变体

| 尺寸 | 描述 |
|------|------|
| sm | `px-2.5 py-1 text-xs rounded-md`，用于徽章、内联操作 |
| md | `px-3 py-1.5 text-xs rounded-full`，用于导航徽章、状态标签 |
| lg | `px-4 py-2 text-sm rounded-xl`，用于主操作按钮 |

---

## 6. 字体系统

**字体族：**

| 角色 | 字体 | 来源 | 用途 |
|------|------|------|------|
| Primary（中文 UI）| `Noto Sans SC` | Google Fonts | 所有中文文字、UI 标签 |
| Secondary（数字/英文）| `DM Sans` | Google Fonts | KPI 数值、版本号、英文标题 |
| Mono（数字表格）| `DM Sans`（tabular-nums）| — | 数据表格、等宽数字 |
| Display | — | — | 无独立 Display 字体，使用 DM Sans Bold |

**字体降级栈：** `"Noto Sans SC", "DM Sans", -apple-system, "Helvetica Neue", system-ui, sans-serif`

**字号比例：**

| 层级 | 字号 | 字重 | 行高 | 字间距 | 用途 |
|------|------|------|------|------|------|
| Display | 30px (`text-3xl`) | 700 | 1.2 | `-0.02em` | KPI 核心数值 |
| H1 | 24px (`text-2xl`) | 700 | 1.3 | `-0.01em` | 页面主标题（未使用）|
| H2 | 18px (`text-lg`) | 700 | 1.4 | `0` | 模块标题（中文名）|
| H3 | 16px (`text-base`) | 600 | 1.5 | `0` | 卡片标题、子模块名 |
| Body | 14px (`text-sm`) | 400 | 1.6 | `0.01em` | 正文、描述文字 |
| Small | 12px (`text-xs`) | 400-500 | 1.5 | `0` | 辅助信息、标签 |
| Label | 11px (`text-[11px]`) | 500-600 | 1.4 | `0` | 导航元数据、状态标签 |
| Caption | 10px (`text-[10px]`) | 400 | 1.4 | `0` | 最小元数据（全局最小字号）|

**文字变换：** 章节标题使用 `uppercase tracking-widest`（全大写 + 极宽字间距），用于区分内容区与导航区。

**标题风格：** 中文标题使用 Noto Sans SC，英文副标题使用 DM Sans 小写，形成双语对照排版（如"模块进展 · MODULE PROGRESS"）。

---

## 7. 间距系统

**基础单位：** 4px（Tailwind 默认，`spacing-1 = 4px`）

**间距比例：** `4px / 8px / 12px / 16px / 20px / 24px / 32px / 40px / 48px / 64px`

| 组件 | 数值 |
|------|------|
| 卡片内边距（标准）| `20px`（`p-5`）|
| 卡片内边距（大型面板）| `32-40px`（`p-8 / p-10`）|
| 卡片间距（网格）| `16px`（`gap-4`）|
| 区块间距 | `32px`（`gap-8` / `mb-8`）|
| 表单字段间距 | `16px`（`gap-4`）|
| 按钮内边距（md）| `12px 16px`（`px-4 py-3`）|
| 列表项高度 | `40px`（最小触控目标）|
| 导航栏高度 | `~60px`（`py-3.5` + 内容）|
| 图标尺寸 sm/md/lg | `12px / 15-17px / 20-24px` |
| 布局最大宽度 | `1400px`（`max-w-[1400px]`）|
| 网格间距 | `16px`（`gap-4`）|
| 容器内边距 | `16px (sm) / 24px (md) / 32px (lg+)` |

---

## 8. 卡片与表面层级系统

| 层级 | 背景（浅色）| 边框 | 圆角 | 阴影 | 用途 |
|------|-----------|------|------|------|------|
| Level 1（基础玻璃卡片）| `oklch(1 0 0 / 0.65)` | 顶部高光 `oklch(1 0 0 / 0.55)` | `rounded-2xl` (16px) | `0 4px 24px -4px shadow/8%` | KPI 卡片、模块卡片、内容面板 |
| Level 2（悬浮/嵌套）| `oklch(0.97 0.004 240 / 0.8)` | `oklch(0 0 0 / 0.08)` | `rounded-xl` (12px) | `0 2px 12px shadow/6%` | 嵌套元素、次级面板 |
| Level 3（弹出/模态）| `oklch(1 0 0 / 0.88)` | `oklch(1 0 0 / 0.55)` | `rounded-2xl` (16px) | `0 16px 48px -8px shadow/12%` | HoverCard 弹出层、Popover |

**交互卡片悬浮：** `-translate-y-1 + shadow-xl`，过渡 `250ms ease`；透明度从 `0.9` 提升至 `1.0`（`glass` 类默认 90% 透明度，悬浮恢复 100%）。

**图片宽高比：** 看板不使用图片内容，图表区域采用 `ResponsiveContainer` 自适应宽度，固定高度（`h-[130px]` 至 `h-[200px]`）。

---

## 9. 圆角系统

| Token | 数值 | 用途 |
|-------|------|------|
| `radius-xs` | `4px` (`rounded-sm`) | 内部小元素 |
| `radius-sm` | `8px` (`rounded-lg`) | 输入框、小卡片 |
| `radius-md` | `12px` (`rounded-xl`) | 按钮、嵌套面板 |
| `radius-lg` | `14px` (`rounded-[0.875rem]`) | 全局基础圆角（`--radius`）|
| `radius-xl` | `16px` (`rounded-2xl`) | **主导圆角**，卡片、大面板 |
| `radius-2xl` | `24px` (`rounded-3xl`) | 超大容器（较少使用）|
| `radius-full` | `9999px` (`rounded-full`) | 药丸按钮、头像、状态点 |

**圆角个性：** 大圆角（`rounded-2xl` 为主），遵循 iOS 26 同心圆角原则（外层 `rounded-2xl`，内层 `rounded-xl`，最内层 `rounded-lg`），营造层次感。

---

## 10. 阴影系统

| Token | CSS 值 | 用途 |
|-------|--------|------|
| `shadow-sm` | `0 1px 3px oklch(0 0 0 / 0.08)` | 轻微浮起 |
| `shadow-md` | `0 4px 16px -4px oklch(0 0 0 / 0.10)` | 标准卡片阴影 |
| `shadow-lg` | `0 8px 32px -8px oklch(0 0 0 / 0.12)` | 导航栏、大面板 |
| `glass-shadow`（浅色）| `oklch(0 0 0 / 0.08)` | 毛玻璃卡片环境阴影 |
| `glass-shadow`（深色）| `oklch(0 0 0 / 0.40)` | 深色模式加深阴影 |
| `glow`（Logo）| `0 2px 8px oklch(0.58 0.22 280 / 0.4)` | 品牌紫色光晕 |
| `inner-specular` | `0 1px 0 0 oklch(1 0 0 / 0.6) inset` | 毛玻璃顶部高光线（核心效果）|
| `inner-bottom` | `0 -1px 0 0 oklch(0 0 0 / 0.06) inset` | 毛玻璃底部暗线 |

**彩色阴影：** 状态色阴影用于里程碑节点（`ring-4 ring-violet-500/25`），不用于卡片。

---

## 11. 动效系统

| Token | 数值 | 用途 |
|-------|------|------|
| `duration-fast` | `150ms` | 按下反馈、图标切换 |
| `duration-normal` | `200-250ms` | 卡片悬浮、状态切换 |
| `duration-slow` | `300-400ms` | 面板展开/收起、页面过渡 |
| `easing-default` | `ease` | 通用过渡 |
| `easing-entrance` | `ease-out` | 元素进入 |
| `easing-exit` | `ease-in` | 元素退出 |
| `hover-transition` | `transform, opacity, box-shadow` | 卡片悬浮属性 |
| `page-transition` | 无（SPA 单页，无路由切换）| — |

**微交互清单：**

| 交互 | 效果 | 时长 |
|------|------|------|
| KPI 数值进场 | `useCountUp` 数字滚动动画 | `1000-1200ms ease-out` |
| KPI sparkline 末点 | SVG `animate` r 从 2.5 到 7 + opacity 淡出（波纹）| `1.6s infinite` |
| 里程碑节点悬浮 | `scale-110` | `300ms` |
| 里程碑节点按下 | `scale-95` | `150ms` |
| 卡片悬浮 | `-translate-y-1 + shadow-xl + opacity 0.9→1` | `250ms ease` |
| 主题切换图标 | `Sun ↔ Moon` 图标切换 + 颜色过渡 | `200ms` |
| 折叠面板展开 | `ChevronDown ↔ ChevronUp` + 内容显示/隐藏 | 即时（无动画）|
| 风险状态点 | `pulse-danger` 快速脉冲 | `1s infinite` |
| 活跃状态点 | `animate-pulse` 标准脉冲 | `2s infinite` |

---

## 12. 视觉效果

| 效果 | 启用 | 说明 |
|------|------|------|
| **Glassmorphism 毛玻璃** | ✅ 核心效果 | `backdrop-filter: blur(20px) saturate(1.8)`，四个变体：`.glass / .glass-elevated / .glass-subtle / .glass-tinted` |
| **Neon Glow 霓虹光晕** | ❌ | 不使用霓虹效果，仅有品牌色柔和光晕 |
| **Gradients 渐变** | ✅ | 背景网格渐变（三径向叠加）+ Logo 线性渐变 |
| **Texture Overlay 纹理** | ❌ | 不使用纹理 |
| **Particle Effects 粒子** | ❌ | 不使用粒子 |
| **Parallax 视差** | ❌ | 背景使用 `background-attachment: fixed` 固定，非视差 |

**效果描述：** 整体采用 Apple iOS 26 Liquid Glass 风格，核心视觉语言是**半透明折射层**。卡片通过 `backdrop-filter: blur + saturate` 实现毛玻璃质感，顶部 `inset` 高光线模拟玻璃边缘反光，底部暗线模拟玻璃厚度。背景固定渐变光晕透过玻璃层产生"环境色染色"效果，在浅色模式下尤为明显（蓝/紫/青三色光晕）。

---

## 13. 图标系统

**图标库：** [Lucide React](https://lucide.dev/)（stroke-based 描边风格，React 组件）

**风格：** 描边（outline），统一 `strokeWidth={1.5}`（Lucide 默认），圆角端点。

**尺寸规范：**

| 场景 | 尺寸 | 示例 |
|------|------|------|
| 导航栏图标 | `17px`（`size={17}`）| Logo Zap、GitBranch |
| 内联状态图标 | `12-13px` | Activity、AlertTriangle |
| 章节标题图标 | `15-16px` | Users、DollarSign |
| 里程碑节点图标 | `17px` | CheckCircle2、Clock、Circle |
| 交互控件图标 | `14-16px` | ChevronDown、ChevronUp |
| 趋势指示图标 | `11px` | TrendingUp、TrendingDown、Minus |

---

## 14. 图像风格

本看板为纯数据可视化产品，不使用照片或插图类图像资产。所有视觉内容均为：

**图表类型：** Recharts 库渲染的 SVG 图表（折线图 `LineChart`、面积图 `AreaChart`、柱状图 `BarChart`、参考线 `ReferenceLine`）。图表背景透明，融入毛玻璃卡片。

**自定义 SVG：** KPI sparkline 迷你折线图（纯 SVG，无库依赖），仪表盘弧形（SVG arc path）。

**图表配色：** 使用 `--chart-1` 至 `--chart-5` 五个语义化图表色 Token，分别对应蓝/绿/橙/紫/红，深浅色模式自动切换。

**宽高比：** 图表容器使用 `ResponsiveContainer width="100%"`，高度固定（`height={130}` 至 `height={200}`）。

---

## 可用性与多语言规范

以下规范在所有派生设计中必须强制执行：

**触控目标：** 所有交互元素最小 `40×40px`（`w-9 h-9` = 36px 为最小值，通过 padding 补足）。里程碑节点按钮为 `w-11 h-11`（44px），符合 WCAG 2.5.5 AAA 标准。

**文字扩展：** 所有文字容器使用 `min-w` + `px-*` 或 `flex-1 min-w-0`，禁止固定宽度文字容器。KPI 标签使用 `truncate max-w-[80px]` 防止溢出。

**系统可见性：** 加载状态使用 `Loader2 animate-spin`，不仅禁用按钮；图表加载使用 `ResponsiveContainer` 自适应，避免布局抖动。

**错误预防：** 危险操作（如数据重置）需二次确认；表单错误显示具体原因（当前看板为只读，无表单操作）。

**多语言安全区：** 所有 Banner 文字区域右侧预留 10% 缓冲，防止葡萄牙语/德语文字溢出（当前版本为中文，但架构预留）。

---

## 附录：设计 Token JSON

以下为可直接用于 LLM 驱动 UI 生成或皮肤切换的原始 Token 对象：

```json
{
  "theme": "light",
  "brandName": "Sukie Project Dashboard",
  "visualStyle": "iOS 26 Liquid Glass — translucent, refractive, adaptive",
  "industryCategory": "project-management / internal-tool / data-dashboard",

  "colors": {
    "primary": {
      "default": "oklch(0.58 0.22 255)",
      "hover":   "oklch(0.52 0.22 255)",
      "press":   "oklch(0.46 0.22 255)",
      "light":   "oklch(0.58 0.22 255 / 0.12)"
    },
    "background": {
      "base":     "oklch(0.975 0.003 240)",
      "surface":  "oklch(1 0 0 / 0.72)",
      "elevated": "oklch(1 0 0 / 0.88)",
      "overlay":  "oklch(0 0 0 / 0.4)",
      "sunken":   "oklch(0 0 0 / 0.06)"
    },
    "text": {
      "primary":   "oklch(0.12 0.008 240)",
      "secondary": "oklch(0.35 0.01 240)",
      "muted":     "oklch(0.52 0.012 240)",
      "inverse":   "oklch(1 0 0)",
      "onPrimary": "oklch(1 0 0)"
    },
    "border": {
      "default":  "oklch(0 0 0 / 0.08)",
      "strong":   "oklch(0 0 0 / 0.16)",
      "subtle":   "oklch(1 0 0 / 0.55)",
      "focus":    "oklch(0.58 0.22 255 / 0.4)"
    },
    "accent":          "oklch(0.62 0.22 280)",
    "accentSecondary": "oklch(0.58 0.24 310)"
  },

  "functionalColors": {
    "success": { "default": "oklch(0.62 0.2 160)",  "light": "oklch(0.62 0.2 160 / 0.10)",  "text": "oklch(0.38 0.18 160)", "icon": "oklch(0.38 0.18 160)" },
    "error":   { "default": "oklch(0.58 0.22 25)",  "light": "oklch(0.58 0.22 25 / 0.10)",  "text": "oklch(0.42 0.22 20)",  "icon": "oklch(0.42 0.22 20)" },
    "warning": { "default": "oklch(0.68 0.19 55)",  "light": "oklch(0.68 0.19 55 / 0.10)",  "text": "oklch(0.42 0.18 55)",  "icon": "oklch(0.42 0.18 55)" },
    "info":    { "default": "oklch(0.58 0.22 255)", "light": "oklch(0.58 0.22 255 / 0.10)", "text": "oklch(0.38 0.18 220)", "icon": "oklch(0.38 0.18 220)" },
    "neutral": { "default": "oklch(0.52 0.012 240)","light": "oklch(0.52 0.012 240 / 0.08)","text": "oklch(0.35 0.01 240)" }
  },

  "typography": {
    "fontFamilyPrimary":   "Noto Sans SC",
    "fontFamilySecondary": "DM Sans",
    "fontFamilyMono":      "DM Sans (tabular-nums)",
    "fontFamilyDisplay":   null,
    "scale": {
      "display": { "size": "30px", "weight": 700, "lineHeight": "1.2",  "letterSpacing": "-0.02em" },
      "h1":      { "size": "24px", "weight": 700, "lineHeight": "1.3",  "letterSpacing": "-0.01em" },
      "h2":      { "size": "18px", "weight": 700, "lineHeight": "1.4",  "letterSpacing": "0" },
      "h3":      { "size": "16px", "weight": 600, "lineHeight": "1.5",  "letterSpacing": "0" },
      "body":    { "size": "14px", "weight": 400, "lineHeight": "1.6",  "letterSpacing": "0.01em" },
      "small":   { "size": "12px", "weight": 400, "lineHeight": "1.5",  "letterSpacing": "0" },
      "label":   { "size": "11px", "weight": 500, "lineHeight": "1.4",  "letterSpacing": "0" },
      "caption": { "size": "10px", "weight": 400, "lineHeight": "1.4",  "letterSpacing": "0" }
    }
  },

  "spacingSystem": {
    "baseUnit": "4px",
    "scale": ["4px","8px","12px","16px","20px","24px","32px","40px","48px","64px"],
    "componentSpacing": {
      "cardPadding":     "20px (p-5) / 32px (p-8) for large panels",
      "cardGap":         "16px (gap-4)",
      "sectionPadding":  "32px (gap-8)",
      "formFieldGap":    "16px",
      "buttonPaddingMd": "12px 16px",
      "listItemHeight":  "40px",
      "navHeight":       "~60px",
      "iconSize":        { "sm": "12px", "md": "16px", "lg": "24px" }
    },
    "layoutMaxWidth":    "1400px",
    "gridGutter":        "16px",
    "containerPadding":  "16px (sm) / 24px (md) / 32px (lg+)"
  },

  "radius": {
    "xs":   "4px",
    "sm":   "8px",
    "md":   "12px",
    "lg":   "14px",
    "xl":   "16px",
    "full": "9999px",
    "radiusStyle": "large-rounded / iOS concentric"
  },

  "shadows": {
    "sm":           "0 1px 3px oklch(0 0 0 / 0.08)",
    "md":           "0 4px 16px -4px oklch(0 0 0 / 0.10)",
    "lg":           "0 8px 32px -8px oklch(0 0 0 / 0.12)",
    "glow":         "0 2px 8px oklch(0.58 0.22 280 / 0.4)",
    "innerShadow":  "0 1px 0 0 oklch(1 0 0 / 0.6) inset",
    "coloredShadow": "ring-4 ring-violet-500/25 (milestone active node)"
  },

  "motion": {
    "durationFast":   "150ms",
    "durationNormal": "250ms",
    "durationSlow":   "300ms",
    "easingDefault":  "ease",
    "easingEntrance": "ease-out",
    "easingExit":     "ease-in",
    "hoverTransitionProperty": "transform, opacity, box-shadow",
    "pageTransition": "none (SPA, no route transitions)",
    "microInteractions": [
      "KPI countUp number animation (1000ms ease-out)",
      "SVG sparkline ripple on last data point (1.6s infinite)",
      "Card hover lift -translate-y-1 + opacity 0.9→1 (250ms)"
    ]
  },

  "effects": {
    "glassmorphism": true,
    "neonGlow":      false,
    "gradients":     true,
    "textureOverlay":false,
    "particleEffects":false,
    "parallax":      false,
    "description":   "iOS 26 Liquid Glass: backdrop-blur(20px) saturate(1.8) + inset top specular highlight + ambient gradient background. Four glass variants: .glass (primary), .glass-elevated (popover), .glass-subtle (nested), .glass-tinted (colored accent)."
  },

  "iconography": {
    "style":   "outline (stroke-based)",
    "library": "Lucide React",
    "size":    "15-17px (nav), 12-13px (inline), 20-24px (section)"
  },

  "imageStyle": {
    "treatment":    "data-visualization only (SVG charts via Recharts)",
    "overlayStyle": null,
    "aspectRatios": ["responsive (100% width, fixed height 130-200px)"]
  }
}
```

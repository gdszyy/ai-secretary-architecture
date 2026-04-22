# 里程碑卡片详情组件 (Milestone Card List) 详细设计文档

## 1. 组件概述

**组件名称**: `MilestoneCardList`
**组件 Key**: `milestone_card_list`
**适用模块**: 里程碑进度 (Milestone Progress)
**组件类型**: 详情组件 (Detail Component)

该组件用于在周报网页中展示项目里程碑的详细列表。它采用竖直滚动的面板布局，每一行代表一个里程碑卡片，直观清晰地展示里程碑的状态、进度、时间对比、负责人及关键交付物。

## 2. 布局与交互设计

### 2.1 整体布局
- **外层容器**: 固定高度（如 `max-h-96`，约 384px），超出内容时竖直滚动 (`overflow-y: auto`)。
- **顶部区域**: 包含标题和状态筛选 Tab（全部 / 进行中 / 已完成 / 延期 / 待启动）。
- **列表区域**: 垂直排列的里程碑卡片列表，卡片之间有适当的间距。

### 2.2 卡片内部布局 (单行)
每个里程碑卡片采用网格或弹性盒布局，包含以下元素：
- **头部**:
  - 左侧: 里程碑名称（粗体，突出显示）。
  - 右侧: 状态标签（颜色区分状态）。
- **信息区**:
  - **时间对比**: 计划时间 vs 实际时间。如果状态为“延期”，则时间文本标红，并附加显示“延期 X 天”的醒目标签。
  - **负责人**: 展示负责人头像（或首字母占位符）及姓名。
- **内容区**:
  - 简短描述或关键交付物（1-2行文本，支持折叠/展开以节省空间）。
- **底部**:
  - 进度条（0-100%），进度条颜色与当前状态标签颜色保持一致。

### 2.3 视觉与颜色规范
根据 `weekly_report_example.tsx` 中的 `STATUS_CONFIG` 规范，状态颜色映射如下：
- **已完成 (done)**: 绿色系 (`emerald`)
- **进行中 (active)**: 蓝色系 (`sky`)
- **延期 (delayed)**: 红色系 (`red`) - **特殊要求**: 延期卡片背景使用淡红色 (`bg-red-50 dark:bg-red-900/10`)，视觉上优先吸引注意。
- **待启动 (upcoming)**: 灰色系 (`slate`)

### 2.4 交互逻辑
- **状态筛选**: 点击顶部 Tab 切换显示的里程碑列表。
- **内容折叠/展开**: 点击描述区域的“展开/收起”按钮，查看完整的交付物描述。
- **无三层交互限制**: 该组件作为详情组件，核心目标是直观展示信息，暂不包含进一步的下钻跳转逻辑。

## 3. 数据结构定义

### 3.1 状态枚举
```typescript
export type MilestoneCardStatus = 'done' | 'active' | 'delayed' | 'upcoming';
```

### 3.2 里程碑数据接口
```typescript
export interface MilestoneCardData {
  /** 里程碑唯一标识 */
  id: string;
  /** 里程碑名称 */
  title: string;
  /** 当前状态 */
  status: MilestoneCardStatus;
  /** 计划完成时间 (YYYY-MM-DD) */
  plannedDate: string;
  /** 实际完成时间或预计完成时间 (YYYY-MM-DD) */
  actualDate?: string;
  /** 延期天数（仅在 status 为 'delayed' 时有效） */
  delayDays?: number;
  /** 负责人姓名 */
  ownerName: string;
  /** 负责人头像 URL（可选） */
  ownerAvatar?: string;
  /** 简短描述或关键交付物 */
  description: string;
  /** 当前进度百分比 (0-100) */
  progress: number;
}
```

## 4. 组件 Props 接口

```typescript
export interface MilestoneCardListProps {
  /** 里程碑数据列表 */
  milestones: MilestoneCardData[];
  /** 组件标题，默认为 "里程碑详情" */
  title?: string;
  /** 自定义外层容器类名 */
  className?: string;
}
```

## 5. 状态筛选逻辑说明

组件内部维护一个 `filterStatus` 状态，初始值为 `'all'`。

```typescript
type FilterOption = 'all' | MilestoneCardStatus;
const [filterStatus, setFilterStatus] = useState<FilterOption>('all');
```

**筛选逻辑**:
在渲染列表前，根据 `filterStatus` 对传入的 `milestones` 数组进行过滤：
- 如果 `filterStatus === 'all'`，返回全部数据。
- 否则，返回 `milestone.status === filterStatus` 的数据。

**排序逻辑 (可选但推荐)**:
为了突出重点，可以对过滤后的列表进行排序：
1. 延期 (`delayed`) 优先显示。
2. 进行中 (`active`) 次之。
3. 待启动 (`upcoming`) 再次之。
4. 已完成 (`done`) 放最后。
或者按照计划时间 (`plannedDate`) 升序排列。本组件默认按状态优先级（延期 > 进行中 > 待启动 > 已完成）排序，同状态下按计划时间排序。

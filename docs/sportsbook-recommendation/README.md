# 体育博彩平台首页推荐系统 · 未来需求规划

> 本目录记录体育博彩平台首页推荐系统的完整需求规划，涵盖冷启动方案（Phase 0）至全个性化方案（Phase 3）的演进路线。详细需求文档存放于独立仓库 [sportsbook-requirements](https://github.com/gdszyy/sportsbook-requirements)。

---

## 系统概述

首页推荐系统由五个核心模块组成，在冷启动阶段全部由规则引擎驱动，随数据积累逐步演进至算法驱动：

| 模块 | 冷启动方案 | 最终形态 |
| :--- | :--- | :--- |
| 比赛推荐 | 全局热度排序 + 运营置顶 | 实时事件驱动 + 个性化排序 |
| 超级赔率 | 交易团队手动选品 | 算法提名 + 人工最终确认 |
| 注单推荐 | 全站最热市场 Top N | 在线学习 + 实时行为响应 |
| 串关推荐 | 人工预制模板库 | 个性化动态组合 |
| 热门联赛 | 地区默认静态排序 | 实时热度 + 个人偏好融合 |

---

## 需求文档结构（8 份 PRD）

```
PRD-01  运营配置平台（Operations CMS）     ← 基础设施，阻塞所有模块
PRD-02  赛事与赔率数据接入规范             ← 基础设施，阻塞所有模块
PRD-03  首页比赛推荐                       ← Sprint 2
PRD-04  热门联赛                           ← Sprint 2
PRD-05  超级赔率                           ← Sprint 3
PRD-06  注单推荐                           ← Sprint 3
PRD-07  串关推荐                           ← Sprint 4
PRD-08  算法接口预留规范                   ← Sprint 4（技术规范）
```

---

## 交付期规划

| Sprint | 内容 | 周期 | 门控条件 |
| :--- | :--- | :--- | :--- |
| Sprint 0 | 前置澄清（人工配置流程 / 算法边界 / 通用平台范围） | 1–2 周 | 输出三份澄清文档 |
| Sprint 1 | PRD-01 运营配置平台 + PRD-02 数据接入规范 | 3–4 周 | 平台就绪，推荐模块可并行 |
| Sprint 2 | PRD-03 比赛推荐 + PRD-04 热门联赛（可并行） | 3–4 周 | — |
| Sprint 3 | PRD-05 超级赔率 + PRD-06 注单推荐（可并行） | 3–4 周 | — |
| Sprint 4 | PRD-07 串关推荐 + PRD-08 算法接口规范 | 3–4 周 | — |

---

## 演进路线（Phase 0 → Phase 3）

```
Phase 0（冷启动）  →  Phase 1（分群个性化）  →  Phase 2（协同过滤）  →  Phase 3（实时全个性化）
触发：上线即可        触发：~10万注单             触发：~100万注单          触发：实时管道就绪
```

详见 [演进路线图](evolution-roadmap.md)。

---

## 关键架构决策

**通用配置平台（CMS）优先于所有推荐模块。** 所有推荐模块的冷启动逻辑都依赖人工配置，PRD-01 是唯一阻塞其他所有需求的文档。建议采用"共用平台 + 模块化扩展"方案：CMS 定义核心框架，各模块配置页面作为插件随对应 Sprint 交付。

**算法接口在第一天预留，能力分阶段激活。** 每个推荐模块在实现时均预留标准化的算法接入字段（如 `personalization_score`、`algorithm_generated`），冷启动阶段默认值为规则结果，未来算法接入后直接填充，无需重构前端和排序逻辑。

---

## 参考资料

| 文件 | 说明 |
| :--- | :--- |
| [体育赛事分级与限额](https://github.com/gdszyy/sportsbook-requirements/blob/main/references/体育赛事分级与限额.xlsx) | 风控参考：赛事分级规则与各级别投注限额 |
| [早盘滚球排序](https://github.com/gdszyy/sportsbook-requirements/blob/main/references/早盘滚球排序.xlsx) | 风控参考：早盘与滚球赛事排序规则 |

---

## 需求仓库

完整需求文档、架构图表、参考资料均存放于：**[gdszyy/sportsbook-requirements](https://github.com/gdszyy/sportsbook-requirements)**

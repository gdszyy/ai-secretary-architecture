# XPBET 首页推荐与活动功能 CMS 数据结构定义

**版本**：1.0
**作者**：Manus AI
**模块**：首页推荐系统、活动系统

本文档定义了 XPBET 首页推荐与活动功能在 CMS 后台配置时的数据结构（JSON Schema）。这些数据结构将用于前后端接口交互以及数据库存储设计。

---

## 1. 首页推荐系统

### 1.1 热门比赛/联赛配置 (Hot Events)

用于定义首页推荐展示的热门比赛或联赛。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "HotEventConfig",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "配置记录唯一标识"
    },
    "type": {
      "type": "string",
      "enum": ["event", "league"],
      "description": "推荐类型：单场比赛或联赛"
    },
    "sport_type": {
      "type": "string",
      "description": "运动类型标识，如 soccer, basketball"
    },
    "target_id": {
      "type": "string",
      "description": "对应的赛事 ID 或联赛 ID"
    },
    "display_name": {
      "type": "string",
      "description": "前端展示的推荐名称"
    },
    "weight": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "description": "展示权重，数字越大排序越靠前"
    },
    "valid_until": {
      "type": ["string", "null"],
      "format": "date-time",
      "description": "有效期至，null 表示长期有效"
    },
    "status": {
      "type": "string",
      "enum": ["active", "paused"],
      "description": "配置状态"
    }
  },
  "required": ["id", "type", "sport_type", "target_id", "display_name", "weight", "status"]
}
```

### 1.2 串关推荐卡片配置 (Parlay Cards)

用于定义首页展示的串关推荐卡片内容。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ParlayCardConfig",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "卡片唯一标识"
    },
    "title": {
      "type": "string",
      "description": "卡片标题，如 '今日精选 2 串 1'"
    },
    "parlay_type": {
      "type": "integer",
      "minimum": 2,
      "description": "串关类型，如 2 表示 2串1"
    },
    "position": {
      "type": "integer",
      "description": "展示位置序号"
    },
    "event_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 2,
      "description": "推荐的赛事 ID 列表，数量需与 parlay_type 一致"
    },
    "valid_until": {
      "type": "string",
      "format": "date-time",
      "description": "有效期至"
    },
    "status": {
      "type": "string",
      "enum": ["active", "paused"],
      "description": "卡片状态"
    }
  },
  "required": ["id", "title", "parlay_type", "position", "event_ids", "valid_until", "status"]
}
```

### 1.3 中奖订单推荐配置 (Winning Orders)

用于定义首页中奖订单的展示规则。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WinningOrderConfig",
  "type": "object",
  "properties": {
    "display_mode": {
      "type": "string",
      "enum": ["recent", "highest_amount", "highest_odds", "manual"],
      "description": "展示模式"
    },
    "display_count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20,
      "description": "展示数量"
    },
    "min_win_amount": {
      "type": "number",
      "minimum": 0,
      "description": "最低中奖金额过滤，0 表示不过滤"
    },
    "time_range_days": {
      "type": "integer",
      "enum": [1, 7, 30],
      "description": "数据时效范围（天）"
    },
    "mask_user_info": {
      "type": "boolean",
      "description": "是否对用户信息进行脱敏"
    },
    "show_win_amount": {
      "type": "boolean",
      "description": "是否展示实际中奖金额"
    },
    "sport_filters": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "运动类型过滤列表，空数组表示展示全部"
    },
    "status": {
      "type": "string",
      "enum": ["active", "paused"],
      "description": "规则启用状态"
    }
  },
  "required": ["display_mode", "display_count", "min_win_amount", "time_range_days", "mask_user_info", "show_win_amount", "status"]
}
```

### 1.4 卡片排序管理 (Card Sort)

用于定义首页各推荐卡片模块的展示顺序。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CardSortConfig",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "module_id": {
        "type": "string",
        "description": "模块唯一标识，如 'hot_events', 'superodds_banner'"
      },
      "priority": {
        "type": "integer",
        "description": "展示优先级，数字越小越靠前"
      },
      "is_visible": {
        "type": "boolean",
        "description": "是否在前端展示"
      }
    },
    "required": ["module_id", "priority", "is_visible"]
  }
}
```

---

## 2. 活动系统

### 2.1 Superodds 活动配置 (Superodds)

用于定义超级赔率活动的参数。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SuperoddsConfig",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "活动唯一标识"
    },
    "name": {
      "type": "string",
      "description": "活动名称"
    },
    "boost_percentage": {
      "type": "number",
      "minimum": 0.1,
      "maximum": 100,
      "description": "赔率加成比例（%）"
    },
    "sport_type": {
      "type": "string",
      "description": "适用运动类型，'all' 表示全部"
    },
    "start_time": {
      "type": "string",
      "format": "date-time",
      "description": "活动开始时间"
    },
    "end_time": {
      "type": "string",
      "format": "date-time",
      "description": "活动结束时间"
    },
    "min_bet_amount": {
      "type": "number",
      "minimum": 0,
      "description": "最低投注金额"
    },
    "max_boost_amount": {
      "type": "number",
      "minimum": 0,
      "description": "最大加赔金额上限"
    },
    "target_event_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "适用赛事 ID 列表，空数组表示适用 sport_type 下的全部赛事"
    },
    "status": {
      "type": "string",
      "enum": ["active", "paused", "ended"],
      "description": "活动状态"
    }
  },
  "required": ["id", "name", "boost_percentage", "sport_type", "start_time", "end_time", "min_bet_amount", "max_boost_amount", "status"]
}
```

### 2.2 串关加赔活动配置 (Parlay Boost)

用于定义串关加赔活动的参数及阶梯比例。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ParlayBoostConfig",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "活动唯一标识"
    },
    "name": {
      "type": "string",
      "description": "活动名称"
    },
    "description": {
      "type": "string",
      "description": "活动描述（前端展示用）"
    },
    "start_time": {
      "type": "string",
      "format": "date-time",
      "description": "活动开始时间"
    },
    "end_time": {
      "type": "string",
      "format": "date-time",
      "description": "活动结束时间"
    },
    "boost_ratios": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "parlay_count": {
            "type": "integer",
            "description": "串关数量"
          },
          "ratio": {
            "type": "number",
            "description": "加赔比例（%）"
          }
        },
        "required": ["parlay_count", "ratio"]
      },
      "description": "串关数量与加赔比例的对应关系"
    },
    "max_boost_per_bet": {
      "type": "number",
      "description": "单笔最大加赔金额"
    },
    "max_boost_per_day": {
      "type": "number",
      "description": "每用户每日加赔上限"
    },
    "conditions": {
      "type": "object",
      "properties": {
        "min_bet_amount": { "type": "number" },
        "max_bet_amount": { "type": "number" },
        "min_parlay_count": { "type": "integer" },
        "max_parlay_count": { "type": "integer" },
        "user_level_req": { "type": "string" },
        "verification_req": { "type": "string" }
      },
      "description": "参与条件"
    },
    "scope": {
      "type": "object",
      "properties": {
        "sport_types": {
          "type": "array",
          "items": { "type": "string" }
        },
        "exclude_event_ids": {
          "type": "array",
          "items": { "type": "string" }
        },
        "market_types": {
          "type": "array",
          "items": { "type": "string" }
        }
      },
      "description": "适用范围"
    },
    "status": {
      "type": "string",
      "enum": ["active", "paused", "ended"],
      "description": "活动状态"
    }
  },
  "required": ["id", "name", "start_time", "end_time", "boost_ratios", "max_boost_per_bet", "conditions", "scope", "status"]
}
```

### 2.3 营销入口配置 (Marketing Entry)

用于控制各活动入口在前端的展示状态与跳转。

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MarketingEntryConfig",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "入口唯一标识"
    },
    "name": {
      "type": "string",
      "description": "入口名称"
    },
    "entry_type": {
      "type": "string",
      "enum": ["banner", "nav_icon", "popup", "sidebar"],
      "description": "入口类型"
    },
    "position": {
      "type": "string",
      "description": "展示位置标识"
    },
    "target_url": {
      "type": "string",
      "description": "点击后的跳转链接"
    },
    "priority": {
      "type": "integer",
      "description": "展示优先级，数字越小优先级越高"
    },
    "is_visible": {
      "type": "boolean",
      "description": "是否在前端展示"
    }
  },
  "required": ["id", "name", "entry_type", "position", "target_url", "priority", "is_visible"]
}
```

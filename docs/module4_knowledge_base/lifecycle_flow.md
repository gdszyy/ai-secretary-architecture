# KB 事实生命周期流程图

本图汇总主动聚合、纠正、查询三条主链路，覆盖 fact 从产生到归档的全过程。

## 1. 总览：Fact 生命周期状态机

```mermaid
stateDiagram-v2
    [*] --> Candidate: 信源扫描或 PM 输入
    Candidate --> Active: 对齐为 NEW
    Candidate --> ActiveExisting: 对齐为 MATCH（追加 source）
    Candidate --> Conflict: 对齐为 CONFLICT
    Conflict --> Active: PM 选择候选
    Conflict --> Active: 自动规则解决
    Active --> Superseded: 被纠正
    Superseded --> [*]: 6 个月未引用→归档
    ActiveExisting --> Superseded: 被纠正
    Active --> Archived: 6 个月未被引用
    Archived --> [*]
```

## 2. 主动聚合扫描全链路

```mermaid
flowchart TD
    classDef src fill:#fde0e0,stroke:#c33
    classDef proc fill:#e0eefd,stroke:#369
    classDef store fill:#e6fbe0,stroke:#3a3
    classDef decision fill:#fdf3d0,stroke:#a80
    classDef alarm fill:#fde6c8,stroke:#c80

    subgraph 触发
        T1[Cron 08:30 daily]:::proc
        T2[Cron hourly]:::proc
        T3[CLI 手动]:::proc
        T4[external hint]:::proc
    end

    subgraph 信源
        S1[Bitable 6 张表]:::src
        S2[Meegle Workitems]:::src
        S3[GitHub Issues/PR]:::src
        S4[PRD 文档 git diff]:::src
        S5[历史周报]:::src
    end

    SCAN[Scanner.scan since=...]:::proc
    EXTRACT[LLM Fact Extractor<br/>evidence_quote 必须存在]:::proc
    ALIGN{对齐器}:::decision

    NEW[创建新 fact<br/>confidence=0.7]:::store
    MATCH[追加 source_refs<br/>confidence += 0.1]:::store
    CONF[写入 kb_conflicts<br/>status=pending]:::store

    AUTORULE{自动规则<br/>能解决吗}:::decision
    ASK[飞书追问 PM<br/>每日 17:00]:::alarm
    PMRES[PM 回复 1/2/3]:::src

    RESOLVED[解决冲突<br/>confidence=1.0]:::store

    T1 & T2 & T3 & T4 --> SCAN
    S1 & S2 & S3 & S4 & S5 --> SCAN
    SCAN --> EXTRACT
    EXTRACT --> ALIGN
    ALIGN -->|NEW| NEW
    ALIGN -->|MATCH| MATCH
    ALIGN -->|CONFLICT| CONF
    CONF --> AUTORULE
    AUTORULE -->|是| RESOLVED
    AUTORULE -->|否| ASK
    ASK --> PMRES
    PMRES --> RESOLVED
```

## 3. 实时纠正全链路

```mermaid
sequenceDiagram
    participant PM
    participant Lark as 飞书群
    participant WH as main.py /lark/webhook
    participant ROUTER as kb_router
    participant NLP as NL Correction Parser
    participant CW as Correction Writer
    participant ST as Bitable kb_facts/sources
    participant AUDIT as Bitable kb_corrections

    PM->>Lark: @AI秘书 支付系统不是已修复，iOS还有问题
    Lark->>WH: 消息事件 (post webhook)
    WH->>ROUTER: route(event)
    ROUTER->>ROUTER: is_at_bot? ✓
    ROUTER->>ROUTER: is_kb_correction(text)? ✓
    ROUTER->>NLP: parse(text, recent_msgs, known_subjects)
    NLP->>NLP: LLM 抽取 {subject, predicate, new_object, conf}
    NLP-->>ROUTER: parsed (conf=0.86)

    Note over ROUTER,AUDIT: 先写审计（无论是否成功）
    ROUTER->>AUDIT: create correction (applied=False)

    alt confidence >= 0.8
        ROUTER->>CW: apply(parsed)
        CW->>ST: find_active_fact(subject, predicate)
        ST-->>CW: target_fact (id=kb-fact-XXX, object=已修复)
        CW->>ST: create new fact (object=新值, conf=0.95, corrected_by=PM)
        CW->>ST: update target_fact.superseded_by = new_fact_id
        CW->>ST: create source (type=human_correction, excerpt=原话)
        CW->>AUDIT: update correction (target_fact_id, created_fact_id, applied=True)
        ROUTER->>Lark: ✅ 已纠正 + 三段式信源回复
    else 0.6 <= confidence < 0.8
        ROUTER->>CW: apply(parsed) with low_confidence_warning
        Note right of CW: 同上路径，但 confidence 标 0.85
        ROUTER->>Lark: ✅ 已纠正，但解析置信 0.7，请确认
    else confidence < 0.6
        ROUTER->>AUDIT: update correction (applied=False, reason=ambiguous)
        ROUTER->>Lark: ❓ 反问澄清 A/B/C
    end
```

## 4. 查询全链路

```mermaid
flowchart TD
    classDef src fill:#fde0e0,stroke:#c33
    classDef proc fill:#e0eefd,stroke:#369
    classDef store fill:#e6fbe0,stroke:#3a3
    classDef decision fill:#fdf3d0,stroke:#a80

    Q[PM @机器人 提问]:::src
    DETECT{is_kb_query?}:::decision
    QE[KB Query Engine]:::proc

    EMB[Embed 问句]:::proc
    VEC_SEARCH[FAISS 向量搜索<br/>topK=20]:::proc
    KW_FILTER[关键词过滤<br/>subject 精确匹配优先]:::proc

    GATHER[聚合 facts<br/>带 source_refs]:::proc
    LLM_SUMMARIZE[LLM 总结<br/>禁止补充原文之外内容]:::proc
    RENDER[三段式渲染<br/>结论 + 信源 + 置信度]:::proc

    REPLY[飞书回复]:::src

    FALLBACK[fallback: KB 暂无相关事实]:::store

    Q --> DETECT
    DETECT -->|yes| QE
    DETECT -->|no| LEGACY[lark_qa_handler 旧路径]:::proc

    QE --> EMB --> VEC_SEARCH --> KW_FILTER --> GATHER
    GATHER -->|hits>0| LLM_SUMMARIZE --> RENDER --> REPLY
    GATHER -->|hits=0| FALLBACK --> RENDER
    LEGACY --> REPLY
```

## 5. 三种通道的输出对比

```mermaid
flowchart LR
    KBA[KBAnswer 对象]
    L[飞书消息<br/>带富文本卡片]
    W[周报片段<br/>Markdown]
    A[API JSON<br/>完整 schema]

    KBA --> L
    KBA --> W
    KBA --> A

    L -->|强制三段式 ✓<br/>excerpt ≤200 字| OUT_L[PM 看]
    W -->|结论嵌入正文<br/>信源附在段尾| OUT_W[周报读者]
    A -->|完整 facts_cited<br/>excerpt 不截断| OUT_A[第三方系统]
```

## 6. 表间关系（ER）

```mermaid
erDiagram
    KB_FACTS ||--o{ KB_FACTS : "superseded_by (self-ref)"
    KB_FACTS }o--|| KB_SOURCES : "source_refs []"
    KB_CORRECTIONS }o--|| KB_FACTS : "target_fact_id / created_fact_id"
    KB_CONFLICTS }o--|| KB_FACTS : "resolution_fact_id"
    KB_FACTS {
        string fact_id PK
        string subject
        string predicate
        text object
        float confidence
        json source_refs
        datetime valid_from
        string superseded_by FK
        string corrected_by
    }
    KB_SOURCES {
        string source_id PK
        string source_type
        json source_locator
        text source_excerpt
        string url
        datetime captured_at
        string hash
    }
    KB_CORRECTIONS {
        string correction_id PK
        string target_fact_id FK
        string created_fact_id FK
        string corrector_open_id
        text raw_message
        json parsed_intent
        bool applied
    }
    KB_CONFLICTS {
        string conflict_id PK
        string subject
        string predicate
        json candidate_facts
        string status
        string resolution_fact_id FK
    }
```

## 7. 关键时间节点

```
00:00 ─┬─ daily_progress_updater 跑（现有）
       │
08:30 ─┤  KB Aggregator daily run（新增）
       │   ├ 全量扫描 6 信源
       │   ├ 抽事实、对齐、写库
       │   └ 出冲突摘要
       │
每整点 ─┤  KB Aggregator hourly run（增量）
       │
17:00 ─┤  KB 冲突追问推送（pending 冲突 → PM）
       │
随时   ─┤  PM @机器人 查询 / 纠正
       │   └ 30 秒内生效
       │
周一06 ─┘  weekly_batch（现有）+ KB 周报集成
```

## 8. 与现有 module2 缓冲区的衔接

```mermaid
flowchart LR
    subgraph M2[Module 2: Buffer]
        BIN[Buffer Item pending]
        BAS[asking]
        BR[ready]
        BAR[archived 进 Bitable]
    end

    subgraph M4[Module 4: KB]
        ING[Aggregator 扫描 Bitable]
        FACT[(kb_facts)]
    end

    BIN --> BAS --> BR --> BAR
    BAR -.->|聚合扫描| ING
    ING --> FACT

    note1[note: KB 不直接对接 Buffer 内部状态<br/>而是通过 Buffer 落地的 Bitable 间接抓取<br/>避免双写复杂度]
```

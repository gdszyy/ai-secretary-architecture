# 信息生命周期流程图

```mermaid
flowchart TD
    %% 定义样式
    classDef source fill:#f9f,stroke:#333,stroke-width:2px;
    classDef process fill:#bbf,stroke:#333,stroke-width:2px;
    classDef decision fill:#ff9,stroke:#333,stroke-width:2px;
    classDef storage fill:#bfb,stroke:#333,stroke-width:2px;
    classDef action fill:#fbb,stroke:#333,stroke-width:2px;

    %% 1. 接收阶段
    subgraph 接收阶段 [1. 接收阶段]
        A1[Lark 群聊/机器人]:::source
        A2[飞书妙记/会议记录]:::source
        A3[Meegle Webhook]:::source
        A4[语音转文字/文件上传]:::source
        B[信息缓冲区入口 (API)]:::process
        A1 --> B
        A2 --> B
        A3 --> B
        A4 --> B
    end

    %% 2. 暂存与清洗阶段
    subgraph 暂存与清洗阶段 [2. 暂存与清洗阶段]
        C[创建信息条目 (Status: pending)]:::storage
        B --> C
        D[AI 意图识别与实体提取]:::process
        C --> D
        E[去重与关联识别]:::process
        D --> E
        F[计算完整度评分]:::process
        E --> F
    end

    %% 3. 补全询问阶段
    subgraph 补全询问阶段 [3. 补全询问阶段]
        G{评分 >= 80?}:::decision
        F --> G
        
        H[标记为 Status: asking]:::process
        G -- 否 --> H
        
        I{询问策略}:::decision
        H --> I
        
        J[即时询问 (高优/紧急)]:::action
        K[批量询问 (低优/日常)]:::action
        I -- 即时 --> J
        I -- 批量 --> K
        
        L[用户回复补充信息]:::source
        J --> L
        K --> L
        
        M[更新信息条目]:::process
        L --> M
        M --> D %% 重新清洗和评分
        
        N{超时未回复?}:::decision
        H -.-> N
        O[标记为 Status: discarded 或降级归档]:::storage
        N -- 是 --> O
    end

    %% 4. 归档与派发阶段
    subgraph 归档与派发阶段 [4. 归档与派发阶段]
        P[标记为 Status: ready]:::process
        G -- 是 --> P
        
        Q{意图与模块路由}:::decision
        P --> Q
        
        R2[Lark 多维表格 (结构化数据)]:::storage
        R3[Meegle (任务分配)]:::storage
        R4[Lark 通知 (备忘提醒)]:::action
        
        Q --> R2
        Q --> R3
        Q --> R4
        
        S[标记为 Status: archived]:::storage
        R2 --> S
        R3 --> S
        R4 --> S
    end
```

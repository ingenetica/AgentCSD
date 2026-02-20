# AgentCSD — Architecture Diagram

## System Overview

```mermaid
graph TB
    subgraph Frontend["Frontend (React + Vite)"]
        UI["UI Panels"]
        WS_Hook["useWebSocket Hook"]
        Stores["Zustand Stores"]
        UI <--> Stores
        Stores <--> WS_Hook
    end

    subgraph Backend["Backend (FastAPI + asyncio)"]
        WSHandler["WebSocket Handler"]
        Orch["Orchestrator"]

        subgraph Loops["Concurrent Async Loops"]
            SLoop["Subconscious Loop<br/>(runs continuously)"]
            SLoudProc["S_loud Processor<br/>(batches signals)"]
        end

        subgraph Layers["Processing Layers"]
            ID["InternalDialogLayer<br/>(C_model)"]
            SC["SubconsciousLayer<br/>(S_model)"]
        end

        subgraph LLMAdapters["LLM Adapters"]
            CLI["ClaudeCLI"]
            API["AnthropicAPI"]
            OAI["OpenAI Compat"]
        end

        subgraph Persistence["Persistence"]
            DB[(SQLite)]
            JSONL["JSONL Logs"]
        end

        WSHandler <--> Orch
        Orch --> SLoop
        Orch --> SLoudProc
        SLoop --> SC
        SLoudProc --> ID
        Orch -->|user message| ID
        SC --> CLI
        SC --> API
        SC --> OAI
        ID --> CLI
        ID --> API
        ID --> OAI
        Orch --> DB
        Orch --> JSONL
    end

    WS_Hook <-->|WebSocket| WSHandler
    CLI -->|subprocess| Claude["Claude Code CLI"]
    API -->|HTTPS| AnthropicCloud["Anthropic API"]
    OAI -->|HTTP| LocalLLM["Ollama / LMStudio"]

    style Frontend fill:#1a1a2e,stroke:#4a9eff,color:#fff
    style Backend fill:#1a1a2e,stroke:#ff6b6b,color:#fff
    style Loops fill:#2d2d44,stroke:#ffd93d,color:#fff
    style Layers fill:#2d2d44,stroke:#6bcb77,color:#fff
    style LLMAdapters fill:#2d2d44,stroke:#4d96ff,color:#fff
    style Persistence fill:#2d2d44,stroke:#ff922b,color:#fff
```

## Data Flow — Complete Cycle

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant O as Orchestrator
    participant ID as Internal Dialog<br/>(C_model)
    participant SC as Subconscious<br/>(S_model)
    participant LLM as LLM Backend
    participant DB as SQLite + JSONL

    Note over SC: Subconscious Loop runs continuously<br/>independent of user interaction

    rect rgb(40, 40, 60)
        Note over SC,LLM: Continuous Subconscious Cycle
        O->>O: Diff check: what changed<br/>since last cycle?
        O->>SC: New context only<br/>(ed_user, ed_agent, id_loud, id_quiet)
        SC->>LLM: Persona Core (system) + context (user)
        Note over LLM: S_model may use<br/>WebSearch / WebFetch
        LLM-->>SC: Raw response
        SC-->>O: S_loud, S_quiet, Mood, Criteria, Trigger
        O->>DB: Persist S_loud, S_quiet, M&C
        O->>FE: s_loud, s_quiet, m_and_c, s_input_context
        O->>O: Queue S_loud for batching
    end

    rect rgb(50, 40, 40)
        Note over U,ID: User Message Flow
        U->>FE: Types message
        FE->>O: user_message (WebSocket)
        O->>DB: Save ED_user
        O->>O: Drain pending S_loud queue
        O->>FE: id_input_context (debug)
        O->>ID: ED_user + S_loud batch +<br/>Mood/Criteria + ID_quiet history
        ID->>LLM: System prompt + user message
        loop Streaming
            LLM-->>ID: chunk
            ID-->>O: chunk
            O-->>FE: ed_agent_chunk
        end
        ID-->>O: Parse → ID_loud + ID_quiet
        O->>FE: ed_agent_done (clean response)
        O->>FE: id_loud, id_quiet
        O->>DB: Persist ID_loud, ID_quiet, ED_agent
        FE->>U: Display response
    end

    rect rgb(40, 50, 40)
        Note over O,ID: S_loud Triggered Response (Autonomous)
        Note over O: S_loud batch ready<br/>(5s delay or trigger=true)
        O->>FE: id_input_context (debug)
        O->>ID: S_loud batch + Mood/Criteria +<br/>ID_quiet history (no ED_user)
        ID->>LLM: Process signals
        LLM-->>ID: Response
        ID-->>O: Parse → ID_loud + ID_quiet
        alt ID_loud has content
            O->>FE: ed_agent_done (autonomous message)
            FE->>U: Display autonomous response
        end
        O->>DB: Persist
        O->>FE: id_loud, id_quiet
    end
```

## Subconscious Loop — Internal Detail

```mermaid
flowchart TD
    Start([Loop Start]) --> Paused{Paused?}
    Paused -->|Yes| Sleep1[Sleep 500ms] --> Paused
    Paused -->|No| Incr[Increment cycle counter]
    Incr --> Diff[Diff against _s_seen_*<br/>Only pass changed values]
    Diff --> SendCtx[Send s_input_context<br/>to frontend]
    SendCtx --> CallS[Call S_model with<br/>Persona Core + new context]
    CallS --> Parse[Parse response:<br/>S_loud, S_quiet, M&C, trigger]
    Parse --> Update[Update shared state<br/>under async lock]
    Update --> HasSLoud{S_loud<br/>non-empty?}

    HasSLoud -->|No| HasSQuiet
    HasSLoud -->|Yes| Queue[Queue S_loud entry]
    Queue --> CheckTrigger{Trigger=true<br/>or batch full?}
    CheckTrigger -->|Yes| ForceDrain[Force immediate drain<br/>→ Internal Dialog]
    CheckTrigger -->|No| WaitBatch[Wait for batch delay<br/>5 seconds]
    ForceDrain --> HasSQuiet
    WaitBatch --> HasSQuiet

    HasSQuiet{S_quiet?} -->|Yes| SaveQuiet[Append to history]
    HasSQuiet -->|No| SaveMC
    SaveQuiet --> SaveMC

    SaveMC[Persist to DB + JSONL<br/>Send to frontend] --> CheckSumm{Cycle %<br/>N == 0?}
    CheckSumm -->|Yes| Summarize[LLM-summarize old entries<br/>Truncate histories]
    CheckSumm -->|No| Paused
    Summarize --> Paused

    style Start fill:#4a9eff,color:#fff
    style CallS fill:#6bcb77,color:#000
    style ForceDrain fill:#ff6b6b,color:#fff
    style Summarize fill:#ffd93d,color:#000
```

## S_loud Batching & Processing

```mermaid
flowchart LR
    subgraph SubLoop["Subconscious Loop"]
        S1["Cycle N<br/>S_loud: 'data found'"]
        S2["Cycle N+1<br/>S_loud: 'risk detected'"]
        S3["Cycle N+2<br/>S_loud: '' (empty)"]
        S4["Cycle N+3<br/>S_loud: 'thesis updated'"]
    end

    subgraph Queue["S_loud Queue"]
        Q["Pending entries<br/>max: 5"]
    end

    subgraph Drain["Drain Triggers"]
        T1["5 second timeout"]
        T2["trigger=true"]
        T3["Queue reaches 5"]
    end

    subgraph Process["Internal Dialog"]
        ID["C_model receives<br/>batched S_loud entries +<br/>Mood/Criteria +<br/>ID_quiet history"]
    end

    S1 -->|enqueue| Q
    S2 -->|enqueue| Q
    S4 -->|enqueue| Q
    Q --> T1
    Q --> T2
    Q --> T3
    T1 --> ID
    T2 --> ID
    T3 --> ID

    style Queue fill:#ffd93d,color:#000
    style Process fill:#6bcb77,color:#000
```

## Shared State & Concurrency

```mermaid
flowchart TD
    subgraph Writers["Writers"]
        SLoop["Subconscious Loop<br/>(writes M&C, S_loud)"]
        UMsg["User Message Handler<br/>(writes ED_user, ID results)"]
    end

    subgraph SharedState["Shared State (protected by _lock)"]
        MC["current_mood<br/>current_criteria"]
        SL["current_s_loud"]
    end

    subgraph Readers["Readers"]
        IDCall["Internal Dialog invocation<br/>(reads M&C for modulation)"]
    end

    subgraph ProcLock["_processing_lock"]
        P["Ensures only ONE Internal Dialog<br/>call at a time:<br/>user message OR S_loud trigger"]
    end

    SLoop -->|async write| SharedState
    UMsg -->|async write| SharedState
    SharedState -->|async read| IDCall
    UMsg --> ProcLock
    IDCall --> ProcLock

    style SharedState fill:#ff922b,color:#000
    style ProcLock fill:#ff6b6b,color:#fff
```

## Persona Core → Model Prompts

```mermaid
flowchart TD
    subgraph Persona["Persona Core (personas/*.md)"]
        P["Identity + Drives + Fears<br/>+ Input/Output format<br/>+ Guiding question"]
    end

    subgraph SModel["S_model (Subconscious)"]
        SS["system_prompt = Persona Core<br/>(entire file, nothing added)"]
        SU["user_message = context tags<br/>(ED_user, ED_agent, ID_loud,<br/>ID_quiet, histories)"]
    end

    subgraph CModel["C_model (Internal Dialog)"]
        CS["system_prompt = INTERNAL_DIALOG_SYSTEM_PROMPT<br/>+ dynamic Mood/Criteria injection"]
        CU["user_message = context tags<br/>(ED_user, S_loud_stream,<br/>ID_quiet_history)"]
    end

    Persona -->|becomes entire<br/>system prompt| SS
    Persona -.->|philosophy influences<br/>but not injected| CS

    SU -->|S_loud output| CU
    SS -->|M&C output| CS

    style Persona fill:#4a9eff,color:#fff
    style SModel fill:#6bcb77,color:#000
    style CModel fill:#ff922b,color:#000
```

## Frontend Panel Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Sidebar  │          Main Content Area                       │
│           │                                                  │
│  Sessions ├──────────────────────┬───────────────────────────┤
│  List     │                      │                           │
│           │   External Dialog    │                           │
│  + New    │   (Chat)             │    Subconscious Panel     │
│           │                      │                           │
│  Config   │                      │    S_loud (signals)       │
│           │                      │    S_quiet (internal)     │
│  Persona  ├──── drag handle ─────┤    Mood & Criteria        │
│  Editor   │                      │                           │
│           │   Internal Dialog    │    [INPUT] blocks per     │
│           │                      │    cycle (collapsible)    │
│           │   ID_loud (said)     │                           │
│           │   ID_quiet (thought) │                           │
│           │                      │                           │
│           │   [INPUT] blocks     │                           │
│           │   (collapsible)      │                           │
│           │                      │◄── drag handle ──►        │
└───────────┴──────────────────────┴───────────────────────────┘
                All panel sizes adjustable via drag handles
```

## Diff-Based Context (Stale Data Prevention)

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant SC as Subconscious

    Note over O: User says "Hello"<br/>last_ed_user = "Hello"<br/>_s_seen_ed_user = ""

    O->>SC: Cycle 1: ed_user="Hello" ✓
    Note over O: _s_seen_ed_user = "Hello"

    O->>SC: Cycle 2: ed_user="" (unchanged, not sent)
    O->>SC: Cycle 3: ed_user="" (still unchanged)

    Note over O: User says "What about BTC?"<br/>last_ed_user = "What about BTC?"

    O->>SC: Cycle 4: ed_user="What about BTC?" ✓
    Note over O: _s_seen_ed_user = "What about BTC?"

    O->>SC: Cycle 5: ed_user="" (unchanged)
```

## Safe Parsing Fallback

```mermaid
flowchart TD
    Raw["Raw C_model output"] --> TryXML{XML tags<br/>found?}
    TryXML -->|Yes| Extract["Extract ID_loud + ID_quiet"]
    TryXML -->|No| TryMD{Markdown headers<br/>found?}
    TryMD -->|Yes| ExtractMD["Extract via markdown fallback"]
    TryMD -->|No| Safe["SAFE FALLBACK:<br/>entire output → ID_quiet<br/>ID_loud = '' (empty)"]

    Extract --> CheckNO{ID_loud ==<br/>'[NO_EXTERNAL_OUTPUT]'?}
    ExtractMD --> CheckNO
    CheckNO -->|Yes| Internal["internal_only = true<br/>Nothing sent to user"]
    CheckNO -->|No| External["ID_loud → user<br/>ID_quiet → private"]
    Safe --> Internal

    style Safe fill:#6bcb77,color:#000
    style Internal fill:#4a9eff,color:#fff
    style External fill:#ff922b,color:#000
```

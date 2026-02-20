# AgentCSD — Conscious Subconscious Dynamic

## Architecture Specification v1.0

---

## 1. Overview

AgentCSD is a conversational agent architecture that simulates cognitive processing levels through three concurrent layers. The central premise is that an agent should not only respond to user input, but must have a continuous internal process — a "subconscious" — that modulates how it thinks and responds, generating its own will.

The system operates like a mind: it thinks many things but only externalizes some. The subconscious runs permanently, generating internal states that dynamically modify the behavior of the internal dialog, which in turn decides what to communicate to the user.

---

## 2. Three-Layer Architecture

### 2.1 External Dialog (Green Layer — No LLM)

**Function:** User interface. Contains no LLM logic. Routes messages between the user and the Internal Dialog.

**Input:**
- User message → tagged as `<ED_user>`

**Output:**
- Response to user → tagged as `<ED_agent>` (sourced from `<ID_loud>` of the Internal Dialog)

**Behavior:**
- Is the application's GUI
- Displays user chat (External Dialog)
- Displays observation panels for Internal Dialog and Subconscious
- Allows editing the Persona Core
- Allows managing sessions, configuring models/backends, pausing/resuming

---

### 2.2 Internal Dialog (Orange Layer — C_model)

**Function:** Conscious thinker. Processes user input modulated by the subconscious state. Decides what to externalize and what to keep internal.

**Model:** Sophisticated LLM (e.g., Claude Sonnet, or powerful model via API/local)

**Activation triggers:**
1. User input (via External Dialog)
2. S_loud with substantive content from the Subconscious (spontaneous thought without user input)

**System Prompt — Static Part:**
Permanent instructions that explain to the C_model:
- Its role as Internal Dialog of AgentCSD
- What each tag means and how to interpret received messages
- That it must produce two types of output: `<ID_loud>` (externalized to the user) and `<ID_quiet>` (kept internal)
- That `<ID_quiet>` is its space to reason, reflect, and accumulate thought without exposing it to the user
- Base behavioral rules

**System Prompt — Dynamic Part (M&C):**
Injected by the Subconscious. Contains:
- Mood: emotional/tonal state to adopt
- Criteria: specific criteria for this moment on how to respond, what to prioritize, what to avoid

**Input (user message to the C_model):**
```xml
<ED_user>What the user said</ED_user>
<S_loud>What the subconscious wants to communicate to the Internal Dialog</S_loud>
<ID_quiet_history>Previous accumulated internal thoughts from the Internal Dialog</ID_quiet_history>
```

**Expected C_model output:**
```xml
<ID_loud>What is sent to the user as a response</ID_loud>
<ID_quiet>Internal thoughts, reasoning, reflections that are not externalized</ID_quiet>
```

**Persistence:**
- The complete history (ID_loud + ID_quiet) is persisted to disk
- ID_quiet accumulates as context for future Internal Dialog turns
- ID_loud is passed to the External Dialog to be shown to the user

---

### 2.3 Subconscious (Blue Layer — S_model)

**Function:** Continuous internal process. Evaluates all available context, generates internal states, and modulates Internal Dialog behavior via M&C. Operates as a perpetual asynchronous loop.

**Model:** Cheap/fast LLM (e.g., Claude Haiku, lightweight local model)

**Execution cycle:**
- Continuous loop: upon finishing a cycle, starts another immediately
- Pauses when the user pauses the application or closes the program
- Resumes when reopened/unpaused

**System Prompt (Persona Core):**
- Immutable `.md` file (cannot be modified by the program)
- Only manually editable from the GUI
- Cannot be replaced, overwritten, or modified by the S_model or any automated process
- Defines personality, values, relevance criteria, and rules for what to externalize as S_loud vs keep as S_quiet
- Defines criteria for generating M&C (Mood and Criteria)
- Defines when a thought is sufficiently relevant to trigger the Internal Dialog without user input

**Input (user message to the S_model):**
```xml
<ED_user>Latest user message (if any)</ED_user>
<ED_agent>Latest response to user (if any)</ED_agent>
<ID_quiet>Recent internal thoughts from the Internal Dialog</ID_quiet>
<ID_loud>Recent responses from the Internal Dialog</ID_loud>
<S_quiet_history>Previous internal thoughts from the Subconscious</S_quiet_history>
<S_loud_history>Previous communications from the Subconscious to the Internal Dialog</S_loud_history>
```

**Expected S_model output:**
```xml
<S_loud>What the subconscious wants to communicate to the Internal Dialog. If nothing relevant, can be empty or absent.</S_loud>
<S_quiet>Internal thoughts of the subconscious not communicated to the Internal Dialog</S_quiet>
<M_AND_C>
  <mood>Suggested tonal/emotional state for the Internal Dialog</mood>
  <criteria>Specific criteria: what to prioritize, what to avoid, how to modulate the response</criteria>
</M_AND_C>
```

**Spontaneous trigger mechanism:**
- If the S_model generates S_loud with substantive content, the orchestrator detects it and activates the Internal Dialog even without user input
- The criteria for what constitutes "substantive content" are defined in the Persona Core
- The orchestrator evaluates whether S_loud has content (non-empty, non-trivial) to decide whether to trigger

**Context window management:**
- Oldest messages are truncated when approaching the window limit
- Every N cycles (configurable), before truncating, the S_model generates a compact summary of what will be discarded
- The summary is persisted as a special message at the beginning of the history
- N is configurable from the GUI

---

## 3. Data Flow

### 3.1 Normal Flow (User sends message)

```
1. User writes message
2. External Dialog tags as <ED_user> and sends to the Orchestrator
3. Orchestrator collects current state:
   - <ED_user> (user message)
   - Latest <S_loud> from the Subconscious
   - Latest <M_AND_C> from the Subconscious
   - <ID_quiet> history from the Internal Dialog
4. Orchestrator builds the Internal Dialog prompt:
   - System prompt = static + dynamic M&C
   - User message = ED_user + S_loud + ID_quiet_history
5. C_model processes and generates <ID_loud> + <ID_quiet>
6. Orchestrator:
   - Sends <ID_loud> to External Dialog → displayed to user as <ED_agent>
   - Persists <ID_quiet> in the Internal Dialog history
   - Feeds <ED_agent>, <ID_loud>, and <ID_quiet> to the next Subconscious cycle
7. Subconscious (running in parallel) incorporates new information in its next cycle
```

### 3.2 Spontaneous Flow (No user input)

```
1. Subconscious completes a cycle and generates S_loud with substantive content
2. Orchestrator detects non-empty S_loud
3. Orchestrator activates Internal Dialog with:
   - System prompt = static + M&C
   - User message = S_loud + ID_quiet_history (no ED_user)
4. C_model processes and generates <ID_loud> + <ID_quiet>
5. Orchestrator sends <ID_loud> to External Dialog as a spontaneous agent message
6. Everything is persisted normally
```

### 3.3 Subconscious Loop

```
Continuous loop:
1. Collect available inputs (ED_user, ED_agent, ID_loud, ID_quiet, S_quiet_history, S_loud_history)
2. Build prompt with Persona Core as system prompt
3. S_model processes and generates S_loud + S_quiet + M&C
4. Orchestrator:
   - Stores S_loud and M&C in shared state (available for Internal Dialog)
   - Persists S_quiet in Subconscious history
   - If S_loud has substantive content → evaluates spontaneous trigger
5. Return to 1 immediately
```

---

## 4. Tags — Complete Reference

| Tag | Origin | Destination | Description |
|-----|--------|-------------|-------------|
| `<ED_user>` | User (via External Dialog) | Internal Dialog, Subconscious | User message |
| `<ED_agent>` | External Dialog | Subconscious | Response shown to user |
| `<ID_loud>` | Internal Dialog (C_model) | External Dialog, Subconscious | Thought externalized to user |
| `<ID_quiet>` | Internal Dialog (C_model) | Internal Dialog (own history), Subconscious | Internal thought not externalized |
| `<S_loud>` | Subconscious (S_model) | Internal Dialog | What the subconscious communicates to the conscious thinker |
| `<S_quiet>` | Subconscious (S_model) | Subconscious (own history) | Internal thought of the subconscious |
| `<M_AND_C>` | Subconscious (S_model) | Internal Dialog (dynamic system prompt) | Mood and Criteria — modulates C_model behavior |
| `<Persona_Core>` | Immutable .md file | Subconscious (fixed system prompt) | Personality, values, criteria of the subconscious |

---

## 5. Persistence and Sessions

### 5.1 Session Model

- Each session has a unique ID (UUID) and creation timestamp
- Multiple sessions can coexist (like saved games)
- A new session can be created without losing previous ones
- Any previous session can be resumed (loads history and complete state)
- On resume, the Subconscious resumes its loop with the previous history loaded

### 5.2 Storage

**Database:** SQLite

Main tables:
- `sessions`: ID, name, creation timestamp, last activity timestamp, persona_core used, model config, state (active/paused/closed)
- `messages`: ID, session_id, layer (external/internal/subconscious), tag, content, timestamp, cycle_number
- `mood_and_criteria`: ID, session_id, mood, criteria, timestamp, cycle_number
- `context_summaries`: ID, session_id, layer, summary, timestamp, cycle covered (from-to)

### 5.3 Per-Session Logs

Folder: `logs/{session_id}/`

Files:
- `external_dialog.jsonl` — All ED_user and ED_agent
- `internal_dialog.jsonl` — All ID_loud and ID_quiet
- `subconscious.jsonl` — All S_loud and S_quiet
- `mood_and_criteria.jsonl` — All generated M&C
- `persona_core_snapshot.md` — Copy of the Persona Core at session start

JSONL format: each line is a JSON with `timestamp`, `tag`, `content`, `cycle_number`.

---

## 6. Model Configuration (LLM Backend)

### 6.1 Abstraction

The system uses a unified interface for invoking LLMs. Each layer (C_model, S_model) can be configured independently.

### 6.2 Supported Backends

| Backend | Use | Configuration |
|---------|-----|---------------|
| Claude Code CLI | Default. Uses Max subscription | Path to Claude Code binary |
| Anthropic API | Alternative cloud | API key + model |
| OpenAI-compatible API | Local models (LMStudio, Ollama, etc.) | Endpoint URL + model |

### 6.3 Per-Layer Configuration

```json
{
  "c_model": {
    "backend": "claude_code_cli",
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096
  },
  "s_model": {
    "backend": "openai_compatible",
    "endpoint": "http://localhost:1234/v1",
    "model": "local-model-name",
    "max_tokens": 2048
  }
}
```

---

## 7. Persona Core

### 7.1 Definition

A markdown (`.md`) file that defines the subconscious identity. It is the equivalent of fundamental personality, values, and operating criteria.

### 7.2 Expected Content

The Persona Core should include (defined by the user):
- Agent identity and personality
- Values and principles
- Relevance criteria: what constitutes important information to communicate to the Internal Dialog
- S_loud vs S_quiet criteria: what to externalize and what to keep internal
- M&C criteria: how to determine mood and criteria for the Internal Dialog
- Spontaneous trigger criteria: when a thought justifies activating the Internal Dialog without user input
- Any other directive that defines the deep behavior of the agent

### 7.3 Immutability

- The file is loaded as the S_model system prompt
- Only manually editable from the GUI by the user
- No program process can modify, replace, or overwrite the file
- When a session starts, a snapshot copy is generated in the logs folder

### 7.4 Multiple Persona Cores

- The user can have multiple Persona Core files
- When creating/resuming a session, they select which one to use
- Each session records which Persona Core was used

---

## 8. Graphical Interface (GUI)

### 8.1 Stack

- **Frontend:** React (served locally)
- **Backend:** Python + FastAPI
- **Communication:** WebSocket for real-time streaming
- **Cross-platform:** Mac and Ubuntu without changes

### 8.2 Panels

1. **External Dialog (Chat):** Classic chat interface. Shows user messages and agent responses. Text input for the user.

2. **Internal Dialog (Observation Panel):** Shows in real-time the ID_loud (marked as externalized) and ID_quiet (marked as internal). Allows viewing the complete reasoning of the agent.

3. **Subconscious (Observation Panel):** Shows in real-time the S_loud, S_quiet, and M&C from each cycle. Allows viewing the subconscious thought stream.

### 8.3 Controls

- **Sessions:** Create new, resume existing, list all
- **Pause/Resume:** Button to pause/resume the subconscious loop
- **Persona Core:** File selector + integrated text editor (manual editing)
- **Model configuration:** Backend and model selector for C_model and S_model
- **Parameters:** N (subconscious summary frequency), max_tokens per layer

---

## 9. Technical Stack

| Component | Technology |
|-----------|------------|
| Orchestrator / Backend | Python 3.11+ with FastAPI |
| Concurrency | asyncio (subconscious loop as async task) |
| Persistence | SQLite + JSONL files |
| Frontend | React (served by FastAPI as static files) |
| Frontend-Backend Communication | WebSocket (real-time streaming) |
| LLM Interface | Abstraction layer with adapters for Claude Code CLI, Anthropic API, OpenAI-compatible API |
| Cross-platform | Mac (development) → Ubuntu (production) |

---

## 10. System Behavior

### 10.1 New Session Start

1. User selects Persona Core
2. User configures models (or uses defaults)
3. Session record is created in SQLite
4. Persona Core snapshot is copied to the logs folder
5. Subconscious loop is started
6. System is ready to receive user input

### 10.2 Resume Session

1. User selects existing session from the list
2. Complete history is loaded (Internal Dialog + Subconscious + External Dialog)
3. The Persona Core associated with that session is loaded
4. Subconscious loop is resumed with the loaded history
5. System continues as if it had never been paused

### 10.3 Pause

1. Subconscious loop stops after completing the current cycle
2. All state is persisted
3. User can still view panels but there is no new activity

### 10.4 Close Program

1. Pauses automatically (same as 10.3)
2. GUI and backend are closed
3. On reopen, user can resume the session or create a new one

---

## 11. Technical Considerations

### 11.1 Substantive S_loud Detection

The orchestrator needs to determine if S_loud has sufficient content to trigger the Internal Dialog. Options:
- **Simple:** S_loud non-empty and with more than N characters (configurable)
- **Tag-based:** The S_model includes an explicit tag `<trigger>true/false</trigger>` as part of its output, evaluated according to Persona Core criteria

Recommendation: use the explicit tag, since the relevance criteria are already defined in the Persona Core and the S_model is best positioned to evaluate them.

### 11.2 Concurrency and Shared State

- The Subconscious and Internal Dialog run as independent asyncio tasks
- Shared state (current S_loud, current M&C) is managed with asyncio locks to avoid race conditions
- The Subconscious writes; the Internal Dialog reads. There is no concurrent writing to the same resource.

### 11.3 Rate Limits with Claude Code CLI + Max

- The Subconscious loop self-throttles naturally: each cycle takes as long as the LLM call takes
- With more accumulated context, cycles are slower (more input tokens)
- If rate limiting is detected, the orchestrator implements exponential backoff

### 11.4 Context Window

- Each layer manages its own window independently
- The Subconscious cumulative summary prevents total context loss when truncating
- The N parameter (summary frequency) is configurable to balance cost vs context retention

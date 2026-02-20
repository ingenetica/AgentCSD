# AgentCSD — Conscious Subconscious Dynamic

A cognitive architecture where two LLM processes run concurrently — one thinks continuously in the background (Subconscious), the other converses with the user modulated by that background state (Internal Dialog). The result is an agent with persistent internal state, emotional modulation, and autonomous behavior.

## How It Works

```
                    ┌─────────────────────────┐
                    │     User (Frontend)     │
                    └────────┬───────▲────────┘
                             │       │
                        ED_user   ED_agent
                             │       │
                    ┌────────▼───────┴────────┐
                    │    Internal Dialog      │
                    │       (C_model)         │
                    │                         │
                    │  Receives:              │
                    │  • User message         │
                    │  • Subconscious signals │
                    │  • Mood & Criteria      │
                    │  • Own past thoughts    │
                    │                         │
                    │  Produces:              │
                    │  • ID_loud → to user    │
                    │  • ID_quiet → private   │
                    └────────▲────────────────┘
                             │
                    S_loud + Mood/Criteria
                             │
                    ┌────────┴────────────────┐
                    │     Subconscious        │
                    │       (S_model)         │
                    │                         │
                    │  Runs continuously.     │
                    │  Reads everything.      │
                    │  Searches the web.      │
                    │                         │
                    │  Produces:              │
                    │  • S_loud → signals up  │
                    │  • S_quiet → private    │
                    │  • Mood & Criteria      │
                    │  • Trigger flag         │
                    └─────────────────────────┘
```

**Three layers, two LLMs, one continuous process:**

- **External Dialog** — The user-facing chat. No LLM — just routes messages between user and Internal Dialog.
- **Internal Dialog (C_model)** — Conscious thinker. Receives user input + subconscious signals. Decides what to say (`ID_loud`) and what to keep private (`ID_quiet`).
- **Subconscious (S_model)** — Runs in a continuous loop. Observes all context, searches the web, generates emotional state (Mood & Criteria), and sends signals to Internal Dialog. Can trigger autonomous responses when something important surfaces.

Neither model knows the other exists. Each experiences a continuous flow of information — no cycle numbers, no architecture references, no instructions about "layers."

## Key Design Decisions

- **Motivational, not instructional.** Persona files define drives (what the agent seeks and fears), not rules. This generates reasoning through tension rather than compliance.
- **Safe by default.** If Internal Dialog output can't be parsed into XML tags, everything is treated as private thought (`ID_quiet`). Nothing leaks to the user accidentally.
- **Diff-based context.** The Subconscious only receives data that changed since its last cycle. No stale repetition.
- **S_loud batching.** Subconscious signals queue for 5 seconds (or max 5 entries) before being delivered to Internal Dialog, preventing spam.
- **Immutable personas.** Once a session starts with a persona, it's locked. The persona file is snapshotted into session logs.

## Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11 + FastAPI + asyncio |
| Frontend | React + Vite + TypeScript + Tailwind + Zustand |
| Communication | WebSocket (real-time streaming) |
| Persistence | SQLite + JSONL logs per session |
| LLM | Pluggable adapters (Claude Code CLI, Anthropic API, OpenAI-compatible) |

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Server starts at `http://localhost:8000`. The frontend is served from `frontend/dist/`.

### Frontend (Development)

```bash
cd frontend
npm install
npm run dev
```

Dev server at `http://localhost:5173` with API proxy to backend.

### Frontend (Production)

```bash
cd frontend
npm run build
```

Built files served automatically by FastAPI at `http://localhost:8000`.

## LLM Backends

Each layer (C_model and S_model) can use a different backend:

| Backend | Description | Requirements |
|---------|-------------|--------------|
| `claude_code_cli` | Claude Code CLI (default) | `claude` binary in PATH |
| `anthropic_api` | Anthropic API directly | API key |
| `openai_compatible` | Ollama, LMStudio, vLLM, etc. | Local server running |

Default configuration (in `backend/config.py`):

```python
{
    "c_model": {
        "backend": "claude_code_cli",
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
    },
    "s_model": {
        "backend": "claude_code_cli",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "tools": ["WebSearch", "WebFetch"],
        "max_turns": 3,
    },
}
```

Only the Claude Code CLI backend supports tool use (WebSearch, WebFetch).

## Persona Core

Persona files in `personas/` define the Subconscious's identity. They become the **entire system prompt** for the S_model — no additional instructions are injected.

A persona defines:
- **Identity** — What the agent is (not what it should do)
- **Drives** — What it seeks and what it fears
- **Input/Output format** — XML tags for structured communication

Two personas are included:
- `default.md` — Reflective thinker focused on genuine benefit to the user
- `trading-analyst.md` — Market analyst with recursive analysis protocol and web search

Create new personas as `.md` files in `personas/` or via the GUI editor.

## UI Layout

Three resizable panels:
- **Left top:** External Dialog (chat)
- **Left bottom:** Internal Dialog (ID_loud and ID_quiet with input context)
- **Right:** Subconscious (S_loud, S_quiet, Mood & Criteria with input context)

Each panel shows collapsible "INPUT" blocks revealing exactly what went into each model invocation.

## API

### REST

```
GET    /api/sessions                     List sessions
GET    /api/sessions/{id}                Session details + messages
GET    /api/sessions/{id}/export         Download all logs as ZIP
DELETE /api/sessions/{id}                Delete session
GET    /api/personas                     List personas
GET    /api/personas/{filename}          Read persona content
POST   /api/personas                     Create persona
PUT    /api/personas/{filename}          Update persona
```

### WebSocket (`/ws`)

**Client sends:**
- `create_session` — Start new session with persona + model config
- `resume_session` — Reconnect to existing session
- `user_message` — Send message to External Dialog
- `pause_session` / `resume_loop` — Control Subconscious loop

**Server sends:**
- `ed_agent_chunk` / `ed_agent_done` — Streaming response to user
- `id_loud` / `id_quiet` — Internal Dialog output
- `s_loud` / `s_quiet` — Subconscious output
- `m_and_c` — Mood & Criteria update
- `id_input_context` / `s_input_context` — Debug: full model input
- `status` — Cycle count and running state

## Data

Runtime data lives in `data/` (gitignored):

```
data/
├── agentcsd.db                    # SQLite database
└── logs/
    └── {session_id}/
        ├── external_dialog.jsonl
        ├── internal_dialog.jsonl
        ├── subconscious.jsonl
        ├── mood_and_criteria.jsonl
        └── persona_core_snapshot.md
```

## Project Structure

```
AgentCSD/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Constants, default prompts
│   ├── orchestrator.py            # Core loop logic
│   ├── models.py                  # Pydantic models
│   ├── database/                  # SQLite schema + repository
│   ├── layers/
│   │   ├── internal_dialog.py     # C_model processing
│   │   └── subconscious.py        # S_model processing
│   ├── llm/
│   │   ├── base.py                # Abstract LLMAdapter
│   │   ├── claude_cli.py          # Claude Code CLI adapter
│   │   ├── anthropic_api.py       # Anthropic API adapter
│   │   └── openai_compat.py       # OpenAI-compatible adapter
│   ├── routes/
│   │   ├── ws.py                  # WebSocket handler
│   │   ├── sessions.py            # Session REST endpoints
│   │   ├── persona.py             # Persona endpoints
│   │   └── config_routes.py       # Config endpoints
│   └── utils/
│       ├── xml_parser.py          # XML/markdown tag extraction
│       └── jsonl.py               # JSONL file handling
├── frontend/
│   └── src/
│       ├── components/            # Layout, ChatPanel, InternalPanel, SubconsciousPanel
│       ├── stores/                # Zustand stores (chat, internal, subconscious, session)
│       ├── hooks/useWebSocket.ts  # WebSocket connection
│       └── lib/                   # API client, types
├── personas/
│   ├── default.md                 # Default reflective persona
│   └── trading-analyst.md         # Market analysis persona
└── data/                          # Runtime data (gitignored)
```

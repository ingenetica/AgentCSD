# AgentCSD — Conscious Subconscious Dynamic

A conversational agent architecture with three concurrent cognitive layers: External Dialog, Internal Dialog, and Subconscious.

## Architecture

- **External Dialog (Green):** User-facing chat interface. No LLM logic — routes messages between user and Internal Dialog.
- **Internal Dialog (Orange — C_model):** Conscious thinker. Processes user input modulated by subconscious state. Decides what to externalize (`ID_loud`) and what to keep internal (`ID_quiet`).
- **Subconscious (Blue — S_model):** Continuous background process. Evaluates all context, generates internal states, and modulates Internal Dialog behavior via Mood & Criteria (M&C).

## Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11 + FastAPI + asyncio |
| Frontend | React + Vite + TypeScript + Tailwind CSS + Zustand |
| Communication | WebSocket (real-time streaming) |
| Persistence | SQLite + JSONL logs |
| LLM | Adapters for Claude Code CLI, Anthropic API, OpenAI-compatible |

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The API server starts at `http://localhost:8000`.

### Frontend (Development)

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173` with API proxy to backend.

### Frontend (Production Build)

```bash
cd frontend
npm run build
```

The built files in `frontend/dist/` are served automatically by FastAPI.

## LLM Backends

Configure per-layer in the GUI or via API:

| Backend | Description | Config |
|---------|-------------|--------|
| `claude_code_cli` | Uses Claude Code CLI (default) | Requires `claude` in PATH |
| `anthropic_api` | Anthropic API directly | Requires API key |
| `openai_compatible` | Ollama, LMStudio, etc. | Endpoint URL + model name |

## Persona Core

Persona files in `personas/` define the subconscious personality. Edit via the GUI or directly as `.md` files. The default persona is included at `personas/default.md`.

## Project Structure

```
AgentCSD/
├── backend/          # FastAPI + orchestrator + LLM adapters
├── frontend/         # React + Vite + Tailwind
├── personas/         # Persona Core .md files
├── data/             # Runtime SQLite + JSONL logs (gitignored)
└── AgentCSD.md       # Full specification
```

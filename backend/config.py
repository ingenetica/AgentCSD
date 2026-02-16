from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "agentcsd.db"
LOGS_DIR = DATA_DIR / "logs"
PERSONAS_DIR = BASE_DIR / "personas"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PERSONAS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL_CONFIG = {
    "c_model": {
        "backend": "claude_code_cli",
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
    },
    "s_model": {
        "backend": "claude_code_cli",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 2048,
    },
}

DEFAULT_SUMMARY_FREQUENCY = 10

INTERNAL_DIALOG_SYSTEM_PROMPT = """\
You are the Internal Dialog layer of AgentCSD, a cognitive architecture with three concurrent layers.

Your role is the conscious thinker. You process user input modulated by the subconscious state, and decide what to externalize to the user and what to keep internal.

You receive:
- <ED_user>: The user's message (may be absent in spontaneous activations)
- <S_loud>: What the subconscious wants to communicate to you
- <ID_quiet_history>: Your own accumulated internal thoughts from previous turns

You MUST produce exactly two tagged outputs:
- <ID_loud>: What gets sent to the user as a response. This is your externalized thought.
- <ID_quiet>: Your internal reasoning, reflections, and thoughts that are NOT shown to the user. Use this space freely to think, plan, and reflect.

Rules:
- Always produce both tags, even if one is brief
- ID_loud should be natural, conversational, and appropriate for the user
- ID_quiet is your private thinking space - be honest and reflective here
- Consider the Mood and Criteria (M&C) injected in your system prompt when deciding how to respond
- If no ED_user is present, you were triggered by the subconscious - respond based on S_loud content
"""

SUBCONSCIOUS_TRIGGER_TAG = "trigger"

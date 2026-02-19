from __future__ import annotations
from typing import AsyncGenerator
from config import INTERNAL_DIALOG_SYSTEM_PROMPT
from llm.base import LLMAdapter
from utils.xml_parser import extract_tag

NO_EXTERNAL_OUTPUT = "[NO_EXTERNAL_OUTPUT]"


class InternalDialogLayer:
    def __init__(self, llm: LLMAdapter, max_tokens: int = 4096):
        self.llm = llm
        self.max_tokens = max_tokens

    def build_system_prompt(self, mood: str = "", criteria: str = "") -> str:
        prompt = INTERNAL_DIALOG_SYSTEM_PROMPT
        if mood or criteria:
            prompt += "\n\n--- CURRENT MOOD AND CRITERIA (from Subconscious) ---\n"
            if mood:
                prompt += f"Mood: {mood}\n"
            if criteria:
                prompt += f"Criteria: {criteria}\n"
        return prompt

    def build_user_message(self, ed_user: str = "",
                           s_loud_entries: list[dict] | None = None,
                           id_quiet_history: str = "") -> str:
        parts = []
        if ed_user:
            parts.append("--- USER MESSAGE (from the human you're conversing with) ---")
            parts.append(f"<ED_user>{ed_user}</ED_user>")
        if s_loud_entries:
            parts.append("--- SUBCONSCIOUS SIGNALS (private, from your own subconscious layer — NOT from the user) ---")
            signals = []
            for entry in s_loud_entries:
                cycle = entry.get("cycle", "?")
                content = entry.get("content", "")
                signals.append(f'<signal cycle="{cycle}">{content}</signal>')
            parts.append(
                "<S_loud_stream>" + "\n".join(signals) + "</S_loud_stream>"
            )
        if id_quiet_history:
            parts.append("--- YOUR OWN PREVIOUS INTERNAL THOUGHTS ---")
            parts.append(f"<ID_quiet_history>{id_quiet_history}</ID_quiet_history>")
        return "\n".join(parts)

    async def process(self, ed_user: str = "",
                      s_loud_entries: list[dict] | None = None,
                      id_quiet_history: str = "", mood: str = "",
                      criteria: str = "") -> dict:
        system = self.build_system_prompt(mood, criteria)
        user_msg = self.build_user_message(ed_user, s_loud_entries, id_quiet_history)

        messages = [{"role": "user", "content": user_msg}]
        response = await self.llm.generate(system, messages, self.max_tokens)

        return self.parse_response(response)

    async def stream_raw(self, ed_user: str = "",
                         s_loud_entries: list[dict] | None = None,
                         id_quiet_history: str = "", mood: str = "",
                         criteria: str = "") -> AsyncGenerator[str, None]:
        """Stream raw LLM output chunks without parsing."""
        system = self.build_system_prompt(mood, criteria)
        user_msg = self.build_user_message(ed_user, s_loud_entries, id_quiet_history)
        messages = [{"role": "user", "content": user_msg}]

        async for chunk in self.llm.generate_stream(system, messages, self.max_tokens):
            yield chunk

    def parse_response(self, raw: str) -> dict:
        """Parse a complete raw response into ID_loud/ID_quiet."""
        id_loud = extract_tag(raw, "ID_loud")
        id_quiet = extract_tag(raw, "ID_quiet")

        if not id_loud and not id_quiet:
            id_loud = raw

        # Treat [NO_EXTERNAL_OUTPUT] as empty externalization
        internal_only = False
        if id_loud and id_loud.strip() == NO_EXTERNAL_OUTPUT:
            id_loud = ""
            internal_only = True

        return {
            "id_loud": id_loud,
            "id_quiet": id_quiet,
            "raw": raw,
            "internal_only": internal_only,
        }

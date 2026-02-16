from typing import AsyncGenerator
from config import INTERNAL_DIALOG_SYSTEM_PROMPT
from llm.base import LLMAdapter
from utils.xml_parser import extract_tag


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

    def build_user_message(self, ed_user: str = "", s_loud: str = "",
                           id_quiet_history: str = "") -> str:
        parts = []
        if ed_user:
            parts.append(f"<ED_user>{ed_user}</ED_user>")
        if s_loud:
            parts.append(f"<S_loud>{s_loud}</S_loud>")
        if id_quiet_history:
            parts.append(f"<ID_quiet_history>{id_quiet_history}</ID_quiet_history>")
        return "\n".join(parts)

    async def process(self, ed_user: str = "", s_loud: str = "",
                      id_quiet_history: str = "", mood: str = "",
                      criteria: str = "") -> dict:
        system = self.build_system_prompt(mood, criteria)
        user_msg = self.build_user_message(ed_user, s_loud, id_quiet_history)

        messages = [{"role": "user", "content": user_msg}]
        response = await self.llm.generate(system, messages, self.max_tokens)

        id_loud = extract_tag(response, "ID_loud")
        id_quiet = extract_tag(response, "ID_quiet")

        # Fallback: if no tags found, treat entire response as ID_loud
        if not id_loud and not id_quiet:
            id_loud = response

        return {"id_loud": id_loud, "id_quiet": id_quiet, "raw": response}

    async def stream_raw(self, ed_user: str = "", s_loud: str = "",
                         id_quiet_history: str = "", mood: str = "",
                         criteria: str = "") -> AsyncGenerator[str, None]:
        """Stream raw LLM output chunks without parsing."""
        system = self.build_system_prompt(mood, criteria)
        user_msg = self.build_user_message(ed_user, s_loud, id_quiet_history)
        messages = [{"role": "user", "content": user_msg}]

        async for chunk in self.llm.generate_stream(system, messages, self.max_tokens):
            yield chunk

    def parse_response(self, raw: str) -> dict:
        """Parse a complete raw response into ID_loud/ID_quiet."""
        id_loud = extract_tag(raw, "ID_loud")
        id_quiet = extract_tag(raw, "ID_quiet")

        if not id_loud and not id_quiet:
            id_loud = raw

        return {"id_loud": id_loud, "id_quiet": id_quiet, "raw": raw}

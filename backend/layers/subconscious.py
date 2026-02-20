from llm.base import LLMAdapter
from utils.xml_parser import extract_tag, extract_m_and_c


class SubconsciousLayer:
    def __init__(self, llm: LLMAdapter, max_tokens: int = 2048):
        self.llm = llm
        self.max_tokens = max_tokens

    def build_user_message(self, ed_user: str = "", ed_agent: str = "",
                           id_quiet: str = "", id_loud: str = "",
                           s_quiet_history: str = "",
                           s_loud_history: str = "",
                           cycle: int = 0) -> str:
        parts = [f"--- CYCLE {cycle} ---"]
        if ed_user:
            parts.append("--- LAST USER MESSAGE ---")
            parts.append(f"<ED_user>{ed_user}</ED_user>")
        if ed_agent:
            parts.append("--- LAST AGENT RESPONSE TO USER ---")
            parts.append(f"<ED_agent>{ed_agent}</ED_agent>")
        if id_loud:
            parts.append("--- LAST INTERNAL DIALOG OUTPUT (what was said to user) ---")
            parts.append(f"<ID_loud>{id_loud}</ID_loud>")
        if id_quiet:
            parts.append("--- LAST INTERNAL DIALOG PRIVATE THOUGHT ---")
            parts.append(f"<ID_quiet>{id_quiet}</ID_quiet>")
        if s_loud_history:
            parts.append("--- YOUR OWN S_LOUD HISTORY (what you already broadcast — DO NOT REPEAT) ---")
            parts.append(f"<S_loud_history>{s_loud_history}</S_loud_history>")
        if s_quiet_history:
            parts.append("--- YOUR OWN S_QUIET HISTORY (your previous internal notes) ---")
            parts.append(f"<S_quiet_history>{s_quiet_history}</S_quiet_history>")
        if not ed_user and not ed_agent and not id_loud and not id_quiet:
            parts.append("<no_new_input/>")
        return "\n".join(parts)

    async def process(self, persona_core: str, ed_user: str = "",
                      ed_agent: str = "", id_quiet: str = "",
                      id_loud: str = "", s_quiet_history: str = "",
                      s_loud_history: str = "", cycle: int = 0) -> dict:
        user_msg = self.build_user_message(
            ed_user, ed_agent, id_quiet, id_loud,
            s_quiet_history, s_loud_history, cycle,
        )

        messages = [{"role": "user", "content": user_msg}]
        response = await self.llm.generate(persona_core, messages, self.max_tokens)

        s_loud = extract_tag(response, "S_loud")
        s_quiet = extract_tag(response, "S_quiet")
        m_and_c = extract_m_and_c(response)
        trigger = extract_tag(response, "trigger").lower().strip()
        should_trigger = trigger in ("true", "yes", "1")

        return {
            "s_loud": s_loud,
            "s_quiet": s_quiet,
            "mood": m_and_c["mood"],
            "criteria": m_and_c["criteria"],
            "trigger": should_trigger,
            "raw": response,
        }

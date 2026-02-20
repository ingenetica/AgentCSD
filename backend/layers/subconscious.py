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
        parts = []

        if ed_user:
            parts.append("El humano acaba de decir:")
            parts.append(f"<ED_user>{ed_user}</ED_user>")
        if ed_agent:
            if parts:
                parts.append("")
            parts.append("Se le respondió:")
            parts.append(f"<ED_agent>{ed_agent}</ED_agent>")
        if id_loud:
            if parts:
                parts.append("")
            parts.append("Lo que se decidió decir en voz alta:")
            parts.append(f"<ID_loud>{id_loud}</ID_loud>")
        if id_quiet:
            if parts:
                parts.append("")
            parts.append("Pensamiento interno que no se dijo:")
            parts.append(f"<ID_quiet>{id_quiet}</ID_quiet>")
        if s_loud_history:
            if parts:
                parts.append("")
            parts.append("Lo que ya comunicaste antes (no lo repitas):")
            parts.append(f"<S_loud_history>{s_loud_history}</S_loud_history>")
        if s_quiet_history:
            if parts:
                parts.append("")
            parts.append("Tus notas internas anteriores:")
            parts.append(f"<S_quiet_history>{s_quiet_history}</S_quiet_history>")

        if not parts:
            parts.append("No hay información nueva.")

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

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMAdapter(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, messages: list[dict],
                       max_tokens: int = 4096) -> str:
        """Send prompt to LLM and return response text.

        Args:
            system_prompt: The system-level instructions.
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts.
            max_tokens: Maximum tokens to generate.

        Returns:
            The generated text response.
        """
        pass

    async def generate_stream(self, system_prompt: str, messages: list[dict],
                              max_tokens: int = 4096) -> AsyncGenerator[str, None]:
        """Stream response chunks from LLM.

        Default implementation yields entire result from generate() as one chunk.
        Subclasses can override for true streaming.
        """
        result = await self.generate(system_prompt, messages, max_tokens)
        yield result

from __future__ import annotations
from typing import AsyncGenerator
from llm.base import LLMAdapter


class AnthropicAPIAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-sonnet-4-5-20250929",
                 api_key: str | None = None):
        import anthropic
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(self, system_prompt: str, messages: list[dict],
                       max_tokens: int = 4096) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    async def generate_stream(self, system_prompt: str, messages: list[dict],
                              max_tokens: int = 4096) -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

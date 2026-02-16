from __future__ import annotations
from typing import AsyncGenerator
from llm.base import LLMAdapter


class OpenAICompatAdapter(LLMAdapter):
    def __init__(self, model: str = "local-model",
                 endpoint: str = "http://localhost:1234/v1",
                 api_key: str | None = None):
        from openai import AsyncOpenAI
        self.model = model
        self.client = AsyncOpenAI(
            base_url=endpoint,
            api_key=api_key or "not-needed",
        )

    async def generate(self, system_prompt: str, messages: list[dict],
                       max_tokens: int = 4096) -> str:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def generate_stream(self, system_prompt: str, messages: list[dict],
                              max_tokens: int = 4096) -> AsyncGenerator[str, None]:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

from __future__ import annotations
import asyncio
import os
from typing import AsyncGenerator
from llm.base import LLMAdapter


class ClaudeCLIAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        self.model = model

    def _build_cmd_and_env(self, system_prompt: str, messages: list[dict]) -> tuple[list[str], dict]:
        user_content = ""
        for msg in messages:
            if msg["role"] == "user":
                user_content += msg["content"] + "\n"
            elif msg["role"] == "assistant":
                user_content += f"[Previous response]: {msg['content']}\n"

        cmd = [
            "claude",
            "--print",
            "--model", self.model,
            "--max-turns", "1",
            "--system-prompt", system_prompt,
            user_content.strip(),
        ]

        env = {k: v for k, v in os.environ.items()
               if not k.startswith("CLAUDE")}
        env["PATH"] = os.environ.get("PATH", "")

        return cmd, env

    async def generate(self, system_prompt: str, messages: list[dict],
                       max_tokens: int = 4096) -> str:
        cmd, env = self._build_cmd_and_env(system_prompt, messages)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                raise RuntimeError(f"Claude CLI error (code {proc.returncode}): {error_msg}")

            return stdout.decode().strip()
        except FileNotFoundError:
            raise RuntimeError(
                "Claude CLI not found. Ensure 'claude' is installed and in PATH."
            )

    async def generate_stream(self, system_prompt: str, messages: list[dict],
                              max_tokens: int = 4096) -> AsyncGenerator[str, None]:
        cmd, env = self._build_cmd_and_env(system_prompt, messages)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            while True:
                chunk = await proc.stdout.read(256)
                if not chunk:
                    break
                yield chunk.decode()

            await proc.wait()
            if proc.returncode != 0:
                stderr = await proc.stderr.read()
                error_msg = stderr.decode().strip()
                raise RuntimeError(f"Claude CLI error (code {proc.returncode}): {error_msg}")
        except FileNotFoundError:
            raise RuntimeError(
                "Claude CLI not found. Ensure 'claude' is installed and in PATH."
            )

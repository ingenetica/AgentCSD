from __future__ import annotations
import asyncio
import shutil
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

from config import LOGS_DIR, PERSONAS_DIR, DEFAULT_MODEL_CONFIG, S_LOUD_BATCH_DELAY, S_LOUD_BATCH_MAX
from database import repository as db
from layers.internal_dialog import InternalDialogLayer
from layers.subconscious import SubconsciousLayer
from llm.base import LLMAdapter
from llm.claude_cli import ClaudeCLIAdapter
from llm.anthropic_api import AnthropicAPIAdapter
from llm.openai_compat import OpenAICompatAdapter
from utils.jsonl import append_jsonl

logger = logging.getLogger("agentcsd.orchestrator")


def create_adapter(config: dict) -> LLMAdapter:
    backend = config.get("backend", "claude_code_cli")
    model = config.get("model", "")
    if backend == "claude_code_cli":
        return ClaudeCLIAdapter(
            model=model,
            tools=config.get("tools"),
            max_turns=config.get("max_turns", 1),
        )
    elif backend == "anthropic_api":
        return AnthropicAPIAdapter(model=model, api_key=config.get("api_key"))
    elif backend == "openai_compatible":
        return OpenAICompatAdapter(
            model=model,
            endpoint=config.get("endpoint", "http://localhost:1234/v1"),
            api_key=config.get("api_key"),
        )
    else:
        raise ValueError(f"Unknown backend: {backend}")


class Orchestrator:
    def __init__(self, send_ws):
        self.send_ws = send_ws  # async callable to send WS messages

        # Session state
        self.session_id: str | None = None
        self.persona_core: str = ""
        self.model_config: dict = DEFAULT_MODEL_CONFIG.copy()
        self.summary_frequency: int = 10

        # Layers
        self.internal_dialog: InternalDialogLayer | None = None
        self.subconscious: SubconsciousLayer | None = None

        # Shared state (accessed by both layers)
        self._lock = asyncio.Lock()
        self.current_s_loud: str = ""
        self.current_mood: str = ""
        self.current_criteria: str = ""
        self.subconscious_cycle: int = 0
        self.is_paused: bool = False

        # Recent data for subconscious input
        self.last_ed_user: str = ""
        self.last_ed_agent: str = ""
        self.last_id_loud: str = ""
        self.last_id_quiet: str = ""

        # Track what the subconscious already saw (to avoid feeding the same data)
        self._s_seen_ed_user: str = ""
        self._s_seen_ed_agent: str = ""
        self._s_seen_id_loud: str = ""
        self._s_seen_id_quiet: str = ""

        # Accumulated histories (windowed)
        self.id_quiet_history: list[str] = []
        self.s_quiet_history: list[str] = []
        self.s_loud_history: list[str] = []

        # Background tasks
        self._subconscious_task: asyncio.Task | None = None
        self._s_loud_processor_task: asyncio.Task | None = None
        self._processing_lock = asyncio.Lock()

        # S_loud batching queue
        self._pending_s_loud: list[dict] = []
        self._s_loud_queue_event = asyncio.Event()
        self._s_loud_force_drain = asyncio.Event()

    def _log_dir(self) -> Path:
        return LOGS_DIR / self.session_id

    def _init_layers(self):
        c_config = self.model_config.get("c_model", {})
        s_config = self.model_config.get("s_model", {})
        self.internal_dialog = InternalDialogLayer(
            llm=create_adapter(c_config),
            max_tokens=c_config.get("max_tokens", 4096),
        )
        self.subconscious = SubconsciousLayer(
            llm=create_adapter(s_config),
            max_tokens=s_config.get("max_tokens", 2048),
        )

    async def create_session(self, name: str, persona_core_filename: str,
                             model_config: dict | None = None,
                             summary_frequency: int = 10) -> str:
        self.session_id = str(uuid.uuid4())
        self.model_config = model_config or DEFAULT_MODEL_CONFIG.copy()
        self.summary_frequency = summary_frequency

        # Load persona core
        persona_path = PERSONAS_DIR / persona_core_filename
        if not persona_path.exists():
            raise FileNotFoundError(f"Persona file not found: {persona_core_filename}")
        self.persona_core = persona_path.read_text(encoding="utf-8")

        # Create DB record
        await db.create_session(
            self.session_id, name, persona_core_filename,
            self.model_config, summary_frequency,
        )

        # Create log dir and snapshot persona
        log_dir = self._log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(persona_path, log_dir / "persona_core_snapshot.md")

        # Init layers and start subconscious
        self._init_layers()
        self._reset_state()
        self._start_subconscious()

        return self.session_id

    async def resume_session(self, session_id: str) -> dict:
        session = await db.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        self.session_id = session_id
        self.model_config = session["model_config"]
        self.summary_frequency = session["summary_frequency"]

        # Load persona core
        persona_path = PERSONAS_DIR / session["persona_core_path"]
        if persona_path.exists():
            self.persona_core = persona_path.read_text(encoding="utf-8")
        else:
            snapshot = self._log_dir() / "persona_core_snapshot.md"
            if snapshot.exists():
                self.persona_core = snapshot.read_text(encoding="utf-8")
            else:
                raise FileNotFoundError("Persona core not found")

        # Load history from DB
        await self._load_history()

        # Init layers and start subconscious
        self._init_layers()
        self.is_paused = False
        self._start_subconscious()

        # Update session status
        await db.update_session(session_id, status="active")

        # Build history payload for frontend
        messages = await db.get_messages(session_id, limit=200)
        mc = await db.get_latest_mood_and_criteria(session_id)

        return {
            "session_id": session_id,
            "messages": messages,
            "mood_and_criteria": mc,
            "cycle": self.subconscious_cycle,
        }

    async def _load_history(self):
        self._reset_state()
        messages = await db.get_messages(self.session_id, limit=200)
        for msg in messages:
            tag = msg["tag"]
            content = msg["content"]
            if tag == "ID_quiet":
                self.id_quiet_history.append(content)
            elif tag == "S_quiet":
                self.s_quiet_history.append(content)
            elif tag == "S_loud":
                self.s_loud_history.append(content)
                self.current_s_loud = content
            elif tag == "ED_user":
                self.last_ed_user = content
            elif tag == "ED_agent":
                self.last_ed_agent = content
            elif tag == "ID_loud":
                self.last_id_loud = content

            if msg["cycle_number"] is not None:
                self.subconscious_cycle = max(
                    self.subconscious_cycle, msg["cycle_number"]
                )

        mc = await db.get_latest_mood_and_criteria(self.session_id)
        if mc:
            self.current_mood = mc["mood"]
            self.current_criteria = mc["criteria"]

        # Load context summaries and prepend the latest of each type
        for layer, history_list in [
            ("internal", self.id_quiet_history),
            ("subconscious", self.s_quiet_history),
            ("subconscious_loud", self.s_loud_history),
        ]:
            summaries = await db.get_context_summaries(self.session_id, layer)
            if summaries:
                latest = summaries[-1]["summary"]
                history_list.insert(0, f"[Previous summary]: {latest}")

    def _reset_state(self):
        self.current_s_loud = ""
        self.current_mood = ""
        self.current_criteria = ""
        self.subconscious_cycle = 0
        self.is_paused = False
        self.last_ed_user = ""
        self.last_ed_agent = ""
        self.last_id_loud = ""
        self.last_id_quiet = ""
        self._s_seen_ed_user = ""
        self._s_seen_ed_agent = ""
        self._s_seen_id_loud = ""
        self._s_seen_id_quiet = ""
        self.id_quiet_history = []
        self.s_quiet_history = []
        self.s_loud_history = []

    def _start_subconscious(self):
        if self._subconscious_task and not self._subconscious_task.done():
            self._subconscious_task.cancel()
        if self._s_loud_processor_task and not self._s_loud_processor_task.done():
            self._s_loud_processor_task.cancel()
        self._subconscious_task = asyncio.create_task(self._subconscious_loop())
        self._s_loud_processor_task = asyncio.create_task(self._s_loud_processor_loop())

    async def pause(self):
        self.is_paused = True
        # Discard any pending S_loud entries so they don't get processed after pause
        self._pending_s_loud.clear()
        self._s_loud_queue_event.clear()
        self._s_loud_force_drain.clear()
        if self.session_id:
            await db.update_session(self.session_id, status="paused")
        await self.send_ws({
            "type": "status",
            "subconscious_running": False,
            "cycle": self.subconscious_cycle,
        })

    async def resume(self):
        self.is_paused = False
        if self.session_id:
            await db.update_session(self.session_id, status="active")
        await self.send_ws({
            "type": "status",
            "subconscious_running": True,
            "cycle": self.subconscious_cycle,
        })

    async def stop(self):
        self.is_paused = True
        for task in (self._subconscious_task, self._s_loud_processor_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def update_config(self, model_config: dict):
        self.model_config = model_config
        self._init_layers()
        if self.session_id:
            await db.update_session(self.session_id, model_config=model_config)

    # --- Core processing ---

    async def handle_user_message(self, content: str):
        if not self.session_id or not self.internal_dialog:
            await self.send_ws({"type": "error", "message": "No active session"})
            return

        async with self._processing_lock:
            now = datetime.now(timezone.utc).isoformat()

            # Save ED_user
            await db.save_message(self.session_id, "external", "ED_user", content)
            self.last_ed_user = content
            append_jsonl(
                self._log_dir() / "external_dialog.jsonl",
                {"tag": "ED_user", "content": content},
            )

            # Drain any pending S_loud into this call
            s_loud_entries = self._drain_pending_s_loud()

            # If no pending S_loud, include latest current_s_loud as a single entry
            if not s_loud_entries:
                async with self._lock:
                    if self.current_s_loud:
                        s_loud_entries = [{"content": self.current_s_loud,
                                           "cycle": self.subconscious_cycle}]

            async with self._lock:
                mood = self.current_mood
                criteria = self.current_criteria

            # Build ID_quiet history string (last N entries)
            id_quiet_str = "\n---\n".join(self.id_quiet_history[-10:])

            # Send input context to frontend (what goes into C_model)
            await self.send_ws({
                "type": "id_input_context",
                "cycle": self.subconscious_cycle,
                "ed_user": content,
                "s_loud_entries": [{"cycle": e.get("cycle"), "content": e.get("content", "")} for e in s_loud_entries] if s_loud_entries else [],
                "mood": mood,
                "criteria": criteria,
                "timestamp": now,
            })

            # Call Internal Dialog with streaming
            raw_response = ""
            async for chunk in self.internal_dialog.stream_raw(
                ed_user=content,
                s_loud_entries=s_loud_entries,
                id_quiet_history=id_quiet_str,
                mood=mood,
                criteria=criteria,
            ):
                raw_response += chunk
                await self.send_ws({
                    "type": "ed_agent_chunk", "content": chunk, "timestamp": now,
                })

            # Parse completed response
            result = self.internal_dialog.parse_response(raw_response)
            id_loud = result["id_loud"]
            id_quiet = result["id_quiet"]

            # Send finalized clean response
            await self.send_ws({
                "type": "ed_agent_done", "content": id_loud, "timestamp": now,
            })

            # Persist
            await db.save_message(self.session_id, "internal", "ID_loud", id_loud)
            await db.save_message(self.session_id, "internal", "ID_quiet", id_quiet)
            await db.save_message(self.session_id, "external", "ED_agent", id_loud)

            self.last_ed_agent = id_loud
            self.last_id_loud = id_loud
            self.last_id_quiet = id_quiet
            if id_quiet:
                self.id_quiet_history.append(id_quiet)

            # JSONL logs
            log_dir = self._log_dir()
            append_jsonl(log_dir / "internal_dialog.jsonl",
                         {"tag": "ID_loud", "content": id_loud})
            append_jsonl(log_dir / "internal_dialog.jsonl",
                         {"tag": "ID_quiet", "content": id_quiet})
            append_jsonl(log_dir / "external_dialog.jsonl",
                         {"tag": "ED_agent", "content": id_loud})

            # Send metadata to frontend
            await self.send_ws({
                "type": "id_loud", "content": id_loud,
                "cycle": self.subconscious_cycle, "timestamp": now,
            })
            await self.send_ws({
                "type": "id_quiet", "content": id_quiet,
                "cycle": self.subconscious_cycle, "timestamp": now,
            })

    def _drain_pending_s_loud(self) -> list[dict]:
        """Atomically drain the pending S_loud queue and return entries."""
        entries = list(self._pending_s_loud)
        self._pending_s_loud.clear()
        self._s_loud_queue_event.clear()
        self._s_loud_force_drain.clear()
        return entries

    async def _s_loud_processor_loop(self):
        """Background loop that batches S_loud signals and feeds them to Internal Dialog."""
        logger.info("S_loud processor loop started for session %s", self.session_id)

        while True:
            try:
                # Wait until there's at least one S_loud queued
                await self._s_loud_queue_event.wait()

                if self.is_paused:
                    await asyncio.sleep(0.5)
                    continue

                # Batch: wait for delay or force-drain, whichever comes first
                try:
                    await asyncio.wait_for(
                        self._s_loud_force_drain.wait(),
                        timeout=S_LOUD_BATCH_DELAY,
                    )
                except asyncio.TimeoutError:
                    pass  # Normal: delay expired, drain now

                # Drain and process
                entries = self._drain_pending_s_loud()
                if entries:
                    await self._process_internal_from_s_loud(entries)

            except asyncio.CancelledError:
                logger.info("S_loud processor loop cancelled")
                break
            except Exception as e:
                logger.error("S_loud processor error: %s", e, exc_info=True)
                await asyncio.sleep(2)

    async def _process_internal_from_s_loud(self, entries: list[dict]):
        """Process batched S_loud entries through Internal Dialog."""
        if not self.internal_dialog or self.is_paused:
            return

        async with self._processing_lock:
            now = datetime.now(timezone.utc).isoformat()

            async with self._lock:
                mood = self.current_mood
                criteria = self.current_criteria

            id_quiet_str = "\n---\n".join(self.id_quiet_history[-10:])

            # Send input context to frontend (what goes into C_model from S_loud)
            await self.send_ws({
                "type": "id_input_context",
                "cycle": self.subconscious_cycle,
                "ed_user": "",
                "s_loud_entries": [{"cycle": e.get("cycle"), "content": e.get("content", "")} for e in entries],
                "mood": mood,
                "criteria": criteria,
                "timestamp": now,
            })

            # Stream raw response (no streaming chunks to chat — this is internal)
            raw_response = ""
            async for chunk in self.internal_dialog.stream_raw(
                ed_user="",
                s_loud_entries=entries,
                id_quiet_history=id_quiet_str,
                mood=mood,
                criteria=criteria,
            ):
                raw_response += chunk
                # Stream to Internal panel only (not chat)
                await self.send_ws({
                    "type": "id_processing_chunk", "content": chunk, "timestamp": now,
                })

            # Parse completed response
            result = self.internal_dialog.parse_response(raw_response)
            id_loud = result["id_loud"]
            id_quiet = result["id_quiet"]
            internal_only = result["internal_only"]

            # Only externalize to chat if there's actual content for the user
            if id_loud and not internal_only:
                await self.send_ws({
                    "type": "ed_agent_done", "content": id_loud, "timestamp": now,
                })
                await db.save_message(self.session_id, "external", "ED_agent", id_loud,
                                      self.subconscious_cycle)
                self.last_ed_agent = id_loud
                append_jsonl(self._log_dir() / "external_dialog.jsonl",
                             {"tag": "ED_agent", "content": id_loud,
                              "cycle_number": self.subconscious_cycle})

            # Always persist ID_loud and ID_quiet
            await db.save_message(self.session_id, "internal", "ID_loud",
                                  id_loud or "[NO_EXTERNAL_OUTPUT]",
                                  self.subconscious_cycle)
            await db.save_message(self.session_id, "internal", "ID_quiet", id_quiet,
                                  self.subconscious_cycle)

            self.last_id_loud = id_loud
            self.last_id_quiet = id_quiet
            if id_quiet:
                self.id_quiet_history.append(id_quiet)

            # JSONL logs
            log_dir = self._log_dir()
            append_jsonl(log_dir / "internal_dialog.jsonl",
                         {"tag": "ID_loud",
                          "content": id_loud or "[NO_EXTERNAL_OUTPUT]",
                          "internal_only": internal_only,
                          "cycle_number": self.subconscious_cycle})
            append_jsonl(log_dir / "internal_dialog.jsonl",
                         {"tag": "ID_quiet", "content": id_quiet,
                          "cycle_number": self.subconscious_cycle})

            # Send metadata to frontend (with internal_only flag)
            await self.send_ws({
                "type": "id_loud",
                "content": id_loud or "[NO_EXTERNAL_OUTPUT]",
                "internal_only": internal_only or (not id_loud),
                "cycle": self.subconscious_cycle, "timestamp": now,
            })
            await self.send_ws({
                "type": "id_quiet", "content": id_quiet,
                "internal_only": True,
                "cycle": self.subconscious_cycle, "timestamp": now,
            })

    # --- Subconscious loop ---

    async def _subconscious_loop(self):
        logger.info("Subconscious loop started for session %s", self.session_id)
        backoff = 1

        while True:
            try:
                if self.is_paused:
                    await asyncio.sleep(0.5)
                    continue

                if not self.subconscious:
                    await asyncio.sleep(1)
                    continue

                self.subconscious_cycle += 1
                cycle = self.subconscious_cycle

                # Build inputs — only pass values that changed since last cycle
                s_quiet_str = "\n---\n".join(self.s_quiet_history[-10:])
                s_loud_str = "\n---\n".join(self.s_loud_history[-10:])

                # Diff: only send what the subconscious hasn't seen yet
                new_ed_user = self.last_ed_user if self.last_ed_user != self._s_seen_ed_user else ""
                new_ed_agent = self.last_ed_agent if self.last_ed_agent != self._s_seen_ed_agent else ""
                new_id_loud = self.last_id_loud if self.last_id_loud != self._s_seen_id_loud else ""
                new_id_quiet = self.last_id_quiet if self.last_id_quiet != self._s_seen_id_quiet else ""

                # Mark as seen for next cycle
                self._s_seen_ed_user = self.last_ed_user
                self._s_seen_ed_agent = self.last_ed_agent
                self._s_seen_id_loud = self.last_id_loud
                self._s_seen_id_quiet = self.last_id_quiet

                now_ctx = datetime.now(timezone.utc).isoformat()
                # Send input context to frontend (what goes into S_model)
                await self.send_ws({
                    "type": "s_input_context",
                    "cycle": cycle,
                    "ed_user": new_ed_user,
                    "ed_agent": new_ed_agent,
                    "id_loud": new_id_loud,
                    "id_quiet": new_id_quiet,
                    "timestamp": now_ctx,
                })

                result = await self.subconscious.process(
                    persona_core=self.persona_core,
                    ed_user=new_ed_user,
                    ed_agent=new_ed_agent,
                    id_quiet=new_id_quiet,
                    id_loud=new_id_loud,
                    s_quiet_history=s_quiet_str,
                    s_loud_history=s_loud_str,
                    cycle=cycle,
                )

                # Update shared state
                async with self._lock:
                    self.current_s_loud = result["s_loud"]
                    if result["mood"]:
                        self.current_mood = result["mood"]
                    if result["criteria"]:
                        self.current_criteria = result["criteria"]

                # Persist
                if result["s_loud"]:
                    await db.save_message(
                        self.session_id, "subconscious", "S_loud",
                        result["s_loud"], cycle,
                    )
                    self.s_loud_history.append(result["s_loud"])

                    # Enqueue S_loud for Internal Dialog processing
                    self._pending_s_loud.append({
                        "content": result["s_loud"],
                        "cycle": cycle,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    self._s_loud_queue_event.set()

                    # Force immediate drain if trigger=true or batch is full
                    if result["trigger"]:
                        logger.info("Spontaneous trigger at cycle %d — force drain", cycle)
                        self._s_loud_force_drain.set()
                    elif len(self._pending_s_loud) >= S_LOUD_BATCH_MAX:
                        logger.info("S_loud batch full (%d) — force drain", len(self._pending_s_loud))
                        self._s_loud_force_drain.set()

                if result["s_quiet"]:
                    await db.save_message(
                        self.session_id, "subconscious", "S_quiet",
                        result["s_quiet"], cycle,
                    )
                    self.s_quiet_history.append(result["s_quiet"])

                if result["mood"] or result["criteria"]:
                    await db.save_mood_and_criteria(
                        self.session_id, result["mood"],
                        result["criteria"], cycle,
                    )

                # JSONL logs
                log_dir = self._log_dir()
                if result["s_loud"]:
                    append_jsonl(log_dir / "subconscious.jsonl",
                                 {"tag": "S_loud", "content": result["s_loud"],
                                  "cycle_number": cycle})
                if result["s_quiet"]:
                    append_jsonl(log_dir / "subconscious.jsonl",
                                 {"tag": "S_quiet", "content": result["s_quiet"],
                                  "cycle_number": cycle})
                if result["mood"] or result["criteria"]:
                    append_jsonl(log_dir / "mood_and_criteria.jsonl",
                                 {"mood": result["mood"],
                                  "criteria": result["criteria"],
                                  "cycle_number": cycle})

                now = datetime.now(timezone.utc).isoformat()

                # Send to frontend
                if result["s_loud"]:
                    await self.send_ws({
                        "type": "s_loud", "content": result["s_loud"],
                        "cycle": cycle, "timestamp": now,
                    })
                if result["s_quiet"]:
                    await self.send_ws({
                        "type": "s_quiet", "content": result["s_quiet"],
                        "cycle": cycle, "timestamp": now,
                    })
                if result["mood"] or result["criteria"]:
                    await self.send_ws({
                        "type": "m_and_c", "mood": result["mood"],
                        "criteria": result["criteria"],
                        "cycle": cycle, "timestamp": now,
                    })

                await self.send_ws({
                    "type": "status",
                    "subconscious_running": not self.is_paused,
                    "cycle": cycle,
                })

                # Context window management: summarize every N cycles
                if cycle % self.summary_frequency == 0 and cycle > 0:
                    await self._maybe_summarize(cycle)

                backoff = 1  # Reset backoff on success

            except asyncio.CancelledError:
                logger.info("Subconscious loop cancelled")
                break
            except Exception as e:
                logger.error("Subconscious loop error: %s", e, exc_info=True)
                await self.send_ws({
                    "type": "error",
                    "message": f"Subconscious error: {str(e)}",
                })
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def _generate_summary(self, entries: list[str], label: str) -> str:
        """Use LLM to generate a concise summary of history entries."""
        try:
            if not self.subconscious or not entries:
                return ""
            combined = "\n---\n".join(entries)
            system_prompt = (
                "You are a summarization assistant. Condense the following history entries "
                f"(labeled '{label}') into a single concise paragraph that preserves the key "
                "themes, decisions, emotional states, and important details. "
                "Be factual and preserve nuance. Output only the summary paragraph."
            )
            messages = [{"role": "user", "content": combined}]
            summary = await self.subconscious.llm.generate(
                system_prompt, messages, max_tokens=512,
            )
            return summary.strip()
        except Exception as e:
            logger.warning("LLM summarization failed for %s, using truncation: %s", label, e)
            # Fallback: simple truncation
            return f"[Summary of {label}]: " + " | ".join(
                s[:100] for s in entries[-5:]
            )

    async def _maybe_summarize(self, cycle: int):
        """Summarize and truncate old history entries using LLM."""
        max_keep = 20

        if len(self.s_quiet_history) > max_keep:
            old = self.s_quiet_history[:-max_keep]
            summary = await self._generate_summary(old, "S_quiet")
            if summary:
                await db.save_context_summary(
                    self.session_id, "subconscious", summary,
                    cycle - len(old), cycle,
                )
                self.s_quiet_history = [f"[Previous summary]: {summary}"] + self.s_quiet_history[-max_keep:]
            else:
                self.s_quiet_history = self.s_quiet_history[-max_keep:]

        if len(self.s_loud_history) > max_keep:
            old = self.s_loud_history[:-max_keep]
            summary = await self._generate_summary(old, "S_loud")
            if summary:
                await db.save_context_summary(
                    self.session_id, "subconscious_loud", summary,
                    cycle - len(old), cycle,
                )
                self.s_loud_history = [f"[Previous summary]: {summary}"] + self.s_loud_history[-max_keep:]
            else:
                self.s_loud_history = self.s_loud_history[-max_keep:]

        if len(self.id_quiet_history) > max_keep:
            old = self.id_quiet_history[:-max_keep]
            summary = await self._generate_summary(old, "ID_quiet")
            if summary:
                await db.save_context_summary(
                    self.session_id, "internal", summary,
                    cycle - len(old), cycle,
                )
                self.id_quiet_history = [f"[Previous summary]: {summary}"] + self.id_quiet_history[-max_keep:]
            else:
                self.id_quiet_history = self.id_quiet_history[-max_keep:]

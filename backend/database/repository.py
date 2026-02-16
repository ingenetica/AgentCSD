from __future__ import annotations
import json
import aiosqlite
from config import DB_PATH
from database.schema import SCHEMA_SQL


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    finally:
        await db.close()


# --- Sessions ---

async def create_session(session_id: str, name: str, persona_core_path: str,
                         model_config: dict, summary_frequency: int = 10) -> dict:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO sessions (id, name, persona_core_path, model_config, summary_frequency) VALUES (?, ?, ?, ?, ?)",
            (session_id, name, persona_core_path, json.dumps(model_config), summary_frequency),
        )
        await db.commit()
        return await get_session(session_id)
    finally:
        await db.close()


async def get_session(session_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        d = dict(row)
        d["model_config"] = json.loads(d["model_config"])
        return d
    finally:
        await db.close()


async def list_sessions() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["model_config"] = json.loads(d["model_config"])
            result.append(d)
        return result
    finally:
        await db.close()


async def update_session(session_id: str, **kwargs) -> dict | None:
    db = await get_db()
    try:
        sets = []
        vals = []
        for k, v in kwargs.items():
            if k == "model_config":
                v = json.dumps(v)
            sets.append(f"{k} = ?")
            vals.append(v)
        sets.append("updated_at = datetime('now')")
        vals.append(session_id)
        await db.execute(
            f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?", vals
        )
        await db.commit()
        return await get_session(session_id)
    finally:
        await db.close()


async def delete_session(session_id: str):
    db = await get_db()
    try:
        await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM mood_and_criteria WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM context_summaries WHERE session_id = ?", (session_id,))
        await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await db.commit()
    finally:
        await db.close()


# --- Messages ---

async def save_message(session_id: str, layer: str, tag: str, content: str,
                       cycle_number: int | None = None) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO messages (session_id, layer, tag, content, cycle_number) VALUES (?, ?, ?, ?, ?)",
            (session_id, layer, tag, content, cycle_number),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_messages(session_id: str, layer: str | None = None,
                       tag: str | None = None, limit: int = 100) -> list[dict]:
    db = await get_db()
    try:
        query = "SELECT * FROM messages WHERE session_id = ?"
        params: list = [session_id]
        if layer:
            query += " AND layer = ?"
            params.append(layer)
        if tag:
            query += " AND tag = ?"
            params.append(tag)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        await db.close()


# --- Mood and Criteria ---

async def save_mood_and_criteria(session_id: str, mood: str, criteria: str,
                                 cycle_number: int) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO mood_and_criteria (session_id, mood, criteria, cycle_number) VALUES (?, ?, ?, ?)",
            (session_id, mood, criteria, cycle_number),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_latest_mood_and_criteria(session_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM mood_and_criteria WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


# --- Context Summaries ---

async def save_context_summary(session_id: str, layer: str, summary: str,
                               cycle_from: int, cycle_to: int) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO context_summaries (session_id, layer, summary, cycle_from, cycle_to) VALUES (?, ?, ?, ?, ?)",
            (session_id, layer, summary, cycle_from, cycle_to),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_context_summaries(session_id: str, layer: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM context_summaries WHERE session_id = ? AND layer = ? ORDER BY cycle_from",
            (session_id, layer),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()

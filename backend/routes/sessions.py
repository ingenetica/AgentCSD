import io
import json
import zipfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from config import LOGS_DIR
from database import repository as db
from models import SessionResponse
from utils.jsonl import read_jsonl

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionResponse])
async def list_sessions():
    return await db.list_sessions()


@router.get("/{session_id}")
async def get_session(session_id: str):
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    messages = await db.get_messages(session_id, limit=500)
    mc = await db.get_latest_mood_and_criteria(session_id)
    return {"session": session, "messages": messages, "mood_and_criteria": mc}


@router.get("/{session_id}/export")
async def export_session_logs(session_id: str):
    """Export all session logs as a ZIP archive."""
    log_dir = LOGS_DIR / session_id
    if not log_dir.exists():
        raise HTTPException(404, "Session logs not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(log_dir.iterdir()):
            if file_path.is_file():
                zf.write(file_path, file_path.name)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="session_{session_id}.zip"'
        },
    )


@router.get("/{session_id}/logs/{filename}")
async def get_session_log(session_id: str, filename: str):
    """Read a specific log file. JSONL files are returned as a JSON array; other files as plain text."""
    log_dir = LOGS_DIR / session_id
    file_path = log_dir / filename

    # Prevent path traversal
    if not file_path.resolve().is_relative_to(log_dir.resolve()):
        raise HTTPException(400, "Invalid filename")

    if not file_path.exists():
        raise HTTPException(404, "Log file not found")

    if file_path.suffix == ".jsonl":
        entries = read_jsonl(file_path)
        return entries

    # For non-JSONL files (e.g. persona_core_snapshot.md), return as plain text
    content = file_path.read_text(encoding="utf-8")
    return StreamingResponse(
        io.StringIO(content),
        media_type="text/plain",
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    await db.delete_session(session_id)
    return {"ok": True}

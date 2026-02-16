from fastapi import APIRouter, HTTPException
from database import repository as db
from models import SessionResponse

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


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    await db.delete_session(session_id)
    return {"ok": True}

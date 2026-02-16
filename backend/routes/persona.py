from fastapi import APIRouter, HTTPException
from config import PERSONAS_DIR
from models import PersonaCreate, PersonaUpdate

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.get("")
async def list_personas():
    files = sorted(PERSONAS_DIR.glob("*.md"))
    return [{"filename": f.name, "size": f.stat().st_size} for f in files]


@router.get("/{filename}")
async def get_persona(filename: str):
    path = PERSONAS_DIR / filename
    if not path.exists() or not path.suffix == ".md":
        raise HTTPException(404, "Persona file not found")
    return {"filename": filename, "content": path.read_text(encoding="utf-8")}


@router.put("/{filename}")
async def update_persona(filename: str, body: PersonaUpdate):
    path = PERSONAS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Persona file not found")
    path.write_text(body.content, encoding="utf-8")
    return {"filename": filename, "ok": True}


@router.post("")
async def create_persona(body: PersonaCreate):
    if not body.filename.endswith(".md"):
        raise HTTPException(400, "Filename must end with .md")
    path = PERSONAS_DIR / body.filename
    if path.exists():
        raise HTTPException(409, "Persona file already exists")
    path.write_text(body.content, encoding="utf-8")
    return {"filename": body.filename, "ok": True}


@router.delete("/{filename}")
async def delete_persona(filename: str):
    path = PERSONAS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Persona file not found")
    if filename == "default.md":
        raise HTTPException(400, "Cannot delete default persona")
    path.unlink()
    return {"ok": True}

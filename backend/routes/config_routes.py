import json
from fastapi import APIRouter
from config import DATA_DIR, DEFAULT_MODEL_CONFIG
from models import ConfigUpdate

router = APIRouter(prefix="/api/config", tags=["config"])

CONFIG_FILE = DATA_DIR / "default_config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_MODEL_CONFIG


def _save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


@router.get("")
async def get_config():
    return _load_config()


@router.put("")
async def update_config(body: ConfigUpdate):
    config = body.llm_config.model_dump()
    _save_config(config)
    return config

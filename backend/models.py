from typing import Optional
from pydantic import BaseModel, Field


class ModelLayerConfig(BaseModel):
    backend: str = "claude_code_cli"
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    endpoint: Optional[str] = None
    api_key: Optional[str] = None


class ModelConfig(BaseModel):
    c_model: ModelLayerConfig = Field(default_factory=ModelLayerConfig)
    s_model: ModelLayerConfig = Field(default_factory=lambda: ModelLayerConfig(
        model="claude-haiku-4-5-20251001", max_tokens=2048
    ))


class CreateSessionRequest(BaseModel):
    name: str
    persona_core: str = "default.md"
    llm_config: ModelConfig = Field(default_factory=ModelConfig)
    summary_frequency: int = 10


class SessionResponse(BaseModel):
    id: str
    name: str
    persona_core_path: str
    llm_config: dict = Field(alias="model_config")
    status: str
    summary_frequency: int
    created_at: str
    updated_at: str


class PersonaCreate(BaseModel):
    filename: str
    content: str


class PersonaUpdate(BaseModel):
    content: str


class ConfigUpdate(BaseModel):
    llm_config: ModelConfig


class MessageResponse(BaseModel):
    id: int
    session_id: str
    layer: str
    tag: str
    content: str
    cycle_number: Optional[int] = None
    created_at: str

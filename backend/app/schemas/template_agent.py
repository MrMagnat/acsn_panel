from pydantic import BaseModel, field_validator
from typing import Optional
import json
from .tool import ToolResponse


class TemplateAgentCreate(BaseModel):
    name: str
    description: str = ""
    llm_url: str = ""
    llm_model: Optional[str] = None
    llm_token: Optional[str] = None
    prompt: str = ""
    skills: str = ""
    energy_per_chat: int = 5
    is_active: bool = True
    tool_ids: list[str] = []
    prompt_suggestions: list[str] = []


class TemplateAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    llm_url: Optional[str] = None
    llm_model: Optional[str] = None
    llm_token: Optional[str] = None
    prompt: Optional[str] = None
    skills: Optional[str] = None
    energy_per_chat: Optional[int] = None
    is_active: Optional[bool] = None
    tool_ids: Optional[list[str]] = None
    prompt_suggestions: Optional[list[str]] = None


class TemplateAgentResponse(BaseModel):
    id: str
    name: str
    description: str
    llm_url: str
    llm_model: Optional[str] = None
    llm_token: Optional[str] = None
    prompt: str
    skills: str
    energy_per_chat: int
    is_active: bool
    prompt_suggestions: list[str] = []
    tools: list[ToolResponse] = []

    @field_validator('prompt_suggestions', mode='before')
    @classmethod
    def parse_suggestions(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []

    model_config = {"from_attributes": True}

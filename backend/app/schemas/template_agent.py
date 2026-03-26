from pydantic import BaseModel
from typing import Optional
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
    tools: list[ToolResponse] = []

    model_config = {"from_attributes": True}

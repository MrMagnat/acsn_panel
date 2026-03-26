from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .tool import ToolResponse


class AgentToolResponse(BaseModel):
    id: str
    tool_id: str
    field_values: dict
    is_configured: bool
    tool: ToolResponse

    model_config = {"from_attributes": True}


class AgentCreate(BaseModel):
    name: str
    description: str = ""
    tool_ids: list[str] = []


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    llm_url: Optional[str] = None
    llm_model: Optional[str] = None
    llm_token: Optional[str] = None
    prompt: Optional[str] = None
    skills: Optional[str] = None
    energy_per_chat: Optional[int] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    is_active: bool
    energy_left: int
    llm_url: str
    llm_model: Optional[str] = None
    llm_token: Optional[str] = None
    prompt: str
    skills: str
    energy_per_chat: int
    created_at: datetime
    agent_tools: list[AgentToolResponse] = []

    model_config = {"from_attributes": True}


class AgentListItem(BaseModel):
    """Краткая информация об агенте для галереи плиток."""
    id: str
    name: str
    is_active: bool
    energy_left: int
    tools_count: int

    model_config = {"from_attributes": True}


class AddToolToAgent(BaseModel):
    tool_id: str


class UpdateToolFields(BaseModel):
    field_values: dict

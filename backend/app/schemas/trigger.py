from pydantic import BaseModel
from typing import Optional
from .tool import ToolResponse


class TriggerCreate(BaseModel):
    agent_id: str
    tool_id: str
    cron_expr: str


class TriggerUpdate(BaseModel):
    cron_expr: Optional[str] = None
    is_active: Optional[bool] = None


class TriggerResponse(BaseModel):
    id: str
    agent_id: str
    tool_id: str
    cron_expr: str
    is_active: bool
    tool: ToolResponse

    model_config = {"from_attributes": True}

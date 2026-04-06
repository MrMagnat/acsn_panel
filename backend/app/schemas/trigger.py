from pydantic import BaseModel
from typing import Optional
from .tool import ToolResponse


class TriggerCreate(BaseModel):
    agent_id: str
    tool_id: str
    cron_expr: str
    timezone: str = "UTC"
    input_data: dict = {}


class TriggerUpdate(BaseModel):
    cron_expr: Optional[str] = None
    is_active: Optional[bool] = None
    timezone: Optional[str] = None
    input_data: Optional[dict] = None


class TriggerResponse(BaseModel):
    id: str
    agent_id: str
    tool_id: str
    cron_expr: str
    timezone: str
    is_active: bool
    input_data: dict
    tool: ToolResponse

    model_config = {"from_attributes": True}

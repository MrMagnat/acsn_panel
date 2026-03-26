from pydantic import BaseModel
from typing import Optional


class ToolFieldBase(BaseModel):
    field_name: str
    hint: str = ""
    required: bool = False
    field_type: str = "text"
    sort_order: int = 0
    is_runtime: bool = False  # True = LLM может задавать/менять через чат


class ToolFieldCreate(ToolFieldBase):
    pass


class ToolFieldResponse(ToolFieldBase):
    id: str
    tool_id: str

    model_config = {"from_attributes": True}


class ToolBase(BaseModel):
    name: str
    description: str = ""
    trigger_hint: str = ""
    webhook_url: str
    is_active: bool = True
    energy_cost: int = 10


class ToolCreate(ToolBase):
    fields: list[ToolFieldCreate] = []


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_hint: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None
    energy_cost: Optional[int] = None
    fields: Optional[list[ToolFieldCreate]] = None


class ToolResponse(ToolBase):
    id: str
    fields: list[ToolFieldResponse] = []

    model_config = {"from_attributes": True}

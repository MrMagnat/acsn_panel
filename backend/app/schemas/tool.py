from pydantic import BaseModel
from typing import Optional


class ToolFieldBase(BaseModel):
    field_name: str
    hint: str = ""
    required: bool = False
    field_type: str = "text"   # text | url | number | json | select
    sort_order: int = 0
    is_runtime: bool = False   # True = LLM может задавать/менять через чат
    options: Optional[str] = None  # JSON-массив для типа select: '["a","b","c"]'


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
    is_maintenance: bool = False
    energy_cost: int = 10
    price_usd: int = 0  # цена в юнитах (1 = $0.0001)
    output_fields: list = []  # [{"name": "result"}, ...]


class ToolCreate(ToolBase):
    fields: list[ToolFieldCreate] = []
    owner_user_id: Optional[str] = None


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_hint: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_maintenance: Optional[bool] = None
    energy_cost: Optional[int] = None
    price_usd: Optional[int] = None
    fields: Optional[list[ToolFieldCreate]] = None
    output_fields: Optional[list] = None
    owner_user_id: Optional[str] = None


class ToolResponse(ToolBase):
    id: str
    fields: list[ToolFieldResponse] = []
    owner_user_id: Optional[str] = None

    model_config = {"from_attributes": True}

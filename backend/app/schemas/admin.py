from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AdminUserResponse(BaseModel):
    """Пользователь в таблице админки."""
    id: str
    email: str
    name: str
    is_admin: bool
    created_at: datetime
    plan: str
    agents_count: int
    tools_count: int

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    is_admin: Optional[bool] = None

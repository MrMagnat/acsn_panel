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
    ascn_user_id: Optional[int] = None
    telegram: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    is_admin: Optional[bool] = None

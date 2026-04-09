from pydantic import BaseModel
from datetime import datetime


class SkillResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    content: str
    icon: str
    category: str
    is_active: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentSkillResponse(BaseModel):
    id: str
    skill_id: str
    skill: SkillResponse

    model_config = {"from_attributes": True}


class SkillCreate(BaseModel):
    name: str
    slug: str
    description: str = ""
    content: str = ""
    icon: str = "✨"
    category: str = ""
    is_active: bool = True
    sort_order: int = 0


class SkillUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    content: str | None = None
    icon: str | None = None
    category: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None

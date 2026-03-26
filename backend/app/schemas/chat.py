from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SendMessageRequest(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tool_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    messages: list[ChatMessageResponse]
    energy_spent: int
    energy_left: int

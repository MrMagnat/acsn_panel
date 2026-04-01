from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SendMessageRequest(BaseModel):
    content: str
    llm_model: Optional[str] = None
    llm_token: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tool_name: Optional[str] = None
    log_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    messages: list[ChatMessageResponse]
    energy_spent: int
    energy_left: int
    trigger_created: bool = False

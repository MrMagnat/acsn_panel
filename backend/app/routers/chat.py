from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.deps import get_current_user
from ..services import chat_service
from ..schemas.chat import SendMessageRequest, ChatResponse, ChatMessageResponse
from ..models.user import User

router = APIRouter(prefix="/chat", tags=["Чат"])


@router.get("/{agent_id}/messages", response_model=list[ChatMessageResponse])
async def get_history(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """История чата агента."""
    return await chat_service.get_chat_history(agent_id, current_user.id, db)


@router.post("/{agent_id}/messages", response_model=ChatResponse)
async def send_message(
    agent_id: str,
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отправить сообщение агенту."""
    return await chat_service.send_message(
        agent_id, current_user.id, data.content, db,
        llm_model=data.llm_model, llm_token=data.llm_token,
    )

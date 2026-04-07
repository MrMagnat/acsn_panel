import json
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.db import get_db
from ..core.deps import get_current_user
from ..services import chat_service
from ..schemas.chat import SendMessageRequest, ChatResponse, ChatMessageResponse
from ..models.user import User
from ..models.subscription import Subscription
from ..models.setting import Setting

router = APIRouter(prefix="/chat", tags=["Чат"])

DEFAULT_ASCN_MODELS = [
    {"id": "openai/gpt-4o-mini",        "name": "GPT-4o mini",       "price_usd": 2},
    {"id": "google/gemini-2.0-flash-001","name": "Gemini 2.0 Flash",  "price_usd": 3},
    {"id": "deepseek/deepseek-r1",       "name": "DeepSeek R1",       "price_usd": 1},
]


async def _get_ascn_config(db: AsyncSession) -> dict:
    result = await db.execute(select(Setting).where(Setting.key == "ascn_config"))
    setting = result.scalar_one_or_none()
    if setting and setting.value:
        return json.loads(setting.value)
    return {"openrouter_key": "", "models": DEFAULT_ASCN_MODELS}


@router.get("/{agent_id}/messages", response_model=list[ChatMessageResponse])
async def get_history(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """История чата агента."""
    return await chat_service.get_chat_history(agent_id, current_user.id, db)


def _public_base_url(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto", "http")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost:8000")
    return f"{proto}://{host}/api"


@router.post("/{agent_id}/messages", response_model=ChatResponse)
async def send_message(
    agent_id: str,
    data: SendMessageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отправить сообщение агенту."""
    effective_provider = data.llm_provider
    effective_token = data.llm_token
    effective_model = data.llm_model
    ascn_price = None
    subscription = None

    if data.llm_provider == "ascn":
        config = await _get_ascn_config(db)
        if not config.get("openrouter_key"):
            raise HTTPException(status_code=502, detail="ASCN ключ не настроен администратором")

        model_cfg = next((m for m in config.get("models", []) if m["id"] == data.llm_model), None)
        if not model_cfg:
            raise HTTPException(status_code=400, detail="Неизвестная ASCN модель")

        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
        subscription = sub_result.scalar_one_or_none()
        if not subscription or subscription.balance_usd < model_cfg["price_usd"]:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="insufficient_balance",
            )

        effective_provider = "openrouter"
        effective_token = config["openrouter_key"]
        ascn_price = model_cfg["price_usd"]

    result = await chat_service.send_message(
        agent_id, current_user.id, data.content, db,
        llm_model=effective_model,
        llm_token=effective_token,
        llm_provider=effective_provider,
        base_url=_public_base_url(request),
    )

    # Списываем баланс после успешного ответа
    if ascn_price and subscription:
        subscription.balance_usd = max(0, subscription.balance_usd - ascn_price)
        await db.flush()

    return result

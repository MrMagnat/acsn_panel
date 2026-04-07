import hashlib
import json
from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.db import get_db
from ..core.config import settings
from ..models.subscription import Subscription
from ..models.user import User
from ..models.knowledge_base import KnowledgeBase, KBRecord
from ..schemas.subscription import SubscriptionWebhookUpdate


def _kb_token(kb_id: str) -> str:
    return hashlib.sha256(f"kb:{kb_id}:{settings.SECRET_KEY}".encode()).hexdigest()[:32]

router = APIRouter(prefix="/webhooks", tags=["Вебхуки"])


@router.post("/subscription-update", status_code=200)
async def subscription_update(
    data: SubscriptionWebhookUpdate,
    x_webhook_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Вебхук от системы подписок для обновления лимитов пользователя.
    Проверяем секрет в заголовке X-Webhook-Secret.
    """
    if x_webhook_secret != settings.SUBSCRIPTION_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неверный секрет вебхука")

    # Проверяем существование пользователя
    user_result = await db.execute(select(User).where(User.id == data.user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # Обновляем или создаём подписку
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == data.user_id))
    subscription = sub_result.scalar_one_or_none()

    if subscription:
        subscription.plan = data.plan
        subscription.max_agents = data.max_agents
        subscription.max_tools_per_agent = data.max_tools_per_agent
        subscription.energy_per_week = data.energy_per_week
    else:
        subscription = Subscription(
            user_id=data.user_id,
            plan=data.plan,
            max_agents=data.max_agents,
            max_tools_per_agent=data.max_tools_per_agent,
            energy_per_week=data.energy_per_week,
        )
        db.add(subscription)

    return {"status": "ok", "message": "Подписка обновлена"}


@router.post("/kb/{kb_id}", status_code=200)
async def kb_add_row(
    kb_id: str,
    payload: dict[str, Any],
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Добавить строку в базу знаний через вебхук (из внешних автоматизаций)."""
    if token != _kb_token(kb_id):
        raise HTTPException(status_code=403, detail="Неверный токен")

    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="База не найдена")

    record = KBRecord(kb_id=kb_id, data=json.dumps(payload, ensure_ascii=False))
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return {"ok": True, "record_id": record.id}


@router.get("/kb/{kb_id}/info", status_code=200)
async def kb_webhook_info(
    kb_id: str,
    token: str = Query(...),
):
    """Получить webhook URL для базы знаний."""
    if token != _kb_token(kb_id):
        raise HTTPException(status_code=403, detail="Неверный токен")
    return {"kb_id": kb_id, "token": _kb_token(kb_id)}

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.trigger import AutoTrigger
from ..models.agent import UserAgent
from ..models.tool import Tool
from ..models.user import User
from ..schemas.trigger import TriggerCreate, TriggerUpdate, TriggerResponse
from ..services.scheduler_service import schedule_trigger, unschedule_trigger
from fastapi import HTTPException, status

router = APIRouter(prefix="/triggers", tags=["Автозапуски"])


@router.post("", response_model=TriggerResponse, status_code=201)
async def create_trigger(
    data: TriggerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать автозапуск для инструмента агента."""
    # Проверяем права на агента
    agent_result = await db.execute(
        select(UserAgent).where(UserAgent.id == data.agent_id, UserAgent.user_id == current_user.id)
    )
    if not agent_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Агент не найден")

    trigger = AutoTrigger(
        agent_id=data.agent_id,
        tool_id=data.tool_id,
        cron_expr=data.cron_expr,
    )
    db.add(trigger)
    await db.flush()

    # Добавляем в планировщик
    schedule_trigger(trigger)

    # Перезагружаем со всеми вложенными связями
    result = await db.execute(
        select(AutoTrigger)
        .where(AutoTrigger.id == trigger.id)
        .options(selectinload(AutoTrigger.tool).selectinload(Tool.fields))
    )
    return result.scalar_one()


@router.patch("/{trigger_id}", response_model=TriggerResponse)
async def update_trigger(
    trigger_id: str,
    data: TriggerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить автозапуск (расписание/статус)."""
    trigger = await _get_trigger_for_user(trigger_id, current_user.id, db)

    if data.cron_expr is not None:
        trigger.cron_expr = data.cron_expr
    if data.is_active is not None:
        trigger.is_active = data.is_active

    await db.flush()

    # Обновляем планировщик
    schedule_trigger(trigger)

    # Перезагружаем со всеми вложенными связями
    result = await db.execute(
        select(AutoTrigger)
        .where(AutoTrigger.id == trigger.id)
        .options(selectinload(AutoTrigger.tool).selectinload(Tool.fields))
    )
    return result.scalar_one()


@router.delete("/{trigger_id}", status_code=204)
async def delete_trigger(
    trigger_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить автозапуск."""
    trigger = await _get_trigger_for_user(trigger_id, current_user.id, db)
    unschedule_trigger(trigger_id)
    await db.delete(trigger)


async def _get_trigger_for_user(trigger_id: str, user_id: str, db: AsyncSession) -> AutoTrigger:
    """Получаем триггер с проверкой принадлежности пользователю."""
    result = await db.execute(
        select(AutoTrigger)
        .join(UserAgent, AutoTrigger.agent_id == UserAgent.id)
        .where(AutoTrigger.id == trigger_id, UserAgent.user_id == user_id)
        .options(selectinload(AutoTrigger.tool).selectinload(Tool.fields))
    )
    trigger = result.scalar_one_or_none()
    if not trigger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Триггер не найден")
    return trigger

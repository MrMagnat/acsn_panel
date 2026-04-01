"""
Run logs: история запусков инструментов + callback от nocode-платформы.
"""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.tool_run_log import ToolRunLog
from ..models.agent import UserAgent
from ..models.user import User

router = APIRouter(tags=["Run Logs"])


# ── Схемы ───────────────────────────────────────────────────────────────────

class RunLogResponse(BaseModel):
    id: str
    tool_id: str
    tool_name: str
    instance_id: str | None
    trigger_type: str
    status: str          # running / success / error
    result_json: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class ToolCallbackPayload(BaseModel):
    """Тело от nocode-платформы когда задача завершилась."""
    instanceId: str
    status: str          # success / error / finished / completed — нормализуем сами
    data: dict | None = None
    error: str | None = None
    result: dict | None = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/run-logs", response_model=list[RunLogResponse])
async def list_all_run_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Все запуски пользователя (все агенты + standalone) — последние 200."""
    result = await db.execute(
        select(ToolRunLog)
        .where(ToolRunLog.user_id == current_user.id)
        .order_by(ToolRunLog.started_at.desc())
        .limit(200)
    )
    return result.scalars().all()


@router.get("/agents/{agent_id}/run-logs", response_model=list[RunLogResponse])
async def list_run_logs(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Последние 50 запусков инструментов агента."""
    # Проверяем права
    agent = (await db.execute(
        select(UserAgent).where(UserAgent.id == agent_id, UserAgent.user_id == current_user.id)
    )).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")

    result = await db.execute(
        select(ToolRunLog)
        .where(ToolRunLog.agent_id == agent_id)
        .order_by(ToolRunLog.started_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.get("/run-logs/{log_id}", response_model=RunLogResponse)
async def get_run_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Один лог — для polling на фронтенде."""
    log = (await db.execute(
        select(ToolRunLog).where(ToolRunLog.id == log_id, ToolRunLog.user_id == current_user.id)
    )).scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Лог не найден")
    return log


@router.post("/run-logs/{log_id}/cancel", response_model=RunLogResponse)
async def cancel_run_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Досрочно завершить запущенный процесс."""
    log = (await db.execute(
        select(ToolRunLog).where(ToolRunLog.id == log_id, ToolRunLog.user_id == current_user.id)
    )).scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Лог не найден")

    log.status = "cancelled"
    log.result_json = json.dumps({"message": "Процесс остановлен пользователем"}, ensure_ascii=False)
    log.finished_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(log)
    return log


@router.delete("/run-logs/{log_id}", status_code=204)
async def delete_run_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить запись из истории запусков."""
    log = (await db.execute(
        select(ToolRunLog).where(ToolRunLog.id == log_id, ToolRunLog.user_id == current_user.id)
    )).scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Лог не найден")
    await db.delete(log)
    await db.commit()


@router.post("/webhooks/tool-callback", status_code=200)
async def tool_callback(
    payload: ToolCallbackPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Callback от nocode-платформы (n8n / make / etc).
    Вызывается когда задача завершилась.
    Тело: { "instanceId": "...", "status": "success", "data": {...} }
    """
    log = (await db.execute(
        select(ToolRunLog).where(
            or_(
                ToolRunLog.instance_id == payload.instanceId,
                ToolRunLog.id == payload.instanceId,
            )
        )
    )).scalar_one_or_none()

    if not log:
        # Лог не найден — игнорируем, не ломаем nocode-платформу
        return {"ok": False, "detail": "log not found"}

    # Нормализуем статус (платформы могут слать разные значения)
    raw = payload.status.lower()
    if raw in ("success", "finished", "completed", "done"):
        log.status = "success"
    else:
        log.status = "error"

    # Сохраняем результат — берём data / result / error в порядке приоритета
    result_data = payload.data or payload.result or {}
    if payload.error:
        result_data["error"] = payload.error

    log.result_json = json.dumps(result_data, ensure_ascii=False)
    log.finished_at = datetime.now(timezone.utc)

    await db.commit()
    return {"ok": True}

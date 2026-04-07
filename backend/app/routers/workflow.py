from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Any

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.workflow import Workflow, WorkflowRun
from ..models.agent import UserAgent
from ..models.user import User
from ..schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowRunResponse
from ..services.workflow_service import run_workflow, receive_callback, get_run_statuses

router = APIRouter(prefix="/workflows", tags=["Воркфлоу"])


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список воркфлоу агента."""
    await _check_agent_owner(agent_id, current_user.id, db)
    result = await db.execute(
        select(Workflow)
        .where(Workflow.agent_id == agent_id)
        .order_by(Workflow.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать воркфлоу."""
    await _check_agent_owner(data.agent_id, current_user.id, db)
    wf = Workflow(agent_id=data.agent_id, name=data.name)
    db.add(wf)
    await db.flush()
    await db.refresh(wf)
    return wf


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wf = await _get_workflow_for_user(workflow_id, current_user.id, db)
    return wf


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Сохранить граф воркфлоу."""
    wf = await _get_workflow_for_user(workflow_id, current_user.id, db)
    if data.name is not None:
        wf.name = data.name
    if data.graph_json is not None:
        wf.graph_json = data.graph_json
    if data.is_active is not None:
        wf.is_active = data.is_active
    await db.flush()
    await db.refresh(wf)
    return wf


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wf = await _get_workflow_for_user(workflow_id, current_user.id, db)
    await db.delete(wf)


@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse)
async def run_workflow_endpoint(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запустить воркфлоу вручную."""
    await _get_workflow_for_user(workflow_id, current_user.id, db)
    run = await run_workflow(workflow_id, current_user.id, db, trigger_type="manual")
    return run


@router.get("/{workflow_id}/running-status")
async def get_running_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Live-статусы нод текущего запуска (in-memory, без DB)."""
    await _get_workflow_for_user(workflow_id, current_user.id, db)
    return get_run_statuses(workflow_id)


@router.post("/runs/{run_id}/callback/{node_id}")
async def node_callback(
    run_id: str,
    node_id: str,
    payload: dict[str, Any],
    token: str = Query(...),
):
    """Callback endpoint для асинхронных инструментов. Без авторизации, защищён токеном."""
    ok = receive_callback(run_id, node_id, token, payload)
    if not ok:
        raise HTTPException(status_code=403, detail="Неверный токен")
    return {"ok": True}


@router.get("/{workflow_id}/runs", response_model=list[WorkflowRunResponse])
async def get_workflow_runs(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """История запусков воркфлоу."""
    await _get_workflow_for_user(workflow_id, current_user.id, db)
    result = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.workflow_id == workflow_id)
        .order_by(WorkflowRun.started_at.desc())
        .limit(20)
    )
    return result.scalars().all()


async def _check_agent_owner(agent_id: str, user_id: str, db: AsyncSession):
    result = await db.execute(
        select(UserAgent).where(UserAgent.id == agent_id, UserAgent.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Агент не найден")


async def _get_workflow_for_user(workflow_id: str, user_id: str, db: AsyncSession) -> Workflow:
    result = await db.execute(
        select(Workflow)
        .join(UserAgent, Workflow.agent_id == UserAgent.id)
        .where(Workflow.id == workflow_id, UserAgent.user_id == user_id)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Воркфлоу не найден")
    return wf

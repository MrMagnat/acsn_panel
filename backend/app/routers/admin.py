from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import Optional

from ..core.db import get_db
from ..core.deps import get_current_admin
from ..models.user import User
from ..models.subscription import Subscription
from ..models.agent import UserAgent
from ..models.agent_tool import AgentTool
from ..models.tool import Tool, ToolField
from ..models.template_agent import TemplateAgent, TemplateAgentTool
from ..models.energy_transaction import EnergyTransaction
from ..schemas.admin import AdminUserResponse, AdminUserUpdate
from ..schemas.tool import ToolCreate, ToolUpdate, ToolResponse
from ..schemas.template_agent import TemplateAgentCreate, TemplateAgentUpdate, TemplateAgentResponse
from pydantic import BaseModel
from datetime import datetime


class EnergyAdjust(BaseModel):
    amount: int          # >0 начислить, <0 списать
    description: str = ""


class EnergyTransactionResponse(BaseModel):
    id: str
    amount: int
    description: str
    agent_id: str | None
    tool_name: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class UserEnergyResponse(BaseModel):
    energy_left: int
    energy_per_week: int
    transactions: list[EnergyTransactionResponse]

router = APIRouter(prefix="/admin", tags=["Администрирование"])


# ─── Пользователи ────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    plan: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Список всех пользователей с информацией о подписке и агентах."""
    query = (
        select(User)
        .options(selectinload(User.subscription), selectinload(User.agents).selectinload(UserAgent.agent_tools))
        .order_by(User.created_at.desc())
    )
    result = await db.execute(query)
    users = result.scalars().all()

    response = []
    for user in users:
        sub = user.subscription
        if plan and sub and sub.plan != plan:
            continue
        agents_count = len(user.agents)
        tools_count = sum(len(a.agent_tools) for a in user.agents)
        response.append(AdminUserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            is_admin=user.is_admin,
            created_at=user.created_at,
            plan=sub.plan if sub else "free",
            agents_count=agents_count,
            tools_count=tools_count,
            ascn_user_id=user.ascn_user_id,
            telegram=user.telegram,
            phone=user.phone,
            avatar_url=user.avatar_url,
        ))
    return response


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Обновить пользователя."""
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.subscription), selectinload(User.agents).selectinload(UserAgent.agent_tools))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if data.name is not None:
        user.name = data.name
    if data.is_admin is not None:
        user.is_admin = data.is_admin

    await db.flush()

    sub = user.subscription
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_admin=user.is_admin,
        created_at=user.created_at,
        plan=sub.plan if sub else "free",
        agents_count=len(user.agents),
        tools_count=sum(len(a.agent_tools) for a in user.agents),
        ascn_user_id=user.ascn_user_id,
        telegram=user.telegram,
        phone=user.phone,
        avatar_url=user.avatar_url,
    )


# ─── Энергия пользователей ───────────────────────────────────────────────────

@router.get("/users/{user_id}/energy", response_model=UserEnergyResponse)
async def get_user_energy(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Баланс энергии и история транзакций пользователя."""
    sub = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = sub.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    txs = await db.execute(
        select(EnergyTransaction)
        .where(EnergyTransaction.user_id == user_id)
        .order_by(EnergyTransaction.created_at.desc())
        .limit(50)
    )
    return UserEnergyResponse(
        energy_left=subscription.energy_left,
        energy_per_week=subscription.energy_per_week,
        transactions=txs.scalars().all(),
    )


@router.post("/users/{user_id}/energy", response_model=UserEnergyResponse)
async def adjust_user_energy(
    user_id: str,
    data: EnergyAdjust,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Начислить или списать энергию пользователю."""
    sub = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = sub.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    subscription.energy_left = max(0, subscription.energy_left + data.amount)

    label = "Начисление" if data.amount > 0 else "Списание"
    desc = data.description or f"{label} администратором"
    db.add(EnergyTransaction(
        user_id=user_id,
        amount=data.amount,
        description=desc,
    ))
    await db.flush()

    txs = await db.execute(
        select(EnergyTransaction)
        .where(EnergyTransaction.user_id == user_id)
        .order_by(EnergyTransaction.created_at.desc())
        .limit(50)
    )
    return UserEnergyResponse(
        energy_left=subscription.energy_left,
        energy_per_week=subscription.energy_per_week,
        transactions=txs.scalars().all(),
    )


# ─── Шаблонные агенты ────────────────────────────────────────────────────────

@router.get("/template-agents", response_model=list[TemplateAgentResponse])
async def list_template_agents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Список всех шаблонных агентов."""
    result = await db.execute(
        select(TemplateAgent)
        .options(selectinload(TemplateAgent.template_tools).selectinload(TemplateAgentTool.tool).selectinload(Tool.fields))
        .order_by(TemplateAgent.name)
    )
    templates = result.scalars().all()
    return [_template_to_response(t) for t in templates]


@router.post("/template-agents", response_model=TemplateAgentResponse, status_code=201)
async def create_template_agent(
    data: TemplateAgentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Создать шаблонный агент."""
    template = TemplateAgent(
        name=data.name,
        description=data.description,
        llm_url=data.llm_url,
        llm_model=data.llm_model,
        llm_token=data.llm_token,
        prompt=data.prompt,
        skills=data.skills,
        energy_per_chat=data.energy_per_chat,
        is_active=data.is_active,
    )
    db.add(template)
    await db.flush()

    await _sync_template_tools(template.id, data.tool_ids, db)
    return _template_to_response(await _get_template(template.id, db))


@router.get("/template-agents/{template_id}", response_model=TemplateAgentResponse)
async def get_template_agent(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Детали шаблонного агента."""
    template = await _get_template(template_id, db)
    return _template_to_response(template)


@router.patch("/template-agents/{template_id}", response_model=TemplateAgentResponse)
async def update_template_agent(
    template_id: str,
    data: TemplateAgentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Обновить шаблонный агент."""
    template = await _get_template(template_id, db)

    for field, value in data.model_dump(exclude_none=True, exclude={"tool_ids"}).items():
        setattr(template, field, value)

    if data.tool_ids is not None:
        await _sync_template_tools(template_id, data.tool_ids, db)

    await db.flush()
    return _template_to_response(await _get_template(template_id, db))


@router.delete("/template-agents/{template_id}", status_code=204)
async def delete_template_agent(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Удалить шаблонный агент."""
    template = await _get_template(template_id, db)
    await db.delete(template)


# ─── Инструменты ─────────────────────────────────────────────────────────────

@router.get("/tools", response_model=list[ToolResponse])
async def list_tools(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Список всех инструментов."""
    result = await db.execute(
        select(Tool).options(selectinload(Tool.fields)).order_by(Tool.name)
    )
    return result.scalars().all()


@router.post("/tools", response_model=ToolResponse, status_code=201)
async def create_tool(
    data: ToolCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Создать инструмент."""
    tool = Tool(
        name=data.name,
        description=data.description,
        trigger_hint=data.trigger_hint,
        webhook_url=data.webhook_url,
        is_active=data.is_active,
        energy_cost=data.energy_cost,
    )
    db.add(tool)
    await db.flush()

    for i, field_data in enumerate(data.fields):
        field = ToolField(tool_id=tool.id, **{**field_data.model_dump(), "sort_order": i})
        db.add(field)

    await db.flush()
    await db.refresh(tool, ["fields"])
    return tool


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Детали инструмента."""
    return await _get_tool(tool_id, db)


@router.patch("/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    data: ToolUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Обновить инструмент."""
    tool = await _get_tool(tool_id, db)

    for field, value in data.model_dump(exclude_none=True, exclude={"fields"}).items():
        setattr(tool, field, value)

    # Если пришли поля — полностью заменяем список
    if data.fields is not None:
        await db.execute(delete(ToolField).where(ToolField.tool_id == tool_id))
        for i, field_data in enumerate(data.fields):
            field = ToolField(tool_id=tool_id, **{**field_data.model_dump(), "sort_order": i})
            db.add(field)

    await db.flush()
    await db.refresh(tool, ["fields"])
    return tool


@router.delete("/tools/{tool_id}", status_code=204)
async def delete_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Удалить инструмент."""
    tool = await _get_tool(tool_id, db)
    await db.delete(tool)


# ─── Вспомогательные функции ─────────────────────────────────────────────────

async def _get_template(template_id: str, db: AsyncSession) -> TemplateAgent:
    result = await db.execute(
        select(TemplateAgent)
        .where(TemplateAgent.id == template_id)
        .options(selectinload(TemplateAgent.template_tools).selectinload(TemplateAgentTool.tool).selectinload(Tool.fields))
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон не найден")
    return template


async def _get_tool(tool_id: str, db: AsyncSession) -> Tool:
    result = await db.execute(
        select(Tool).where(Tool.id == tool_id).options(selectinload(Tool.fields))
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инструмент не найден")
    return tool


async def _sync_template_tools(template_id: str, tool_ids: list[str], db: AsyncSession) -> None:
    """Синхронизируем инструменты шаблона: удаляем старые, добавляем новые."""
    await db.execute(delete(TemplateAgentTool).where(TemplateAgentTool.template_id == template_id))
    for tool_id in tool_ids:
        db.add(TemplateAgentTool(template_id=template_id, tool_id=tool_id))
    await db.flush()


def _template_to_response(template: TemplateAgent) -> TemplateAgentResponse:
    """Конвертируем шаблон в схему ответа."""
    tools = [tt.tool for tt in template.template_tools if tt.tool]
    return TemplateAgentResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        llm_url=template.llm_url,
        llm_model=template.llm_model,
        llm_token=template.llm_token,
        prompt=template.prompt,
        skills=template.skills,
        energy_per_chat=template.energy_per_chat,
        is_active=template.is_active,
        tools=tools,
    )

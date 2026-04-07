from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.deps import get_current_user
from ..services import agent_service
from ..schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentListItem,
    AddToolToAgent, UpdateToolFields, AgentToolResponse,
)
from ..models.user import User

router = APIRouter(prefix="/agents", tags=["Агенты"])


@router.get("", response_model=list[AgentListItem])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список агентов текущего пользователя."""
    agents = await agent_service.get_user_agents(current_user.id, db)
    return [
        AgentListItem(
            id=a.id,
            name=a.name,
            is_active=a.is_active,
            energy_left=a.energy_left,
            tools_count=len(a.agent_tools),
        )
        for a in agents
    ]


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать нового агента."""
    return await agent_service.create_agent(current_user.id, data, db)


@router.post("/from-template/{template_id}", response_model=AgentResponse, status_code=201)
async def create_from_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать агента из шаблона."""
    return await agent_service.create_agent_from_template(current_user.id, template_id, db)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Детали агента."""
    return await agent_service.get_agent_by_id(agent_id, current_user.id, db)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить агента."""
    return await agent_service.update_agent(agent_id, current_user.id, data, db)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить агента."""
    await agent_service.delete_agent(agent_id, current_user.id, db)


@router.post("/{agent_id}/tools", response_model=AgentToolResponse, status_code=201)
async def add_tool(
    agent_id: str,
    data: AddToolToAgent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Добавить инструмент агенту."""
    return await agent_service.add_tool_to_agent(agent_id, current_user.id, data.tool_id, db)


@router.delete("/{agent_id}/tools/{tool_id}", status_code=204)
async def remove_tool(
    agent_id: str,
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить инструмент у агента."""
    await agent_service.remove_tool_from_agent(agent_id, current_user.id, tool_id, db)


@router.post("/{agent_id}/tools/{tool_id}/run")
async def run_tool(
    agent_id: str,
    tool_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запустить инструмент вручную — вызвать его webhook с сохранёнными полями."""
    base_url = _public_base_url(request)
    return await agent_service.run_tool_manually(agent_id, current_user.id, tool_id, db, base_url=base_url)


def _public_base_url(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto", "http")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost:8000")
    return f"{proto}://{host}/api"


@router.patch("/{agent_id}/tools/{tool_id}", response_model=AgentToolResponse)
async def update_tool_fields(
    agent_id: str,
    tool_id: str,
    data: UpdateToolFields,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить настройки полей инструмента у агента."""
    return await agent_service.update_tool_fields(agent_id, current_user.id, tool_id, data, db)

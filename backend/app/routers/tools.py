from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.tool import Tool
from ..models.template_agent import TemplateAgent, TemplateAgentTool
from ..models.user import User
from ..schemas.tool import ToolResponse
from ..schemas.template_agent import TemplateAgentResponse
from ..services import agent_service

router = APIRouter(prefix="/tools", tags=["Магазин инструментов"])


class StandaloneRunRequest(BaseModel):
    field_values: dict = {}


@router.get("", response_model=list[ToolResponse])
async def list_tools(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Магазин инструментов — список всех активных инструментов."""
    result = await db.execute(
        select(Tool)
        .where(Tool.is_active == True)
        .options(selectinload(Tool.fields))
        .order_by(Tool.name)
    )
    return result.scalars().all()


@router.get("/template-agents", response_model=list[TemplateAgentResponse])
async def list_active_template_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Публичный список активных шаблонных агентов (для всех авторизованных пользователей)."""
    result = await db.execute(
        select(TemplateAgent)
        .where(TemplateAgent.is_active == True)
        .options(
            selectinload(TemplateAgent.template_tools)
            .selectinload(TemplateAgentTool.tool)
            .selectinload(Tool.fields)
        )
        .order_by(TemplateAgent.name)
    )
    templates = result.scalars().all()
    return [
        TemplateAgentResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            llm_url=t.llm_url,
            prompt=t.prompt,
            skills=t.skills,
            energy_per_chat=t.energy_per_chat,
            is_active=t.is_active,
            tools=[tt.tool for tt in t.template_tools if tt.tool],
        )
        for t in templates
    ]


@router.post("/{tool_id}/run")
async def run_tool_standalone(
    tool_id: str,
    data: StandaloneRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запустить инструмент напрямую из магазина без агента."""
    return await agent_service.run_tool_standalone(current_user.id, tool_id, data.field_values, db)

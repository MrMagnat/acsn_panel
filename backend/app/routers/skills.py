from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.skill import Skill, AgentSkill
from ..models.agent import UserAgent
from ..schemas.skill import SkillResponse, AgentSkillResponse

router = APIRouter(tags=["Скиллы"])


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Каталог всех активных скиллов."""
    result = await db.execute(
        select(Skill)
        .where(Skill.is_active == True)
        .order_by(Skill.sort_order, Skill.name)
    )
    return result.scalars().all()


@router.post("/agents/{agent_id}/skills/{skill_id}", response_model=AgentSkillResponse, status_code=201)
async def add_skill_to_agent(
    agent_id: str,
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Добавить скилл агенту."""
    # Проверяем агента
    agent = (await db.execute(
        select(UserAgent).where(UserAgent.id == agent_id, UserAgent.user_id == current_user.id)
    )).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")

    # Проверяем скилл
    skill = (await db.execute(select(Skill).where(Skill.id == skill_id))).scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Скилл не найден")

    # Не добавляем дубли
    existing = (await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id, AgentSkill.skill_id == skill_id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Скилл уже добавлен")

    agent_skill = AgentSkill(agent_id=agent_id, skill_id=skill_id)
    db.add(agent_skill)
    await db.flush()
    await db.refresh(agent_skill, ["skill"])
    return agent_skill


@router.delete("/agents/{agent_id}/skills/{skill_id}", status_code=204)
async def remove_skill_from_agent(
    agent_id: str,
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удалить скилл у агента."""
    # Проверяем агента
    agent = (await db.execute(
        select(UserAgent).where(UserAgent.id == agent_id, UserAgent.user_id == current_user.id)
    )).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")

    agent_skill = (await db.execute(
        select(AgentSkill).where(AgentSkill.agent_id == agent_id, AgentSkill.skill_id == skill_id)
    )).scalar_one_or_none()
    if not agent_skill:
        raise HTTPException(status_code=404, detail="Скилл не найден у агента")

    await db.delete(agent_skill)

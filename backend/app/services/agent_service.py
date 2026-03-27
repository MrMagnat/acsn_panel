from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from ..models.agent import UserAgent
from ..models.agent_tool import AgentTool
from ..models.tool import Tool, ToolField
from ..models.subscription import Subscription
from ..models.template_agent import TemplateAgent, TemplateAgentTool
from ..models.energy_transaction import EnergyTransaction
from ..models.tool_run_log import ToolRunLog
from ..models.trigger import AutoTrigger
from ..schemas.agent import AgentCreate, AgentUpdate, UpdateToolFields


async def get_user_agents(user_id: str, db: AsyncSession) -> list[UserAgent]:
    """Получаем список агентов пользователя с количеством инструментов."""
    result = await db.execute(
        select(UserAgent)
        .where(UserAgent.user_id == user_id)
        .options(selectinload(UserAgent.agent_tools).selectinload(AgentTool.tool).selectinload(Tool.fields))
        .order_by(UserAgent.created_at)
    )
    return result.scalars().all()


async def get_agent_by_id(agent_id: str, user_id: str, db: AsyncSession) -> UserAgent:
    """Получаем агента по ID, проверяем принадлежность пользователю."""
    result = await db.execute(
        select(UserAgent)
        .where(UserAgent.id == agent_id, UserAgent.user_id == user_id)
        .options(
            selectinload(UserAgent.agent_tools).selectinload(AgentTool.tool).selectinload(Tool.fields),
            selectinload(UserAgent.auto_triggers).selectinload(AutoTrigger.tool),
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Агент не найден")
    return agent


async def create_agent(user_id: str, data: AgentCreate, db: AsyncSession) -> UserAgent:
    """Создаём нового агента, проверяя лимит подписки."""
    # Получаем подписку пользователя
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Подписка не найдена")

    # Проверяем лимит агентов
    count_result = await db.execute(
        select(func.count()).where(UserAgent.user_id == user_id)
    )
    agents_count = count_result.scalar()
    if agents_count >= subscription.max_agents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Лимит агентов для вашей подписки ({subscription.max_agents}) достигнут",
        )

    # Создаём агента
    agent = UserAgent(
        user_id=user_id,
        name=data.name,
        description=data.description,
        energy_left=subscription.energy_per_week,
    )
    db.add(agent)
    await db.flush()

    # Добавляем инструменты если указаны
    if data.tool_ids:
        await _add_tools_to_agent(agent, data.tool_ids, subscription.max_tools_per_agent, db)

    # Перезагружаем агента со всеми связями для корректной сериализации
    await db.flush()
    return await get_agent_by_id(agent.id, user_id, db)


async def create_agent_from_template(user_id: str, template_id: str, db: AsyncSession) -> UserAgent:
    """Создаём агента из шаблона со всеми инструментами шаблона."""
    # Получаем шаблон
    result = await db.execute(
        select(TemplateAgent)
        .where(TemplateAgent.id == template_id, TemplateAgent.is_active == True)
        .options(selectinload(TemplateAgent.template_tools).selectinload(TemplateAgentTool.tool))
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон не найден")

    # Проверяем лимит подписки
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = sub_result.scalar_one_or_none()

    count_result = await db.execute(select(func.count()).where(UserAgent.user_id == user_id))
    if count_result.scalar() >= subscription.max_agents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Лимит агентов достигнут",
        )

    # Создаём агента из шаблона
    agent = UserAgent(
        user_id=user_id,
        name=template.name,
        description=template.description,
        llm_url=template.llm_url,
        llm_model=template.llm_model,
        llm_token=template.llm_token,
        prompt=template.prompt,
        skills=template.skills,
        energy_per_chat=template.energy_per_chat,
        energy_left=subscription.energy_per_week,
    )
    db.add(agent)
    await db.flush()

    # Добавляем инструменты из шаблона (не больше лимита)
    tool_ids = [tt.tool_id for tt in template.template_tools]
    if tool_ids:
        await _add_tools_to_agent(agent, tool_ids, subscription.max_tools_per_agent, db)

    # Перезагружаем агента со всеми связями для корректной сериализации
    await db.flush()
    return await get_agent_by_id(agent.id, user_id, db)


async def update_agent(agent_id: str, user_id: str, data: AgentUpdate, db: AsyncSession) -> UserAgent:
    """Обновляем поля агента."""
    agent = await get_agent_by_id(agent_id, user_id, db)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(agent, field, value)

    await db.flush()
    # Возвращаем с перезагрузкой чтобы все связи были доступны
    return await get_agent_by_id(agent_id, user_id, db)


async def delete_agent(agent_id: str, user_id: str, db: AsyncSession) -> None:
    """Удаляем агента пользователя и снимаем его триггеры с планировщика."""
    from ..services.scheduler_service import unschedule_trigger

    agent = await get_agent_by_id(agent_id, user_id, db)

    # Снимаем все триггеры агента с планировщика (до удаления из БД)
    for trigger in agent.auto_triggers:
        unschedule_trigger(trigger.id)

    await db.delete(agent)


async def add_tool_to_agent(agent_id: str, user_id: str, tool_id: str, db: AsyncSession) -> AgentTool:
    """Добавляем инструмент агенту, проверяя лимит подписки."""
    agent = await get_agent_by_id(agent_id, user_id, db)

    # Получаем лимит из подписки
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = sub_result.scalar_one_or_none()

    # Считаем текущее количество инструментов
    current_tools = len(agent.agent_tools)
    if current_tools >= subscription.max_tools_per_agent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Лимит инструментов ({subscription.max_tools_per_agent}) достигнут. Улучшите подписку.",
        )

    # Проверяем, что инструмент существует и активен
    tool_result = await db.execute(select(Tool).where(Tool.id == tool_id, Tool.is_active == True))
    tool = tool_result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инструмент не найден")

    # Проверяем, что инструмент ещё не добавлен
    existing = await db.execute(
        select(AgentTool).where(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Инструмент уже добавлен")

    agent_tool = AgentTool(agent_id=agent_id, tool_id=tool_id)
    db.add(agent_tool)
    await db.flush()

    # Перезагружаем со всеми вложенными связями (tool + tool.fields)
    result = await db.execute(
        select(AgentTool)
        .where(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id)
        .options(selectinload(AgentTool.tool).selectinload(Tool.fields))
    )
    return result.scalar_one()


async def remove_tool_from_agent(agent_id: str, user_id: str, tool_id: str, db: AsyncSession) -> None:
    """Удаляем инструмент у агента."""
    # Проверяем права доступа
    await get_agent_by_id(agent_id, user_id, db)

    result = await db.execute(
        select(AgentTool).where(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id)
    )
    agent_tool = result.scalar_one_or_none()
    if not agent_tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инструмент не найден у агента")

    await db.delete(agent_tool)


async def update_tool_fields(
    agent_id: str, user_id: str, tool_id: str, data: UpdateToolFields, db: AsyncSession
) -> AgentTool:
    """Обновляем значения полей инструмента и пересчитываем is_configured."""
    # Проверяем права
    await get_agent_by_id(agent_id, user_id, db)

    result = await db.execute(
        select(AgentTool)
        .where(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id)
        .options(selectinload(AgentTool.tool).selectinload(Tool.fields))
    )
    agent_tool = result.scalar_one_or_none()
    if not agent_tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инструмент не найден у агента")

    agent_tool.field_values = data.field_values

    # Пересчитываем is_configured: все required поля должны быть заполнены
    required_fields = [f.field_name for f in agent_tool.tool.fields if f.required]
    agent_tool.is_configured = all(
        data.field_values.get(fname) for fname in required_fields
    )

    await db.flush()

    # Перезагружаем со всеми вложенными связями
    result = await db.execute(
        select(AgentTool)
        .where(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id)
        .options(selectinload(AgentTool.tool).selectinload(Tool.fields))
    )
    return result.scalar_one()


async def run_tool_manually(agent_id: str, user_id: str, tool_id: str, db: AsyncSession) -> dict:
    """Ручной запуск инструмента — вызываем webhook с сохранёнными field_values."""
    import httpx
    from sqlalchemy import update as sa_update

    # Проверяем права и загружаем agent_tool
    await get_agent_by_id(agent_id, user_id, db)

    result = await db.execute(
        select(AgentTool)
        .where(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id)
        .options(selectinload(AgentTool.tool).selectinload(Tool.fields))
    )
    agent_tool = result.scalar_one_or_none()
    if not agent_tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Инструмент не найден у агента")

    tool = agent_tool.tool
    energy_cost = tool.energy_cost

    # Проверяем и списываем энергию с аккаунта
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = sub_result.scalar_one_or_none()
    if not subscription or subscription.energy_left < energy_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Недостаточно энергии для запуска инструмента",
        )

    upd = await db.execute(
        sa_update(Subscription)
        .where(Subscription.id == subscription.id, Subscription.energy_left >= energy_cost)
        .values(energy_left=Subscription.energy_left - energy_cost)
        .returning(Subscription.energy_left)
    )
    row = upd.fetchone()
    energy_left_after = row[0] if row else subscription.energy_left

    db.add(EnergyTransaction(
        user_id=user_id,
        amount=-energy_cost,
        description=f"Ручной запуск: {tool.name}",
        agent_id=agent_id,
        tool_name=tool.name,
    ))

    # Создаём лог запуска заранее
    run_log = ToolRunLog(
        agent_id=agent_id,
        user_id=user_id,
        tool_id=tool_id,
        tool_name=tool.name,
        trigger_type="manual",
        status="running",
    )
    db.add(run_log)
    await db.flush()  # получаем run_log.id

    # По умолчанию instance_id = log_id, чтобы n8n мог вернуть его обратно
    run_log.instance_id = str(run_log.id)

    payload = {
        "fields": agent_tool.field_values or {},
        "args": {},
        "agent_id": agent_id,
        "user_id": user_id,
        "log_id": str(run_log.id),
        "instance_id": str(run_log.id),  # n8n должен вернуть это в callback
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(tool.webhook_url, json=payload)
            response.raise_for_status()
            webhook_data = response.json()

        # Сохраняем instanceId если вернулся (асинхронный webhook)
        instance_id = webhook_data.get("instanceId") or webhook_data.get("instance_id")
        if instance_id:
            run_log.instance_id = instance_id
            # Оставляем status="running" — результат придёт через callback
        else:
            # Синхронный webhook — результат уже здесь
            import json as _json
            run_log.status = "success"
            run_log.result_json = _json.dumps(webhook_data, ensure_ascii=False)
            from datetime import datetime, timezone
            run_log.finished_at = datetime.now(timezone.utc)

        await db.flush()
        return {
            "status": "ok",
            "log_id": run_log.id,
            "instance_id": instance_id,
            "energy_left": energy_left_after,
        }
    except httpx.TimeoutException:
        import json as _json
        run_log.status = "error"
        run_log.result_json = _json.dumps({"error": "Инструмент не ответил (таймаут 30 сек)"})
        from datetime import datetime, timezone
        run_log.finished_at = datetime.now(timezone.utc)
        await db.flush()
        return {"status": "error", "log_id": run_log.id, "result": "Таймаут", "energy_left": energy_left_after}
    except Exception as e:
        import json as _json
        run_log.status = "error"
        run_log.result_json = _json.dumps({"error": str(e)})
        from datetime import datetime, timezone
        run_log.finished_at = datetime.now(timezone.utc)
        await db.flush()
        return {"status": "error", "log_id": run_log.id, "result": str(e), "energy_left": energy_left_after}


async def _add_tools_to_agent(
    agent: UserAgent, tool_ids: list[str], max_tools: int, db: AsyncSession
) -> None:
    """Вспомогательная функция для массового добавления инструментов."""
    tools_to_add = tool_ids[:max_tools]
    for tool_id in tools_to_add:
        tool_result = await db.execute(select(Tool).where(Tool.id == tool_id, Tool.is_active == True))
        if tool_result.scalar_one_or_none():
            db.add(AgentTool(agent_id=agent.id, tool_id=tool_id))

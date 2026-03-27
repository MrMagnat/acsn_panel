"""
Сервис автозапусков инструментов по расписанию.
Использует APScheduler с хранением задач в PostgreSQL для персистентности при рестартах.
"""
import httpx
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..models.trigger import AutoTrigger
from ..models.agent import UserAgent
from ..models.agent_tool import AgentTool
from ..models.tool import Tool
from ..models.subscription import Subscription
from ..models.energy_transaction import EnergyTransaction
from ..models.tool_run_log import ToolRunLog
from ..core.config import settings

logger = logging.getLogger(__name__)

# Глобальный экземпляр планировщика
scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Получаем или создаём экземпляр планировщика (MemoryJobStore — задачи загружаются из БД при старте)."""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


def start_scheduler():
    """Запускаем планировщик."""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("Планировщик автозапусков запущен")


def stop_scheduler():
    """Останавливаем планировщик."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Планировщик автозапусков остановлен")


def schedule_trigger(trigger: AutoTrigger) -> None:
    """Добавляем или обновляем задачу в планировщике."""
    sched = get_scheduler()
    job_id = f"trigger_{trigger.id}"

    # Удаляем существующую задачу если есть
    if sched.get_job(job_id):
        sched.remove_job(job_id)

    if not trigger.is_active:
        return

    try:
        # Парсим cron-выражение (формат: "минута час день_месяца месяц день_недели")
        parts = trigger.cron_expr.split()
        if len(parts) != 5:
            logger.warning(f"Неверный формат cron для триггера {trigger.id}: {trigger.cron_expr}")
            return

        cron_trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )

        sched.add_job(
            func=execute_trigger,
            trigger=cron_trigger,
            args=[trigger.id, trigger.agent_id, trigger.tool_id],
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Триггер {trigger.id} запланирован: {trigger.cron_expr}")
    except Exception as e:
        logger.error(f"Ошибка планирования триггера {trigger.id}: {e}")


def unschedule_trigger(trigger_id: str) -> None:
    """Удаляем задачу из планировщика."""
    sched = get_scheduler()
    job_id = f"trigger_{trigger_id}"
    if sched.get_job(job_id):
        sched.remove_job(job_id)
        logger.info(f"Триггер {trigger_id} удалён из планировщика")


async def execute_trigger(trigger_id: str, agent_id: str, tool_id: str) -> None:
    """Выполняем триггер: вызываем webhook инструмента."""
    from ..core.db import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            # Загружаем агент и инструмент
            agent_result = await db.execute(
                select(UserAgent)
                .where(UserAgent.id == agent_id, UserAgent.is_active == True)
            )
            agent = agent_result.scalar_one_or_none()
            if not agent:
                logger.warning(f"Триггер {trigger_id}: агент {agent_id} не найден или неактивен")
                return

            at_result = await db.execute(
                select(AgentTool)
                .where(AgentTool.agent_id == agent_id, AgentTool.tool_id == tool_id, AgentTool.is_configured == True)
                .options(selectinload(AgentTool.tool))
            )
            agent_tool = at_result.scalar_one_or_none()
            if not agent_tool:
                logger.warning(f"Триггер {trigger_id}: инструмент {tool_id} не настроен")
                return

            # Загружаем подписку и списываем энергию с аккаунта
            energy_cost = agent_tool.tool.energy_cost
            sub_result = await db.execute(
                select(Subscription).where(Subscription.user_id == agent.user_id)
            )
            subscription = sub_result.scalar_one_or_none()
            if not subscription or subscription.energy_left < energy_cost:
                logger.warning(f"Триггер {trigger_id}: недостаточно энергии у пользователя {agent.user_id}")
                return

            upd = await db.execute(
                update(Subscription)
                .where(Subscription.id == subscription.id, Subscription.energy_left >= energy_cost)
                .values(energy_left=Subscription.energy_left - energy_cost)
            )
            if upd.rowcount == 0:
                logger.warning(f"Триггер {trigger_id}: не удалось списать энергию (race condition)")
                return

            db.add(EnergyTransaction(
                user_id=agent.user_id,
                amount=-energy_cost,
                description=f"Автозапуск: {agent_tool.tool.name}",
                agent_id=agent_id,
                tool_name=agent_tool.tool.name,
            ))

            # Создаём лог запуска
            run_log = ToolRunLog(
                agent_id=agent_id,
                user_id=agent.user_id,
                tool_id=tool_id,
                tool_name=agent_tool.tool.name,
                trigger_type="auto",
                status="running",
            )
            db.add(run_log)
            await db.flush()  # получаем run_log.id
            run_log.instance_id = str(run_log.id)

            # Вызываем webhook
            payload = {
                "fields": agent_tool.field_values,
                "args": {},
                "agent_id": agent_id,
                "user_id": agent.user_id,
                "trigger_id": trigger_id,
                "log_id": str(run_log.id),
                "instance_id": str(run_log.id),
            }

            import json as _json
            from datetime import datetime, timezone

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(agent_tool.tool.webhook_url, json=payload)
                    response.raise_for_status()
                    webhook_data = response.json()

                # Если вернулся instanceId — результат придёт через callback
                instance_id = webhook_data.get("instanceId") or webhook_data.get("instance_id")
                if instance_id:
                    run_log.instance_id = instance_id
                    # status остаётся "running"
                else:
                    run_log.status = "success"
                    run_log.result_json = _json.dumps(webhook_data, ensure_ascii=False)
                    run_log.finished_at = datetime.now(timezone.utc)

            except Exception as webhook_err:
                run_log.status = "error"
                run_log.result_json = _json.dumps({"error": str(webhook_err)}, ensure_ascii=False)
                run_log.finished_at = datetime.now(timezone.utc)
                logger.error(f"Триггер {trigger_id}: ошибка webhook: {webhook_err}")

            await db.commit()
            logger.info(f"Триггер {trigger_id} выполнен, лог: {run_log.id}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка выполнения триггера {trigger_id}: {e}")


async def refresh_energy_weekly(db: AsyncSession) -> None:
    """Обновляем энергию всех агентов до weekly лимита из подписки."""
    from ..models.subscription import Subscription

    logger.info("Запуск еженедельного обновления энергии...")

    # Загружаем всех пользователей с подписками и агентами
    result = await db.execute(select(Subscription))
    subscriptions = result.scalars().all()

    for sub in subscriptions:
        await db.execute(
            update(UserAgent)
            .where(UserAgent.user_id == sub.user_id)
            .values(energy_left=sub.energy_per_week)
        )

    await db.commit()
    logger.info("Энергия обновлена для всех пользователей")

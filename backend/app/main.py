from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.db import AsyncSessionLocal
from .routers import auth, agents, tools, chat, triggers, admin, webhooks, subscription, run_logs
from .services.scheduler_service import start_scheduler, stop_scheduler, get_scheduler, schedule_trigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from .models.trigger import AutoTrigger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запуск и остановка фоновых сервисов."""
    # Запускаем планировщик автозапусков
    start_scheduler()

    # Добавляем задачу еженедельного обновления энергии (каждое воскресенье в 00:00 UTC)
    sched = get_scheduler()
    sched.add_job(
        func=_weekly_energy_refresh,
        trigger=CronTrigger(day_of_week="sun", hour=0, minute=0),
        id="weekly_energy_refresh",
        replace_existing=True,
    )

    # Загружаем все активные триггеры из БД при старте
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AutoTrigger).where(AutoTrigger.is_active == True)
        )
        for trigger in result.scalars().all():
            schedule_trigger(trigger)

    yield

    # Останавливаем планировщик при завершении
    stop_scheduler()


async def _weekly_energy_refresh():
    """Обёртка для запуска через планировщик."""
    async with AsyncSessionLocal() as db:
        from .services.scheduler_service import refresh_energy_weekly
        await refresh_energy_weekly(db)


app = FastAPI(
    title="ASCN AI Platform API",
    description="Платформа для управления ИИ-агентами и инструментами",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — разрешаем запросы от фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://85.193.84.93",
        "https://85.193.84.93",
        "https://businesspanel.ru",
        "https://www.businesspanel.ru",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(tools.router)
app.include_router(chat.router)
app.include_router(triggers.router)
app.include_router(admin.router)
app.include_router(webhooks.router)
app.include_router(subscription.router)
app.include_router(run_logs.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

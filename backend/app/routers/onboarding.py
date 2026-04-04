import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.db import get_db
from ..models.setting import Setting

router = APIRouter(prefix="/onboarding", tags=["Онбординг"])

DEFAULT_CONFIG = {
    "enabled": True,
    "video_url": "",
    "support_url": "https://t.me/ascnai_nocode",
    "steps": [
        {
            "id": "welcome",
            "element": "",
            "route": "/cabinet/office",
            "title": "Добро пожаловать в ASCN! 👋",
            "description": "За <strong>2–3 минуты</strong> вы узнаете всё необходимое, чтобы получать первые результаты от ваших ИИ-агентов.",
            "image_url": "",
            "side": "over"
        },
        {
            "id": "nav-office",
            "element": "#nav-office",
            "route": "/cabinet/office",
            "title": "Мой офис",
            "description": "Это ваш главный экран. Здесь собраны все ваши ИИ-агенты — каждый заточен под конкретную задачу.",
            "image_url": "",
            "side": "right"
        },
        {
            "id": "agent-list",
            "element": "#agent-list",
            "route": "/cabinet/office",
            "title": "Ваши агенты",
            "description": "Каждый агент — это ИИ с набором инструментов. Нажмите на карточку агента, чтобы открыть чат и поставить ему задачу.",
            "image_url": "",
            "side": "top"
        },
        {
            "id": "add-agent",
            "element": "#add-agent-btn",
            "route": "/cabinet/office",
            "title": "Создать нового агента",
            "description": "Нажмите «+», чтобы создать агента. Задайте имя, выберите ИИ-модель и добавьте инструменты — агент готов за минуту.",
            "image_url": "",
            "side": "top"
        },
        {
            "id": "nav-tools",
            "element": "#nav-tools",
            "route": "/cabinet/office",
            "title": "Инструменты",
            "description": "Инструменты — это конкретные действия: отправить запрос, обработать данные, сгенерировать контент. Агент вызывает их автоматически при необходимости.",
            "image_url": "",
            "side": "right"
        },
        {
            "id": "tools-grid",
            "element": "#tools-grid",
            "route": "/cabinet/tools",
            "title": "Библиотека инструментов",
            "description": "Все доступные инструменты — здесь. Каждый описан: что делает и сколько стоит токенов. Вы можете запустить любой инструмент вручную — нажмите кнопку «Запустить».",
            "image_url": "",
            "side": "top"
        },
        {
            "id": "nav-history",
            "element": "#nav-history",
            "route": "/cabinet/tools",
            "title": "История запусков",
            "description": "Все результаты работы инструментов сохраняются здесь. Просматривайте их в любое время.",
            "image_url": "",
            "side": "right"
        },
        {
            "id": "user-energy",
            "element": "#user-energy",
            "route": "/cabinet/tools",
            "title": "Токены (энергия)",
            "description": "Каждое использование инструмента расходует токены. Ваш баланс отображается здесь и обновляется каждую неделю.",
            "image_url": "",
            "side": "top"
        },
        {
            "id": "finish",
            "element": "",
            "route": "",
            "title": "Вы готовы к работе! 🎉",
            "description": "Отлично! Теперь вы знаете, как пользоваться платформой. Посмотрите полное видео-руководство или сразу начните работать с агентами.",
            "image_url": "",
            "side": "over"
        }
    ]
}


@router.get("/ascn-models")
async def get_ascn_models(db: AsyncSession = Depends(get_db)):
    """Публичный список ASCN-моделей с ценами (без ключа)."""
    from ..models.setting import Setting
    result = await db.execute(select(Setting).where(Setting.key == "ascn_config"))
    setting = result.scalar_one_or_none()
    if setting and setting.value:
        config = json.loads(setting.value)
        return config.get("models", [])
    return [
        {"id": "openai/gpt-4o-mini",         "name": "GPT-4o mini",      "price_usd": 2},
        {"id": "google/gemini-2.0-flash-001", "name": "Gemini 2.0 Flash", "price_usd": 3},
        {"id": "deepseek/deepseek-r1",        "name": "DeepSeek R1",      "price_usd": 1},
    ]


@router.get("")
async def get_onboarding(db: AsyncSession = Depends(get_db)):
    """Получить конфиг онбординга (публичный эндпоинт)."""
    result = await db.execute(select(Setting).where(Setting.key == "onboarding"))
    setting = result.scalar_one_or_none()
    if setting and setting.value:
        return json.loads(setting.value)
    return DEFAULT_CONFIG

"""
Seed: 4 шаблонных агента + 20 инструментов.
Запуск: python seed_agents.py
"""
import asyncio
import uuid
from app.core.db import AsyncSessionLocal as db_session
from app.models.tool import Tool, ToolField
from app.models.template_agent import TemplateAgent, TemplateAgentTool
from sqlalchemy import select


def uid(): return str(uuid.uuid4())


TOOLS = [
    # ── ТГ-агент ──────────────────────────────────────────────────────────────
    {
        "id": uid(), "name": "ТГ-рассылка",
        "description": "Массовая рассылка сообщений по базе Telegram-аккаунтов или в чаты.",
        "webhook_url": "https://hooks.ascn.ai/tg-broadcast",
        "energy_cost": 15,
        "fields": [
            {"field_name": "api_id", "hint": "API ID из my.telegram.org", "required": True},
            {"field_name": "api_hash", "hint": "API Hash из my.telegram.org", "required": True},
            {"field_name": "session_string", "hint": "Строка сессии Telethon/Pyrogram", "required": True},
        ],
    },
    {
        "id": uid(), "name": "ТГ-шиллер",
        "description": "Автоматически продвигает продукт/канал в тематических чатах Telegram.",
        "webhook_url": "https://hooks.ascn.ai/tg-shiller",
        "energy_cost": 12,
        "fields": [
            {"field_name": "api_id", "hint": "API ID из my.telegram.org", "required": True},
            {"field_name": "api_hash", "hint": "API Hash из my.telegram.org", "required": True},
            {"field_name": "session_string", "hint": "Строка сессии", "required": True},
            {"field_name": "target_chats", "hint": "Ссылки на чаты через запятую", "required": False},
        ],
    },
    {
        "id": uid(), "name": "ТГ-прогрев аккаунта",
        "description": "Прогревает Telegram-аккаунт: подписки, реакции, просмотры для снижения риска бана.",
        "webhook_url": "https://hooks.ascn.ai/tg-warmup",
        "energy_cost": 8,
        "fields": [
            {"field_name": "api_id", "hint": "API ID из my.telegram.org", "required": True},
            {"field_name": "api_hash", "hint": "API Hash из my.telegram.org", "required": True},
            {"field_name": "session_string", "hint": "Строка сессии", "required": True},
        ],
    },
    {
        "id": uid(), "name": "ТГ-продажник",
        "description": "Ведёт диалог с потенциальным клиентом в Telegram, закрывает на покупку.",
        "webhook_url": "https://hooks.ascn.ai/tg-seller",
        "energy_cost": 10,
        "fields": [
            {"field_name": "bot_token", "hint": "Токен бота из @BotFather", "required": True},
            {"field_name": "sales_script", "hint": "Скрипт продаж (URL или текст)", "required": False},
        ],
    },
    {
        "id": uid(), "name": "ТГ-саппорт",
        "description": "Отвечает на вопросы пользователей в Telegram-боте или группе 24/7.",
        "webhook_url": "https://hooks.ascn.ai/tg-support",
        "energy_cost": 8,
        "fields": [
            {"field_name": "bot_token", "hint": "Токен бота из @BotFather", "required": True},
            {"field_name": "knowledge_base_url", "hint": "Ссылка на базу знаний (Google Doc, Notion и т.д.)", "required": False},
        ],
    },
    {
        "id": uid(), "name": "ТГ-контент-завод",
        "description": "Парсит каналы конкурентов и генерирует уникальный контент для вашего канала.",
        "webhook_url": "https://hooks.ascn.ai/tg-content",
        "energy_cost": 20,
        "fields": [
            {"field_name": "bot_token", "hint": "Токен бота для публикации", "required": True},
            {"field_name": "channel_id", "hint": "ID или username вашего канала", "required": True},
            {"field_name": "competitor_channels", "hint": "Каналы конкурентов через запятую (@channel1, @channel2)", "required": True},
        ],
    },

    # ── Инста-агент ───────────────────────────────────────────────────────────
    {
        "id": uid(), "name": "Инста-парсер аккаунтов",
        "description": "Парсит подписчиков, лайки и комментарии целевых Instagram-аккаунтов.",
        "webhook_url": "https://hooks.ascn.ai/insta-parser",
        "energy_cost": 12,
        "fields": [
            {"field_name": "instagram_session", "hint": "Куки-сессия Instagram (sessionid)", "required": True},
            {"field_name": "target_accounts", "hint": "Аккаунты для парсинга через запятую", "required": True},
        ],
    },
    {
        "id": uid(), "name": "Инста-рассылка",
        "description": "Отправляет Direct-сообщения по списку Instagram-пользователей.",
        "webhook_url": "https://hooks.ascn.ai/insta-dm",
        "energy_cost": 15,
        "fields": [
            {"field_name": "instagram_session", "hint": "Куки-сессия Instagram (sessionid)", "required": True},
        ],
    },
    {
        "id": uid(), "name": "Инста-продажник",
        "description": "Ведёт диалог в Direct, отвечает на вопросы и закрывает на продажу.",
        "webhook_url": "https://hooks.ascn.ai/insta-seller",
        "energy_cost": 10,
        "fields": [
            {"field_name": "instagram_session", "hint": "Куки-сессия Instagram (sessionid)", "required": True},
            {"field_name": "sales_script", "hint": "Скрипт продаж", "required": False},
        ],
    },
    {
        "id": uid(), "name": "Инста-контент-завод",
        "description": "Генерирует посты, Reels-сценарии и Stories на основе трендов и конкурентов.",
        "webhook_url": "https://hooks.ascn.ai/insta-content",
        "energy_cost": 18,
        "fields": [
            {"field_name": "instagram_session", "hint": "Куки-сессия Instagram (sessionid)", "required": True},
            {"field_name": "niche", "hint": "Ниша / тема аккаунта", "required": True},
        ],
    },
    {
        "id": uid(), "name": "Инста-генератор видео",
        "description": "Создаёт короткие видео (Reels) по сценарию с помощью ИИ.",
        "webhook_url": "https://hooks.ascn.ai/insta-video",
        "energy_cost": 30,
        "fields": [
            {"field_name": "runway_api_key", "hint": "API-ключ Runway ML или аналогичного сервиса", "required": True},
            {"field_name": "style", "hint": "Стиль видео: cinematic / cartoon / realistic", "required": False},
        ],
    },

    # ── SEO-агент ─────────────────────────────────────────────────────────────
    {
        "id": uid(), "name": "Поиск лёгких взлётов",
        "description": "Находит низкоконкурентные поисковые запросы в нише с высоким потенциалом.",
        "webhook_url": "https://hooks.ascn.ai/seo-quickwins",
        "energy_cost": 15,
        "fields": [
            {"field_name": "dataforseo_login", "hint": "Логин DataForSEO API", "required": True},
            {"field_name": "dataforseo_password", "hint": "Пароль DataForSEO API", "required": True},
            {"field_name": "niche", "hint": "Ниша или seed-keywords через запятую", "required": True},
        ],
    },
    {
        "id": uid(), "name": "SEO-заголовки",
        "description": "Генерирует оптимизированные заголовки (H1, title, description) под ключевые запросы.",
        "webhook_url": "https://hooks.ascn.ai/seo-titles",
        "energy_cost": 8,
        "fields": [
            {"field_name": "target_keyword", "hint": "Основной ключевой запрос", "required": True},
            {"field_name": "language", "hint": "Язык контента: ru / en", "required": False},
        ],
    },
    {
        "id": uid(), "name": "SEO-статья",
        "description": "Пишет полноценную SEO-статью под ключевой запрос с разметкой H1–H3.",
        "webhook_url": "https://hooks.ascn.ai/seo-article",
        "energy_cost": 25,
        "fields": [
            {"field_name": "target_keyword", "hint": "Основной ключевой запрос", "required": True},
            {"field_name": "word_count", "hint": "Желаемый объём статьи в словах (например 1500)", "required": False},
            {"field_name": "language", "hint": "Язык контента: ru / en", "required": False},
        ],
    },
    {
        "id": uid(), "name": "Советы по оптимизации сайта",
        "description": "Анализирует сайт и даёт конкретные рекомендации по SEO-улучшениям.",
        "webhook_url": "https://hooks.ascn.ai/seo-audit",
        "energy_cost": 12,
        "fields": [
            {"field_name": "site_url", "hint": "URL сайта для анализа", "required": True, "field_type": "url"},
        ],
    },
    {
        "id": uid(), "name": "Динамические мета-теги",
        "description": "Автоматически генерирует уникальные title и description для каждой страницы сайта.",
        "webhook_url": "https://hooks.ascn.ai/seo-meta",
        "energy_cost": 10,
        "fields": [
            {"field_name": "site_url", "hint": "URL сайта", "required": True, "field_type": "url"},
            {"field_name": "cms_api_key", "hint": "API-ключ CMS (WordPress, Tilda и т.д.)", "required": False},
        ],
    },

    # ── ИИ-продажник ─────────────────────────────────────────────────────────
    {
        "id": uid(), "name": "Рассылка по холодной базе ТГ",
        "description": "Отправляет персонализированные холодные предложения по базе Telegram-контактов.",
        "webhook_url": "https://hooks.ascn.ai/cold-tg",
        "energy_cost": 15,
        "fields": [
            {"field_name": "api_id", "hint": "API ID из my.telegram.org", "required": True},
            {"field_name": "api_hash", "hint": "API Hash из my.telegram.org", "required": True},
            {"field_name": "session_string", "hint": "Строка сессии", "required": True},
        ],
    },
    {
        "id": uid(), "name": "ИИ-продажник в чате",
        "description": "Общается с клиентом в реальном времени, выявляет потребности и закрывает сделку.",
        "webhook_url": "https://hooks.ascn.ai/ai-seller-chat",
        "energy_cost": 10,
        "fields": [
            {"field_name": "bot_token", "hint": "Токен Telegram-бота", "required": True},
            {"field_name": "crm_webhook", "hint": "Webhook для передачи лида в CRM", "required": False, "field_type": "url"},
        ],
    },
    {
        "id": uid(), "name": "Рассылка рекламного предложения",
        "description": "Рассылает рекламные офферы через Telegram-бота по подписчикам.",
        "webhook_url": "https://hooks.ascn.ai/promo-broadcast",
        "energy_cost": 12,
        "fields": [
            {"field_name": "bot_token", "hint": "Токен Telegram-бота", "required": True},
            {"field_name": "offer_text", "hint": "Текст рекламного предложения", "required": True},
        ],
    },
    {
        "id": uid(), "name": "Напоминалка",
        "description": "Автоматически отправляет напоминания клиентам о встречах, оплате или незакрытых сделках.",
        "webhook_url": "https://hooks.ascn.ai/reminder",
        "energy_cost": 5,
        "fields": [
            {"field_name": "bot_token", "hint": "Токен Telegram-бота", "required": True},
            {"field_name": "crm_webhook", "hint": "Webhook CRM для получения списка напоминаний", "required": False, "field_type": "url"},
        ],
    },
]

AGENTS = [
    {
        "name": "ТГ-агент",
        "description": "Полный набор инструментов для работы с Telegram: рассылки, шиллинг, прогрев аккаунтов, продажи, поддержка и генерация контента.",
        "prompt": (
            "Ты мощный Telegram-агент. Помогаешь пользователю автоматизировать работу в Telegram: "
            "организуешь рассылки, прогрев аккаунтов, продажи и создание контента. "
            "Используй доступные инструменты по запросу пользователя. "
            "Всегда уточняй детали перед запуском массовых действий."
        ),
        "skills": "Telegram API, массовые рассылки, прогрев аккаунтов, автоматизация продаж, контент-маркетинг",
        "energy_per_chat": 5,
        "tools": ["ТГ-рассылка", "ТГ-шиллер", "ТГ-прогрев аккаунта", "ТГ-продажник", "ТГ-саппорт", "ТГ-контент-завод"],
    },
    {
        "name": "Инста-агент",
        "description": "Автоматизация Instagram: парсинг аудитории, Direct-рассылки, продажи, генерация постов и Reels.",
        "prompt": (
            "Ты Instagram-агент. Помогаешь пользователю автоматизировать присутствие в Instagram: "
            "парсить аудиторию, вести переписки, создавать контент и видео. "
            "Всегда соблюдай лимиты платформы и предупреждай о рисках."
        ),
        "skills": "Instagram API, парсинг, Direct-маркетинг, создание Reels и постов, ИИ-видео",
        "energy_per_chat": 5,
        "tools": ["Инста-парсер аккаунтов", "Инста-рассылка", "Инста-продажник", "Инста-контент-завод", "Инста-генератор видео"],
    },
    {
        "name": "SEO-агент",
        "description": "Находит точки роста в поиске, пишет SEO-статьи, оптимизирует заголовки и мета-теги вашего сайта.",
        "prompt": (
            "Ты SEO-агент. Помогаешь пользователю продвигать сайт в поисковых системах. "
            "Находишь низкоконкурентные запросы, пишешь оптимизированный контент, "
            "даёшь рекомендации по техническому SEO и управляешь мета-тегами."
        ),
        "skills": "SEO-анализ, подбор ключевых слов, написание SEO-контента, технический аудит, мета-теги",
        "energy_per_chat": 5,
        "tools": ["Поиск лёгких взлётов", "SEO-заголовки", "SEO-статья", "Советы по оптимизации сайта", "Динамические мета-теги"],
    },
    {
        "name": "ИИ-продажник",
        "description": "Автоматизирует весь цикл продаж: холодные рассылки, диалог с клиентом, рекламные офферы и напоминания.",
        "prompt": (
            "Ты ИИ-продажник. Твоя задача — генерировать лиды и закрывать сделки. "
            "Ведёшь холодные рассылки, общаешься с клиентами в чатах, отправляешь офферы "
            "и напоминания. Всегда нацелен на конверсию. "
            "Уточняй у пользователя целевую аудиторию и оффер перед запуском кампаний."
        ),
        "skills": "Холодные продажи, скрипты продаж, CRM-интеграция, Telegram-боты, автоматизация воронки",
        "energy_per_chat": 5,
        "tools": ["Рассылка по холодной базе ТГ", "ИИ-продажник в чате", "Рассылка рекламного предложения", "Напоминалка"],
    },
]


async def seed():
    async with db_session() as db:
        # Проверяем — не добавлено ли уже
        existing = await db.execute(
            __import__('sqlalchemy', fromlist=['select']).select(TemplateAgent).where(TemplateAgent.name == "ТГ-агент")
        )
        if existing.scalar_one_or_none():
            print("Агенты уже существуют, пропускаем.")
            return

        # Создаём инструменты
        tool_map = {}  # name -> id
        for t in TOOLS:
            fields = t.pop("fields", [])
            tool = Tool(**t)
            db.add(tool)
            await db.flush()
            for i, f in enumerate(fields):
                db.add(ToolField(tool_id=tool.id, sort_order=i, **f))
            tool_map[tool.name] = tool.id
            print(f"  ✓ Инструмент: {tool.name}")

        await db.flush()

        # Создаём шаблонных агентов
        for a in AGENTS:
            tool_names = a.pop("tools")
            agent = TemplateAgent(id=uid(), is_active=True, llm_url="https://api.openai.com/v1/chat/completions", **a)
            db.add(agent)
            await db.flush()
            for name in tool_names:
                if name in tool_map:
                    db.add(TemplateAgentTool(id=uid(), template_id=agent.id, tool_id=tool_map[name]))
            print(f"  ✓ Агент: {agent.name} ({len(tool_names)} инструментов)")

        await db.commit()
        print("\n✅ Готово: 4 агента и 20 инструментов добавлены.")


if __name__ == "__main__":
    asyncio.run(seed())

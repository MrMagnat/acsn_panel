"""
Скрипт добавления демо-данных: 3 инструмента + 1 шаблонный агент.
Запуск: python seed_demo.py
"""
import asyncio
import uuid
from app.core.db import AsyncSessionLocal as async_session_maker
from app.models.tool import Tool, ToolField
from app.models.template_agent import TemplateAgent, TemplateAgentTool
from sqlalchemy import select


async def seed():
    async with async_session_maker() as db:
        # Проверяем — возможно данные уже добавлены
        existing = await db.execute(select(Tool).limit(1))
        if existing.scalar_one_or_none():
            print("Демо-данные уже существуют, пропускаем.")
            return

        # ── Инструмент 1: Отправка email ──────────────────────────────────────
        tool1_id = str(uuid.uuid4())
        tool1 = Tool(
            id=tool1_id,
            name="Отправка Email",
            description="Отправляет письмо на указанный адрес через SMTP. Поддерживает тему и тело письма.",
            webhook_url="https://hooks.example.com/send-email",
            is_active=True,
            energy_cost=5,
        )
        db.add(tool1)

        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool1_id, field_name="smtp_host", hint="Адрес SMTP-сервера, например smtp.gmail.com", required=True, field_type="text", sort_order=0))
        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool1_id, field_name="smtp_port", hint="Порт SMTP, обычно 587 или 465", required=True, field_type="number", sort_order=1))
        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool1_id, field_name="smtp_user", hint="Email-адрес отправителя", required=True, field_type="text", sort_order=2))
        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool1_id, field_name="smtp_password", hint="Пароль или App Password от почты", required=True, field_type="text", sort_order=3))

        # ── Инструмент 2: Поиск в Google ─────────────────────────────────────
        tool2_id = str(uuid.uuid4())
        tool2 = Tool(
            id=tool2_id,
            name="Поиск в Google",
            description="Выполняет поиск в Google и возвращает топ-5 результатов с заголовками и ссылками.",
            webhook_url="https://hooks.example.com/google-search",
            is_active=True,
            energy_cost=8,
        )
        db.add(tool2)

        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool2_id, field_name="api_key", hint="Google Custom Search API Key", required=True, field_type="text", sort_order=0))
        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool2_id, field_name="search_engine_id", hint="ID поискового движка из Google Console", required=True, field_type="text", sort_order=1))
        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool2_id, field_name="results_count", hint="Количество результатов (1-10)", required=False, field_type="number", sort_order=2))

        # ── Инструмент 3: Telegram-уведомление ───────────────────────────────
        tool3_id = str(uuid.uuid4())
        tool3 = Tool(
            id=tool3_id,
            name="Telegram Уведомление",
            description="Отправляет сообщение в Telegram-чат или канал через Bot API.",
            webhook_url="https://hooks.example.com/telegram-notify",
            is_active=True,
            energy_cost=3,
        )
        db.add(tool3)

        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool3_id, field_name="bot_token", hint="Токен бота из @BotFather", required=True, field_type="text", sort_order=0))
        db.add(ToolField(id=str(uuid.uuid4()), tool_id=tool3_id, field_name="chat_id", hint="ID чата или канала (например -1001234567890)", required=True, field_type="text", sort_order=1))

        # ── Шаблонный агент: Email-ассистент ─────────────────────────────────
        template_id = str(uuid.uuid4())
        template = TemplateAgent(
            id=template_id,
            name="Email-ассистент",
            description="Помогает составлять и отправлять деловые письма. Ищет информацию в интернете и уведомляет в Telegram о важных событиях.",
            llm_url="https://api.openai.com/v1/chat/completions",
            prompt=(
                "Ты деловой email-ассистент. Помогаешь пользователю составлять профессиональные письма, "
                "искать информацию для ответов и отправлять уведомления. "
                "Всегда пиши вежливо и по делу. При запросе поиска — используй инструмент Google Search. "
                "При необходимости отправить письмо — используй инструмент Email. "
                "Об отправке уведомляй пользователя через Telegram."
            ),
            skills="Деловая переписка, поиск информации, управление уведомлениями",
            energy_per_chat=5,
            is_active=True,
        )
        db.add(template)

        # Привязываем все три инструмента к шаблону
        for tid in [tool1_id, tool2_id, tool3_id]:
            db.add(TemplateAgentTool(id=str(uuid.uuid4()), template_id=template_id, tool_id=tid))

        await db.commit()
        print("✓ Демо-данные успешно добавлены:")
        print("  — Инструмент: Отправка Email")
        print("  — Инструмент: Поиск в Google")
        print("  — Инструмент: Telegram Уведомление")
        print("  — Шаблонный агент: Email-ассистент")


if __name__ == "__main__":
    asyncio.run(seed())

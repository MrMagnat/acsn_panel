import httpx
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from ..models.agent import UserAgent
from ..models.agent_tool import AgentTool
from ..models.tool import Tool
from ..models.chat import ChatMessage
from ..models.subscription import Subscription
from ..models.energy_transaction import EnergyTransaction
from ..models.tool_run_log import ToolRunLog
from ..models.trigger import AutoTrigger
from ..services.scheduler_service import schedule_trigger
from ..schemas.chat import ChatResponse, ChatMessageResponse


async def get_chat_history(agent_id: str, user_id: str, db: AsyncSession) -> list[ChatMessage]:
    """Получаем историю сообщений чата агента."""
    # Проверяем принадлежность агента пользователю
    agent_result = await db.execute(
        select(UserAgent).where(UserAgent.id == agent_id, UserAgent.user_id == user_id)
    )
    if not agent_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Агент не найден")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.agent_id == agent_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()


PROVIDER_URLS = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai":     "https://api.openai.com/v1/chat/completions",
    "deepseek":   "https://api.deepseek.com/chat/completions",
    "google":     "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "anthropic":  "https://api.anthropic.com/v1/messages",
}


async def send_message(
    agent_id: str, user_id: str, content: str, db: AsyncSession,
    llm_model: str | None = None, llm_token: str | None = None,
    llm_provider: str | None = None,
    base_url: str | None = None,
) -> ChatResponse:
    """Отправляем сообщение агенту, вызываем LLM и инструменты по необходимости."""
    # Загружаем агента с инструментами
    agent_result = await db.execute(
        select(UserAgent)
        .where(UserAgent.id == agent_id, UserAgent.user_id == user_id)
        .options(
            selectinload(UserAgent.agent_tools).selectinload(AgentTool.tool).selectinload(Tool.fields)
        )
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Агент не найден")

    if not agent.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Агент неактивен")

    # Проверяем наличие Agents Token
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = sub_result.scalar_one_or_none()
    if not subscription or subscription.tokens_left < agent.energy_per_chat:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Недостаточно Agents Token.",
        )

    # Сохраняем сообщение пользователя
    user_msg = ChatMessage(agent_id=agent_id, role="user", content=content)
    db.add(user_msg)
    await db.flush()

    new_messages = [user_msg]
    total_energy_spent = 0

    # Все инструменты агента — для системных операций (настройка, автозапуск)
    all_agent_tools = agent.agent_tools
    # Только настроенные — для вызова вебхуков
    configured_tools = [at for at in agent.agent_tools if at.is_configured]

    # Строим описание инструментов в формате function calling
    tool_definitions = _build_tool_definitions(configured_tools)

    # Загружаем историю для контекста (последние 20 сообщений)
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.agent_id == agent_id, ChatMessage.role.in_(["user", "assistant"]))
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    history = list(reversed(history_result.scalars().all()))

    # Формируем сообщения для LLM
    messages = []
    for msg in history[:-1]:  # Исключаем только что добавленное
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": content})

    # Строим полный системный промпт с описанием инструментов
    system_prompt = _build_system_prompt(agent, all_agent_tools)

    # Вызываем LLM если настроен (OpenRouter или кастомный URL)
    assistant_content = ""
    effective_model = llm_model or agent.llm_model
    effective_token = llm_token or agent.llm_token
    effective_provider = llm_provider or "openrouter"
    if effective_model:
        llm_url = PROVIDER_URLS.get(effective_provider, PROVIDER_URLS["openrouter"])
    else:
        llm_url = agent.llm_url

    # Системные инструменты + пользовательские
    system_tool_defs = _build_system_tool_definitions(agent, all_agent_tools)
    all_tool_defs = system_tool_defs + tool_definitions

    trigger_created = False

    if llm_url:
        try:
            try:
                llm_response = await _call_llm(
                    llm_url=llm_url,
                    system_prompt=system_prompt,
                    messages=messages,
                    tools=all_tool_defs,
                    llm_model=effective_model,
                    llm_token=effective_token,
                    provider=effective_provider,
                )
            except Exception as tool_err:
                # Модель не поддерживает tool use — повторяем без инструментов
                err_str = str(tool_err).lower()
                if "tool" in err_str or "function" in err_str or "endpoints" in err_str:
                    llm_response = await _call_llm(
                        llm_url=llm_url,
                        system_prompt=system_prompt,
                        messages=messages,
                        tools=[],
                        llm_model=effective_model,
                        llm_token=effective_token,
                        provider=effective_provider,
                    )
                else:
                    raise

            if llm_response.get("tool_call"):
                tool_call = llm_response["tool_call"]
                tool_fn = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})
                tool_call_id = tool_call.get("id", "call_0")
                raw_assistant = llm_response.get("raw_message", {})

                # --- Системный инструмент: сохранить настройки ---
                if tool_fn == "save_tool_settings":
                    sys_result, tool_msg_content = await _handle_save_settings(
                        tool_args, agent, all_agent_tools, db
                    )
                    tool_msg = ChatMessage(
                        agent_id=agent_id, role="tool",
                        content=tool_msg_content, tool_name="⚙️ Сохранение настроек",
                    )
                    db.add(tool_msg)
                    new_messages.append(tool_msg)
                    messages.append({"role": "assistant", "content": raw_assistant.get("content"), "tool_calls": raw_assistant.get("tool_calls", [])})
                    messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": tool_msg_content})
                    final = await _call_llm(llm_url=llm_url, system_prompt=system_prompt, messages=messages, tools=[], llm_model=effective_model, llm_token=effective_token, provider=effective_provider)
                    assistant_content = final.get("content", "") or "Настройки сохранены."

                # --- Системный инструмент: создать автозапуск ---
                elif tool_fn == "create_auto_trigger":
                    sys_result, tool_msg_content = await _handle_create_trigger(
                        tool_args, agent, user_id, all_agent_tools, db
                    )
                    trigger_created = sys_result
                    tool_msg = ChatMessage(
                        agent_id=agent_id, role="tool",
                        content=tool_msg_content, tool_name="🕐 Автозапуск",
                    )
                    db.add(tool_msg)
                    new_messages.append(tool_msg)
                    messages.append({"role": "assistant", "content": raw_assistant.get("content"), "tool_calls": raw_assistant.get("tool_calls", [])})
                    messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": tool_msg_content})
                    final = await _call_llm(llm_url=llm_url, system_prompt=system_prompt, messages=messages, tools=[], llm_model=effective_model, llm_token=effective_token, provider=effective_provider)
                    assistant_content = final.get("content", "") or "Автозапуск создан."

                # --- Пользовательский инструмент (webhook) ---
                else:
                    matched_at = next(
                        (at for at in configured_tools if _tool_fn_name(at.tool.id) == tool_fn), None
                    )
                    tool_name = matched_at.tool.name if matched_at else tool_fn

                    if matched_at:
                        merged_fields = {**(matched_at.field_values or {}), **tool_args}

                        # Создаём run_log с trigger_type="chat"
                        run_log = ToolRunLog(
                            agent_id=agent_id,
                            user_id=user_id,
                            tool_id=matched_at.tool.id,
                            tool_name=tool_name,
                            trigger_type="chat",
                            status="running",
                        )
                        db.add(run_log)
                        await db.flush()
                        run_log.instance_id = str(run_log.id)

                        tool_result = await _call_tool_webhook(
                            webhook_url=matched_at.tool.webhook_url,
                            field_values=merged_fields,
                            tool_args={},
                            agent_id=agent_id,
                            user_id=user_id,
                            log_id=str(run_log.id),
                            instance_id=str(run_log.id),
                            base_url=base_url,
                        )

                        from datetime import datetime, timezone as tz
                        # Если вебхук вернул instanceId — это async-запуск, ждём коллбэка
                        instance_id = tool_result.get("instanceId") or tool_result.get("instance_id")
                        if instance_id:
                            run_log.instance_id = instance_id
                            # status остаётся "running" — результат придёт через callback
                        else:
                            run_log.status = "success" if tool_result.get("status") != "error" else "error"
                            run_log.result_json = json.dumps(tool_result, ensure_ascii=False)
                            run_log.finished_at = datetime.now(tz.utc)

                        tool_msg = ChatMessage(
                            agent_id=agent_id,
                            role="tool",
                            content=json.dumps(tool_result, ensure_ascii=False),
                            tool_name=tool_name,
                            log_id=str(run_log.id),
                        )
                        db.add(tool_msg)
                        new_messages.append(tool_msg)

                        energy_cost = matched_at.tool.energy_cost
                        await _spend_energy(subscription, energy_cost, db)
                        await _log_transaction(user_id, -energy_cost, f"Инструмент: {tool_name}", agent_id, tool_name, db)
                        total_energy_spent += energy_cost

                        messages.append({"role": "assistant", "content": raw_assistant.get("content"), "tool_calls": raw_assistant.get("tool_calls", [])})
                        messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": json.dumps(tool_result, ensure_ascii=False)})

                        final = await _call_llm(llm_url=llm_url, system_prompt=system_prompt, messages=messages, tools=[], llm_model=effective_model, llm_token=effective_token, provider=effective_provider)
                        assistant_content = final.get("content", "") or f"Инструмент «{tool_name}» выполнен."
                    else:
                        assistant_content = llm_response.get("content", "")
            else:
                assistant_content = llm_response.get("content", "")

        except Exception as e:
            assistant_content = f"Ошибка при обращении к LLM: {str(e)}"
    else:
        assistant_content = "LLM не настроен. Выберите модель и введите API-ключ в шапке чата."

    # Сохраняем ответ ассистента
    assistant_msg = ChatMessage(agent_id=agent_id, role="assistant", content=assistant_content)
    db.add(assistant_msg)
    new_messages.append(assistant_msg)

    await _spend_energy(subscription, agent.energy_per_chat, db)
    await _log_transaction(user_id, -agent.energy_per_chat, "Чат с агентом", agent_id, None, db)
    total_energy_spent += agent.energy_per_chat

    await db.flush()

    return ChatResponse(
        messages=[
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                tool_name=getattr(msg, "tool_name", None),
                log_id=getattr(msg, "log_id", None),
                created_at=msg.created_at,
            )
            for msg in new_messages
        ],
        energy_spent=total_energy_spent,
        energy_left=subscription.energy_left,
        trigger_created=trigger_created,
    )


async def _spend_energy(subscription: Subscription, amount: int, db: AsyncSession) -> None:
    """Атомарно списываем Agents Token, не допуская ухода в минус."""
    result = await db.execute(
        update(Subscription)
        .where(Subscription.id == subscription.id, Subscription.tokens_left >= amount)
        .values(tokens_left=Subscription.tokens_left - amount)
        .returning(Subscription.tokens_left)
    )
    row = result.fetchone()
    if row:
        subscription.tokens_left = row[0]


async def _log_transaction(
    user_id: str, amount: int, description: str,
    agent_id: str | None, tool_name: str | None, db: AsyncSession
) -> None:
    """Записываем транзакцию энергии в лог."""
    db.add(EnergyTransaction(
        user_id=user_id,
        amount=amount,
        description=description,
        agent_id=agent_id,
        tool_name=tool_name,
    ))


def _build_system_tool_definitions(agent, configured_tools: list) -> list[dict]:
    """Системные инструменты — всегда доступны LLM для управления агентом."""
    tools = []

    # Строим enum и описание инструментов для системных вызовов
    if configured_tools:
        tool_ids_enum = [at.tool.id for at in configured_tools]
        tool_id_desc = "ID инструмента. Доступные: " + ", ".join(
            f'"{at.tool.id}" = «{at.tool.name}»' for at in configured_tools
        )
        fields_desc = "; ".join(
            f"«{at.tool.name}» (id={at.tool.id}): поля {[f.field_name for f in at.tool.fields]}"
            for at in configured_tools if at.tool.fields
        )

        # Инструмент: сохранить настройки
        tools.append({
            "type": "function",
            "function": {
                "name": "save_tool_settings",
                "description": (
                    "Сохраняет новые настройки инструмента агента. "
                    "Используй когда пользователь хочет изменить/настроить параметры и сохранить их. "
                    f"Поля инструментов: {fields_desc}"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tool_id": {"type": "string", "description": tool_id_desc, "enum": tool_ids_enum},
                        "field_values": {"type": "object", "description": "Словарь с новыми значениями полей"},
                    },
                    "required": ["tool_id", "field_values"],
                },
            },
        })

        # Инструмент: создать автозапуск
        tools.append({
            "type": "function",
            "function": {
                "name": "create_auto_trigger",
                "description": (
                    "Создаёт автозапуск инструмента по расписанию (cron). "
                    "Используй когда пользователь хочет запускать инструмент автоматически. "
                    "Примеры cron: '0 9 * * 1' = каждый понедельник в 9:00, '0 */6 * * *' = каждые 6 часов, '0 10 * * *' = каждый день в 10:00."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tool_id": {"type": "string", "description": tool_id_desc, "enum": tool_ids_enum},
                        "cron_expr": {"type": "string", "description": "Cron-выражение расписания"},
                        "timezone": {"type": "string", "description": "Часовой пояс, например Europe/Moscow", "default": "UTC"},
                    },
                    "required": ["tool_id", "cron_expr"],
                },
            },
        })

    return tools


async def _handle_save_settings(
    args: dict, agent, configured_tools: list, db: AsyncSession
) -> tuple[bool, str]:
    """Обрабатывает системный вызов save_tool_settings."""
    tool_id = args.get("tool_id", "")
    field_values = args.get("field_values", {})

    matched_at = next((at for at in configured_tools if at.tool.id == tool_id), None)
    if not matched_at:
        return False, json.dumps({"status": "error", "message": "Инструмент не найден"})

    # Мёрджим с существующими значениями
    updated = {**(matched_at.field_values or {}), **field_values}
    await db.execute(
        update(AgentTool)
        .where(AgentTool.id == matched_at.id)
        .values(field_values=updated, is_configured=True)
    )
    matched_at.field_values = updated
    matched_at.is_configured = True

    return True, json.dumps({"status": "ok", "message": f"Настройки «{matched_at.tool.name}» сохранены", "saved": field_values})


async def _handle_create_trigger(
    args: dict, agent, user_id: str, configured_tools: list, db: AsyncSession
) -> tuple[bool, str]:
    """Обрабатывает системный вызов create_auto_trigger."""
    tool_id = args.get("tool_id", "")
    cron_expr = args.get("cron_expr", "")
    timezone = args.get("timezone", "UTC")

    matched_at = next((at for at in configured_tools if at.tool.id == tool_id), None)
    if not matched_at:
        return False, json.dumps({"status": "error", "message": "Инструмент не найден"})

    trigger = AutoTrigger(
        agent_id=agent.id,
        tool_id=tool_id,
        cron_expr=cron_expr,
        timezone=timezone,
    )
    db.add(trigger)
    await db.flush()
    schedule_trigger(trigger)

    return True, json.dumps({
        "status": "ok",
        "message": f"Автозапуск для «{matched_at.tool.name}» создан",
        "cron": cron_expr,
        "timezone": timezone,
    })


def _build_system_prompt(agent, configured_tools: list) -> str:
    """Строим полный системный промпт: базовый + скиллы + блок инструментов."""
    parts = []

    # 0. Жёсткие правила поведения — всегда первые
    parts.append(
        "## Базовые правила\n"
        "- Ты — специализированный AI-ассистент. Отвечай ТОЛЬКО по теме своего назначения и своих инструментов.\n"
        "- НИКОГДА не перечисляй свои возможности списком (типа '1. Я умею... 2. Я могу...'). Это запрещено.\n"
        "- Если пользователь спрашивает 'что ты умеешь' или 'расскажи о себе' — ответь одной фразой о своей специализации и доступных инструментах, без нумерованных списков.\n"
        "- Отвечай тезисно и по делу. Без воды, без приветственных монологов."
    )

    # 1. Базовый промпт агента
    if agent.prompt and agent.prompt.strip():
        parts.append(agent.prompt.strip())

    # 2. Скиллы / знания
    if agent.skills and agent.skills.strip():
        parts.append(f"## Твои знания и навыки\n{agent.skills.strip()}")

    # 3. Блок инструментов — только если есть настроенные
    if configured_tools:
        tool_lines = []
        for at in configured_tools:
            tool = at.tool
            configured_values = at.field_values or {}
            desc = tool.description.strip() if tool.description else ""
            hint = tool.trigger_hint.strip() if tool.trigger_hint else ""
            line = f"- **{tool.name}**"
            if desc:
                line += f": {desc}"
            if hint:
                line += f"\n  → Используй когда: {hint}"
            # Показываем ВСЕ поля инструмента с текущими значениями
            if tool.fields:
                field_descs = []
                for f in tool.fields:
                    cur = configured_values.get(f.field_name, "")
                    req = " (обязательное)" if f.required else ""
                    if cur:
                        field_descs.append(f'"{f.field_name}"{req}: сейчас "{str(cur)[:40]}"')
                    else:
                        field_descs.append(f'"{f.field_name}"{req}: не задано')
                line += f"\n  → Поля: {', '.join(field_descs)}"
            tool_lines.append(line)

        parts.append(
            "## Доступные инструменты\n"
            "У тебя есть следующие инструменты:\n"
            + "\n".join(tool_lines)
        )
        parts.append(
            "## Правила работы с инструментами\n"
            "1. НИКОГДА не вызывай инструмент сразу. Сначала спроси пользователя о значениях всех полей.\n"
            "   - Если поле уже заполнено — покажи текущее значение и спроси, оставить или изменить.\n"
            "   - Если поле пустое — обязательно запроси у пользователя перед вызовом.\n"
            "2. Вызывай инструмент ТОЛЬКО после того, как пользователь явно подтвердил или предоставил все значения.\n"
            "3. После получения результата — объясни его пользователю кратко и по-человечески.\n"
            "4. Если инструмент вернул ошибку — сообщи об этом и предложи что можно сделать.\n"
            "5. Если пользователь просит сохранить настройки — используй save_tool_settings.\n"
            "6. Если пользователь просит настроить автозапуск — используй create_auto_trigger."
        )

    return "\n\n".join(parts) if parts else ""


def _tool_fn_name(tool_id: str) -> str:
    """Генерируем ASCII-имя функции из tool.id (OpenAI требует [a-zA-Z0-9_-])."""
    return "tool_" + tool_id.replace("-", "_")


def _build_tool_definitions(agent_tools: list) -> list[dict]:
    """Строим описание инструментов в формате совместимом с OpenAI function calling.

    Все поля инструмента включаются как ОПЦИОНАЛЬНЫЕ параметры.
    - Поля с уже сохранёнными значениями: LLM может переопределить если пользователь указал другое значение.
    - Поля без значений: LLM должен заполнить из контекста разговора.
    При вызове: tool_args от LLM мёрджатся поверх field_values (LLM-значения приоритетнее).
    """
    definitions = []
    for at in agent_tools:
        tool = at.tool
        configured_values = at.field_values or {}
        properties = {}
        required_runtime = []

        for field in tool.fields:
            # Только поля с is_runtime=True видит LLM
            if not field.is_runtime:
                continue
            has_value = bool(configured_values.get(field.field_name))
            description = field.hint or field.field_name
            if has_value:
                current = configured_values[field.field_name]
                description += f' (сейчас: "{current[:60]}"; можно переопределить)'
            properties[field.field_name] = {
                "type": "string",
                "description": description,
            }
            # Required если поле обязательно и ещё не заполнено
            if field.required and not has_value:
                required_runtime.append(field.field_name)

        # Объединяем description + trigger_hint для лучшего понимания LLM
        full_description = f"Инструмент: {tool.name}."
        if tool.description:
            full_description += f" {tool.description.strip()}"
        if tool.trigger_hint:
            full_description += f" Используй когда: {tool.trigger_hint.strip()}"

        definitions.append({
            "type": "function",
            "function": {
                # Имя ОБЯЗАТЕЛЬНО ASCII [a-zA-Z0-9_-] — используем tool_id
                "name": _tool_fn_name(tool.id),
                "description": full_description.strip(),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required_runtime,
                },
            },
        })
    return definitions


async def _call_llm(
    llm_url: str, system_prompt: str, messages: list, tools: list,
    llm_model: str | None = None, llm_token: str | None = None,
    provider: str = "openrouter",
) -> dict:
    """Вызываем LLM. Поддерживаем OpenAI-совместимые API и Anthropic Messages API."""
    if provider == "anthropic":
        return await _call_anthropic(llm_url, system_prompt, messages, tools, llm_model, llm_token)

    # ── OpenAI-совместимые провайдеры ──────────────────────────────────────────
    payload = {
        "messages": [{"role": "system", "content": system_prompt}] + messages if system_prompt else messages,
    }
    if llm_model:
        payload["model"] = llm_model
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    headers = {"Content-Type": "application/json"}
    if llm_token:
        headers["Authorization"] = f"Bearer {llm_token}"
    if "openrouter.ai" in llm_url:
        headers["HTTP-Referer"] = "http://85.193.84.93"
        headers["X-Title"] = "ASCN AI Platform"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(llm_url, json=payload, headers=headers)
        if not response.is_success:
            try:
                err_body = response.json()
                err_msg = err_body.get("error", {}).get("message", "") or str(err_body)
            except Exception:
                err_msg = response.text[:300]
            raise httpx.HTTPStatusError(
                f"{response.status_code}: {err_msg}",
                request=response.request, response=response,
            )
        data = response.json()

    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    result = {
        "content": message.get("content", "") or "",
        "raw_message": message,
    }
    tool_calls = message.get("tool_calls", [])
    if tool_calls:
        first_call = tool_calls[0]
        result["tool_call"] = {
            "id": first_call.get("id", "call_0"),
            "name": first_call["function"]["name"],
            "arguments": json.loads(first_call["function"].get("arguments", "{}")),
        }

    return result


async def _call_anthropic(
    llm_url: str, system_prompt: str, messages: list, tools: list,
    llm_model: str | None, llm_token: str | None,
) -> dict:
    """Anthropic Messages API. Конвертируем OpenAI-формат ↔ Anthropic."""

    # ── Конвертация инструментов OpenAI → Anthropic ─────────────────────────
    anthropic_tools = []
    for t in tools:
        fn = t.get("function", {})
        anthropic_tools.append({
            "name": fn.get("name"),
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })

    # ── Конвертация messages OpenAI → Anthropic ──────────────────────────────
    anthropic_messages = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        tool_calls = msg.get("tool_calls", [])

        if role == "system":
            continue  # system идёт отдельно
        elif role == "assistant":
            parts = []
            if content:
                parts.append({"type": "text", "text": content})
            for tc in tool_calls:
                fn = tc.get("function", {})
                try:
                    inp = json.loads(fn.get("arguments", "{}"))
                except Exception:
                    inp = {}
                parts.append({"type": "tool_use", "id": tc.get("id", "call_0"),
                               "name": fn.get("name"), "input": inp})
            anthropic_messages.append({"role": "assistant", "content": parts or (content or "")})
        elif role == "tool":
            # tool_result должен идти как user-сообщение
            anthropic_messages.append({
                "role": "user",
                "content": [{"type": "tool_result",
                              "tool_use_id": msg.get("tool_call_id", "call_0"),
                              "content": content or ""}],
            })
        else:
            anthropic_messages.append({"role": role, "content": content or ""})

    payload: dict = {
        "model": llm_model or "claude-3-5-haiku-20241022",
        "max_tokens": 4096,
        "messages": anthropic_messages,
    }
    if system_prompt:
        payload["system"] = system_prompt
    if anthropic_tools:
        payload["tools"] = anthropic_tools

    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key": llm_token or "",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(llm_url, json=payload, headers=headers)
        if not response.is_success:
            try:
                err_body = response.json()
                err_msg = err_body.get("error", {}).get("message", "") or str(err_body)
            except Exception:
                err_msg = response.text[:300]
            raise httpx.HTTPStatusError(
                f"{response.status_code}: {err_msg}",
                request=response.request, response=response,
            )
        data = response.json()

    # ── Парсинг ответа Anthropic → единый формат ─────────────────────────────
    content_blocks = data.get("content", [])
    text_content = " ".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
    tool_use = next((b for b in content_blocks if b.get("type") == "tool_use"), None)

    # Сохраняем raw_message в OpenAI-формате для совместимости с историей
    raw_tool_calls = []
    if tool_use:
        raw_tool_calls = [{
            "id": tool_use.get("id", "call_0"),
            "function": {
                "name": tool_use.get("name"),
                "arguments": json.dumps(tool_use.get("input", {}), ensure_ascii=False),
            },
        }]

    result: dict = {
        "content": text_content,
        "raw_message": {
            "content": text_content,
            "tool_calls": raw_tool_calls,
        },
    }
    if tool_use:
        result["tool_call"] = {
            "id": tool_use.get("id", "call_0"),
            "name": tool_use.get("name"),
            "arguments": tool_use.get("input", {}),
        }
    return result


async def _call_tool_webhook(
    webhook_url: str,
    field_values: dict,
    tool_args: dict,
    agent_id: str,
    user_id: str,
    log_id: str | None = None,
    instance_id: str | None = None,
    base_url: str | None = None,
) -> dict:
    """Вызываем webhook нашего движка для запуска воркфлоу инструмента."""
    from ..core.config import settings
    _base = base_url or settings.APP_BASE_URL
    payload = {
        **field_values,
        "fields": field_values,
        "args": tool_args,
        "agent_id": agent_id,
        "user_id": user_id,
        "log_id": log_id,
        "instance_id": instance_id,
        "callback_url": f"{_base}/webhooks/tool-callback",
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        return {"result": "Инструмент не ответил (таймаут 30 сек)", "status": "error"}
    except Exception as e:
        return {"result": f"Ошибка вызова инструмента: {str(e)}", "status": "error"}

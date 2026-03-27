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


async def send_message(agent_id: str, user_id: str, content: str, db: AsyncSession) -> ChatResponse:
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

    # Проверяем наличие энергии (минимум energy_per_chat)
    # Загружаем подписку пользователя для проверки энергии
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = sub_result.scalar_one_or_none()
    if not subscription or subscription.energy_left < agent.energy_per_chat:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Недостаточно энергии. Энергия обновляется каждую неделю.",
        )

    # Сохраняем сообщение пользователя
    user_msg = ChatMessage(agent_id=agent_id, role="user", content=content)
    db.add(user_msg)
    await db.flush()

    new_messages = [user_msg]
    total_energy_spent = 0

    # Получаем только настроенные (configured) инструменты для передачи в LLM
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
    system_prompt = _build_system_prompt(agent, configured_tools)

    # Вызываем LLM если настроен (OpenRouter или кастомный URL)
    assistant_content = ""
    llm_url = "https://openrouter.ai/api/v1/chat/completions" if agent.llm_model else agent.llm_url
    if llm_url:
        try:
            llm_response = await _call_llm(
                llm_url=llm_url,
                system_prompt=system_prompt,
                messages=messages,
                tools=tool_definitions,
                llm_model=agent.llm_model,
                llm_token=agent.llm_token,
            )

            # Обрабатываем tool_call от LLM
            if llm_response.get("tool_call"):
                tool_call = llm_response["tool_call"]
                tool_fn = tool_call.get("name")   # это "tool_<id>"
                tool_args = tool_call.get("arguments", {})

                # Находим нужный agent_tool по fn-имени (tool_<id>)
                matched_at = next(
                    (at for at in configured_tools if _tool_fn_name(at.tool.id) == tool_fn), None
                )
                tool_name = matched_at.tool.name if matched_at else tool_fn
                tool_call_id = tool_call.get("id", "call_0")

                if matched_at:
                    # Мёрджим сохранённые настройки + аргументы от LLM
                    # LLM-аргументы имеют приоритет (переопределяют для этой сессии)
                    merged_fields = {**(matched_at.field_values or {}), **tool_args}

                    # Вызываем webhook инструмента
                    tool_result = await _call_tool_webhook(
                        webhook_url=matched_at.tool.webhook_url,
                        field_values=merged_fields,
                        tool_args={},   # уже влито в field_values
                        agent_id=agent_id,
                        user_id=user_id,
                    )

                    # Сохраняем результат вызова инструмента
                    tool_msg = ChatMessage(
                        agent_id=agent_id,
                        role="tool",
                        content=json.dumps(tool_result, ensure_ascii=False),
                        tool_name=tool_name,
                    )
                    db.add(tool_msg)
                    new_messages.append(tool_msg)

                    # Списываем энергию за инструмент атомарно с аккаунта
                    energy_cost = matched_at.tool.energy_cost
                    await _spend_energy(subscription, energy_cost, db)
                    await _log_transaction(user_id, -energy_cost, f"Инструмент: {tool_name}", agent_id, tool_name, db)
                    total_energy_spent += energy_cost

                    # Строим правильную историю для второго вызова LLM
                    # OpenAI требует: assistant (с tool_calls) → tool (с tool_call_id)
                    raw_assistant = llm_response.get("raw_message", {})
                    messages.append({
                        "role": "assistant",
                        "content": raw_assistant.get("content"),
                        "tool_calls": raw_assistant.get("tool_calls", []),
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })

                    final_response = await _call_llm(
                        llm_url=llm_url,
                        system_prompt=system_prompt,
                        messages=messages,
                        tools=[],
                        llm_model=agent.llm_model,
                        llm_token=agent.llm_token,
                    )
                    assistant_content = final_response.get("content", "") or f"Инструмент «{tool_name}» выполнен."
                else:
                    assistant_content = llm_response.get("content", "")
            else:
                assistant_content = llm_response.get("content", "")

        except Exception as e:
            assistant_content = f"Ошибка при обращении к LLM: {str(e)}"
    else:
        assistant_content = "LLM не настроен для данного агента. Выберите модель в настройках агента."

    # Сохраняем ответ ассистента
    assistant_msg = ChatMessage(agent_id=agent_id, role="assistant", content=assistant_content)
    db.add(assistant_msg)
    new_messages.append(assistant_msg)

    # Списываем энергию за вызов чата атомарно с аккаунта
    await _spend_energy(subscription, agent.energy_per_chat, db)
    await _log_transaction(user_id, -agent.energy_per_chat, f"Чат с агентом", agent_id, None, db)
    total_energy_spent += agent.energy_per_chat

    await db.flush()

    return ChatResponse(
        messages=[
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                tool_name=getattr(msg, "tool_name", None),
                created_at=msg.created_at,
            )
            for msg in new_messages
        ],
        energy_spent=total_energy_spent,
        energy_left=subscription.energy_left,
    )


async def _spend_energy(subscription: Subscription, amount: int, db: AsyncSession) -> None:
    """Атомарно списываем энергию с аккаунта, не допуская ухода в минус."""
    result = await db.execute(
        update(Subscription)
        .where(Subscription.id == subscription.id, Subscription.energy_left >= amount)
        .values(energy_left=Subscription.energy_left - amount)
        .returning(Subscription.energy_left)
    )
    row = result.fetchone()
    if row:
        subscription.energy_left = row[0]


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


def _build_system_prompt(agent, configured_tools: list) -> str:
    """Строим полный системный промпт: базовый + скиллы + блок инструментов."""
    parts = []

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
            # Перечисляем runtime-поля — те что пользователь может задавать через чат
            runtime_fields = [f for f in tool.fields if f.is_runtime]
            if runtime_fields:
                field_descs = []
                for f in runtime_fields:
                    cur = configured_values.get(f.field_name, "")
                    if cur:
                        field_descs.append(f'"{f.field_name}" (сейчас: "{cur[:40]}")')
                    else:
                        field_descs.append(f'"{f.field_name}"')
                line += f"\n  → Параметры которые можно задать: {', '.join(field_descs)}"
            tool_lines.append(line)

        parts.append(
            "## Доступные инструменты\n"
            "У тебя есть следующие инструменты. Используй их когда это уместно — "
            "не объясняй пользователю как они работают, просто вызывай и сообщай результат.\n"
            + "\n".join(tool_lines)
        )
        parts.append(
            "## Правила работы с инструментами\n"
            "1. Если запрос пользователя явно или косвенно требует действия — вызови подходящий инструмент.\n"
            "2. После получения результата инструмента — объясни его пользователю кратко и по-человечески.\n"
            "3. Если инструмент вернул ошибку — сообщи об этом и предложи что можно сделать."
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
    llm_model: str | None = None, llm_token: str | None = None
) -> dict:
    """Вызываем LLM через HTTP. Ожидаем OpenAI-совместимый API (OpenRouter или кастомный)."""
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

    # OpenRouter требует HTTP-Referer и X-Title для идентификации приложения
    if "openrouter.ai" in llm_url:
        headers["HTTP-Referer"] = "https://businesspanel.ru"
        headers["X-Title"] = "ASCN AI Platform"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(llm_url, json=payload, headers=headers)
        if not response.is_success:
            # Показываем тело ответа для диагностики
            try:
                err_body = response.json()
                err_msg = err_body.get("error", {}).get("message", "") or str(err_body)
            except Exception:
                err_msg = response.text[:300]
            raise httpx.HTTPStatusError(
                f"{response.status_code}: {err_msg}",
                request=response.request,
                response=response,
            )
        data = response.json()

    # Парсим ответ в единый формат
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})

    result = {
        "content": message.get("content", "") or "",
        "raw_message": message,  # полный объект для последующего добавления в историю
    }

    # Проверяем наличие вызова инструмента
    tool_calls = message.get("tool_calls", [])
    if tool_calls:
        first_call = tool_calls[0]
        result["tool_call"] = {
            "id": first_call.get("id", "call_0"),   # tool_call_id для ответа
            "name": first_call["function"]["name"],
            "arguments": json.loads(first_call["function"].get("arguments", "{}")),
        }

    return result


async def _call_tool_webhook(
    webhook_url: str,
    field_values: dict,
    tool_args: dict,
    agent_id: str,
    user_id: str,
) -> dict:
    """Вызываем webhook нашего движка для запуска воркфлоу инструмента."""
    payload = {
        "fields": field_values,
        "args": tool_args,
        "agent_id": agent_id,
        "user_id": user_id,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        return {"result": "Инструмент не ответил (таймаут 30 сек)", "status": "error"}
    except Exception as e:
        return {"result": f"Ошибка вызова инструмента: {str(e)}", "status": "error"}

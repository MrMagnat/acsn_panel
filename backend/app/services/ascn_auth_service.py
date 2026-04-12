"""
Интеграция с главным сервисом ASCN.
Два режима:
  - login_via_ascn(email, password) — дев-режим, логинимся через API
  - sync_from_token(token)          — прод-режим, токен из куки
"""
import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from ..models.user import User
from ..models.subscription import Subscription
from ..models.tariff_plan import TariffPlan
from ..models.setting import Setting
from ..core.security import create_access_token, create_refresh_token
from ..schemas.auth import TokenResponse

ASCN_API = "https://api.ascn.ai"

DEFAULT_TARIFF_MAPPINGS = [
    {"slug": "default", "name": "Базовый", "max_agents": 1, "max_tools_per_agent": 2},
]


async def _get_tariff_mappings(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Setting).where(Setting.key == "tariff_mappings"))
    row = result.scalar_one_or_none()
    if not row:
        return DEFAULT_TARIFF_MAPPINGS
    try:
        return json.loads(row.value)
    except Exception:
        return DEFAULT_TARIFF_MAPPINGS


async def _sync_subscription(user: User, ascn_token: str, db: AsyncSession) -> None:
    """Запрашивает подписку ASCN и обновляет локальную."""
    headers = {"Authorization": f"Bearer {ascn_token}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{ASCN_API}/billing/me/subscription/current/",
                params={"tariff_type": "no-code", "lang": "ru", "limit": 10},
                headers=headers,
            )
        if not resp.is_success:
            return

        data = resp.json()
        rows = data.get("rows", [])
        # Берём первую неистёкшую подписку
        active = next((r for r in rows if not r.get("expired", True)), None)
        if not active:
            active = rows[0] if rows else None
        if not active:
            return

        tariff = active.get("tariff", {})
        slug = tariff.get("slug", "default")
        plan_name = tariff.get("name", slug)
        credits = tariff.get("nocode_credits_count", 0) or 0

        # Ищем маппинг ASCN slug → локальный тариф
        mappings = await _get_tariff_mappings(db)
        mapping = next((m for m in mappings if m["slug"] == slug), None)
        if not mapping:
            mapping = next((m for m in mappings if m["slug"] == "default"), DEFAULT_TARIFF_MAPPINGS[0])

        # Обновляем подписку
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        sub = sub_result.scalar_one_or_none()
        if not sub:
            sub = Subscription(user_id=user.id)
            db.add(sub)
            await db.flush()

        sub.plan = slug
        sub.plan_name = plan_name
        # ASCN energy убрана — используем только Agents Token
        sub.max_agents = mapping.get("max_agents", sub.max_agents)
        sub.max_tools_per_agent = mapping.get("max_tools_per_agent", sub.max_tools_per_agent)

        # Привязываем локальный TariffPlan если задан local_plan_slug в маппинге
        local_slug = mapping.get("local_plan_slug")
        if local_slug:
            plan_result = await db.execute(select(TariffPlan).where(TariffPlan.slug == local_slug, TariffPlan.is_active == True))
            local_plan = plan_result.scalar_one_or_none()
            if local_plan and sub.tariff_plan_id != local_plan.id:
                sub.tariff_plan_id = local_plan.id
                sub.tokens_per_month = local_plan.tokens_per_month
                # Пополняем токены только при смене тарифа
                sub.tokens_left = local_plan.tokens_per_month

    except Exception:
        pass  # Не ломаем логин если ASCN недоступен


async def login_via_ascn(email: str, password: str, db: AsyncSession) -> TokenResponse:
    """Дев-режим: логинимся email/паролем через ASCN API, синхронизируем юзера."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{ASCN_API}/auth/login/",
            json={"email": email, "password": password},
        )
        if resp.status_code == 401 or resp.status_code == 422:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )
        if not resp.is_success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ошибка авторизации ASCN: {resp.status_code}",
            )
        token = resp.json().get("access_token")

    return await sync_from_token(token, db)


async def sync_from_token(ascn_token: str, db: AsyncSession) -> TokenResponse:
    """Прод-режим: валидируем токен ASCN, создаём/обновляем локального юзера."""
    headers = {"Authorization": f"Bearer {ascn_token}"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Проверяем токен
        test = await client.get(f"{ASCN_API}/auth/test-token/", headers=headers)
        if not test.is_success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен ASCN недействителен",
            )

        # 2. Получаем профиль
        profile_resp = await client.get(f"{ASCN_API}/users/me/", headers=headers)
        if not profile_resp.is_success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Не удалось получить профиль ASCN",
            )
        profile = profile_resp.json()

    ascn_id = profile["id"]
    email = profile["email"]
    name = profile.get("full_name") or email.split("@")[0]

    # 3. Ищем юзера по ascn_user_id или email
    result = await db.execute(select(User).where(User.ascn_user_id == ascn_id))
    user = result.scalar_one_or_none()

    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    telegram = profile.get("telegram")
    phone = profile.get("phone")
    avatar_url = profile.get("avatar")

    if user:
        user.ascn_user_id = ascn_id
        user.name = name
        user.telegram = telegram
        user.phone = phone
        user.avatar_url = avatar_url
    else:
        import uuid
        user = User(
            email=email,
            password_hash="__ascn__" + str(uuid.uuid4()),
            name=name,
            ascn_user_id=ascn_id,
            telegram=telegram,
            phone=phone,
            avatar_url=avatar_url,
        )
        db.add(user)
        await db.flush()
        db.add(Subscription(user_id=user.id))

    await db.flush()

    # 4. Синхронизируем подписку ASCN
    await _sync_subscription(user, ascn_token, db)
    await db.flush()

    return TokenResponse(
        access_token=create_access_token({"sub": user.id}),
        refresh_token=create_refresh_token({"sub": user.id}),
    )

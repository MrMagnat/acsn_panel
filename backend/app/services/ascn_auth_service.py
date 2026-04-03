"""
Интеграция с главным сервисом ASCN.
Два режима:
  - login_via_ascn(email, password) — дев-режим, логинимся через API
  - sync_from_token(token)          — прод-режим, токен из куки
"""
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from ..models.user import User
from ..models.subscription import Subscription
from ..core.security import create_access_token, create_refresh_token
from ..schemas.auth import TokenResponse

ASCN_API = "https://dev-api.ascn.ai"


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
        # Может быть уже зарегистрирован локально по email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    telegram = profile.get("telegram")
    phone = profile.get("phone")
    avatar_url = profile.get("avatar")

    if user:
        # Обновляем данные
        user.ascn_user_id = ascn_id
        user.name = name
        user.telegram = telegram
        user.phone = phone
        user.avatar_url = avatar_url
    else:
        # Создаём нового юзера (пароль заблокирован — только ASCN-логин)
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

        # Дефолтная подписка
        db.add(Subscription(user_id=user.id))

    await db.flush()

    return TokenResponse(
        access_token=create_access_token({"sub": user.id}),
        refresh_token=create_refresh_token({"sub": user.id}),
    )

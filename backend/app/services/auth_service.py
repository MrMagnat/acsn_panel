from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from ..models.user import User
from ..models.subscription import Subscription
from ..core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from ..schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from jose import JWTError


async def register_user(data: RegisterRequest, db: AsyncSession) -> TokenResponse:
    """Регистрируем нового пользователя и создаём дефолтную подписку."""
    # Проверяем, что email не занят
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован")

    # Создаём пользователя
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    await db.flush()  # Чтобы получить user.id

    # Создаём дефолтную подписку free
    subscription = Subscription(user_id=user.id)
    db.add(subscription)
    await db.flush()

    # Генерируем токены
    tokens = _generate_tokens(user.id)
    return tokens


async def login_user(data: LoginRequest, db: AsyncSession) -> TokenResponse:
    """Аутентифицируем пользователя по email и паролю."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    return _generate_tokens(user.id)


async def refresh_tokens(refresh_token: str, db: AsyncSession) -> TokenResponse:
    """Обновляем пару токенов по refresh token."""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен невалиден или истёк")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    return _generate_tokens(user.id)


def _generate_tokens(user_id: str) -> TokenResponse:
    """Вспомогательная функция для генерации пары токенов."""
    return TokenResponse(
        access_token=create_access_token({"sub": user_id}),
        refresh_token=create_refresh_token({"sub": user_id}),
    )

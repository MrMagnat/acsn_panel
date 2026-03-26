from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_db
from ..core.deps import get_current_user
from ..core.security import hash_password
from ..services import auth_service
from ..schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


class UpdateMeRequest(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя."""
    return await auth_service.register_user(data, db)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Вход в систему."""
    return await auth_service.login_user(data, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Обновление токенов по refresh token."""
    return await auth_service.refresh_tokens(data.refresh_token, db)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить имя или пароль текущего пользователя."""
    if data.name:
        current_user.name = data.name
    if data.password:
        current_user.password_hash = hash_password(data.password)
    await db.flush()
    return current_user

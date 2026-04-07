from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./ascn.db"
    REDIS_URL: str = ""
    SECRET_KEY: str = "change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Данные для seed-пользователя администратора
    ADMIN_EMAIL: str = "admin@ascn.io"
    ADMIN_PASSWORD: str = "admin123"

    # Секрет для вебхука системы подписок
    SUBSCRIPTION_WEBHOOK_SECRET: str = "webhook_secret"

    # Публичный URL сервера (используется в callback_url для инструментов)
    APP_BASE_URL: str = "http://localhost:8000/api"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

from sqlalchemy import String, Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, gen_uuid


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # ID пользователя в главном сервисе ASCN (для SSO-интеграции)
    ascn_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)
    agents: Mapped[list["UserAgent"]] = relationship("UserAgent", back_populates="user")

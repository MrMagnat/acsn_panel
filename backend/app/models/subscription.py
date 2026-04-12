from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, gen_uuid


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Локальный тариф платформы
    tariff_plan_id: Mapped[str | None] = mapped_column(String, ForeignKey("tariff_plans.id", ondelete="SET NULL"), nullable=True)
    tokens_left: Mapped[int] = mapped_column(Integer, default=0, nullable=False)      # собственные токены платформы
    tokens_per_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # кэш из tariff_plan

    # ASCN-синхронизация (остаются для обратной совместимости)
    plan: Mapped[str] = mapped_column(String(100), default="free", nullable=False)
    plan_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_agents: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_tools_per_agent: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    energy_per_week: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    energy_left: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    balance_usd: Mapped[int] = mapped_column(Integer, default=0, nullable=False)       # баланс ИИ в центах
    renewed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    partner_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="subscription")
    tariff_plan: Mapped["TariffPlan | None"] = relationship("TariffPlan", back_populates="subscriptions")

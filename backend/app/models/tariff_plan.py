from sqlalchemy import String, Integer, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, gen_uuid


class TariffPlan(Base):
    __tablename__ = "tariff_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_rub: Mapped[int] = mapped_column(Integer, default=0)          # в копейках, 0 = бесплатно
    max_agents: Mapped[int] = mapped_column(Integer, default=1)
    max_tools_per_agent: Mapped[int] = mapped_column(Integer, default=2)
    max_workflows: Mapped[int] = mapped_column(Integer, default=1)
    tokens_per_month: Mapped[int] = mapped_column(Integer, default=100)  # собственные токены платформы
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)     # применяется новым пользователям
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="tariff_plan")

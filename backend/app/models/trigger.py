from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from .base import Base, gen_uuid


class AutoTrigger(Base):
    __tablename__ = "auto_triggers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False)
    tool_id: Mapped[str] = mapped_column(String, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    cron_expr: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Собственные значения полей для этого автозапуска (перекрывают field_values инструмента)
    input_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    agent: Mapped["UserAgent"] = relationship("UserAgent", back_populates="auto_triggers")
    tool: Mapped["Tool"] = relationship("Tool")

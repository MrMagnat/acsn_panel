from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from .base import Base, gen_uuid


class AgentTool(Base):
    __tablename__ = "agent_tools"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False)
    tool_id: Mapped[str] = mapped_column(String, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    # JSON с заполненными значениями полей инструмента
    field_values: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # True если все обязательные поля заполнены
    is_configured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Связи
    agent: Mapped["UserAgent"] = relationship("UserAgent", back_populates="agent_tools")
    tool: Mapped["Tool"] = relationship("Tool", back_populates="agent_tools")

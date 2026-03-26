from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, gen_uuid


class ToolRunLog(Base):
    __tablename__ = "tool_run_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    tool_id: Mapped[str] = mapped_column(String, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    instance_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # instanceId от webhook
    trigger_type: Mapped[str] = mapped_column(String(50), default="manual")      # manual / chat / auto
    status: Mapped[str] = mapped_column(String(50), default="running")           # running / success / error
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, gen_uuid


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    tool_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    log_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agent: Mapped["UserAgent"] = relationship("UserAgent", back_populates="chat_messages")

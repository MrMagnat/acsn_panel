from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, gen_uuid


class UserAgent(Base):
    __tablename__ = "user_agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    energy_left: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    llm_url: Mapped[str] = mapped_column(String(500), default="")
    llm_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    llm_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[str] = mapped_column(Text, default="")
    energy_per_chat: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    prompt_suggestions: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="agents")
    agent_tools: Mapped[list["AgentTool"]] = relationship("AgentTool", back_populates="agent", cascade="all, delete-orphan")
    chat_messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="agent", cascade="all, delete-orphan")
    auto_triggers: Mapped[list["AutoTrigger"]] = relationship("AutoTrigger", back_populates="agent", cascade="all, delete-orphan")
    workflows: Mapped[list["Workflow"]] = relationship("Workflow", back_populates="agent", cascade="all, delete-orphan")

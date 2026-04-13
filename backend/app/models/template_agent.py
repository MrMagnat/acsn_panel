from sqlalchemy import String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from .base import Base, gen_uuid


class TemplateAgent(Base):
    __tablename__ = "template_agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    llm_url: Mapped[str] = mapped_column(String(500), default="")
    llm_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    llm_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[str] = mapped_column(Text, default="")
    energy_per_chat: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_maintenance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prompt_suggestions: Mapped[str] = mapped_column(Text, default="[]")
    # Скиллы из каталога, которые предустанавливаются агенту при создании из шаблона
    skill_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    template_tools: Mapped[list["TemplateAgentTool"]] = relationship("TemplateAgentTool", back_populates="template", cascade="all, delete-orphan")


class TemplateAgentTool(Base):
    __tablename__ = "template_agent_tools"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    template_id: Mapped[str] = mapped_column(String, ForeignKey("template_agents.id", ondelete="CASCADE"), nullable=False)
    tool_id: Mapped[str] = mapped_column(String, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)

    template: Mapped["TemplateAgent"] = relationship("TemplateAgent", back_populates="template_tools")
    tool: Mapped["Tool"] = relationship("Tool")

from sqlalchemy import String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, gen_uuid


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    trigger_hint: Mapped[str] = mapped_column(Text, default="")
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    energy_cost: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    fields: Mapped[list["ToolField"]] = relationship("ToolField", back_populates="tool", cascade="all, delete-orphan")
    agent_tools: Mapped[list["AgentTool"]] = relationship("AgentTool", back_populates="tool")


class ToolField(Base):
    __tablename__ = "tool_fields"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    tool_id: Mapped[str] = mapped_column(String, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hint: Mapped[str] = mapped_column(String(500), default="")
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # is_runtime=True → LLM видит поле как параметр и может менять через чат
    # is_runtime=False → поле только в настройках, LLM его не трогает
    is_runtime: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Для типа select: JSON-массив строк ["вариант1", "вариант2"]
    options: Mapped[str | None] = mapped_column(Text, nullable=True)

    tool: Mapped["Tool"] = relationship("Tool", back_populates="fields")

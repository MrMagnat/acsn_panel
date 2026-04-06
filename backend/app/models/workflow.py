from datetime import datetime, timezone
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from .base import Base, gen_uuid


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Новый воркфлоу")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Граф воркфлоу:
    # {
    #   "nodes": [{"id":"n1","tool_id":"...","position":{"x":0,"y":0},"input_data":{}}],
    #   "edges": [{"id":"e1","source":"n1","sourceHandle":"out_field","target":"n2","targetHandle":"in_field"}]
    # }
    graph_json: Mapped[dict] = mapped_column(JSON, default=lambda: {"nodes": [], "edges": []}, nullable=False)

    agent: Mapped["UserAgent"] = relationship("UserAgent", back_populates="workflows")
    runs: Mapped[list["WorkflowRun"]] = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    workflow_id: Mapped[str] = mapped_column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)  # manual | cron | chat
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)  # running | success | error
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {node_id: {field: value}}
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="runs")

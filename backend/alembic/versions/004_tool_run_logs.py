"""Add tool_run_logs table for tracking tool execution results

Revision ID: 004_tool_run_logs
Revises: 003_llm_settings
Create Date: 2026-03-26
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "004_tool_run_logs"
down_revision: Union[str, None] = "004_field_is_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tool_run_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("tool_id", sa.String(), nullable=False),
        sa.Column("tool_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("instance_id", sa.String(255), nullable=True),   # instanceId от webhook
        sa.Column("trigger_type", sa.String(50), nullable=False, server_default="manual"),  # manual/chat/auto
        sa.Column("status", sa.String(50), nullable=False, server_default="running"),       # running/success/error
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tool_run_logs_agent_id", "tool_run_logs", ["agent_id"])
    op.create_index("ix_tool_run_logs_instance_id", "tool_run_logs", ["instance_id"])


def downgrade() -> None:
    op.drop_index("ix_tool_run_logs_instance_id", table_name="tool_run_logs")
    op.drop_index("ix_tool_run_logs_agent_id", table_name="tool_run_logs")
    op.drop_table("tool_run_logs")

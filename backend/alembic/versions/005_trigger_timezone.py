"""Add timezone to auto_triggers

Revision ID: 005_trigger_timezone
Revises: 004_tool_run_logs
Create Date: 2026-03-27
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "005_trigger_timezone"
down_revision: Union[str, None] = "004_tool_run_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "auto_triggers",
        sa.Column("timezone", sa.String(100), nullable=False, server_default="UTC"),
    )


def downgrade() -> None:
    op.drop_column("auto_triggers", "timezone")

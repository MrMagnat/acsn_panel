"""Add trigger_hint to tools table

Revision ID: 004_tool_trigger_hint
Revises: 003_llm_settings
Create Date: 2026-03-26
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "004_tool_trigger_hint"
down_revision: Union[str, None] = "003_llm_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column("trigger_hint", sa.Text(), nullable=True, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("tools", "trigger_hint")

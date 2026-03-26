"""Add is_runtime to tool_fields

Revision ID: 004_field_is_runtime
Revises: 003_llm_settings
Create Date: 2026-03-26
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "004_field_is_runtime"
down_revision: Union[str, None] = "004_tool_trigger_hint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # is_runtime=True → поле показывается LLM как параметр (можно менять через чат)
    # is_runtime=False → поле скрыто от LLM, берётся только из настроек агента
    op.add_column(
        "tool_fields",
        sa.Column("is_runtime", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tool_fields", "is_runtime")

"""Add llm_model and llm_token to user_agents and template_agents

Revision ID: 003_llm_settings
Revises: 002_account_energy
Create Date: 2026-03-26
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "003_llm_settings"
down_revision: Union[str, None] = "002_account_energy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_agents", sa.Column("llm_model", sa.String(200), nullable=True))
    op.add_column("user_agents", sa.Column("llm_token", sa.String(500), nullable=True))
    op.add_column("template_agents", sa.Column("llm_model", sa.String(200), nullable=True))
    op.add_column("template_agents", sa.Column("llm_token", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("user_agents", "llm_model")
    op.drop_column("user_agents", "llm_token")
    op.drop_column("template_agents", "llm_model")
    op.drop_column("template_agents", "llm_token")

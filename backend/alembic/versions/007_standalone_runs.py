"""standalone_runs: make agent_id nullable in tool_run_logs

Revision ID: 007
Revises: 006
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006_chat_log_id'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('tool_run_logs', 'agent_id', nullable=True)


def downgrade():
    op.alter_column('tool_run_logs', 'agent_id', nullable=False)

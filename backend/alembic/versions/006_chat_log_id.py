"""Add log_id to chat_messages

Revision ID: 006_chat_log_id
Revises: 005_trigger_timezone
Create Date: 2026-04-01
"""
import sqlalchemy as sa
from alembic import op

revision = "006_chat_log_id"
down_revision = "005_trigger_timezone"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("chat_messages", sa.Column("log_id", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("chat_messages", "log_id")

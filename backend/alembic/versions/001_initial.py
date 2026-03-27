"""Initial migration — создаём все таблицы и seed admin

Revision ID: 001_initial
Revises:
Create Date: 2026-03-25

"""
from typing import Sequence, Union
import uuid
import os

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("plan", sa.String(100), nullable=False, server_default="free"),
        sa.Column("max_agents", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_tools_per_agent", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("energy_per_week", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("renewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tools",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("webhook_url", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("energy_cost", sa.Integer(), nullable=False, server_default="10"),
    )

    op.create_table(
        "tool_fields",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tool_id", sa.String(), sa.ForeignKey("tools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("hint", sa.String(500), nullable=False, server_default=""),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("field_type", sa.String(50), nullable=False, server_default="text"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "template_agents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("llm_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("skills", sa.Text(), nullable=False, server_default=""),
        sa.Column("energy_per_chat", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
    )

    op.create_table(
        "template_agent_tools",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("template_id", sa.String(), sa.ForeignKey("template_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_id", sa.String(), sa.ForeignKey("tools.id", ondelete="CASCADE"), nullable=False),
    )

    op.create_table(
        "user_agents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("energy_left", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("llm_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("skills", sa.Text(), nullable=False, server_default=""),
        sa.Column("energy_per_chat", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_agents_user_id", "user_agents", ["user_id"])

    op.create_table(
        "agent_tools",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_id", sa.String(), sa.ForeignKey("tools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_values", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_configured", sa.Boolean(), nullable=False, server_default="0"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("tool_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_agent_id", "chat_messages", ["agent_id"])

    op.create_table(
        "auto_triggers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), sa.ForeignKey("user_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_id", sa.String(), sa.ForeignKey("tools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cron_expr", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
    )

    # ── Seed: admin пользователь ───────────────────────────────────────────
    import bcrypt

    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@ascn.io")
    password_hash = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
    admin_id = str(uuid.uuid4())
    sub_id = str(uuid.uuid4())

    op.execute(
        sa.text(
            "INSERT INTO users (id, email, password_hash, name, is_admin) "
            "VALUES (:id, :email, :hash, :name, true)"
        ).bindparams(id=admin_id, email=admin_email, hash=password_hash, name="Administrator")
    )
    op.execute(
        sa.text(
            "INSERT INTO subscriptions (id, user_id, plan, max_agents, max_tools_per_agent, energy_per_week) "
            "VALUES (:id, :user_id, 'admin', 999, 999, 999999)"
        ).bindparams(id=sub_id, user_id=admin_id)
    )


def downgrade() -> None:
    op.drop_table("auto_triggers")
    op.drop_table("chat_messages")
    op.drop_table("agent_tools")
    op.drop_table("user_agents")
    op.drop_table("template_agent_tools")
    op.drop_table("template_agents")
    op.drop_table("tool_fields")
    op.drop_table("tools")
    op.drop_table("subscriptions")
    op.drop_table("users")

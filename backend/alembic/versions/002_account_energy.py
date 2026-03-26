"""Account-level energy: energy_left в subscriptions + таблица energy_transactions

Revision ID: 002_account_energy
Revises: 001_initial
Create Date: 2026-03-26
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "002_account_energy"
down_revision: Union[str, None] = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем energy_left в subscriptions (начальное значение = energy_per_week)
    op.add_column(
        "subscriptions",
        sa.Column("energy_left", sa.Integer(), nullable=False, server_default="100"),
    )

    # Синхронизируем energy_left = energy_per_week для существующих записей
    op.execute("UPDATE subscriptions SET energy_left = energy_per_week")

    # Таблица транзакций энергии (лог начислений и списаний)
    op.create_table(
        "energy_transactions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),          # >0 начисление, <0 списание
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("agent_id", sa.String(), nullable=True),          # какой агент потратил
        sa.Column("tool_name", sa.String(255), nullable=True),      # какой инструмент
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_energy_transactions_user_id", "energy_transactions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_energy_transactions_user_id", table_name="energy_transactions")
    op.drop_table("energy_transactions")
    op.drop_column("subscriptions", "energy_left")

"""tariff_plan_usd: rename price_rub to price_usd, add balance_usd_per_month

Revision ID: 020
Revises: 019
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tariff_plans', sa.Column('price_usd', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tariff_plans', sa.Column('balance_usd_per_month', sa.Integer(), nullable=False, server_default='0'))
    # Копируем значения из price_rub в price_usd
    op.execute("UPDATE tariff_plans SET price_usd = price_rub")
    op.drop_column('tariff_plans', 'price_rub')


def downgrade():
    op.add_column('tariff_plans', sa.Column('price_rub', sa.Integer(), nullable=False, server_default='0'))
    op.execute("UPDATE tariff_plans SET price_rub = price_usd")
    op.drop_column('tariff_plans', 'balance_usd_per_month')
    op.drop_column('tariff_plans', 'price_usd')

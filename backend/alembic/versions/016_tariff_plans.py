"""tariff_plans: own platform tariffs + subscription tokens

Revision ID: 016
Revises: 015
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    # Создаём таблицу тарифных планов
    op.create_table(
        'tariff_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_rub', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_agents', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_tools_per_agent', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('max_workflows', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('tokens_per_month', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    # Добавляем поля в subscriptions
    op.add_column('subscriptions', sa.Column('tariff_plan_id', sa.String(), nullable=True))
    op.add_column('subscriptions', sa.Column('tokens_left', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('subscriptions', sa.Column('tokens_per_month', sa.Integer(), nullable=False, server_default='0'))

    op.create_foreign_key(
        'fk_subscriptions_tariff_plan',
        'subscriptions', 'tariff_plans',
        ['tariff_plan_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade():
    op.drop_constraint('fk_subscriptions_tariff_plan', 'subscriptions', type_='foreignkey')
    op.drop_column('subscriptions', 'tokens_per_month')
    op.drop_column('subscriptions', 'tokens_left')
    op.drop_column('subscriptions', 'tariff_plan_id')
    op.drop_table('tariff_plans')

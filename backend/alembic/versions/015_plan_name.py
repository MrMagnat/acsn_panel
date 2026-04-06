"""plan_name: add ASCN tariff name to subscriptions

Revision ID: 015
Revises: 014
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa

revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('subscriptions', sa.Column('plan_name', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('subscriptions', 'plan_name')

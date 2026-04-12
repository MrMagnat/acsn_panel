"""tariff hide_upgrade flag

Revision ID: 024
Revises: 023
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tariff_plans', sa.Column('hide_upgrade', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('tariff_plans', 'hide_upgrade')

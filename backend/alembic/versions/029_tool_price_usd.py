"""add price_usd to tools

Revision ID: 029
Revises: 028
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tools', sa.Column('price_usd', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('tools', 'price_usd')

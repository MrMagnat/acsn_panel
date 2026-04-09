"""tariff_max_kb: add max_knowledge_bases to tariff_plans

Revision ID: 021
Revises: 020
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tariff_plans', sa.Column('max_knowledge_bases', sa.Integer(), nullable=False, server_default='1'))


def downgrade():
    op.drop_column('tariff_plans', 'max_knowledge_bases')

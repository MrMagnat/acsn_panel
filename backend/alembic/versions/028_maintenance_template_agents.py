"""Add is_maintenance to template_agents

Revision ID: 028
Revises: 027
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('template_agents', sa.Column('is_maintenance', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('template_agents', 'is_maintenance')

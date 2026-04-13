"""Add is_maintenance flag to tools, agents, skills

Revision ID: 027
Revises: 026
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tools', sa.Column('is_maintenance', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_agents', sa.Column('is_maintenance', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('skills', sa.Column('is_maintenance', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('template_agents', sa.Column('is_maintenance', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('tools', 'is_maintenance')
    op.drop_column('user_agents', 'is_maintenance')
    op.drop_column('skills', 'is_maintenance')
    op.drop_column('template_agents', 'is_maintenance')

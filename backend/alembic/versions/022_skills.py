"""skills: add skills catalog and agent_skills junction table

Revision ID: 022
Revises: 021
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'skills',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), server_default=''),
        sa.Column('content', sa.Text(), server_default=''),
        sa.Column('icon', sa.String(50), server_default='✨'),
        sa.Column('category', sa.String(100), server_default=''),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'agent_skills',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('agent_id', sa.String(), sa.ForeignKey('user_agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.String(), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
    )


def downgrade():
    op.drop_table('agent_skills')
    op.drop_table('skills')

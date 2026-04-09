"""template_agent_skills: add skill_ids JSON column to template_agents

Revision ID: 023
Revises: 022
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('template_agents', sa.Column('skill_ids', sa.JSON(), server_default='[]', nullable=False))


def downgrade():
    op.drop_column('template_agents', 'skill_ids')

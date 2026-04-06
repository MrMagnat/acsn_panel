"""prompt_suggestions: add quick prompt buttons to agents

Revision ID: 014
Revises: 013
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('template_agents', sa.Column('prompt_suggestions', sa.Text(), nullable=False, server_default='[]'))
    op.add_column('user_agents', sa.Column('prompt_suggestions', sa.Text(), nullable=False, server_default='[]'))


def downgrade():
    op.drop_column('template_agents', 'prompt_suggestions')
    op.drop_column('user_agents', 'prompt_suggestions')

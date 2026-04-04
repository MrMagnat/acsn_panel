"""field_options: add options column to tool_fields for select type

Revision ID: 008
Revises: 007
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tool_fields', sa.Column('options', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('tool_fields', 'options')

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
    with op.batch_alter_table('tool_fields') as batch_op:
        batch_op.add_column(sa.Column('options', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('tool_fields') as batch_op:
        batch_op.drop_column('options')

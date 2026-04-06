"""trigger input_data: add saved field values to auto_triggers

Revision ID: 016
Revises: 015
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa

revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('auto_triggers', sa.Column('input_data', sa.JSON(), nullable=False, server_default='{}'))


def downgrade():
    op.drop_column('auto_triggers', 'input_data')

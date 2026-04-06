"""tool output_fields: add output field definitions to tools

Revision ID: 017
Revises: 016
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tools', sa.Column('output_fields', sa.JSON(), nullable=False, server_default='[]'))


def downgrade():
    op.drop_column('tools', 'output_fields')

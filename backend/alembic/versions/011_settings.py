"""settings: key/value store for app configuration (onboarding etc.)

Revision ID: 011
Revises: 010
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table('settings')

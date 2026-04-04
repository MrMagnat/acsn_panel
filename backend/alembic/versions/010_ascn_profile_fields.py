"""ascn_profile_fields: add telegram, phone, avatar_url to users

Revision ID: 010
Revises: 009
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('telegram', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))


def downgrade():
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'telegram')

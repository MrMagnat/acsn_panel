"""ascn_user_id: add ascn_user_id to users for SSO integration

Revision ID: 009
Revises: 008
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('ascn_user_id', sa.Integer(), nullable=True))
    op.create_index('ix_users_ascn_user_id', 'users', ['ascn_user_id'], unique=True)


def downgrade():
    op.drop_index('ix_users_ascn_user_id', table_name='users')
    op.drop_column('users', 'ascn_user_id')

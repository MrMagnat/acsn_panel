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
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('ascn_user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_users_ascn_user_id', ['ascn_user_id'], unique=True)


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_ascn_user_id')
        batch_op.drop_column('ascn_user_id')

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
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('telegram', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('avatar_url', sa.String(500), nullable=True))


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('avatar_url')
        batch_op.drop_column('phone')
        batch_op.drop_column('telegram')

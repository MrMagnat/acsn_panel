"""tool owner_user_id
Revision ID: 025
Revises: 024
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tools', sa.Column('owner_user_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_tools_owner_user_id', 'tools', 'users', ['owner_user_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_tools_owner_user_id', 'tools', ['owner_user_id'])


def downgrade():
    op.drop_index('ix_tools_owner_user_id', 'tools')
    op.drop_constraint('fk_tools_owner_user_id', 'tools', type_='foreignkey')
    op.drop_column('tools', 'owner_user_id')

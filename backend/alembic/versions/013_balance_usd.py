"""balance_usd: add dollar balance to subscriptions for ASCN AI key reselling

Revision ID: 013
Revises: 012
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('subscriptions') as batch_op:
        batch_op.add_column(sa.Column('balance_usd', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('subscriptions') as batch_op:
        batch_op.drop_column('balance_usd')

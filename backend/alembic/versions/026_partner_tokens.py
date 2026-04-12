"""partner tokens and transactions
Revision ID: 026
Revises: 025
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('subscriptions', sa.Column('partner_tokens', sa.Integer(), nullable=False, server_default='0'))
    op.create_table('partner_transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('tool_id', sa.String(), nullable=True),
        sa.Column('tool_name', sa.String(255), nullable=True),
        sa.Column('from_user_id', sa.String(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(500), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_table('partner_withdraw_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade():
    op.drop_table('partner_withdraw_requests')
    op.drop_table('partner_transactions')
    op.drop_column('subscriptions', 'partner_tokens')

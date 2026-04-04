"""knowledge_base: tables for user knowledge bases (mini spreadsheet DB)

Revision ID: 012
Revises: 011
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'knowledge_bases',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        'kb_fields',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('kb_id', sa.String(), sa.ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('field_type', sa.String(50), nullable=False, server_default='text'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_table(
        'kb_records',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('kb_id', sa.String(), sa.ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('data', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('kb_records')
    op.drop_table('kb_fields')
    op.drop_table('knowledge_bases')

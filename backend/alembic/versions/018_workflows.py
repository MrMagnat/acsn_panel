"""workflows: create workflows and workflow_runs tables

Revision ID: 018
Revises: 017
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa

revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'workflows',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, server_default='Новый воркфлоу'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('graph_json', sa.JSON(), nullable=False, server_default='{"nodes":[],"edges":[]}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['user_agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workflow_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('workflow_runs')
    op.drop_table('workflows')

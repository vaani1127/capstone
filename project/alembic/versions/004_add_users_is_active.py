"""Add is_active column to users table for soft-delete support

Revision ID: 004
Revises: 003
Create Date: 2026-05-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active with server_default=true so all existing rows are backfilled
    # to active immediately — no data migration needed.
    op.add_column(
        'users',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
        ),
    )
    op.create_index('idx_users_is_active', 'users', ['is_active'])


def downgrade() -> None:
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_column('users', 'is_active')

"""Add token_version and is_walk_in columns to users table

Revision ID: 008
Revises: 007
Create Date: 2026-06-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # token_version: used to invalidate all existing JWTs for a user on
    # deactivation. server_default=0 backfills existing rows automatically.
    op.add_column(
        'users',
        sa.Column(
            'token_version',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )

    # is_walk_in: marks user accounts auto-created for walk-in patients.
    # server_default=false so all existing rows are treated as non-walk-in.
    op.add_column(
        'users',
        sa.Column(
            'is_walk_in',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'is_walk_in')
    op.drop_column('users', 'token_version')

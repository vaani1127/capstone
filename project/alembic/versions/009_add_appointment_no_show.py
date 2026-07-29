"""Add no_show to appointment_status enum and no_show_at column

Revision ID: 009
Revises: 008
Create Date: 2026-06-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only ALTER the PostgreSQL enum type if it actually exists.  The DB may
    # store appointments.status as VARCHAR (created via create_all()), in which
    # case the column already accepts 'no_show' and no DDL change is needed.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'appointment_status'
            ) THEN
                ALTER TYPE appointment_status ADD VALUE IF NOT EXISTS 'no_show';
            END IF;
        END
        $$;
    """)

    # Add the no_show_at timestamp column (nullable — only populated on NO_SHOW).
    op.add_column(
        'appointments',
        sa.Column('no_show_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('appointments', 'no_show_at')
    # Note: PostgreSQL does not support removing values from an enum type.
    # To fully revert, recreate the enum without 'no_show' and ALTER the column.

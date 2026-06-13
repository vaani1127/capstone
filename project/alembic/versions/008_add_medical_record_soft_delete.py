"""Add soft-delete columns to medical_records table

Adds is_deleted, deleted_at, and deleted_by so that medical records can be
logically removed without breaking the blockchain audit chain. Hard deletes
are prohibited — the row must always remain present for hash-chain verification.

Revision ID: 008
Revises: 007
Create Date: 2026-06-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # is_deleted: backfill all existing rows as NOT deleted (server_default=false)
    op.add_column(
        'medical_records',
        sa.Column(
            'is_deleted',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
    )

    # deleted_at: UTC timestamp of when the record was soft-deleted (NULL = not deleted)
    op.add_column(
        'medical_records',
        sa.Column(
            'deleted_at',
            sa.DateTime(),
            nullable=True,
        ),
    )

    # deleted_by: FK to users.id — who performed the soft-delete (NULL = not deleted)
    op.add_column(
        'medical_records',
        sa.Column(
            'deleted_by',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )

    # Index for efficient filtering of non-deleted records
    op.create_index(
        'idx_medical_records_is_deleted',
        'medical_records',
        ['is_deleted'],
    )


def downgrade() -> None:
    op.drop_index('idx_medical_records_is_deleted', table_name='medical_records')
    op.drop_column('medical_records', 'deleted_by')
    op.drop_column('medical_records', 'deleted_at')
    op.drop_column('medical_records', 'is_deleted')

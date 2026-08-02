"""Add missing updated_at and created_at/updated_at columns

Revision ID: 013
Revises: 012
Create Date: 2026-08-01 00:00:00.000000

Fixes critical schema mismatch:
- anomaly_alerts is missing updated_at column (ORM model expects it)
- audit_chain is missing both created_at and updated_at columns (ORM model expects both)

These columns are required by BaseModel but were not created in earlier migrations.
Existing alerts/audit rows will get current timestamp as created_at/updated_at.
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at to anomaly_alerts (created_at already exists from migration 003)
    op.add_column(
        'anomaly_alerts',
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )

    # Add created_at and updated_at to audit_chain (neither exists)
    op.add_column(
        'audit_chain',
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )
    op.add_column(
        'audit_chain',
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )

    # Create index on updated_at for both tables (common for timestamp queries)
    op.create_index(
        'ix_anomaly_alerts_updated_at',
        'anomaly_alerts',
        ['updated_at'],
    )
    op.create_index(
        'ix_audit_chain_updated_at',
        'audit_chain',
        ['updated_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_audit_chain_updated_at', table_name='audit_chain')
    op.drop_index('ix_anomaly_alerts_updated_at', table_name='anomaly_alerts')
    op.drop_column('audit_chain', 'updated_at')
    op.drop_column('audit_chain', 'created_at')
    op.drop_column('anomaly_alerts', 'updated_at')

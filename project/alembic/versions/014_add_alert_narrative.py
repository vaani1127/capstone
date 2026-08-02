"""Add narrative column to anomaly_alerts

Revision ID: 014
Revises: 013
Create Date: 2026-08-01 00:00:00.000000

Adds a narrative column (Text, nullable) to store template-based alert explanations.
Existing rows are backfilled with NULL (narrative only populated on new alert creation).
"""
from alembic import op
import sqlalchemy as sa


revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'anomaly_alerts',
        sa.Column(
            'narrative',
            sa.Text(),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_anomaly_alerts_narrative_not_null',
        'anomaly_alerts',
        ['narrative'],
        postgresql_where=sa.text('narrative IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('ix_anomaly_alerts_narrative_not_null', table_name='anomaly_alerts')
    op.drop_column('anomaly_alerts', 'narrative')

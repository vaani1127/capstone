"""Add trigger_type column to anomaly_alerts

Revision ID: 011
Revises: 010
Create Date: 2026-06-23 00:00:00.000000

Adds a trigger_type VARCHAR(32) column to anomaly_alerts so that
sustained-trend escalation alerts can be identified structurally rather
than by substring-matching the explanation text.

Existing rows are back-filled to "single_event" (the previous and only
behaviour before this migration).
"""
from alembic import op
import sqlalchemy as sa

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'anomaly_alerts',
        sa.Column(
            'trigger_type',
            sa.String(32),
            nullable=False,
            server_default='single_event',
        ),
    )
    op.create_index(
        'ix_anomaly_alerts_trigger_type',
        'anomaly_alerts',
        ['trigger_type'],
    )


def downgrade() -> None:
    op.drop_index('ix_anomaly_alerts_trigger_type', table_name='anomaly_alerts')
    op.drop_column('anomaly_alerts', 'trigger_type')

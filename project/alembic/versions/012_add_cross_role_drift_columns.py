"""Add cross-role drift detection columns to behavioral_scores

Revision ID: 012
Revises: 011
Create Date: 2026-08-01 00:00:00.000000

Adds three columns to behavioral_scores to support cross-role behavioral
drift detection:
  - nearest_other_role: VARCHAR(32), the role whose centroid the user is
    closest to (other than their own role). Used for insider-threat detection
    when a user's access pattern drifts toward higher-privilege operations.
  - cross_role_distance: FLOAT, the Euclidean distance from the user's
    feature vector to the nearest other role's centroid.
  - trigger_type: VARCHAR(32), the type of trigger that caused this score
    to be escalated (if any) — "single_event", "sustained_trend", or
    "identity_drift". Nullable for backward compatibility.
"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'behavioral_scores',
        sa.Column(
            'nearest_other_role',
            sa.String(32),
            nullable=True,
        ),
    )
    op.add_column(
        'behavioral_scores',
        sa.Column(
            'cross_role_distance',
            sa.Float(),
            nullable=True,
        ),
    )
    op.add_column(
        'behavioral_scores',
        sa.Column(
            'trigger_type',
            sa.String(32),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_behavioral_scores_nearest_other_role',
        'behavioral_scores',
        ['nearest_other_role'],
    )


def downgrade() -> None:
    op.drop_index('ix_behavioral_scores_nearest_other_role', table_name='behavioral_scores')
    op.drop_column('behavioral_scores', 'trigger_type')
    op.drop_column('behavioral_scores', 'cross_role_distance')
    op.drop_column('behavioral_scores', 'nearest_other_role')

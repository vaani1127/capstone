"""Add consultation_start_time column to appointments

Revision ID: 015
Revises: 014
Create Date: 2026-08-06 00:00:00.000000

Adds consultation_start_time (DateTime, nullable) to track when a
consultation started (status transitions to IN_PROGRESS). This column
existed on the SQLAlchemy model but was never added by a migration.
"""
from alembic import op
import sqlalchemy as sa


revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'appointments',
        sa.Column('consultation_start_time', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('appointments', 'consultation_start_time')

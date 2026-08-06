"""Add missing updated_at columns to doctors and medical_records

Revision ID: 016
Revises: 015
Create Date: 2026-08-06 00:00:00.000000

Fixes schema drift: doctors and medical_records were missing the
updated_at column that BaseModel requires on every model. Found via a
full model-vs-live-schema audit after the appointments.consultation_start_time
gap (migration 015) surfaced the same class of bug.
"""
from alembic import op
import sqlalchemy as sa


revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'doctors',
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )
    op.add_column(
        'medical_records',
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
    )


def downgrade() -> None:
    op.drop_column('medical_records', 'updated_at')
    op.drop_column('doctors', 'updated_at')

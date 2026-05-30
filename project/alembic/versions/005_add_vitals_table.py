"""Add vitals table for patient vital sign recordings

Revision ID: 005
Revises: 004
Create Date: 2026-05-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'vitals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('recorded_by', sa.Integer(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('systolic_bp', sa.Integer(), nullable=True),
        sa.Column('diastolic_bp', sa.Integer(), nullable=True),
        sa.Column('heart_rate', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('respiratory_rate', sa.Integer(), nullable=True),
        sa.Column('oxygen_saturation', sa.Float(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('height_cm', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'],
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'],
                                ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_vitals_patient_id', 'vitals', ['patient_id'])
    op.create_index('idx_vitals_appointment_id', 'vitals', ['appointment_id'])
    op.create_index('idx_vitals_recorded_by', 'vitals', ['recorded_by'])
    op.create_index('idx_vitals_recorded_at', 'vitals', ['recorded_at'])


def downgrade() -> None:
    op.drop_index('idx_vitals_recorded_at', table_name='vitals')
    op.drop_index('idx_vitals_recorded_by', table_name='vitals')
    op.drop_index('idx_vitals_appointment_id', table_name='vitals')
    op.drop_index('idx_vitals_patient_id', table_name='vitals')
    op.drop_table('vitals')

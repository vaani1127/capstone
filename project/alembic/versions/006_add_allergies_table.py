"""Add allergies table for patient allergy records

Revision ID: 006
Revises: 005
Create Date: 2026-05-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'allergies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('recorded_by', sa.Integer(), nullable=False),
        sa.Column('allergen', sa.String(255), nullable=False),
        sa.Column('reaction', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('onset_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint(
            "severity IN ('mild', 'moderate', 'severe')",
            name='ck_allergies_severity',
        ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_allergies_patient_id', 'allergies', ['patient_id'])
    op.create_index('idx_allergies_recorded_by', 'allergies', ['recorded_by'])
    op.create_index('idx_allergies_is_active', 'allergies', ['is_active'])
    op.create_index('idx_allergies_severity', 'allergies', ['severity'])


def downgrade() -> None:
    op.drop_index('idx_allergies_severity', table_name='allergies')
    op.drop_index('idx_allergies_is_active', table_name='allergies')
    op.drop_index('idx_allergies_recorded_by', table_name='allergies')
    op.drop_index('idx_allergies_patient_id', table_name='allergies')
    op.drop_table('allergies')

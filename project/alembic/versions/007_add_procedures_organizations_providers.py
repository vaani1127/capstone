"""Add procedures, organizations, and providers tables

Revision ID: 007
Revises: 006
Create Date: 2026-05-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # organizations — standalone, no patient/user dependency
    # -------------------------------------------------------------------------
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('zip', sa.String(20), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('revenue', sa.Numeric(15, 2), nullable=True),
        sa.Column('utilization', sa.Float(), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_organizations_name', 'organizations', ['name'])
    op.create_index('idx_organizations_city', 'organizations', ['city'])
    op.create_index('idx_organizations_state', 'organizations', ['state'])

    # -------------------------------------------------------------------------
    # providers — may or may not have a system user account or org affiliation
    # -------------------------------------------------------------------------
    op.create_table(
        'providers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('gender', sa.String(10), nullable=True),
        sa.Column('speciality', sa.String(100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('zip', sa.String(20), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('encounter_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('procedure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_providers_user_id', 'providers', ['user_id'])
    op.create_index('idx_providers_organization_id', 'providers', ['organization_id'])
    op.create_index('idx_providers_speciality', 'providers', ['speciality'])
    op.create_index('idx_providers_city', 'providers', ['city'])

    # -------------------------------------------------------------------------
    # procedures — linked to patients; performer and appointment are nullable
    # -------------------------------------------------------------------------
    op.create_table(
        'procedures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('procedure_code', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('performed_at', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('base_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['encounter_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_procedures_patient_id', 'procedures', ['patient_id'])
    op.create_index('idx_procedures_encounter_id', 'procedures', ['encounter_id'])
    op.create_index('idx_procedures_performed_by', 'procedures', ['performed_by'])
    op.create_index('idx_procedures_performed_at', 'procedures', ['performed_at'])


def downgrade() -> None:
    op.drop_index('idx_procedures_performed_at', table_name='procedures')
    op.drop_index('idx_procedures_performed_by', table_name='procedures')
    op.drop_index('idx_procedures_encounter_id', table_name='procedures')
    op.drop_index('idx_procedures_patient_id', table_name='procedures')
    op.drop_table('procedures')

    op.drop_index('idx_providers_city', table_name='providers')
    op.drop_index('idx_providers_speciality', table_name='providers')
    op.drop_index('idx_providers_organization_id', table_name='providers')
    op.drop_index('idx_providers_user_id', table_name='providers')
    op.drop_table('providers')

    op.drop_index('idx_organizations_state', table_name='organizations')
    op.drop_index('idx_organizations_city', table_name='organizations')
    op.drop_index('idx_organizations_name', table_name='organizations')
    op.drop_table('organizations')

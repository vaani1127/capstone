"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2026-02-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # ============================================================================
    # USERS TABLE
    # ============================================================================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint("role IN ('Admin', 'Doctor', 'Nurse', 'Patient')", name='users_role_check'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        comment='Stores all system users with role-based access control'
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])
    
    # ============================================================================
    # PATIENTS TABLE
    # ============================================================================
    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('blood_group', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Stores patient demographic and contact information'
    )
    op.create_index('idx_patients_user_id', 'patients', ['user_id'])
    
    # ============================================================================
    # DOCTORS TABLE
    # ============================================================================
    op.create_table(
        'doctors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('specialization', sa.String(length=255), nullable=True),
        sa.Column('license_number', sa.String(length=100), nullable=True),
        sa.Column('average_consultation_duration', sa.Integer(), server_default='15', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Stores doctor credentials and consultation metrics'
    )
    op.create_index('idx_doctors_user_id', 'doctors', ['user_id'])
    op.create_index('idx_doctors_specialization', 'doctors', ['specialization'])
    
    # Add column comment
    op.execute("""
        COMMENT ON COLUMN doctors.average_consultation_duration IS 
        'Rolling average consultation time in minutes, updated after each consultation'
    """)
    
    # ============================================================================
    # APPOINTMENTS TABLE
    # ============================================================================
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('doctor_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='scheduled', nullable=True),
        sa.Column('appointment_type', sa.String(length=50), server_default='scheduled', nullable=True),
        sa.Column('queue_position', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint("status IN ('scheduled', 'checked_in', 'in_progress', 'completed', 'cancelled')", 
                          name='appointments_status_check'),
        sa.CheckConstraint("appointment_type IN ('scheduled', 'walk_in')", 
                          name='appointments_type_check'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Manages appointments and queue system'
    )
    op.create_index('idx_appointments_doctor_status', 'appointments', ['doctor_id', 'status'])
    op.create_index('idx_appointments_patient', 'appointments', ['patient_id'])
    op.create_index('idx_appointments_scheduled_time', 'appointments', ['scheduled_time'])
    op.create_index('idx_appointments_queue_position', 'appointments', ['doctor_id', 'queue_position'],
                   postgresql_where=sa.text("status IN ('checked_in', 'in_progress')"))
    
    # Add column comment
    op.execute("""
        COMMENT ON COLUMN appointments.queue_position IS 
        'Position in the doctor queue, NULL if not in queue'
    """)
    
    # ============================================================================
    # MEDICAL RECORDS TABLE
    # ============================================================================
    op.create_table(
        'medical_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('doctor_id', sa.Integer(), nullable=True),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('consultation_notes', sa.Text(), nullable=True),
        sa.Column('diagnosis', sa.Text(), nullable=True),
        sa.Column('prescription', sa.Text(), nullable=True),
        sa.Column('version_number', sa.Integer(), server_default='1', nullable=True),
        sa.Column('parent_record_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_record_id'], ['medical_records.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Stores medical records with version control'
    )
    op.create_index('idx_medical_records_patient', 'medical_records', ['patient_id'])
    op.create_index('idx_medical_records_doctor', 'medical_records', ['doctor_id'])
    op.create_index('idx_medical_records_appointment', 'medical_records', ['appointment_id'])
    op.create_index('idx_medical_records_parent', 'medical_records', ['parent_record_id'])
    op.create_index('idx_medical_records_created_at', 'medical_records', [sa.text('created_at DESC')])
    
    # Add column comments
    op.execute("""
        COMMENT ON COLUMN medical_records.version_number IS 
        'Version number for record versioning, increments on updates'
    """)
    op.execute("""
        COMMENT ON COLUMN medical_records.parent_record_id IS 
        'References the original record for version tracking'
    """)
    
    # ============================================================================
    # AUDIT CHAIN TABLE
    # ============================================================================
    op.create_table(
        'audit_chain',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('record_type', sa.String(length=50), nullable=False),
        sa.Column('record_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('previous_hash', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_tampered', sa.Boolean(), server_default='false', nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Blockchain-inspired audit trail for integrity verification'
    )
    op.create_index('idx_audit_chain_record', 'audit_chain', ['record_id', 'record_type'])
    op.create_index('idx_audit_chain_timestamp', 'audit_chain', [sa.text('timestamp DESC')])
    op.create_index('idx_audit_chain_user', 'audit_chain', ['user_id'])
    op.create_index('idx_audit_chain_hash', 'audit_chain', ['hash'])
    op.create_index('idx_audit_chain_tampered', 'audit_chain', ['is_tampered'],
                   postgresql_where=sa.text('is_tampered = TRUE'))
    
    # Add column comments
    op.execute("""
        COMMENT ON COLUMN audit_chain.hash IS 
        'SHA-256 hash of record_data + timestamp + user_id + previous_hash'
    """)
    op.execute("""
        COMMENT ON COLUMN audit_chain.previous_hash IS 
        'Hash of the previous audit entry, "0" for genesis block'
    """)
    op.execute("""
        COMMENT ON COLUMN audit_chain.is_tampered IS 
        'Flag indicating if tampering was detected during verification'
    """)
    
    # ============================================================================
    # TRIGGERS
    # ============================================================================
    
    # Create trigger function for updating updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers for users table
    op.execute("""
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create triggers for appointments table
    op.execute("""
        CREATE TRIGGER update_appointments_updated_at
            BEFORE UPDATE ON appointments
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_appointments_updated_at ON appointments')
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON users')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('audit_chain')
    op.drop_table('medical_records')
    op.drop_table('appointments')
    op.drop_table('doctors')
    op.drop_table('patients')
    op.drop_table('users')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')

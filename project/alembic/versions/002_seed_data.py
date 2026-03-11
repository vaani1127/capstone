"""Seed data for testing

Revision ID: 002
Revises: 001
Create Date: 2026-02-27 10:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Insert seed data for testing purposes.
    Passwords are hashed using bcrypt with the plaintext password 'password123'
    """
    
    # Bcrypt hash for 'password123' (cost factor 12)
    password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYqYqYqYq'
    
    # ============================================================================
    # SEED USERS
    # ============================================================================
    op.execute(f"""
        INSERT INTO users (name, email, password_hash, role, created_at, updated_at) VALUES
        ('Admin User', 'admin@healthsaathi.com', '{password_hash}', 'Admin', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Dr. Rajesh Kumar', 'rajesh.kumar@healthsaathi.com', '{password_hash}', 'Doctor', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Dr. Priya Sharma', 'priya.sharma@healthsaathi.com', '{password_hash}', 'Doctor', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Dr. Amit Patel', 'amit.patel@healthsaathi.com', '{password_hash}', 'Doctor', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Nurse Sunita', 'sunita@healthsaathi.com', '{password_hash}', 'Nurse', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Nurse Kavita', 'kavita@healthsaathi.com', '{password_hash}', 'Nurse', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Rahul Verma', 'rahul.verma@example.com', '{password_hash}', 'Patient', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Anjali Singh', 'anjali.singh@example.com', '{password_hash}', 'Patient', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Vikram Malhotra', 'vikram.malhotra@example.com', '{password_hash}', 'Patient', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Neha Gupta', 'neha.gupta@example.com', '{password_hash}', 'Patient', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Arjun Reddy', 'arjun.reddy@example.com', '{password_hash}', 'Patient', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)
    
    # ============================================================================
    # SEED DOCTORS
    # ============================================================================
    op.execute("""
        INSERT INTO doctors (user_id, specialization, license_number, average_consultation_duration, created_at) VALUES
        (2, 'General Medicine', 'MED-2024-001', 15, CURRENT_TIMESTAMP),
        (3, 'Pediatrics', 'MED-2024-002', 20, CURRENT_TIMESTAMP),
        (4, 'Cardiology', 'MED-2024-003', 25, CURRENT_TIMESTAMP)
    """)
    
    # ============================================================================
    # SEED PATIENTS
    # ============================================================================
    op.execute("""
        INSERT INTO patients (user_id, date_of_birth, gender, phone, address, blood_group, created_at) VALUES
        (7, '1985-03-15', 'Male', '+91-9876543210', '123 MG Road, Bangalore, Karnataka', 'O+', CURRENT_TIMESTAMP),
        (8, '1990-07-22', 'Female', '+91-9876543211', '456 Park Street, Kolkata, West Bengal', 'A+', CURRENT_TIMESTAMP),
        (9, '1978-11-08', 'Male', '+91-9876543212', '789 Marine Drive, Mumbai, Maharashtra', 'B+', CURRENT_TIMESTAMP),
        (10, '1995-05-30', 'Female', '+91-9876543213', '321 Connaught Place, New Delhi', 'AB+', CURRENT_TIMESTAMP),
        (11, '1982-09-12', 'Male', '+91-9876543214', '654 Anna Salai, Chennai, Tamil Nadu', 'O-', CURRENT_TIMESTAMP)
    """)
    
    # ============================================================================
    # SEED APPOINTMENTS
    # ============================================================================
    # Create some scheduled appointments for today and tomorrow
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    op.execute(f"""
        INSERT INTO appointments (patient_id, doctor_id, scheduled_time, status, appointment_type, queue_position, created_at, updated_at) VALUES
        -- Today's appointments
        (1, 1, '{today} 09:00:00', 'completed', 'scheduled', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (2, 1, '{today} 09:30:00', 'completed', 'scheduled', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (3, 2, '{today} 10:00:00', 'in_progress', 'scheduled', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (4, 1, '{today} 10:00:00', 'checked_in', 'scheduled', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (5, 1, '{today} 10:30:00', 'checked_in', 'walk_in', 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (1, 3, '{today} 11:00:00', 'scheduled', 'scheduled', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        
        -- Tomorrow's appointments
        (2, 2, '{tomorrow} 09:00:00', 'scheduled', 'scheduled', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (3, 1, '{tomorrow} 10:00:00', 'scheduled', 'scheduled', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (4, 3, '{tomorrow} 11:00:00', 'scheduled', 'scheduled', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (5, 2, '{tomorrow} 14:00:00', 'scheduled', 'scheduled', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)
    
    # ============================================================================
    # SEED MEDICAL RECORDS
    # ============================================================================
    op.execute("""
        INSERT INTO medical_records (patient_id, doctor_id, appointment_id, consultation_notes, diagnosis, prescription, version_number, parent_record_id, created_by, created_at) VALUES
        (1, 1, 1, 
         'Patient complained of mild fever and headache for 2 days. Temperature: 99.5°F. BP: 120/80. No other symptoms observed.',
         'Viral Fever',
         'Tab. Paracetamol 500mg - 1 tablet thrice daily for 3 days. Plenty of fluids and rest.',
         1, NULL, 2, CURRENT_TIMESTAMP),
        
        (2, 1, 2,
         'Follow-up visit for diabetes management. Blood sugar levels stable. Patient following diet plan.',
         'Type 2 Diabetes Mellitus - Controlled',
         'Tab. Metformin 500mg - 1 tablet twice daily (continue). Review after 3 months.',
         1, NULL, 2, CURRENT_TIMESTAMP),
        
        (3, 2, 3,
         'Child presented with cough and cold symptoms. No fever. Throat slightly red. Chest clear on auscultation.',
         'Upper Respiratory Tract Infection',
         'Syrup Cetirizine 5ml twice daily for 5 days. Steam inhalation. Avoid cold foods.',
         1, NULL, 3, CURRENT_TIMESTAMP)
    """)
    
    # ============================================================================
    # SEED AUDIT CHAIN (Genesis Block + Medical Records)
    # ============================================================================
    # Genesis block
    op.execute("""
        INSERT INTO audit_chain (record_id, record_type, record_data, hash, previous_hash, timestamp, user_id, is_tampered) VALUES
        (0, 'genesis', '{"block": "genesis", "message": "HealthSaathi Audit Chain Initialized"}', 
         '0000000000000000000000000000000000000000000000000000000000000000', 
         '0', 
         CURRENT_TIMESTAMP, 
         1, 
         false)
    """)
    
    # Audit entries for medical records (simplified hashes for seed data)
    op.execute("""
        INSERT INTO audit_chain (record_id, record_type, record_data, hash, previous_hash, timestamp, user_id, is_tampered) VALUES
        (1, 'medical_record', 
         '{"patient_id": 1, "doctor_id": 1, "diagnosis": "Viral Fever"}',
         'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2',
         '0000000000000000000000000000000000000000000000000000000000000000',
         CURRENT_TIMESTAMP,
         2,
         false),
        
        (2, 'medical_record',
         '{"patient_id": 2, "doctor_id": 1, "diagnosis": "Type 2 Diabetes Mellitus - Controlled"}',
         'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3',
         'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2',
         CURRENT_TIMESTAMP,
         2,
         false),
        
        (3, 'medical_record',
         '{"patient_id": 3, "doctor_id": 2, "diagnosis": "Upper Respiratory Tract Infection"}',
         'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4',
         'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3',
         CURRENT_TIMESTAMP,
         3,
         false)
    """)


def downgrade() -> None:
    """
    Remove all seed data
    """
    # Delete in reverse order to respect foreign key constraints
    op.execute('DELETE FROM audit_chain WHERE id > 0')
    op.execute('DELETE FROM medical_records')
    op.execute('DELETE FROM appointments')
    op.execute('DELETE FROM patients')
    op.execute('DELETE FROM doctors')
    op.execute('DELETE FROM users')

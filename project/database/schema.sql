-- HealthSaathi Database Schema
-- PostgreSQL Database Schema for Healthcare Management System
-- Version: 1.0
-- Created: 2026-02-27

-- Enable UUID extension for future use
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS TABLE
-- ============================================================================
-- Stores all system users with role-based access control
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('Admin', 'Doctor', 'Nurse', 'Patient')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster email lookups during authentication
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================================
-- PATIENTS TABLE
-- ============================================================================
-- Stores patient demographic information
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth DATE,
    gender VARCHAR(20),
    phone VARCHAR(20),
    address TEXT,
    blood_group VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster user_id lookups
CREATE INDEX idx_patients_user_id ON patients(user_id);

-- ============================================================================
-- DOCTORS TABLE
-- ============================================================================
-- Stores doctor-specific information and consultation metrics
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    specialization VARCHAR(255),
    license_number VARCHAR(100),
    average_consultation_duration INTEGER DEFAULT 15, -- in minutes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster user_id lookups
CREATE INDEX idx_doctors_user_id ON doctors(user_id);
CREATE INDEX idx_doctors_specialization ON doctors(specialization);

-- ============================================================================
-- APPOINTMENTS TABLE
-- ============================================================================
-- Stores all appointments (scheduled and walk-in) with queue management
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'checked_in', 'in_progress', 'completed', 'cancelled')),
    appointment_type VARCHAR(50) DEFAULT 'scheduled' CHECK (appointment_type IN ('scheduled', 'walk_in')),
    queue_position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Composite index for efficient queue queries by doctor and status
CREATE INDEX idx_appointments_doctor_status ON appointments(doctor_id, status);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_scheduled_time ON appointments(scheduled_time);
CREATE INDEX idx_appointments_queue_position ON appointments(doctor_id, queue_position) WHERE status IN ('checked_in', 'in_progress');

-- ============================================================================
-- MEDICAL RECORDS TABLE
-- ============================================================================
-- Stores consultation notes, diagnoses, and prescriptions with versioning
CREATE TABLE medical_records (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
    consultation_notes TEXT,
    diagnosis TEXT,
    prescription TEXT,
    version_number INTEGER DEFAULT 1,
    parent_record_id INTEGER REFERENCES medical_records(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient patient history retrieval
CREATE INDEX idx_medical_records_patient ON medical_records(patient_id);
CREATE INDEX idx_medical_records_doctor ON medical_records(doctor_id);
CREATE INDEX idx_medical_records_appointment ON medical_records(appointment_id);
CREATE INDEX idx_medical_records_parent ON medical_records(parent_record_id);
CREATE INDEX idx_medical_records_created_at ON medical_records(created_at DESC);

-- ============================================================================
-- AUDIT CHAIN TABLE
-- ============================================================================
-- Blockchain-inspired audit trail for tamper detection and integrity verification
CREATE TABLE audit_chain (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    record_type VARCHAR(50) NOT NULL,
    record_data JSONB NOT NULL,
    hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_tampered BOOLEAN DEFAULT FALSE
);

-- Indexes for efficient audit queries and chain verification
CREATE INDEX idx_audit_chain_record ON audit_chain(record_id, record_type);
CREATE INDEX idx_audit_chain_timestamp ON audit_chain(timestamp DESC);
CREATE INDEX idx_audit_chain_user ON audit_chain(user_id);
CREATE INDEX idx_audit_chain_hash ON audit_chain(hash);
CREATE INDEX idx_audit_chain_tampered ON audit_chain(is_tampered) WHERE is_tampered = TRUE;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to automatically update updated_at timestamp on users table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'Stores all system users with role-based access control';
COMMENT ON TABLE patients IS 'Stores patient demographic and contact information';
COMMENT ON TABLE doctors IS 'Stores doctor credentials and consultation metrics';
COMMENT ON TABLE appointments IS 'Manages appointments and queue system';
COMMENT ON TABLE medical_records IS 'Stores medical records with version control';
COMMENT ON TABLE audit_chain IS 'Blockchain-inspired audit trail for integrity verification';

COMMENT ON COLUMN doctors.average_consultation_duration IS 'Rolling average consultation time in minutes, updated after each consultation';
COMMENT ON COLUMN appointments.queue_position IS 'Position in the doctor queue, NULL if not in queue';
COMMENT ON COLUMN medical_records.version_number IS 'Version number for record versioning, increments on updates';
COMMENT ON COLUMN medical_records.parent_record_id IS 'References the original record for version tracking';
COMMENT ON COLUMN audit_chain.hash IS 'SHA-256 hash of record_data + timestamp + user_id + previous_hash';
COMMENT ON COLUMN audit_chain.previous_hash IS 'Hash of the previous audit entry, "0" for genesis block';
COMMENT ON COLUMN audit_chain.is_tampered IS 'Flag indicating if tampering was detected during verification';

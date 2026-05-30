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
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster email lookups during authentication
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    consultation_start_time TIMESTAMP,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    is_tampered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient audit queries and chain verification
CREATE INDEX idx_audit_chain_record ON audit_chain(record_id, record_type);
CREATE INDEX idx_audit_chain_timestamp ON audit_chain(timestamp DESC);
CREATE INDEX idx_audit_chain_user ON audit_chain(user_id);
CREATE INDEX idx_audit_chain_hash ON audit_chain(hash);
CREATE INDEX idx_audit_chain_tampered ON audit_chain(is_tampered) WHERE is_tampered = TRUE;

-- ============================================================================
-- ANOMALY ALERTS TABLE
-- ============================================================================
-- Stores ML-generated behavioural anomaly detection results per user session
CREATE TABLE IF NOT EXISTS anomaly_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    anomaly_score FLOAT NOT NULL,
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),
    top_features JSONB NOT NULL DEFAULT '[]',
    explanation TEXT NOT NULL,
    audit_entry_id INTEGER REFERENCES audit_chain(id) ON DELETE SET NULL,
    is_acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_user ON anomaly_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_severity ON anomaly_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_created_at ON anomaly_alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_acknowledged ON anomaly_alerts(is_acknowledged);

COMMENT ON TABLE anomaly_alerts IS 'ML-generated behavioural anomaly detection alerts with SHAP explainability';
COMMENT ON COLUMN anomaly_alerts.anomaly_score IS 'IsolationForest anomaly score normalised to 0–1; alerts persisted when score > 0.50';
COMMENT ON COLUMN anomaly_alerts.severity IS 'LOW (<0.60), MEDIUM (0.60–0.74), HIGH (>=0.75)';
COMMENT ON COLUMN anomaly_alerts.top_features IS 'JSON array of top-3 SHAP feature attributions: [{feature, value, contribution}]';
COMMENT ON COLUMN anomaly_alerts.audit_entry_id IS 'Triggering audit_chain block; SET NULL on audit entry deletion';

-- ============================================================================
-- VITALS TABLE
-- ============================================================================
-- Stores patient vital sign measurements recorded by nurses or doctors.
-- BMI is computed in the application layer and stored for fast retrieval.
CREATE TABLE vitals (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
    recorded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    temperature FLOAT,
    respiratory_rate INTEGER,
    oxygen_saturation FLOAT,
    weight_kg FLOAT,
    height_cm FLOAT,
    bmi FLOAT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vitals_patient_id ON vitals(patient_id);
CREATE INDEX idx_vitals_appointment_id ON vitals(appointment_id);
CREATE INDEX idx_vitals_recorded_by ON vitals(recorded_by);
CREATE INDEX idx_vitals_recorded_at ON vitals(recorded_at DESC);

COMMENT ON TABLE vitals IS 'Patient vital sign measurements; BMI computed from weight_kg and height_cm in the application layer';
COMMENT ON COLUMN vitals.temperature IS 'Body temperature in degrees Fahrenheit';
COMMENT ON COLUMN vitals.oxygen_saturation IS 'Peripheral oxygen saturation (SpO2) as a percentage 0-100';
COMMENT ON COLUMN vitals.bmi IS 'Body Mass Index: weight_kg / (height_cm / 100)^2, stored to 1 decimal place';

-- ============================================================================
-- ALLERGIES TABLE
-- ============================================================================
-- Stores patient allergy records with severity classification.
-- Records are never deleted; doctors deactivate them to preserve full history.
CREATE TABLE allergies (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    recorded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    allergen VARCHAR(255) NOT NULL,
    reaction TEXT,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('mild', 'moderate', 'severe')),
    onset_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_allergies_patient_id ON allergies(patient_id);
CREATE INDEX idx_allergies_recorded_by ON allergies(recorded_by);
CREATE INDEX idx_allergies_is_active ON allergies(is_active);
CREATE INDEX idx_allergies_severity ON allergies(severity);

COMMENT ON TABLE allergies IS 'Patient allergy records; is_active=false marks deactivated (not deleted) entries';
COMMENT ON COLUMN allergies.severity IS 'Clinical severity tier: mild | moderate | severe';
COMMENT ON COLUMN allergies.is_active IS 'Set to false by a doctor when the allergy is no longer relevant; record is preserved for audit history';

-- ============================================================================
-- ORGANIZATIONS TABLE
-- ============================================================================
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    phone VARCHAR(30),
    revenue NUMERIC(15, 2),
    utilization FLOAT,
    lat FLOAT,
    lon FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_organizations_city ON organizations(city);
CREATE INDEX idx_organizations_state ON organizations(state);

COMMENT ON TABLE organizations IS 'Healthcare organisations; revenue and utilization are pre-aggregated analytics fields';

-- ============================================================================
-- PROVIDERS TABLE
-- ============================================================================
CREATE TABLE providers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(10),
    speciality VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    lat FLOAT,
    lon FLOAT,
    encounter_count INTEGER NOT NULL DEFAULT 0,
    procedure_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_providers_user_id ON providers(user_id);
CREATE INDEX idx_providers_organization_id ON providers(organization_id);
CREATE INDEX idx_providers_speciality ON providers(speciality);
CREATE INDEX idx_providers_city ON providers(city);

COMMENT ON TABLE providers IS 'Healthcare providers; user_id is nullable for externally imported providers without system accounts';
COMMENT ON COLUMN providers.encounter_count IS 'Pre-aggregated count of encounters; updated by import pipeline';
COMMENT ON COLUMN providers.procedure_count IS 'Pre-aggregated count of procedures; updated by import pipeline';

-- ============================================================================
-- PROCEDURES TABLE
-- ============================================================================
CREATE TABLE procedures (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
    performed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    procedure_code VARCHAR(20),
    description TEXT NOT NULL,
    performed_at TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    outcome TEXT,
    base_cost NUMERIC(10, 2),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_procedures_patient_id ON procedures(patient_id);
CREATE INDEX idx_procedures_encounter_id ON procedures(encounter_id);
CREATE INDEX idx_procedures_performed_by ON procedures(performed_by);
CREATE INDEX idx_procedures_performed_at ON procedures(performed_at DESC);

COMMENT ON TABLE procedures IS 'Clinical procedures performed on patients; base_cost is the list price before insurance adjustments';
COMMENT ON COLUMN procedures.procedure_code IS 'ICD or CPT procedure code (optional)';

COMMENT ON TABLE vitals IS 'Patient vital sign measurements; BMI computed from weight_kg and height_cm in the application layer';
COMMENT ON COLUMN vitals.temperature IS 'Body temperature in degrees Fahrenheit';
COMMENT ON COLUMN vitals.oxygen_saturation IS 'Peripheral oxygen saturation (SpO2) as a percentage 0-100';
COMMENT ON COLUMN vitals.bmi IS 'Body Mass Index: weight_kg / (height_cm / 100)^2, stored to 1 decimal place';

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

CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_doctors_updated_at
    BEFORE UPDATE ON doctors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_medical_records_updated_at
    BEFORE UPDATE ON medical_records
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

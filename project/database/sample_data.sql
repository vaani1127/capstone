-- Sample Data for HealthSaathi Database
-- This script inserts test data for development and testing purposes
-- WARNING: Do not use in production!

-- ============================================================================
-- USERS
-- ============================================================================
-- Password for all users: "password123" (hashed with bcrypt cost 12)
-- Hash: $2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC

INSERT INTO users (name, email, password_hash, role) VALUES
-- Admin users
('Admin User', 'admin@healthsaathi.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Admin'),

-- Doctor users
('Dr. Rajesh Kumar', 'rajesh.kumar@healthsaathi.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Doctor'),
('Dr. Priya Sharma', 'priya.sharma@healthsaathi.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Doctor'),
('Dr. Amit Patel', 'amit.patel@healthsaathi.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Doctor'),

-- Nurse users
('Nurse Anjali', 'anjali@healthsaathi.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Nurse'),
('Nurse Kavita', 'kavita@healthsaathi.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Nurse'),

-- Patient users
('Rahul Verma', 'rahul.verma@example.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Patient'),
('Sneha Gupta', 'sneha.gupta@example.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Patient'),
('Vikram Singh', 'vikram.singh@example.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Patient'),
('Meera Reddy', 'meera.reddy@example.com', '$2b$12$RdKxgKYcGgvyJWayxnW3FutNNB6ZVgAtVs8qW4jKUpo5LGWf9bzgC', 'Patient');

-- ============================================================================
-- PATIENTS
-- ============================================================================

INSERT INTO patients (user_id, date_of_birth, gender, phone, address, blood_group) VALUES
(7, '1985-03-15', 'Male', '+91-9876543210', '123 MG Road, Bangalore, Karnataka', 'O+'),
(8, '1990-07-22', 'Female', '+91-9876543211', '456 Park Street, Mumbai, Maharashtra', 'A+'),
(9, '1978-11-30', 'Male', '+91-9876543212', '789 Lake View, Delhi, NCR', 'B+'),
(10, '1995-05-18', 'Female', '+91-9876543213', '321 Beach Road, Chennai, Tamil Nadu', 'AB+');

-- ============================================================================
-- DOCTORS
-- ============================================================================

INSERT INTO doctors (user_id, specialization, license_number, average_consultation_duration) VALUES
(2, 'General Medicine', 'MED-2015-001234', 15),
(3, 'Pediatrics', 'MED-2018-005678', 20),
(4, 'Cardiology', 'MED-2012-009876', 25);

-- ============================================================================
-- APPOINTMENTS
-- ============================================================================

-- Scheduled appointments for today and tomorrow
INSERT INTO appointments (patient_id, doctor_id, scheduled_time, status, appointment_type, queue_position) VALUES
-- Today's appointments
(1, 1, CURRENT_TIMESTAMP + INTERVAL '2 hours', 'scheduled', 'scheduled', NULL),
(2, 1, CURRENT_TIMESTAMP + INTERVAL '3 hours', 'scheduled', 'scheduled', NULL),
(3, 2, CURRENT_TIMESTAMP + INTERVAL '1 hour', 'checked_in', 'scheduled', 1),
(4, 2, CURRENT_TIMESTAMP + INTERVAL '2 hours', 'scheduled', 'scheduled', NULL),

-- Walk-in appointments (in queue)
(1, 3, CURRENT_TIMESTAMP, 'checked_in', 'walk_in', 1),
(2, 3, CURRENT_TIMESTAMP, 'checked_in', 'walk_in', 2),

-- Tomorrow's appointments
(3, 1, CURRENT_TIMESTAMP + INTERVAL '1 day', 'scheduled', 'scheduled', NULL),
(4, 2, CURRENT_TIMESTAMP + INTERVAL '1 day', 'scheduled', 'scheduled', NULL);

-- ============================================================================
-- MEDICAL RECORDS
-- ============================================================================

-- Sample consultation notes and prescriptions
INSERT INTO medical_records (patient_id, doctor_id, appointment_id, consultation_notes, diagnosis, prescription, version_number, parent_record_id, created_by) VALUES
(1, 1, 1, 
 'Patient complains of fever and headache for 2 days. Temperature: 101°F. BP: 120/80.',
 'Viral Fever',
 'Tab. Paracetamol 500mg - 1 tablet thrice daily for 3 days. Rest and plenty of fluids.',
 1, NULL, 2),

(2, 2, 3,
 'Child presented with cough and cold. No fever. Throat slightly red.',
 'Upper Respiratory Tract Infection',
 'Syrup Cetirizine 5ml twice daily for 5 days. Steam inhalation recommended.',
 1, NULL, 3),

(3, 1, 7,
 'Follow-up visit. Patient reports improvement in symptoms. No fever.',
 'Viral Fever - Resolved',
 'Continue rest. No medication needed.',
 1, NULL, 2);

-- ============================================================================
-- AUDIT CHAIN
-- ============================================================================
-- NOTE: Audit chain entries are NOT pre-seeded.
-- Real SHA-256 hash-linked entries are created automatically by the backend
-- whenever medical records or appointments are created/updated via the API.
-- Pre-seeding with fake hashes would make all entries show as tampered.
-- Create entries by using the API after loading this data.

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify data insertion
SELECT 'Users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'Patients', COUNT(*) FROM patients
UNION ALL
SELECT 'Doctors', COUNT(*) FROM doctors
UNION ALL
SELECT 'Appointments', COUNT(*) FROM appointments
UNION ALL
SELECT 'Medical Records', COUNT(*) FROM medical_records
UNION ALL
SELECT 'Audit Chain', COUNT(*) FROM audit_chain;

-- Display sample data summary
SELECT 
    u.name as user_name,
    u.role,
    u.email
FROM users u
ORDER BY u.role, u.name;

SELECT 
    p.id,
    u.name as patient_name,
    p.blood_group,
    p.phone
FROM patients p
JOIN users u ON p.user_id = u.id;

SELECT 
    d.id,
    u.name as doctor_name,
    d.specialization,
    d.average_consultation_duration
FROM doctors d
JOIN users u ON d.user_id = u.id;

SELECT 
    a.id,
    pu.name as patient_name,
    du.name as doctor_name,
    a.scheduled_time,
    a.status,
    a.appointment_type,
    a.queue_position
FROM appointments a
JOIN patients p ON a.patient_id = p.id
JOIN users pu ON p.user_id = pu.id
JOIN doctors d ON a.doctor_id = d.id
JOIN users du ON d.user_id = du.id
ORDER BY a.scheduled_time;

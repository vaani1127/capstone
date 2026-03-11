-- Sample Data for HealthSaathi Database
-- This script inserts test data for development and testing purposes
-- WARNING: Do not use in production!

-- ============================================================================
-- USERS
-- ============================================================================
-- Password for all users: "password123" (hashed with bcrypt cost 12)
-- Hash: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6

INSERT INTO users (name, email, password_hash, role) VALUES
-- Admin users
('Admin User', 'admin@healthsaathi.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Admin'),

-- Doctor users
('Dr. Rajesh Kumar', 'rajesh.kumar@healthsaathi.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Doctor'),
('Dr. Priya Sharma', 'priya.sharma@healthsaathi.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Doctor'),
('Dr. Amit Patel', 'amit.patel@healthsaathi.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Doctor'),

-- Nurse users
('Nurse Anjali', 'anjali@healthsaathi.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Nurse'),
('Nurse Kavita', 'kavita@healthsaathi.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Nurse'),

-- Patient users
('Rahul Verma', 'rahul.verma@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Patient'),
('Sneha Gupta', 'sneha.gupta@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Patient'),
('Vikram Singh', 'vikram.singh@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Patient'),
('Meera Reddy', 'meera.reddy@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qviu6', 'Patient');

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

-- Genesis block
INSERT INTO audit_chain (record_id, record_type, record_data, hash, previous_hash, user_id, is_tampered) VALUES
(0, 'genesis', '{"message": "Genesis block for HealthSaathi audit chain"}', 
 '0000000000000000000000000000000000000000000000000000000000000000',
 '0',
 1, FALSE);

-- Sample audit entries for medical records
INSERT INTO audit_chain (record_id, record_type, record_data, hash, previous_hash, user_id, is_tampered) VALUES
(1, 'medical_record', 
 '{"patient_id": 1, "doctor_id": 1, "diagnosis": "Viral Fever", "timestamp": "2026-02-27T10:30:00Z"}',
 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2',
 '0000000000000000000000000000000000000000000000000000000000000000',
 2, FALSE),

(2, 'medical_record',
 '{"patient_id": 2, "doctor_id": 2, "diagnosis": "Upper Respiratory Tract Infection", "timestamp": "2026-02-27T11:00:00Z"}',
 'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3',
 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2',
 3, FALSE),

(3, 'medical_record',
 '{"patient_id": 3, "doctor_id": 1, "diagnosis": "Viral Fever - Resolved", "timestamp": "2026-02-27T14:30:00Z"}',
 'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4',
 'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3',
 2, FALSE);

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

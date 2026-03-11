# HealthSaathi: Mobile-Based Secure Healthcare System

## 1. Project Overview

HealthSaathi is a mobile-based healthcare management system designed to:
- Optimize patient flow and reduce waiting times
- Secure medical records using blockchain-inspired hash chaining
- Provide complete auditability and tamper detection
- Ensure role-based secure access to healthcare data

## 2. User Stories and Acceptance Criteria

### 2.1 User Management

#### US-1: User Registration and Authentication
As a healthcare facility staff member or patient, I want to register and login securely so that I can access the system.

**Acceptance Criteria:**
- 1.1 Users can register with name, email, and password
- 1.2 Passwords are hashed using bcrypt before storage
- 1.3 Users can login with email and password
- 1.4 System generates JWT tokens upon successful authentication
- 1.5 JWT tokens expire after a configured time period
- 1.6 Invalid credentials return appropriate error messages

#### US-2: Role-Based Access Control
As a system administrator, I want to assign roles to users so that access to features is controlled based on responsibilities.

**Acceptance Criteria:**
- 2.1 System supports four roles: Admin, Doctor, Nurse, Patient
- 2.2 Each user is assigned exactly one role during registration
- 2.3 Role-based middleware enforces access control on all protected endpoints
- 2.4 Unauthorized access attempts are logged and rejected with 403 status

### 2.2 Appointment & Scheduling Management

#### US-3: Patient Appointment Booking
As a patient, I want to book appointments with doctors so that I can receive medical care at a scheduled time.

**Acceptance Criteria:**
- 3.1 Patients can view available doctors and their specializations
- 3.2 Patients can select a doctor and preferred time slot
- 3.3 System validates appointment availability before confirmation
- 3.4 Patients receive confirmation with appointment details
- 3.5 System prevents double-booking of time slots

#### US-4: Walk-in Patient Registration
As a nurse or admin, I want to register walk-in patients so that they can be added to the queue immediately.

**Acceptance Criteria:**
- 4.1 Nurse/Admin can create patient records with demographics
- 4.2 Walk-in patients are automatically added to the appropriate doctor's queue
- 4.3 System assigns queue position based on arrival time
- 4.4 Walk-in registration is completed within 30 seconds

#### US-5: Real-Time Queue Status
As a patient or staff member, I want to view real-time queue status so that I know current waiting times.

**Acceptance Criteria:**
- 5.1 System displays current queue length for each doctor
- 5.2 Queue updates are pushed to clients within 2 seconds via WebSockets
- 5.3 Queue position is displayed for each waiting patient
- 5.4 System shows estimated waiting time for each patient in queue

#### US-6: Appointment Management
As a patient, I want to cancel or reschedule appointments so that I can manage my healthcare schedule.

**Acceptance Criteria:**
- 6.1 Patients can cancel appointments up to 2 hours before scheduled time
- 6.2 Patients can reschedule to available time slots
- 6.3 Cancellations immediately update queue status
- 6.4 System sends notifications for cancellation/rescheduling confirmations

### 2.3 Patient Flow Optimization

#### US-7: Intelligent Queue Management
As a system, I want to optimize patient flow so that waiting times are minimized and resources are utilized efficiently.

**Acceptance Criteria:**
- 7.1 System tracks queue length per doctor in real-time
- 7.2 System calculates estimated waiting time using: queue_length × average_consultation_duration
- 7.3 System maintains rolling average consultation duration per doctor
- 7.4 Average consultation duration updates after each completed consultation
- 7.5 System suggests least busy doctor for new appointments
- 7.6 Queue status updates are broadcast via WebSockets to all connected clients

### 2.4 Medical Record Management

#### US-8: Consultation Documentation
As a doctor, I want to create and update consultation notes so that patient care is properly documented.

**Acceptance Criteria:**
- 8.1 Doctors can create consultation notes for their patients
- 8.2 Consultation notes include: symptoms, diagnosis, observations
- 8.3 Each consultation creates a new medical record entry
- 8.4 System maintains version control for all record updates
- 8.5 Only the treating doctor can create/update consultation notes

#### US-9: Prescription Management
As a doctor, I want to create prescriptions so that patients receive proper medication instructions.

**Acceptance Criteria:**
- 9.1 Doctors can create prescriptions linked to consultations
- 9.2 Prescriptions include: medication name, dosage, frequency, duration
- 9.3 Prescriptions are stored as part of medical records
- 9.4 Each prescription update creates a new version

#### US-10: Patient Medical History Access
As a patient, I want to view my medical history so that I can track my healthcare journey.

**Acceptance Criteria:**
- 10.1 Patients can view all their consultation notes (read-only)
- 10.2 Patients can view all their prescriptions (read-only)
- 10.3 Medical history is displayed in chronological order
- 10.4 Patients can view version history of their records
- 10.5 Patients cannot modify any medical records

### 2.5 Blockchain-Based Integrity Layer

#### US-11: Tamper-Proof Medical Records
As a healthcare administrator, I want medical records to be tamper-proof so that data integrity is guaranteed.

**Acceptance Criteria:**
- 11.1 Every medical record create/update generates a SHA-256 hash
- 11.2 Hash includes: record_data + timestamp + user_id + previous_hash
- 11.3 Hash entries are stored in an audit chain table
- 11.4 Each hash entry links to the previous hash (blockchain structure)
- 11.5 Genesis block (first entry) has previous_hash = "0"

#### US-12: Integrity Verification
As a system, I want to verify record integrity on access so that tampering is detected immediately.

**Acceptance Criteria:**
- 12.1 System recomputes hash when medical records are accessed
- 12.2 Recomputed hash is compared with stored hash
- 12.3 Hash mismatch triggers tampering alert
- 12.4 Tampering alerts are logged with timestamp and record details
- 12.5 Tampered records are flagged in the UI
- 12.6 Integrity verification completes within 100ms

#### US-13: Immutable Audit Trail
As an auditor, I want to view complete audit logs so that all record modifications are traceable.

**Acceptance Criteria:**
- 13.1 All record modifications are logged in audit chain
- 13.2 Audit entries include: record_id, record_type, hash, previous_hash, timestamp, user_id
- 13.3 Audit chain entries cannot be deleted or modified
- 13.4 Audit logs are queryable by date range, user, and record type
- 13.5 System provides audit dashboard for administrators

### 2.6 Audit & Logging

#### US-14: Administrative Audit Dashboard
As an administrator, I want to view audit logs so that I can monitor system activity and ensure compliance.

**Acceptance Criteria:**
- 14.1 Admin dashboard displays all audit chain entries
- 14.2 Dashboard supports filtering by date, user, and record type
- 14.3 Dashboard displays tampering alerts prominently
- 14.4 Dashboard shows record version history
- 14.5 Audit data can be exported for compliance reporting

## 3. Non-Functional Requirements

### 3.1 Security
- NFR-1: All communication uses HTTPS with valid SSL certificates
- NFR-2: Role-based authorization is enforced on all protected endpoints
- NFR-3: Sensitive medical data is stored off-chain (database only)
- NFR-4: Only hash values are stored in the audit chain
- NFR-5: JWT tokens use secure signing algorithms (HS256 or RS256)

### 3.2 Performance
- NFR-6: Real-time queue updates reflect within 2 seconds
- NFR-7: Waiting time estimation completes instantly (<100ms)
- NFR-8: System supports minimum 200 concurrent users
- NFR-9: API response time <500ms for 95th percentile
- NFR-10: Hash verification completes within 100ms

### 3.3 Reliability
- NFR-11: Audit logs are immutable and cannot be deleted
- NFR-12: Data consistency is maintained across all updates
- NFR-13: System maintains 99.5% uptime
- NFR-14: Database transactions ensure ACID properties

### 3.4 Usability
- NFR-15: Mobile-first user interface design
- NFR-16: Simple and intuitive UI for small healthcare facilities
- NFR-17: Maximum 3 clicks to reach any major feature
- NFR-18: Support for offline queue viewing (cached data)

### 3.5 Scalability
- NFR-19: Backend architecture supports horizontal scaling
- NFR-20: Database supports future expansion to multiple facilities
- NFR-21: WebSocket connections support auto-reconnection
- NFR-22: System handles 1000+ appointments per day

## 4. System Constraints

- Mobile application developed using Flutter
- Backend developed using FastAPI (Python) or Node.js
- Database: PostgreSQL
- Blockchain logic implemented via SHA-256 hash chaining
- Real-time communication via WebSockets
- Deployment on cloud infrastructure (AWS/GCP/Azure)

## 5. Out of Scope (Future Enhancements)

- AI-based waiting time prediction
- Integration with insurance systems
- Multi-hospital network support
- Interoperability with national EHR systems
- Advanced analytics dashboard
- Telemedicine features
- Payment processing

# HealthSaathi: Implementation Tasks

## Phase 1: Foundation & Infrastructure

### 1. Database Setup
- [x] 1.1 Create PostgreSQL database schema
  - Create users table with role enum
  - Create patients table with demographics
  - Create doctors table with specialization
  - Create appointments table with status tracking
  - Create medical_records table with versioning
  - Create audit_chain table for blockchain integrity
  - Add all necessary indexes for performance

- [x] 1.2 Create database migration scripts
  - Setup migration tool (Alembic for Python or Knex for Node.js)
  - Create initial migration for all tables
  - Add seed data for testing

### 2. Backend API Foundation
- [x] 2.1 Setup backend project structure
  - Initialize FastAPI or Node.js project
  - Configure environment variables
  - Setup project folder structure
  - Configure CORS and security headers

- [x] 2.2 Implement database connection layer
  - Setup ORM (SQLAlchemy for Python or Sequelize for Node.js)
  - Create database connection pool
  - Implement connection error handling

- [x] 2.3 Create data models
  - User model
  - Patient model
  - Doctor model
  - Appointment model
  - MedicalRecord model
  - AuditChain model

## Phase 2: Authentication & Authorization

### 3. User Authentication
- [x] 3.1 Implement user registration
  - Create registration endpoint
  - Validate input data
  - Hash passwords using bcrypt
  - Store user in database
  - Return success response

- [x] 3.2 Implement user login
  - Create login endpoint
  - Validate credentials
  - Generate JWT token
  - Return token and user info

- [x] 3.3 Implement JWT token validation
  - Create middleware to validate JWT tokens
  - Extract user info from token
  - Handle expired tokens
  - Implement token refresh mechanism

### 4. Role-Based Access Control
- [x] 4.1 Implement RBAC middleware
  - Create role checking decorator/middleware
  - Enforce role requirements on protected routes
  - Return 403 for unauthorized access
  - Log unauthorized access attempts

- [x] 4.2 Protect all API endpoints
  - Apply authentication middleware to all protected routes
  - Apply role-based authorization to role-specific routes
  - Document required roles for each endpoint

## Phase 3: Appointment & Queue Management

### 5. Appointment Booking
- [x] 5.1 Implement appointment creation
  - Create appointment booking endpoint
  - Validate doctor availability
  - Prevent double-booking
  - Assign queue position
  - Return confirmation

- [x] 5.2 Implement appointment listing
  - Get appointments by patient
  - Get appointments by doctor
  - Filter by status and date range
  - Sort by scheduled time

- [x] 5.3 Implement appointment cancellation
  - Create cancellation endpoint
  - Validate cancellation rules (2 hours before)
  - Update appointment status
  - Update queue positions

- [x] 5.4 Implement appointment rescheduling
  - Create rescheduling endpoint
  - Check new time slot availability
  - Update appointment time
  - Update queue position

### 6. Walk-in Patient Registration
- [x] 6.1 Implement walk-in registration
  - Create walk-in registration endpoint (Nurse/Admin only)
  - Create patient record if new
  - Create appointment with walk-in type
  - Add to doctor's queue immediately
  - Return queue position and estimated wait time

### 7. Queue Management
- [x] 7.1 Implement queue status tracking
  - Create endpoint to get current queue for a doctor
  - Calculate queue positions
  - Calculate estimated waiting times
  - Return queue data with patient info

- [x] 7.2 Implement queue updates
  - Update queue when appointment checked in
  - Update queue when consultation starts
  - Update queue when consultation completes
  - Recalculate positions when patient removed

- [x] 7.3 Implement average consultation duration tracking
  - Track actual consultation duration
  - Update doctor's average using exponential moving average
  - Store updated average in database

## Phase 4: Real-Time Communication

### 8. WebSocket Implementation
- [x] 8.1 Setup WebSocket server
  - Configure WebSocket server
  - Implement connection authentication using JWT
  - Maintain connection pool by user_id
  - Handle connection errors and reconnection

- [x] 8.2 Implement queue update broadcasting
  - Broadcast queue updates when queue changes
  - Send updates to all clients viewing that doctor's queue
  - Include queue length and estimated wait times

- [x] 8.3 Implement appointment status notifications
  - Broadcast appointment status changes
  - Send to specific patient and doctor
  - Include appointment details

## Phase 5: Medical Records Management

### 9. Consultation Notes
- [x] 9.1 Implement consultation note creation
  - Create endpoint for doctors to create notes
  - Validate doctor authorization
  - Link to appointment
  - Store in medical_records table
  - Set version_number to 1

- [x] 9.2 Implement consultation note updates
  - Create endpoint to update existing notes
  - Create new version (increment version_number)
  - Link to parent record
  - Preserve original record

### 10. Prescription Management
- [x] 10.1 Implement prescription creation
  - Create endpoint for doctors to create prescriptions
  - Include medication, dosage, frequency, duration
  - Link to consultation/appointment
  - Store in medical_records table

- [x] 10.2 Implement prescription updates
  - Create endpoint to update prescriptions
  - Create new version
  - Preserve original prescription

### 11. Medical History Access
- [x] 11.1 Implement patient medical history retrieval
  - Create endpoint for patients to view their records
  - Return all consultations and prescriptions
  - Sort by date (newest first)
  - Enforce read-only access

- [x] 11.2 Implement version history retrieval
  - Create endpoint to get all versions of a record
  - Show version number and timestamp
  - Display who made each change

## Phase 6: Blockchain Integrity Layer

### 12. Hash Generation
- [x] 12.1 Implement hash generation function
  - Create function to generate SHA-256 hash
  - Include record_data, timestamp, user_id, previous_hash
  - Use consistent JSON serialization (sorted keys)
  - Return hex digest

- [x] 12.2 Implement audit chain entry creation
  - Get previous hash from last audit entry
  - Generate hash for new record
  - Create audit_chain entry
  - Link to medical record

- [x] 12.3 Integrate hash generation with medical records
  - Trigger hash generation on record create
  - Trigger hash generation on record update
  - Store audit entry in same transaction
  - Handle genesis block (previous_hash = "0")

### 13. Integrity Verification
- [x] 13.1 Implement integrity verification function
  - Fetch audit entry for record
  - Fetch actual record data
  - Recompute hash
  - Compare with stored hash
  - Return verification result

- [x] 13.2 Implement tamper detection
  - Call verification on record access
  - Log tampering alert if mismatch detected
  - Flag record as tampered in database
  - Return tampering status to client

- [x] 13.3 Implement chain verification
  - Create function to verify entire chain
  - Verify each block's hash
  - Verify previous_hash links
  - Report any inconsistencies

## Phase 7: Audit & Logging

### 14. Audit Dashboard
- [x] 14.1 Implement audit log retrieval
  - Create endpoint to get audit logs (Admin only)
  - Support filtering by date range
  - Support filtering by user
  - Support filtering by record type
  - Paginate results

- [x] 14.2 Implement tampering alert retrieval
  - Create endpoint to get tampering alerts (Admin only)
  - Show flagged records
  - Include timestamp and details
  - Sort by severity/date

- [x] 14.3 Implement audit log export
  - Create endpoint to export audit logs
  - Support CSV or JSON format
  - Include all relevant fields
  - Enforce admin-only access

## Phase 8: Mobile Application

### 15. Flutter App Setup
- [x] 15.1 Initialize Flutter project
  - Create new Flutter project
  - Setup folder structure
  - Configure dependencies (http, provider, web_socket_channel)
  - Setup environment configuration

- [x] 15.2 Implement API client
  - Create HTTP client with base URL
  - Implement JWT token management
  - Add token to request headers
  - Handle token expiration and refresh

- [x] 15.3 Implement WebSocket client
  - Create WebSocket connection manager
  - Implement authentication
  - Handle connection events
  - Implement auto-reconnection

### 16. Authentication UI
- [x] 16.1 Create login screen
  - Design login form (email, password)
  - Implement form validation
  - Call login API
  - Store JWT token
  - Navigate to role-specific dashboard

- [x] 16.2 Create registration screen
  - Design registration form
  - Implement form validation
  - Call registration API
  - Handle success/error responses

### 17. Patient Dashboard
- [x] 17.1 Create patient home screen
  - Display upcoming appointments
  - Show quick actions (book appointment, view history)
  - Display notifications

- [x] 17.2 Create appointment booking screen
  - List available doctors
  - Show doctor specializations
  - Select doctor and time slot
  - Confirm booking
  - Show confirmation message

- [x] 17.3 Create queue status screen
  - Display current queue for selected doctor
  - Show patient's queue position
  - Show estimated waiting time
  - Update in real-time via WebSocket

- [x] 17.4 Create medical history screen
  - List all consultations
  - List all prescriptions
  - Show details on tap
  - Display version history

### 18. Doctor Dashboard
- [x] 18.1 Create doctor home screen
  - Display today's appointments
  - Show current queue
  - Quick actions (start consultation, view patient)

- [x] 18.2 Create queue management screen
  - List patients in queue
  - Show queue positions
  - Mark consultation as started
  - Mark consultation as completed

- [x] 18.3 Create consultation screen
  - Display patient information
  - Form to enter consultation notes
  - Form to create prescription
  - Save and complete consultation

### 19. Nurse Dashboard
- [x] 19.1 Create nurse home screen
  - Display today's appointments
  - Show queue status for all doctors
  - Quick action for walk-in registration

- [x] 19.2 Create walk-in registration screen
  - Form to enter patient details
  - Select doctor
  - Submit registration
  - Show queue position and wait time

### 20. Admin Dashboard
- [x] 20.1 Create admin home screen
  - Display system statistics
  - Show recent activity
  - Quick links to management screens

- [x] 20.2 Create user management screen
  - List all users
  - Create new users
  - Edit user details
  - Assign roles

- [x] 20.3 Create audit dashboard screen
  - Display audit logs
  - Filter by date, user, record type
  - Show tampering alerts
  - Export audit logs

## Phase 9: Testing

### 21. Backend Testing
- [x] 21.1 Write unit tests for authentication
  - Test registration logic
  - Test login logic
  - Test JWT generation and validation
  - Test password hashing

- [x] 21.2 Write unit tests for appointments
  - Test appointment creation
  - Test availability checking
  - Test cancellation logic
  - Test rescheduling logic

- [x] 21.3 Write unit tests for queue management
  - Test queue position calculation
  - Test waiting time calculation
  - Test average duration updates

- [x] 21.4 Write unit tests for medical records
  - Test record creation
  - Test versioning logic
  - Test access control

- [x] 21.5 Write unit tests for blockchain integrity
  - Test hash generation
  - Test integrity verification
  - Test tamper detection
  - Test chain verification

- [x] 21.6 Write integration tests
  - Test complete appointment booking flow
  - Test complete consultation flow
  - Test WebSocket communication
  - Test API endpoints with authentication

### 22. Mobile App Testing
- [x] 22.1 Write widget tests
  - Test login screen
  - Test registration screen
  - Test appointment booking flow
  - Test queue status display

- [x] 22.2 Write integration tests
  - Test API integration
  - Test WebSocket integration
  - Test navigation flows

## Phase 10: Deployment

### 23. Backend Deployment
- [-] 23.1 Setup production environment
  - Configure cloud infrastructure (AWS/GCP/Azure)
  - Setup managed PostgreSQL database
  - Configure environment variables
  - Setup SSL certificates

- [ ] 23.2 Deploy backend application
  - Build production image
  - Deploy to cloud servers
  - Configure load balancer
  - Enable auto-scaling

- [ ] 23.3 Setup monitoring and logging
  - Configure application logging
  - Setup monitoring dashboards
  - Configure alerts
  - Setup error tracking

### 24. Mobile App Deployment
- [ ] 24.1 Prepare for release
  - Update app icons and splash screens
  - Configure app signing
  - Update version numbers
  - Test on multiple devices

- [ ] 24.2 Deploy to app stores
  - Build release APK/IPA
  - Create store listings
  - Submit to Google Play Store
  - Submit to Apple App Store (if applicable)

## Phase 11: Documentation

### 25. Technical Documentation
- [x] 25.1 Write API documentation
  - Document all endpoints
  - Include request/response examples
  - Document authentication requirements
  - Document error codes

- [x] 25.2 Write deployment guide
  - Document infrastructure setup
  - Document deployment process
  - Document environment configuration
  - Document backup and recovery procedures

### 26. User Documentation
- [x] 26.1 Write user guides
  - Patient user guide
  - Doctor user guide
  - Nurse user guide
  - Admin user guide

- [x] 26.2 Create training materials
  - Video tutorials
  - Quick start guides
  - FAQ document

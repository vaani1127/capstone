# HealthSaathi: System Design Document

## 1. System Architecture

HealthSaathi follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────┐
│   Mobile Application (Flutter)      │
│   - Patient, Doctor, Nurse, Admin   │
└──────────────┬──────────────────────┘
               │ HTTPS/WebSocket
┌──────────────▼──────────────────────┐
│   Backend API (FastAPI/Node.js)     │
│   - Authentication & Authorization  │
│   - Business Logic                  │
│   - WebSocket Server                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   PostgreSQL Database               │
│   - User Data                       │
│   - Medical Records                 │
│   - Audit Chain                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Blockchain Integrity Layer        │
│   - Hash Chain Verification         │
│   - Tamper Detection                │
└─────────────────────────────────────┘
```

## 2. Component Design

### 2.1 Mobile Application Layer

**Technology:** Flutter

**User Interfaces:**

1. **Patient Dashboard**
   - View appointments
   - Book new appointments
   - View queue status and waiting time
   - Access medical history
   - View prescriptions

2. **Doctor Dashboard**
   - View appointment schedule
   - View current queue
   - Create consultation notes
   - Write prescriptions
   - Mark consultations as complete

3. **Nurse Dashboard**
   - Register walk-in patients
   - View queue status
   - Manage appointment check-ins

4. **Admin Dashboard**
   - User management
   - View audit logs
   - Monitor system activity
   - View tampering alerts
   - Generate reports

**State Management:** Provider or Riverpod
**API Communication:** HTTP client with JWT token management
**Real-time Updates:** WebSocket client

### 2.2 Backend Layer

**Technology:** FastAPI (Python) or Node.js with Express

**Core Modules:**

1. **Authentication Module**
   - User registration
   - Login with JWT generation
   - Token validation middleware
   - Password hashing with bcrypt

2. **Authorization Module**
   - Role-based access control (RBAC)
   - Permission checking middleware
   - Route protection decorators

3. **Appointment Module**
   - Appointment booking logic
   - Availability checking
   - Cancellation and rescheduling
   - Walk-in registration

4. **Queue Management Module**
   - Real-time queue tracking
   - Waiting time calculation
   - Queue position management
   - Doctor workload balancing

5. **Medical Records Module**
   - Consultation note creation
   - Prescription management
   - Version control
   - Record retrieval with access control

6. **Blockchain Integrity Module**
   - Hash generation
   - Hash chain management
   - Integrity verification
   - Tamper detection

7. **Audit Module**
   - Audit log creation
   - Audit query API
   - Tampering alert management

8. **WebSocket Module**
   - Connection management
   - Queue update broadcasting
   - Appointment status notifications

**API Structure:**
```
/api/v1/
  /auth
    POST /register
    POST /login
    POST /refresh
  /appointments
    GET /
    POST /
    PUT /:id
    DELETE /:id
  /queue
    GET /status
    GET /doctor/:id
  /medical-records
    GET /patient/:id
    POST /
    PUT /:id
    GET /:id/versions
  /audit
    GET /logs
    GET /tampering-alerts
  /users
    GET /
    POST /
    PUT /:id
```

### 2.3 Database Layer (PostgreSQL)

**Schema Design:**

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('Admin', 'Doctor', 'Nurse', 'Patient')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patients table
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

-- Doctors table
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    specialization VARCHAR(255),
    license_number VARCHAR(100),
    average_consultation_duration INTEGER DEFAULT 15, -- in minutes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appointments table
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    doctor_id INTEGER REFERENCES doctors(id),
    scheduled_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'checked_in', 'in_progress', 'completed', 'cancelled')),
    appointment_type VARCHAR(50) DEFAULT 'scheduled' CHECK (appointment_type IN ('scheduled', 'walk_in')),
    queue_position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medical Records table
CREATE TABLE medical_records (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    doctor_id INTEGER REFERENCES doctors(id),
    appointment_id INTEGER REFERENCES appointments(id),
    consultation_notes TEXT,
    diagnosis TEXT,
    prescription TEXT,
    version_number INTEGER DEFAULT 1,
    parent_record_id INTEGER REFERENCES medical_records(id),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Chain table
CREATE TABLE audit_chain (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    record_type VARCHAR(50) NOT NULL,
    record_data JSONB NOT NULL,
    hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    is_tampered BOOLEAN DEFAULT FALSE
);

-- Indexes for performance
CREATE INDEX idx_appointments_doctor_status ON appointments(doctor_id, status);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_medical_records_patient ON medical_records(patient_id);
CREATE INDEX idx_audit_chain_record ON audit_chain(record_id, record_type);
CREATE INDEX idx_audit_chain_timestamp ON audit_chain(timestamp);
```

## 3. Blockchain Integrity Design

### 3.1 Hash Generation Algorithm

```python
import hashlib
import json
from datetime import datetime

def generate_hash(record_data: dict, user_id: int, previous_hash: str) -> str:
    """
    Generate SHA-256 hash for a medical record
    """
    hash_input = {
        'record_data': record_data,
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'previous_hash': previous_hash
    }
    
    # Convert to JSON string with sorted keys for consistency
    hash_string = json.dumps(hash_input, sort_keys=True)
    
    # Generate SHA-256 hash
    return hashlib.sha256(hash_string.encode()).hexdigest()
```

### 3.2 Hash Chain Structure

Each block in the audit chain contains:
- **Current Hash:** SHA-256 hash of current record + metadata
- **Previous Hash:** Hash of the previous block in the chain
- **Timestamp:** When the record was created/modified
- **User ID:** Who performed the operation
- **Record Reference:** Link to the actual medical record

**Genesis Block:**
- First entry in the chain
- `previous_hash = "0"`
- Establishes the chain foundation

### 3.3 Tamper Detection Process

```python
def verify_integrity(record_id: int, record_type: str) -> bool:
    """
    Verify the integrity of a medical record
    """
    # 1. Fetch audit entry
    audit_entry = get_audit_entry(record_id, record_type)
    
    # 2. Fetch actual record data
    record_data = get_record_data(record_id, record_type)
    
    # 3. Recompute hash
    recomputed_hash = generate_hash(
        record_data=record_data,
        user_id=audit_entry.user_id,
        previous_hash=audit_entry.previous_hash
    )
    
    # 4. Compare hashes
    if recomputed_hash != audit_entry.hash:
        # Tampering detected!
        log_tampering_alert(record_id, record_type)
        return False
    
    return True
```

### 3.4 Chain Verification

Periodically verify the entire chain:
1. Start from genesis block
2. Verify each block's hash
3. Verify each block's previous_hash matches the previous block's hash
4. Flag any inconsistencies

## 4. Patient Flow Optimization Design

### 4.1 Waiting Time Calculation

**Formula:**
```
Estimated Waiting Time = Queue Position × Average Consultation Duration
```

**Implementation:**
```python
def calculate_waiting_time(doctor_id: int, queue_position: int) -> int:
    """
    Calculate estimated waiting time in minutes
    """
    doctor = get_doctor(doctor_id)
    avg_duration = doctor.average_consultation_duration
    
    # Account for current consultation in progress
    current_consultation_remaining = get_current_consultation_remaining_time(doctor_id)
    
    waiting_time = (queue_position - 1) * avg_duration + current_consultation_remaining
    
    return waiting_time
```

### 4.2 Dynamic Average Consultation Duration

Update after each completed consultation:
```python
def update_average_consultation_duration(doctor_id: int, actual_duration: int):
    """
    Update rolling average using exponential moving average
    """
    doctor = get_doctor(doctor_id)
    alpha = 0.3  # Smoothing factor
    
    new_average = (alpha * actual_duration) + ((1 - alpha) * doctor.average_consultation_duration)
    
    update_doctor(doctor_id, average_consultation_duration=new_average)
```

### 4.3 Queue Management

**Queue Operations:**
- Add patient to queue (on check-in)
- Remove patient from queue (on consultation complete)
- Update queue positions (when patient removed)
- Broadcast queue updates via WebSocket

## 5. Security Design

### 5.1 Authentication Flow

1. User submits credentials (email, password)
2. Backend validates credentials
3. Backend generates JWT token with payload:
   ```json
   {
     "user_id": 123,
     "email": "user@example.com",
     "role": "Doctor",
     "exp": 1234567890
   }
   ```
4. Token returned to client
5. Client includes token in Authorization header for subsequent requests

### 5.2 Authorization Middleware

```python
def require_role(*allowed_roles):
    """
    Decorator to enforce role-based access control
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            user = get_current_user(request)
            if user.role not in allowed_roles:
                return Response(status=403, data={"error": "Forbidden"})
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@require_role('Doctor')
def create_consultation(request):
    # Only doctors can access this endpoint
    pass
```

### 5.3 Password Security

- Use bcrypt with cost factor 12
- Never store plaintext passwords
- Implement password strength requirements
- Support password reset flow

### 5.4 Data Security

- **In Transit:** HTTPS for all communications
- **At Rest:** Database encryption
- **Medical Data:** Stored off-chain in database
- **Audit Chain:** Only hashes stored, not sensitive data

## 6. Real-Time Communication Design

### 6.1 WebSocket Architecture

**Connection Management:**
- Clients connect to WebSocket server on login
- Server maintains connection pool by user_id
- Connections authenticated using JWT

**Event Types:**
```javascript
// Queue update event
{
  "event": "queue_update",
  "data": {
    "doctor_id": 5,
    "queue_length": 3,
    "patients": [...]
  }
}

// Appointment status change
{
  "event": "appointment_status",
  "data": {
    "appointment_id": 123,
    "status": "in_progress"
  }
}
```

### 6.2 Broadcasting Strategy

- Queue updates broadcast to all connected clients viewing that doctor's queue
- Appointment updates sent to specific patient and doctor
- Use room-based broadcasting for efficiency

## 7. API Design Patterns

### 7.1 RESTful Conventions

- Use HTTP methods appropriately (GET, POST, PUT, DELETE)
- Use plural nouns for resources
- Use nested routes for relationships
- Return appropriate status codes

### 7.2 Response Format

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2026-02-27T10:30:00Z"
}
```

### 7.3 Error Handling

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Email or password is incorrect",
    "details": {}
  },
  "timestamp": "2026-02-27T10:30:00Z"
}
```

## 8. Deployment Architecture

### 8.1 Infrastructure Components

```
┌─────────────────────────────────────┐
│   Load Balancer (HTTPS)             │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────┐
│  Backend    │  │  Backend    │
│  Instance 1 │  │  Instance 2 │
└──────┬──────┘  └──────┬──────┘
       │                │
       └───────┬────────┘
               │
┌──────────────▼──────────────────────┐
│   PostgreSQL (Managed Service)      │
└─────────────────────────────────────┘
```

### 8.2 Deployment Checklist

- SSL certificates configured
- Environment variables secured
- Database backups automated
- Monitoring and logging enabled
- Auto-scaling configured
- WebSocket support enabled on load balancer

## 9. Testing Strategy

### 9.1 Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Aim for 80%+ code coverage

### 9.2 Integration Tests
- Test API endpoints
- Test database operations
- Test WebSocket connections

### 9.3 Security Tests
- Test authentication flows
- Test authorization rules
- Test hash integrity verification
- Penetration testing

### 9.4 Performance Tests
- Load testing with 200+ concurrent users
- Stress testing queue updates
- Database query optimization

## 10. Monitoring and Observability

### 10.1 Metrics to Track
- API response times
- Database query performance
- WebSocket connection count
- Queue update latency
- Hash verification time
- Error rates

### 10.2 Logging
- Application logs (info, warning, error)
- Audit logs (immutable)
- Security events
- Performance metrics

### 10.3 Alerts
- High error rates
- Slow response times
- Tampering detection
- System downtime

## 11. Future Enhancements

- AI-based waiting time prediction using machine learning
- Integration with insurance systems for claims processing
- Multi-hospital network support with centralized patient records
- Interoperability with national EHR systems
- Advanced analytics dashboard with predictive insights
- Telemedicine features for remote consultations
- Payment processing integration
- Mobile app offline mode with sync

# HealthSaathi Database Schema

This directory contains the PostgreSQL database schema for the HealthSaathi healthcare management system.

## Files

- `schema.sql` - Complete database schema with tables, indexes, triggers, and comments
- `validate_schema.sh` - Bash script to validate the schema syntax and structure

## Schema Overview

The database consists of 6 main tables:

### 1. **users**
Stores all system users with role-based access control.
- Roles: Admin, Doctor, Nurse, Patient
- Includes authentication credentials (email, password_hash)
- Timestamps for audit tracking

### 2. **patients**
Stores patient demographic information.
- Links to users table via user_id
- Contains personal details: DOB, gender, phone, address, blood group
- Supports walk-in and registered patients

### 3. **doctors**
Stores doctor-specific information.
- Links to users table via user_id
- Contains specialization and license information
- Tracks average consultation duration for queue management

### 4. **appointments**
Manages all appointments and queue system.
- Supports both scheduled and walk-in appointments
- Status tracking: scheduled, checked_in, in_progress, completed, cancelled
- Queue position management for real-time waiting time calculation

### 5. **medical_records**
Stores consultation notes, diagnoses, and prescriptions.
- Version control system with parent_record_id
- Links to patient, doctor, and appointment
- Immutable history of all medical records

### 6. **audit_chain**
Blockchain-inspired audit trail for integrity verification.
- SHA-256 hash chain for tamper detection
- Stores record snapshots as JSONB
- Links each entry to previous hash (blockchain structure)
- Tamper detection flag

## Key Features

### Indexes
The schema includes optimized indexes for:
- Fast authentication lookups (email)
- Efficient queue queries (doctor_id, status, queue_position)
- Quick patient history retrieval (patient_id, created_at)
- Audit trail queries (timestamp, record_id, hash)

### Triggers
Automatic timestamp updates:
- `updated_at` column automatically updated on record modification
- Applies to users and appointments tables

### Constraints
- Foreign key relationships with appropriate CASCADE/SET NULL actions
- CHECK constraints for enum-like fields (role, status, appointment_type)
- UNIQUE constraint on user email

### Comments
All tables and important columns include descriptive comments for documentation.

## Usage

### Creating the Database

```bash
# Create database
createdb healthsaathi

# Apply schema
psql -d healthsaathi -f database/schema.sql
```

### Validating the Schema

```bash
# Make the validation script executable
chmod +x database/validate_schema.sh

# Run validation
./database/validate_schema.sh
```

The validation script will:
1. Check if PostgreSQL is installed
2. Create a temporary database
3. Apply the schema
4. Verify tables, indexes, and triggers were created
5. Display a summary
6. Clean up the temporary database

### Connecting to the Database

```bash
# Connect using psql
psql -d healthsaathi

# View all tables
\dt

# View table structure
\d users
\d appointments
\d medical_records
\d audit_chain

# View indexes
\di
```

## Schema Design Principles

1. **Normalization**: Tables are normalized to 3NF to reduce redundancy
2. **Performance**: Strategic indexes for common query patterns
3. **Integrity**: Foreign keys and constraints ensure data consistency
4. **Auditability**: Timestamps and audit chain for complete traceability
5. **Scalability**: Design supports horizontal scaling and partitioning
6. **Security**: Separation of concerns with role-based access control

## Blockchain Integrity

The audit_chain table implements a blockchain-inspired hash chain:

```
Block 0 (Genesis):  previous_hash = "0"
                    hash = SHA256(record_data + timestamp + user_id + "0")
                    
Block 1:            previous_hash = Block 0 hash
                    hash = SHA256(record_data + timestamp + user_id + Block 0 hash)
                    
Block 2:            previous_hash = Block 1 hash
                    hash = SHA256(record_data + timestamp + user_id + Block 1 hash)
```

This structure ensures:
- Any modification to historical records is detectable
- Complete audit trail of all changes
- Cryptographic proof of data integrity

## Migration Strategy

For production deployments, consider using a migration tool:
- **Python/FastAPI**: Alembic
- **Node.js**: Knex.js or Sequelize migrations

This allows for:
- Version-controlled schema changes
- Rollback capabilities
- Incremental updates without data loss

## Performance Considerations

### Query Optimization
- Use prepared statements to prevent SQL injection
- Leverage indexes for WHERE, JOIN, and ORDER BY clauses
- Monitor slow queries using `pg_stat_statements`

### Connection Pooling
- Implement connection pooling in application layer
- Recommended pool size: 10-20 connections per backend instance

### Maintenance
- Regular VACUUM and ANALYZE operations
- Monitor table bloat
- Archive old audit_chain entries if needed

## Security Best Practices

1. **Never store plaintext passwords** - Use bcrypt with cost factor 12+
2. **Use parameterized queries** - Prevent SQL injection
3. **Limit database user permissions** - Grant only necessary privileges
4. **Enable SSL connections** - Encrypt data in transit
5. **Regular backups** - Automated daily backups with point-in-time recovery
6. **Audit logging** - Enable PostgreSQL audit logging for compliance

## Future Enhancements

Potential schema extensions:
- Table partitioning for large datasets (appointments, audit_chain)
- Full-text search indexes for medical records
- Materialized views for analytics
- Time-series tables for real-time metrics
- Multi-tenancy support for multiple healthcare facilities

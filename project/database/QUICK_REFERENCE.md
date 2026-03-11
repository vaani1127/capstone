# HealthSaathi Database Quick Reference

## Quick Start

```bash
# Create database
createdb healthsaathi

# Apply schema
psql -d healthsaathi -f database/schema.sql

# Load sample data (optional)
psql -d healthsaathi -f database/sample_data.sql

# Verify schema
psql -d healthsaathi -f database/verify_schema.sql
```

## Table Summary

| Table | Purpose | Key Fields |
|-------|---------|------------|
| users | Authentication & RBAC | email, password_hash, role |
| patients | Patient demographics | user_id, date_of_birth, blood_group |
| doctors | Doctor info & metrics | user_id, specialization, avg_consultation_duration |
| appointments | Scheduling & queue | patient_id, doctor_id, status, queue_position |
| medical_records | Clinical data & versioning | patient_id, diagnosis, prescription, version_number |
| audit_chain | Blockchain integrity | record_id, hash, previous_hash |

## Common Queries

### Authentication
```sql
-- Find user by email
SELECT * FROM users WHERE email = 'user@example.com';

-- Get user with role
SELECT id, name, email, role FROM users WHERE email = ? AND role = 'Doctor';
```

### Queue Management
```sql
-- Get current queue for a doctor
SELECT a.*, p.*, u.name as patient_name
FROM appointments a
JOIN patients p ON a.patient_id = p.id
JOIN users u ON p.user_id = u.id
WHERE a.doctor_id = ? 
  AND a.status IN ('checked_in', 'in_progress')
ORDER BY a.queue_position;

-- Calculate waiting time
SELECT 
    a.queue_position,
    d.average_consultation_duration,
    (a.queue_position * d.average_consultation_duration) as estimated_wait_minutes
FROM appointments a
JOIN doctors d ON a.doctor_id = d.id
WHERE a.id = ?;
```

### Medical Records
```sql
-- Get patient history
SELECT * FROM medical_records
WHERE patient_id = ?
ORDER BY created_at DESC;

-- Get record versions
SELECT * FROM medical_records
WHERE parent_record_id = ? OR id = ?
ORDER BY version_number;
```

### Audit Trail
```sql
-- Get audit logs for a record
SELECT * FROM audit_chain
WHERE record_id = ? AND record_type = 'medical_record'
ORDER BY timestamp DESC;

-- Find tampered records
SELECT * FROM audit_chain
WHERE is_tampered = TRUE
ORDER BY timestamp DESC;

-- Verify chain integrity
SELECT 
    id,
    hash,
    previous_hash,
    LAG(hash) OVER (ORDER BY id) as expected_previous_hash
FROM audit_chain
ORDER BY id;
```

## Index Usage

```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public';
```

## Maintenance

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check slow queries (requires pg_stat_statements)
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Backup & Restore

```bash
# Backup
pg_dump healthsaathi > backup_$(date +%Y%m%d).sql

# Restore
psql -d healthsaathi < backup_20260227.sql

# Backup with compression
pg_dump healthsaathi | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore from compressed
gunzip -c backup_20260227.sql.gz | psql -d healthsaathi
```

## Connection String Examples

```bash
# Local connection
postgresql://localhost/healthsaathi

# With credentials
postgresql://username:password@localhost:5432/healthsaathi

# With SSL
postgresql://username:password@host:5432/healthsaathi?sslmode=require
```

## Environment Variables

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=healthsaathi
export PGUSER=healthsaathi_user
export PGPASSWORD=secure_password
```

## Troubleshooting

```sql
-- Check active connections
SELECT * FROM pg_stat_activity WHERE datname = 'healthsaathi';

-- Kill long-running query
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE pid = <process_id>;

-- Check locks
SELECT * FROM pg_locks WHERE NOT granted;

-- Check database size
SELECT pg_size_pretty(pg_database_size('healthsaathi'));
```

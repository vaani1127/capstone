# HealthSaathi Database Migration Guide

This guide explains how to set up and use database migrations for the HealthSaathi healthcare system.

## Overview

HealthSaathi uses **Alembic** for database migrations. Alembic is a lightweight database migration tool for SQLAlchemy, providing:
- Version control for database schema
- Upgrade and downgrade capabilities
- Migration history tracking
- Safe schema changes in production

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI and Uvicorn (web framework)
- SQLAlchemy and Alembic (database ORM and migrations)
- psycopg2-binary (PostgreSQL driver)
- Other required packages

### 2. Configure Database

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and set your database credentials:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/healthsaathi
```

### 3. Create Database

Using PostgreSQL command line:
```bash
createdb healthsaathi
```

Or using psql:
```sql
CREATE DATABASE healthsaathi;
```

### 4. Run Migrations

Using the helper script (recommended):
```bash
python migrate.py upgrade
```

Or using Alembic directly:
```bash
alembic upgrade head
```

### 5. Load Test Data (Optional)

For development and testing:
```bash
python migrate.py seed
```

## Migration Files

### Current Migrations

1. **001_initial_schema.py** - Creates the complete database schema
   - Users table with role-based access control
   - Patients and Doctors tables
   - Appointments table with queue management
   - Medical records table with versioning
   - Audit chain table for blockchain integrity
   - All indexes, constraints, and triggers

2. **002_seed_data.py** - Inserts test data
   - Sample users (Admin, Doctors, Nurses, Patients)
   - Doctor profiles with specializations
   - Patient demographics
   - Sample appointments
   - Medical records with consultations
   - Audit chain genesis block

## Using the Migration Helper Script

The `migrate.py` script provides convenient commands:

### Apply All Migrations
```bash
python migrate.py upgrade
```
Applies all pending migrations to bring the database to the latest version.

### Rollback Last Migration
```bash
python migrate.py downgrade
```
Reverts the most recent migration.

### Reset Database
```bash
python migrate.py reset
```
Rolls back all migrations and reapplies them. Useful for development.

### Check Current Version
```bash
python migrate.py current
```
Shows which migration version the database is currently at.

### View Migration History
```bash
python migrate.py history
```
Displays all available migrations and their status.

### Load Seed Data
```bash
python migrate.py seed
```
Applies the seed data migration for testing purposes.

### Create New Migration
```bash
python migrate.py create "add user preferences table"
```
Creates a new migration file with the specified message.

## Using Alembic Directly

If you prefer to use Alembic commands directly:

### Upgrade to Latest
```bash
alembic upgrade head
```

### Upgrade One Step
```bash
alembic upgrade +1
```

### Downgrade One Step
```bash
alembic downgrade -1
```

### Downgrade to Base
```bash
alembic downgrade base
```

### Show Current Version
```bash
alembic current
```

### Show History
```bash
alembic history --verbose
```

### Create New Migration
```bash
alembic revision -m "description"
```

## Seed Data Details

The seed data migration includes:

### Users (All passwords: `password123`)

| Email | Role | Name |
|-------|------|------|
| admin@healthsaathi.com | Admin | Admin User |
| rajesh.kumar@healthsaathi.com | Doctor | Dr. Rajesh Kumar |
| priya.sharma@healthsaathi.com | Doctor | Dr. Priya Sharma |
| amit.patel@healthsaathi.com | Doctor | Dr. Amit Patel |
| sunita@healthsaathi.com | Nurse | Nurse Sunita |
| kavita@healthsaathi.com | Nurse | Nurse Kavita |
| rahul.verma@example.com | Patient | Rahul Verma |
| anjali.singh@example.com | Patient | Anjali Singh |
| vikram.malhotra@example.com | Patient | Vikram Malhotra |
| neha.gupta@example.com | Patient | Neha Gupta |
| arjun.reddy@example.com | Patient | Arjun Reddy |

### Doctors

| Name | Specialization | License Number |
|------|----------------|----------------|
| Dr. Rajesh Kumar | General Medicine | MED-2024-001 |
| Dr. Priya Sharma | Pediatrics | MED-2024-002 |
| Dr. Amit Patel | Cardiology | MED-2024-003 |

### Sample Data
- 5 patients with complete demographics
- 10 appointments (today and tomorrow)
- 3 medical records with consultations and prescriptions
- Audit chain with genesis block and 3 audit entries

## Database Schema

### Tables

1. **users** - System users with role-based access
   - Roles: Admin, Doctor, Nurse, Patient
   - Password hashing with bcrypt
   - Email uniqueness constraint

2. **patients** - Patient demographic information
   - Links to users table
   - Stores DOB, gender, phone, address, blood group

3. **doctors** - Doctor credentials and metrics
   - Links to users table
   - Specialization and license number
   - Average consultation duration tracking

4. **appointments** - Appointment scheduling and queue
   - Links to patients and doctors
   - Status tracking (scheduled, checked_in, in_progress, completed, cancelled)
   - Queue position management
   - Appointment type (scheduled, walk_in)

5. **medical_records** - Medical records with versioning
   - Consultation notes, diagnosis, prescription
   - Version control with parent_record_id
   - Links to patient, doctor, and appointment

6. **audit_chain** - Blockchain-inspired audit trail
   - SHA-256 hash chain for integrity
   - Stores record data as JSONB
   - Tamper detection flag
   - Links to previous hash (blockchain structure)

### Key Features

- **Foreign Key Constraints**: Ensure referential integrity
- **Check Constraints**: Validate enum values (roles, statuses)
- **Indexes**: Optimize query performance
- **Triggers**: Auto-update timestamps
- **Comments**: Document table and column purposes

## Creating New Migrations

### Manual Migration

1. Create a new migration file:
```bash
python migrate.py create "add email verification"
```

2. Edit the generated file in `alembic/versions/`:
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), default=False))

def downgrade() -> None:
    op.drop_column('users', 'email_verified')
```

3. Apply the migration:
```bash
python migrate.py upgrade
```

### Auto-generate Migration (requires SQLAlchemy models)

```bash
alembic revision --autogenerate -m "description"
```

Note: Auto-generation requires SQLAlchemy models to be defined and imported in `alembic/env.py`.

## Production Deployment

### Best Practices

1. **Never use seed data in production**
   - Only apply migration 001 (schema)
   - Skip migration 002 (seed data)

2. **Always backup before migrating**
   ```bash
   pg_dump healthsaathi > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Test in staging first**
   - Apply migrations to staging environment
   - Verify application functionality
   - Then apply to production

4. **Use environment variables**
   - Never commit `.env` file
   - Use secure credential management
   - Different credentials per environment

5. **Run migrations as part of deployment**
   ```bash
   # In deployment script
   python migrate.py upgrade
   ```

6. **Monitor migration execution**
   - Check logs for errors
   - Verify data integrity
   - Test application after migration

### Production Migration Command

```bash
# Only apply schema, skip seed data
alembic upgrade 001
```

Or to apply all migrations except seed:
```bash
# Apply all migrations
alembic upgrade head

# Then rollback seed data if accidentally applied
alembic downgrade -1
```

## Troubleshooting

### Connection Errors

**Problem**: Cannot connect to database

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   pg_isready
   ```

2. Check database exists:
   ```bash
   psql -l | grep healthsaathi
   ```

3. Verify credentials in `.env`

4. Test connection:
   ```bash
   psql postgresql://user:pass@localhost:5432/healthsaathi
   ```

### Migration Conflicts

**Problem**: Migration version mismatch

**Solutions**:
1. Check current version:
   ```bash
   alembic current
   ```

2. View history:
   ```bash
   alembic history
   ```

3. Stamp to specific version (use with caution):
   ```bash
   alembic stamp head
   ```

### Rollback Issues

**Problem**: Cannot rollback migration

**Solutions**:
1. Check for data dependencies
2. Manually fix data issues
3. Use SQL to resolve conflicts
4. Consider creating a new migration to fix issues

### Reset Development Database

If your development database gets into a bad state:

```bash
# Drop and recreate database
dropdb healthsaathi
createdb healthsaathi

# Reapply migrations
python migrate.py upgrade

# Load seed data
python migrate.py seed
```

## File Structure

```
project/
├── alembic/                    # Alembic migrations directory
│   ├── versions/               # Migration files
│   │   ├── 001_initial_schema.py
│   │   └── 002_seed_data.py
│   ├── env.py                  # Alembic environment config
│   ├── script.py.mako          # Migration template
│   └── README.md               # Alembic-specific docs
├── database/                   # Database documentation
│   ├── schema.sql              # Reference schema
│   └── ...
├── alembic.ini                 # Alembic configuration
├── migrate.py                  # Migration helper script
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .env                        # Environment variables (gitignored)
└── MIGRATION_GUIDE.md          # This file
```

## Next Steps

After setting up migrations:

1. **Develop Backend API**
   - Create SQLAlchemy models
   - Implement FastAPI endpoints
   - Add authentication and authorization

2. **Implement Business Logic**
   - Appointment booking
   - Queue management
   - Medical records
   - Blockchain integrity

3. **Add Tests**
   - Unit tests for migrations
   - Integration tests for database operations
   - Test rollback scenarios

4. **Setup CI/CD**
   - Automated migration testing
   - Staging environment migrations
   - Production deployment pipeline

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

For issues or questions:
1. Check this guide
2. Review Alembic documentation
3. Check migration logs
4. Consult the development team

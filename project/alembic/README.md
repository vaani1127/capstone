# HealthSaathi Database Migrations

This directory contains Alembic database migrations for the HealthSaathi healthcare system.

## Prerequisites

1. PostgreSQL installed and running
2. Python 3.8+ installed
3. Virtual environment activated

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Update the `.env` file with your database credentials:
```
DATABASE_URL=postgresql://username:password@localhost:5432/healthsaathi
```

4. Create the database:
```bash
createdb healthsaathi
```
Or using psql:
```sql
CREATE DATABASE healthsaathi;
```

## Running Migrations

### Apply all migrations (upgrade to latest):
```bash
alembic upgrade head
```

### Apply migrations one at a time:
```bash
alembic upgrade +1
```

### Rollback last migration:
```bash
alembic downgrade -1
```

### Rollback all migrations:
```bash
alembic downgrade base
```

### Check current migration version:
```bash
alembic current
```

### View migration history:
```bash
alembic history
```

## Migration Files

- **001_initial_schema.py**: Creates all database tables, indexes, triggers, and constraints
- **002_seed_data.py**: Inserts test data for development and testing

## Seed Data

The seed data migration (002) includes:

### Users (Password: `password123` for all users)
- 1 Admin: admin@healthsaathi.com
- 3 Doctors: rajesh.kumar@, priya.sharma@, amit.patel@healthsaathi.com
- 2 Nurses: sunita@, kavita@healthsaathi.com
- 5 Patients: Various patient accounts

### Doctors
- Dr. Rajesh Kumar - General Medicine
- Dr. Priya Sharma - Pediatrics
- Dr. Amit Patel - Cardiology

### Sample Data
- Patient demographics
- Appointments (today and tomorrow)
- Medical records with consultations
- Audit chain with genesis block

## Creating New Migrations

To create a new migration:
```bash
alembic revision -m "description of changes"
```

For auto-generating migrations (requires SQLAlchemy models):
```bash
alembic revision --autogenerate -m "description of changes"
```

## Database Schema

The database includes the following tables:
- **users**: System users with role-based access
- **patients**: Patient demographic information
- **doctors**: Doctor credentials and metrics
- **appointments**: Appointment scheduling and queue management
- **medical_records**: Medical records with versioning
- **audit_chain**: Blockchain-inspired audit trail

## Troubleshooting

### Connection Issues
If you get connection errors, verify:
1. PostgreSQL is running
2. Database exists
3. Credentials in `.env` are correct
4. Database URL format is correct

### Migration Conflicts
If migrations are out of sync:
```bash
# Check current version
alembic current

# View history
alembic history

# Stamp database to specific version (use with caution)
alembic stamp head
```

### Reset Database
To completely reset the database:
```bash
# Rollback all migrations
alembic downgrade base

# Reapply all migrations
alembic upgrade head
```

## Production Deployment

For production:
1. Never use seed data migration in production
2. Use environment variables for database credentials
3. Run migrations as part of deployment pipeline
4. Always backup database before running migrations
5. Test migrations in staging environment first

## Notes

- The `alembic.ini` file contains the default database URL, but it's overridden by the `DATABASE_URL` environment variable
- All timestamps use UTC
- Foreign key constraints ensure referential integrity
- Triggers automatically update `updated_at` timestamps
- The audit chain starts with a genesis block (previous_hash = "0")

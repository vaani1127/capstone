# HealthSaathi - Quick Start Guide

Get the HealthSaathi database up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and update with your database credentials
# DATABASE_URL=postgresql://username:password@localhost:5432/healthsaathi
```

### 3. Create Database

```bash
# Using createdb command
createdb healthsaathi

# OR using psql
psql -U postgres -c "CREATE DATABASE healthsaathi;"
```

### 4. Run Migrations

```bash
# Apply all migrations
python migrate.py upgrade
```

### 5. Load Test Data (Optional)

```bash
# Load seed data for development/testing
python migrate.py seed
```

### 6. Verify Setup

```bash
# Run verification tests
python test_migrations.py
```

## What You Get

After running the migrations, your database will have:

### Tables
- ✅ users (with role-based access control)
- ✅ patients (demographic information)
- ✅ doctors (credentials and metrics)
- ✅ appointments (scheduling and queue management)
- ✅ medical_records (with versioning)
- ✅ audit_chain (blockchain-inspired integrity)

### Test Data (if you ran seed)
- 11 users (1 Admin, 3 Doctors, 2 Nurses, 5 Patients)
- 3 doctor profiles
- 5 patient profiles
- 10 sample appointments
- 3 medical records
- Audit chain with genesis block

### Test Credentials
All test users have password: `password123`

**Admin:**
- admin@healthsaathi.com

**Doctors:**
- rajesh.kumar@healthsaathi.com (General Medicine)
- priya.sharma@healthsaathi.com (Pediatrics)
- amit.patel@healthsaathi.com (Cardiology)

**Nurses:**
- sunita@healthsaathi.com
- kavita@healthsaathi.com

**Patients:**
- rahul.verma@example.com
- anjali.singh@example.com
- vikram.malhotra@example.com
- neha.gupta@example.com
- arjun.reddy@example.com

## Common Commands

```bash
# Apply migrations
python migrate.py upgrade

# Rollback last migration
python migrate.py downgrade

# Reset database (rollback all and reapply)
python migrate.py reset

# Check current version
python migrate.py current

# View migration history
python migrate.py history

# Load seed data
python migrate.py seed

# Create new migration
python migrate.py create "description"

# Run tests
python test_migrations.py
```

## Troubleshooting

### Can't connect to database?
1. Check PostgreSQL is running: `pg_isready`
2. Verify credentials in `.env`
3. Ensure database exists: `psql -l | grep healthsaathi`

### Alembic not found?
```bash
pip install -r requirements.txt
```

### Migration errors?
```bash
# Reset and try again
python migrate.py reset
```

### Need to start fresh?
```bash
# Drop and recreate database
dropdb healthsaathi
createdb healthsaathi

# Reapply migrations
python migrate.py upgrade
python migrate.py seed
```

## Next Steps

1. **Start Backend Development**
   - Create SQLAlchemy models
   - Implement FastAPI endpoints
   - Add authentication

2. **Read Documentation**
   - `MIGRATION_GUIDE.md` - Detailed migration guide
   - `alembic/README.md` - Alembic-specific docs
   - `database/README.md` - Database schema docs

3. **Explore the Schema**
   ```bash
   psql healthsaathi
   \dt          # List tables
   \d users     # Describe users table
   \d+ appointments  # Detailed table info
   ```

## Need Help?

- Check `MIGRATION_GUIDE.md` for detailed documentation
- Review migration files in `alembic/versions/`
- Run `python migrate.py help` for command reference
- Run `python test_migrations.py` to verify setup

## Production Deployment

⚠️ **Important**: Never use seed data in production!

```bash
# Production: Only apply schema migration
alembic upgrade 001

# Skip the seed data migration (002)
```

---

**Ready to build!** 🚀

Your database is now set up and ready for backend development.

# HealthSaathi - Quick Start Setup (5 Minutes)

Get HealthSaathi running locally in 5 minutes!

## Prerequisites

- Python 3.9+ 
- PostgreSQL 13+
- pip

## Setup Steps

All steps run from the `backend/` directory!

### 1. Install Python Dependencies

From project root:

```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables

From project root:

```bash
cp .env.example .env
# Edit .env with your database credentials:
# For Neon Cloud DB:
# DATABASE_URL=postgresql://user:password@host/database?sslmode=require&channel_binding=require
# For Local PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/healthsaathi
```

### 3. Create & Setup Database

From the `backend/` directory:

```bash
cd backend
python setup_tables.py
```

This creates all required tables:
- users, patients, doctors, appointments, medical_records, audit_chain

### 4. Load Test Data (Optional)

From the `backend/` directory:

```bash
python load_test_data.py
```

### 5. Run Backend

From the `backend/` directory:

```bash
python run.py
```

Visit http://localhost:8000/api/docs to see interactive API documentation.

## Test Credentials (if seed data loaded)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@healthsaathi.com | password123 |
| Doctor | rajesh.kumar@healthsaathi.com | password123 |
| Nurse | sunita@healthsaathi.com | password123 |
| Patient | rahul.verma@example.com | password123 |

## What You Get

✅ Complete database schema with 6 tables  
✅ JWT authentication with roles (Admin, Doctor, Nurse, Patient)  
✅ 20+ API endpoints  
✅ Real-time queue management  
✅ Blockchain-backed medical records  
✅ Complete audit trail  

## Next Steps

- Read [4_API_DOCUMENTATION.md](4_API_DOCUMENTATION.md) for API details
- Read [7_USER_GUIDE.md](7_USER_GUIDE.md) for feature walkthroughs
- Check [5_DEPLOYMENT.md](5_DEPLOYMENT.md) for production setup

---

For detailed setup, see [2_BACKEND_SETUP.md](2_BACKEND_SETUP.md) and [3_DATABASE_SETUP.md](3_DATABASE_SETUP.md).

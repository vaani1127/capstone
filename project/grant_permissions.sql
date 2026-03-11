-- Grant necessary permissions to healthsaathi_user
-- Run this as the postgres superuser

-- Connect to the healthsaathi_db database
\c healthsaathi_db

-- Grant all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE healthsaathi_db TO healthsaathi_user;

-- Grant usage and create on the public schema
GRANT USAGE, CREATE ON SCHEMA public TO healthsaathi_user;

-- Grant all privileges on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO healthsaathi_user;

-- Grant all privileges on all sequences in public schema
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO healthsaathi_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO healthsaathi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO healthsaathi_user;

-- Make healthsaathi_user the owner of the public schema (optional but recommended)
ALTER SCHEMA public OWNER TO healthsaathi_user;

\echo 'Permissions granted successfully!'

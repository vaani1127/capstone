-- Schema Verification Queries
-- Run these queries after applying schema.sql to verify the database structure

-- ============================================================================
-- TABLE VERIFICATION
-- ============================================================================

-- List all tables
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- ============================================================================
-- COLUMN VERIFICATION
-- ============================================================================

-- Verify users table structure
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- Verify appointments table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'appointments'
ORDER BY ordinal_position;

-- Verify audit_chain table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'audit_chain'
ORDER BY ordinal_position;

-- ============================================================================
-- INDEX VERIFICATION
-- ============================================================================

-- List all indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Count indexes per table
SELECT 
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY index_count DESC;

-- ============================================================================
-- CONSTRAINT VERIFICATION
-- ============================================================================

-- List all foreign key constraints
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule,
    rc.update_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- List all check constraints
SELECT
    tc.table_name,
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints AS tc
JOIN information_schema.check_constraints AS cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.constraint_type = 'CHECK'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- ============================================================================
-- TRIGGER VERIFICATION
-- ============================================================================

-- List all triggers
SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement,
    action_timing
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;

-- ============================================================================
-- RELATIONSHIP VERIFICATION
-- ============================================================================

-- Verify table relationships (entity-relationship diagram in text)
SELECT 
    'users -> patients' as relationship,
    COUNT(*) as constraint_exists
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
    AND table_name = 'patients'
    AND constraint_name LIKE '%user_id%'

UNION ALL

SELECT 
    'users -> doctors' as relationship,
    COUNT(*) as constraint_exists
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
    AND table_name = 'doctors'
    AND constraint_name LIKE '%user_id%'

UNION ALL

SELECT 
    'patients -> appointments' as relationship,
    COUNT(*) as constraint_exists
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
    AND table_name = 'appointments'
    AND constraint_name LIKE '%patient_id%'

UNION ALL

SELECT 
    'doctors -> appointments' as relationship,
    COUNT(*) as constraint_exists
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
    AND table_name = 'appointments'
    AND constraint_name LIKE '%doctor_id%'

UNION ALL

SELECT 
    'appointments -> medical_records' as relationship,
    COUNT(*) as constraint_exists
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
    AND table_name = 'medical_records'
    AND constraint_name LIKE '%appointment_id%';

-- ============================================================================
-- SUMMARY STATISTICS
-- ============================================================================

-- Overall schema summary
SELECT 
    'Tables' as object_type,
    COUNT(*) as count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'

UNION ALL

SELECT 
    'Indexes' as object_type,
    COUNT(*) as count
FROM pg_indexes
WHERE schemaname = 'public'

UNION ALL

SELECT 
    'Foreign Keys' as object_type,
    COUNT(*) as count
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public'

UNION ALL

SELECT 
    'Check Constraints' as object_type,
    COUNT(*) as count
FROM information_schema.table_constraints
WHERE constraint_type = 'CHECK' AND table_schema = 'public'

UNION ALL

SELECT 
    'Triggers' as object_type,
    COUNT(*) as count
FROM information_schema.triggers
WHERE trigger_schema = 'public';

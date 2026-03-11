#!/bin/bash
# Schema Validation Script for HealthSaathi Database
# This script validates the PostgreSQL schema syntax

echo "=========================================="
echo "HealthSaathi Database Schema Validator"
echo "=========================================="
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL client (psql) is not installed"
    echo "Please install PostgreSQL to validate the schema"
    exit 1
fi

echo "✓ PostgreSQL client found"
echo ""

# Check if schema file exists
if [ ! -f "database/schema.sql" ]; then
    echo "❌ Schema file not found: database/schema.sql"
    exit 1
fi

echo "✓ Schema file found"
echo ""

# Validate SQL syntax using PostgreSQL's --dry-run equivalent
# We'll create a temporary database for validation
DB_NAME="healthsaathi_validation_temp_$$"

echo "Creating temporary validation database..."
createdb "$DB_NAME" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Could not create temporary database"
    echo "Attempting syntax validation only..."
    
    # Basic syntax check
    psql -d postgres -f database/schema.sql --single-transaction --set ON_ERROR_STOP=on --dry-run 2>&1 | head -20
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "✓ Basic syntax validation passed"
    else
        echo "❌ Syntax errors detected in schema"
        exit 1
    fi
else
    echo "✓ Temporary database created"
    echo ""
    echo "Applying schema to validation database..."
    
    # Apply schema
    psql -d "$DB_NAME" -f database/schema.sql --single-transaction --set ON_ERROR_STOP=on
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Schema applied successfully"
        echo ""
        echo "Validating schema structure..."
        
        # Check tables
        TABLE_COUNT=$(psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
        echo "  - Tables created: $TABLE_COUNT"
        
        # Check indexes
        INDEX_COUNT=$(psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';")
        echo "  - Indexes created: $INDEX_COUNT"
        
        # Check triggers
        TRIGGER_COUNT=$(psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public';")
        echo "  - Triggers created: $TRIGGER_COUNT"
        
        echo ""
        echo "✓ All validations passed!"
        echo ""
        echo "Schema Summary:"
        psql -d "$DB_NAME" -c "\dt"
        
    else
        echo ""
        echo "❌ Schema validation failed"
        dropdb "$DB_NAME" 2>/dev/null
        exit 1
    fi
    
    # Cleanup
    echo ""
    echo "Cleaning up temporary database..."
    dropdb "$DB_NAME"
    echo "✓ Cleanup complete"
fi

echo ""
echo "=========================================="
echo "Validation Complete"
echo "=========================================="

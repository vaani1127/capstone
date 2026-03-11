#!/bin/bash
# HealthSaathi Database Restore Script

set -e

# Configuration
BACKUP_FILE="${1}"

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-healthsaathi}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if backup file is provided
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not specified${NC}"
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HealthSaathi Database Restore${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Timestamp: $(date)"
echo "Database: $DB_NAME@$DB_HOST:$DB_PORT"
echo "Backup file: $BACKUP_FILE"
echo ""

# Warning
echo -e "${RED}WARNING: This will overwrite the current database!${NC}"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Verify backup integrity
echo -e "${YELLOW}Verifying backup integrity...${NC}"
if ! gunzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo -e "${RED}✗ Backup file is corrupted${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backup integrity verified${NC}"

# Create backup of current database before restore
echo -e "${YELLOW}Creating backup of current database...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CURRENT_BACKUP="/tmp/healthsaathi_pre_restore_$TIMESTAMP.sql.gz"
export PGPASSWORD="$DB_PASSWORD"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$CURRENT_BACKUP"
echo -e "${GREEN}✓ Current database backed up to: $CURRENT_BACKUP${NC}"

# Drop and recreate database
echo -e "${YELLOW}Dropping and recreating database...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;
EOF

echo -e "${GREEN}✓ Database recreated${NC}"

# Restore from backup
echo -e "${YELLOW}Restoring from backup...${NC}"
if gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; then
    echo -e "${GREEN}✓ Database restored successfully${NC}"
    
    # Verify restoration
    echo -e "${YELLOW}Verifying restoration...${NC}"
    USERS_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users;")
    APPOINTMENTS_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM appointments;")
    
    echo "Users: $USERS_COUNT"
    echo "Appointments: $APPOINTMENTS_COUNT"
    echo -e "${GREEN}✓ Verification complete${NC}"
    
else
    echo -e "${RED}✗ Restore failed!${NC}"
    echo "Attempting to restore from pre-restore backup..."
    
    gunzip -c "$CURRENT_BACKUP" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
    echo -e "${YELLOW}Restored to pre-restore state${NC}"
    exit 1
fi

unset PGPASSWORD

echo ""
echo -e "${GREEN}Restore process complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart application services"
echo "2. Verify application functionality"
echo "3. Check audit logs"
echo ""

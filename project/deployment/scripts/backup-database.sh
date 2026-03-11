#!/bin/bash
# HealthSaathi Database Backup Script

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/healthsaathi}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/healthsaathi_$TIMESTAMP.sql.gz"

# Database configuration (from environment or defaults)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-healthsaathi}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD}"

# S3 configuration (optional)
S3_BUCKET="${S3_BUCKET}"
S3_PREFIX="${S3_PREFIX:-healthsaathi/backups}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}HealthSaathi Database Backup${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Timestamp: $(date)"
echo "Database: $DB_NAME@$DB_HOST:$DB_PORT"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Perform backup
echo -e "${YELLOW}Starting backup...${NC}"
export PGPASSWORD="$DB_PASSWORD"

if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    echo -e "${GREEN}✓ Backup completed successfully${NC}"
    echo "Backup file: $BACKUP_FILE"
    
    # Get file size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup size: $BACKUP_SIZE"
    
    # Upload to S3 if configured
    if [ -n "$S3_BUCKET" ]; then
        echo -e "${YELLOW}Uploading to S3...${NC}"
        if aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/$S3_PREFIX/$(basename $BACKUP_FILE)"; then
            echo -e "${GREEN}✓ Uploaded to S3${NC}"
        else
            echo -e "${RED}✗ Failed to upload to S3${NC}"
        fi
    fi
    
    # Clean up old backups
    echo -e "${YELLOW}Cleaning up old backups...${NC}"
    find "$BACKUP_DIR" -name "healthsaathi_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo -e "${GREEN}✓ Old backups cleaned up (retention: $RETENTION_DAYS days)${NC}"
    
    # Verify backup integrity
    echo -e "${YELLOW}Verifying backup integrity...${NC}"
    if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ Backup integrity verified${NC}"
    else
        echo -e "${RED}✗ Backup integrity check failed${NC}"
        exit 1
    fi
    
else
    echo -e "${RED}✗ Backup failed!${NC}"
    exit 1
fi

unset PGPASSWORD

echo ""
echo -e "${GREEN}Backup process complete!${NC}"
echo ""

# List recent backups
echo "Recent backups:"
ls -lh "$BACKUP_DIR" | tail -5

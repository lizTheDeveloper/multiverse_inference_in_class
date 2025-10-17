#!/bin/bash
# Backup script for Multiverse Inference Gateway
# Backs up database to local directory and optionally to GCS

set -e  # Exit on error

# Configuration
APP_DIR="/opt/multiverse-gateway"
DB_FILE="$APP_DIR/gateway.db"
BACKUP_DIR="$HOME/backups/multiverse-gateway"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7

# GCS bucket (optional - set to enable cloud backup)
GCS_BUCKET="${GCS_BACKUP_BUCKET:-}"

echo "=========================================="
echo "Multiverse Gateway - Backup"
echo "=========================================="
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file not found: $DB_FILE"
    exit 1
fi

echo "Backing up database..."
echo "  Source: $DB_FILE"
echo "  Destination: $BACKUP_DIR"
echo ""

# Backup using SQLite backup command (proper way - handles locks)
BACKUP_FILE="$BACKUP_DIR/gateway_$DATE.db"

sqlite3 "$DB_FILE" ".backup $BACKUP_FILE"

# Verify backup was created
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Backup created: gateway_$DATE.db ($SIZE)"
else
    echo "✗ Backup failed!"
    exit 1
fi

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"
echo "✓ Compressed: gateway_$DATE.db.gz"

# Upload to GCS if configured
if [ -n "$GCS_BUCKET" ]; then
    echo ""
    echo "Uploading to Google Cloud Storage..."

    if command -v gsutil &> /dev/null; then
        gsutil cp "$BACKUP_FILE.gz" "gs://$GCS_BUCKET/multiverse-gateway/gateway_$DATE.db.gz"
        echo "✓ Uploaded to: gs://$GCS_BUCKET/multiverse-gateway/gateway_$DATE.db.gz"
    else
        echo "✗ gsutil not found. Install Google Cloud SDK to enable GCS backups."
    fi
fi

# Clean up old backups
echo ""
echo "Cleaning up old backups (keeping last $KEEP_DAYS days)..."
find "$BACKUP_DIR" -name "gateway_*.db.gz" -mtime +$KEEP_DAYS -delete
REMAINING=$(find "$BACKUP_DIR" -name "gateway_*.db.gz" | wc -l)
echo "✓ Backups remaining: $REMAINING"

# List recent backups
echo ""
echo "Recent backups:"
ls -lh "$BACKUP_DIR"/gateway_*.db.gz | tail -5

echo ""
echo "=========================================="
echo "Backup Complete!"
echo "=========================================="
echo ""

# Add to crontab reminder
if ! crontab -l 2>/dev/null | grep -q "backup.sh"; then
    echo "Tip: Add to crontab for automatic daily backups:"
    echo "  crontab -e"
    echo "  0 2 * * * $APP_DIR/deploy/backup.sh >> $HOME/backup.log 2>&1"
    echo ""
fi

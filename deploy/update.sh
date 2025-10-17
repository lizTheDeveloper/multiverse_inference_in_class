#!/bin/bash
# Update script for Multiverse Inference Gateway
# Pulls latest code and restarts the service

set -e  # Exit on error

echo "=========================================="
echo "Multiverse Gateway - Update"
echo "=========================================="
echo ""

# Check not running as root
if [ "$EUID" -eq 0 ]; then
   echo "Do NOT run this script as root"
   echo "Run as gateway user: sudo su - gateway"
   exit 1
fi

# Set application directory
APP_DIR="/opt/multiverse-gateway"
cd "$APP_DIR"

echo "Working directory: $(pwd)"
echo ""

# Backup database
echo "1. Backing up database..."
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/backups"
mkdir -p "$BACKUP_DIR"

if [ -f "gateway.db" ]; then
    cp gateway.db "$BACKUP_DIR/gateway_$DATE.db"
    echo "   Backup saved to: $BACKUP_DIR/gateway_$DATE.db"
fi

# Pull latest code
echo "2. Pulling latest code..."
git fetch origin
git pull origin main

# Activate virtual environment
echo "3. Activating virtual environment..."
source env/bin/activate

# Update dependencies
echo "4. Updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations if needed
echo "5. Checking database..."
python -c "import asyncio; from app.utils.database import init_database; asyncio.run(init_database())"

# Test the update
echo "6. Testing update..."
python -c "from app.main import app; print('✓ Application imports successfully')"

echo ""
echo "=========================================="
echo "Update Complete!"
echo "=========================================="
echo ""
echo "To apply the update:"
echo "  sudo systemctl restart multiverse-gateway"
echo ""
echo "To check status:"
echo "  sudo systemctl status multiverse-gateway"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u multiverse-gateway -f"
echo ""

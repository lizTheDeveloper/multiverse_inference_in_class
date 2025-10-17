#!/bin/bash
# Installation script for Multiverse Inference Gateway
# Run this as the gateway user (not root)

set -e  # Exit on error

echo "=========================================="
echo "Multiverse Gateway - Installation"
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

# Create virtual environment
echo "1. Creating Python virtual environment..."
python3.11 -m venv env
source env/bin/activate

# Upgrade pip
echo "2. Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "3. Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "4. Creating .env file..."
    cp .env.example .env

    # Generate secure API key
    ADMIN_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s/your-super-secret-admin-key-change-this-in-production/$ADMIN_KEY/" .env

    echo "Generated secure ADMIN_API_KEY"
    echo "IMPORTANT: Save this key: $ADMIN_KEY"
else
    echo "4. .env file already exists, skipping..."
fi

# Create logs directory
echo "5. Creating logs directory..."
mkdir -p logs

# Initialize database
echo "6. Initializing database..."
python -c "import asyncio; from app.utils.database import init_database; asyncio.run(init_database())"

# Test installation
echo "7. Testing installation..."
python -c "from app.main import app; print('✓ Application imports successfully')"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review .env configuration"
echo "2. Install systemd service (as root):"
echo "   sudo cp deploy/multiverse-gateway.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable multiverse-gateway"
echo "   sudo systemctl start multiverse-gateway"
echo "3. Configure nginx (see deploy/nginx.conf)"
echo "4. Set up SSL with certbot"
echo ""

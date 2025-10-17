#!/bin/bash
# GCE Instance Setup Script for Multiverse Inference Gateway
# This script initializes a fresh GCE instance for running the gateway

set -e  # Exit on error

echo "=========================================="
echo "Multiverse Gateway - GCE Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   echo "Please run as root (use sudo)"
   exit 1
fi

# Update system
echo "1. Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "2. Installing system dependencies..."
apt-get install -y \
    software-properties-common \
    build-essential \
    git \
    curl \
    wget \
    ufw \
    nginx \
    certbot \
    python3-certbot-nginx

# Install Python 3.11
echo "3. Installing Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip

# Verify Python installation
python3.11 --version

# Create gateway user
echo "4. Creating gateway user..."
if id "gateway" &>/dev/null; then
    echo "User 'gateway' already exists"
else
    useradd -r -m -s /bin/bash gateway
    echo "User 'gateway' created"
fi

# Create application directory
echo "5. Creating application directory..."
mkdir -p /opt/multiverse-gateway
chown gateway:gateway /opt/multiverse-gateway

# Configure firewall
echo "6. Configuring firewall..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw status

# Configure automatic security updates
echo "7. Enabling automatic security updates..."
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

echo ""
echo "=========================================="
echo "GCE Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Switch to gateway user: sudo su - gateway"
echo "2. Clone repository to /opt/multiverse-gateway"
echo "3. Run deploy/install.sh as gateway user"
echo ""

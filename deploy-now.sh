#!/bin/bash
set -e

echo "=== Deploying to GCE ==="

# Go to server and deploy
gcloud compute ssh multiverse-gateway --project=multiverseschool --zone=us-west1-b << 'ENDSSH'
set -e

cd /opt/multiverse-gateway

echo "1. Backing up..."
sudo cp -a . "../gateway-backup-$(date +%Y%m%d-%H%M%S)"

echo "2. Checking if git repo exists..."
if [ ! -d .git ]; then
    echo "   No git repo found, files were deployed manually"
    echo "   Pulling from GitHub..."
    
    cd /tmp
    git clone https://github.com/YOUR_USERNAME/multiverse_inference_in_class.git
    
    sudo systemctl stop multiverse-gateway
    
    sudo -u gateway cp -r /tmp/multiverse_inference_in_class/app/* /opt/multiverse-gateway/app/
    sudo -u gateway cp /tmp/multiverse_inference_in_class/requirements.txt /opt/multiverse-gateway/
    
    rm -rf /tmp/multiverse_inference_in_class
else
    echo "   Git repo exists, pulling..."
    sudo systemctl stop multiverse-gateway
    sudo -u gateway git pull origin main
fi

echo "3. Installing dependencies..."
sudo -u gateway env/bin/pip install -q -r requirements.txt

echo "4. Checking for PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "   Installing PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

echo "5. Setting up database..."
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='multiverse_gateway'" 2>/dev/null || echo "0")
if [ "$DB_EXISTS" != "1" ]; then
    sudo -u postgres psql << 'PSQL'
CREATE USER gateway_user WITH PASSWORD 'gateway_pass_2024';
CREATE DATABASE multiverse_gateway OWNER gateway_user;
GRANT ALL PRIVILEGES ON DATABASE multiverse_gateway TO gateway_user;
PSQL
fi

echo "6. Updating .env..."
if ! grep -q "POSTGRES_CONNECTION_STRING" .env 2>/dev/null; then
    echo 'POSTGRES_CONNECTION_STRING="postgresql://gateway_user:gateway_pass_2024@localhost:5432/multiverse_gateway"' | sudo -u gateway tee -a .env
fi

echo "7. Starting service..."
sudo systemctl start multiverse-gateway

sleep 5

echo "8. Status check..."
sudo systemctl status multiverse-gateway --no-pager | head -10

echo ""
echo "✅ Deployment complete!"

ENDSSH

echo "Done!"


#!/bin/bash

#
# Deploy session authentication and fixes to GCE
#

set -e

echo "=== Deployment Script: Session Auth + Root Redirect Fix ==="
echo ""

# Configuration
PROJECT="multiverseschool"
ZONE="us-west1-b"
INSTANCE="multiverse-gateway"
DEPLOY_DIR="/opt/multiverse-gateway"

echo "Target: $INSTANCE in $PROJECT/$ZONE"
echo ""

# Check if we have the PostgreSQL connection string
if [ -z "$POSTGRES_CONNECTION_STRING" ]; then
    echo "⚠️  WARNING: POSTGRES_CONNECTION_STRING environment variable not set"
    echo "   Session authentication will not work without it."
    echo ""
    read -p "Do you want to enter the PostgreSQL connection string now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter PostgreSQL connection string: " POSTGRES_CONNECTION_STRING
        export POSTGRES_CONNECTION_STRING
    fi
fi

echo "📦 Step 1: Creating deployment package..."
cd "$(dirname "$0")/.."

# Create temp directory for deployment
TEMP_DIR=$(mktemp -d)
echo "   Using temp dir: $TEMP_DIR"

# Copy updated files
mkdir -p "$TEMP_DIR/app/utils"
mkdir -p "$TEMP_DIR/app/routers"
cp app/main.py "$TEMP_DIR/app/"
cp app/utils/auth.py "$TEMP_DIR/app/utils/"
cp app/utils/session_auth.py "$TEMP_DIR/app/utils/"
cp app/routers/admin.py "$TEMP_DIR/app/routers/"
cp requirements.txt "$TEMP_DIR/"

echo "   ✅ Files packaged"
echo ""

echo "📤 Step 2: Uploading files to GCE..."
gcloud compute scp --recurse "$TEMP_DIR/*" \
    "${INSTANCE}:/tmp/gateway-update/" \
    --project="$PROJECT" \
    --zone="$ZONE"
echo "   ✅ Files uploaded"
echo ""

echo "🔧 Step 3: Installing updates on GCE..."
gcloud compute ssh "$INSTANCE" \
    --project="$PROJECT" \
    --zone="$ZONE" \
    -- 'bash -s' << 'ENDSSH'

set -e

echo "   → Stopping gateway service..."
sudo systemctl stop multiverse-gateway

echo "   → Backing up current installation..."
sudo cp -r /opt/multiverse-gateway /opt/multiverse-gateway.backup.$(date +%Y%m%d_%H%M%S)

echo "   → Installing updated files..."
sudo -u gateway cp /tmp/gateway-update/app/main.py /opt/multiverse-gateway/app/
sudo -u gateway cp /tmp/gateway-update/app/utils/auth.py /opt/multiverse-gateway/app/utils/
sudo -u gateway cp /tmp/gateway-update/app/utils/session_auth.py /opt/multiverse-gateway/app/utils/
sudo -u gateway cp /tmp/gateway-update/app/routers/admin.py /opt/multiverse-gateway/app/routers/
sudo -u gateway cp /tmp/gateway-update/requirements.txt /opt/multiverse-gateway/

echo "   → Installing new dependencies..."
cd /opt/multiverse-gateway
sudo -u gateway ./env/bin/pip install -q google-cloud-firestore==2.14.0 psycopg2-binary==2.9.9

echo "   → Cleaning up temp files..."
rm -rf /tmp/gateway-update

echo "   → Starting gateway service..."
sudo systemctl start multiverse-gateway

echo "   → Waiting for service to start..."
sleep 5

echo "   → Checking service status..."
sudo systemctl status multiverse-gateway --no-pager | head -15

ENDSSH

echo "   ✅ Installation complete"
echo ""

# Update .env if we have the connection string
if [ -n "$POSTGRES_CONNECTION_STRING" ]; then
    echo "🔐 Step 4: Configuring database connection..."
    gcloud compute ssh "$INSTANCE" \
        --project="$PROJECT" \
        --zone="$ZONE" \
        -- "bash -c 'sudo -u gateway bash -c \"echo \\\"POSTGRES_CONNECTION_STRING=$POSTGRES_CONNECTION_STRING\\\" >> /opt/multiverse-gateway/.env && sudo systemctl restart multiverse-gateway\"'"
    echo "   ✅ Database connection configured"
    echo ""
else
    echo "⚠️  Step 4: Skipping database configuration (no connection string provided)"
    echo "   To enable session auth later, run:"
    echo "   gcloud compute ssh $INSTANCE --project=$PROJECT --zone=$ZONE"
    echo "   sudo nano /opt/multiverse-gateway/.env"
    echo "   # Add: POSTGRES_CONNECTION_STRING=postgresql://..."
    echo "   sudo systemctl restart multiverse-gateway"
    echo ""
fi

echo "🧪 Step 5: Testing deployment..."
echo "   Testing root redirect..."
curl -sI https://inference.themultiverse.school/ | grep -E "HTTP|Location" || echo "   ⚠️  Could not verify redirect"

echo "   Testing health endpoint..."
curl -sf https://inference.themultiverse.school/health > /dev/null && echo "   ✅ Health check passed" || echo "   ⚠️  Health check failed"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Changes deployed:"
echo "  - Root path (/) now redirects to /dashboard"
echo "  - Session-based authentication for admin endpoints"
echo "  - Admins logged into themultiverse.school don't need API keys"
echo ""
echo "Test URLs:"
echo "  - https://inference.themultiverse.school (should redirect to dashboard)"
echo "  - https://inference.themultiverse.school/dashboard"
echo "  - https://inference.themultiverse.school/health"
echo ""

if [ -z "$POSTGRES_CONNECTION_STRING" ]; then
    echo "⚠️  Note: Session authentication will not work until you configure POSTGRES_CONNECTION_STRING"
    echo "   See SESSION_AUTH_SETUP.md for details"
    echo ""
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo "Done!"


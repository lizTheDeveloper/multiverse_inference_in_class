#!/usr/bin/env python3
"""
Deploy updates to GCE instance
"""
import subprocess
import sys
import os

PROJECT = "multiverseschool"
ZONE = "us-west1-b"
INSTANCE = "multiverse-gateway"

def run_command(cmd, check=True):
    """Run a command and return output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        print(f"Command failed with code {result.returncode}")
        sys.exit(1)
    return result

def main():
    print("=" * 60)
    print("Deploying to GCE")
    print("=" * 60)
    print()
    
    # Step 1: Copy files to instance
    print("📦 Step 1: Copying files to instance...")
    files_to_copy = [
        "app/main.py",
        "app/utils/auth.py",
        "app/utils/session_auth.py",
        "app/routers/admin.py",
        "requirements.txt"
    ]
    
    for file in files_to_copy:
        cmd = f"gcloud compute scp {file} {INSTANCE}:/tmp/{os.path.basename(file)} --project={PROJECT} --zone={ZONE}"
        run_command(cmd)
    
    print("   ✅ Files copied")
    print()
    
    # Step 2: Deploy on instance
    print("🚀 Step 2: Deploying on instance...")
    
    deploy_script = """
set -e
cd /opt/multiverse-gateway

echo "Backing up..."
sudo cp -a . ../gateway-backup-$(date +%Y%m%d-%H%M%S)

echo "Stopping service..."
sudo systemctl stop multiverse-gateway

echo "Installing files..."
sudo -u gateway cp /tmp/main.py app/
sudo -u gateway cp /tmp/auth.py app/utils/
sudo -u gateway cp /tmp/session_auth.py app/utils/
sudo -u gateway cp /tmp/admin.py app/routers/
sudo -u gateway cp /tmp/requirements.txt .

echo "Installing dependencies..."
sudo -u gateway env/bin/pip install -q google-cloud-firestore==2.14.0 psycopg2-binary==2.9.9

echo "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    sudo apt update && sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    echo "Creating database..."
    sudo -u postgres psql -c "CREATE USER gateway_user WITH PASSWORD 'gateway_pass_2024';" || true
    sudo -u postgres psql -c "CREATE DATABASE multiverse_gateway OWNER gateway_user;" || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE multiverse_gateway TO gateway_user;" || true
fi

echo "Updating .env..."
if ! grep -q "POSTGRES_CONNECTION_STRING" .env; then
    echo '' >> .env
    echo 'POSTGRES_CONNECTION_STRING="postgresql://gateway_user:gateway_pass_2024@localhost:5432/multiverse_gateway"' >> .env
fi

echo "Starting service..."
sudo systemctl start multiverse-gateway

sleep 5

echo "Checking status..."
sudo systemctl status multiverse-gateway --no-pager | head -10

echo ""
echo "✅ Deployment complete!"
"""
    
    cmd = f"gcloud compute ssh {INSTANCE} --project={PROJECT} --zone={ZONE} --command='bash -c \"{deploy_script}\"'"
    run_command(cmd, check=False)
    
    print()
    print("=" * 60)
    print("✅ Deployment finished!")
    print("=" * 60)
    print()
    print("Test the deployment:")
    print("  - https://inference.themultiverse.school/")
    print("  - https://inference.themultiverse.school/dashboard")
    print()

if __name__ == "__main__":
    main()


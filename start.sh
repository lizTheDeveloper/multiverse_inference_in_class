#!/bin/bash
# Startup script for Multiverse Inference Gateway

set -e  # Exit on error

echo "========================================="
echo "Multiverse Inference Gateway - Starting"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "env" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: python3.11 -m venv env"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found!"
    echo "Using .env.example as template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env file. Please edit it with your configuration."
        echo ""
        echo "IMPORTANT: Set ADMIN_API_KEY in .env before continuing!"
        exit 1
    else
        echo "Error: .env.example not found either!"
        exit 1
    fi
fi

# Load environment variables
echo "Loading environment variables..."
set -a
source .env
set +a

# Check if ADMIN_API_KEY is set
if [ -z "$ADMIN_API_KEY" ] || [ "$ADMIN_API_KEY" = "your-super-secret-admin-key-change-this-in-production" ]; then
    echo "Error: ADMIN_API_KEY not properly set in .env file!"
    echo "Please set a secure API key (at least 16 characters)"
    exit 1
fi

# Check if Python dependencies are installed
echo "Checking dependencies..."
python -c "import fastapi" 2>/dev/null || {
    echo "Dependencies not found. Installing..."
    pip install -r requirements.txt
}

# Set default values if not set
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
RELOAD=${RELOAD:-false}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo ""
echo "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Log Level: $LOG_LEVEL"
echo "  Reload: $RELOAD"
echo ""

# Start the server
echo "Starting gateway..."
echo "----------------------------------------"

if [ "$RELOAD" = "true" ]; then
    echo "Running in development mode with auto-reload..."
    python -m uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level "$(echo $LOG_LEVEL | tr '[:upper:]' '[:lower:]')"
else
    echo "Running in production mode..."
    python -m uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --log-level "$(echo $LOG_LEVEL | tr '[:upper:]' '[:lower:]')"
fi

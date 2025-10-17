#!/bin/bash
# Shutdown script for Multiverse Inference Gateway

echo "=========================================="
echo "Multiverse Inference Gateway - Stopping"
echo "=========================================="
echo ""

# Get PORT from .env if it exists
if [ -f ".env" ]; then
    source .env
fi

PORT=${PORT:-8000}

echo "Looking for gateway process on port $PORT..."

# Find process ID
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ -z "$PID" ]; then
    echo "No process found running on port $PORT"
    exit 0
fi

echo "Found process $PID running on port $PORT"
echo "Sending shutdown signal..."

# Send SIGTERM for graceful shutdown
kill -TERM $PID

# Wait for up to 10 seconds for graceful shutdown
echo "Waiting for graceful shutdown..."
for i in {1..10}; do
    if ! kill -0 $PID 2>/dev/null; then
        echo "Gateway stopped successfully!"
        exit 0
    fi
    echo "  Waiting... ($i/10)"
    sleep 1
done

# If still running, force kill
if kill -0 $PID 2>/dev/null; then
    echo "Graceful shutdown timeout. Forcing shutdown..."
    kill -9 $PID
    echo "Gateway force-stopped."
else
    echo "Gateway stopped successfully!"
fi

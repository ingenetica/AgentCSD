#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Build frontend if dist/ is missing
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend..."
    (cd frontend && npm install && npm run build)
fi

echo "Starting AgentCSD on http://localhost:8000"
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

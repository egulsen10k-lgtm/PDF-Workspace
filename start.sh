#!/usr/bin/env bash
set -e

echo "================================================================"
echo "  ILovePDF Personal Local Replacement Launcher"
echo "================================================================"

# Copy .env.example to .env if not exists
if [ ! -f .env ]; then
    echo "[1/4] Creating .env from .env.example..."
    cp .env.example .env
fi

# Function to kill processes on ports 8000 and 3000
cleanup_ports() {
    echo "Clearing any lingering processes on ports 8000 & 3000..."
    if command -v lsof &> /dev/null; then
        PID_8000=$(lsof -t -i:8000 2>/dev/null || true)
        if [ -n "$PID_8000" ]; then
            kill -9 $PID_8000 2>/dev/null || true
        fi
        PID_3000=$(lsof -t -i:3000 2>/dev/null || true)
        if [ -n "$PID_3000" ]; then
            kill -9 $PID_3000 2>/dev/null || true
        fi
    fi
}

cleanup_ports

# Check if Docker is running and available
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "Docker daemon detected. Launching full stack via Docker Compose..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up --build
    else
        docker compose up --build
    fi
else
    echo "Launching local services (FastAPI Backend + Next.js Frontend)..."
    mkdir -p data/storage

    # Python virtualenv setup
    if [ ! -d "venv" ]; then
        echo "[2/4] Setting up Python virtual environment..."
        python3 -m venv venv
        ./venv/bin/pip install --upgrade pip
        ./venv/bin/pip install -r backend/requirements.txt
    fi

    # Frontend setup
    if [ ! -d "frontend/node_modules" ]; then
        echo "[3/4] Installing frontend dependencies..."
        (cd frontend && npm install)
    fi

    if [ ! -d "frontend/.next" ]; then
        echo "[3/4] Building Next.js frontend..."
        (cd frontend && npm run build)
    fi

    echo "[4/4] Starting servers..."

    # Trap to kill background jobs when user presses Ctrl+C
    cleanup_servers() {
        echo ""
        echo "Shutting down servers..."
        if [ -n "$BACKEND_PID" ]; then kill -TERM "$BACKEND_PID" 2>/dev/null || true; fi
        if [ -n "$FRONTEND_PID" ]; then kill -TERM "$FRONTEND_PID" 2>/dev/null || true; fi
        cleanup_ports
        exit 0
    }
    trap cleanup_servers INT TERM EXIT

    # Start FastAPI Backend
    PYTHONPATH=backend ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    # Start Next.js Frontend
    (cd frontend && npm run start) &
    FRONTEND_PID=$!

    # Wait for servers to spin up
    sleep 2

    echo ""
    echo "================================================================"
    echo "  🚀 All Services Running Locally!"
    echo "================================================================"
    echo "  • Web GUI:         http://localhost:3000"
    echo "  • Master Password: admin123  (configurable in .env)"
    echo "  • Backend API:     http://localhost:8000"
    echo "  • API Swagger:     http://localhost:8000/docs"
    echo "================================================================"
    echo "  Press Ctrl+C to stop all servers."
    echo ""

    wait $BACKEND_PID $FRONTEND_PID
fi

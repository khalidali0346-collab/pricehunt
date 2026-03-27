#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== PriceHunt Startup ==="

# Backend
echo "[1/2] Starting backend..."
cd "$ROOT/backend"

if [ ! -d ".venv" ]; then
  echo "  Creating Python virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "  Installing backend dependencies..."
pip install -q -r requirements.txt

echo "  Backend running on http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Frontend
echo "[2/2] Starting frontend..."
cd "$ROOT/frontend"

if [ ! -d "node_modules" ]; then
  echo "  Installing frontend dependencies..."
  npm install --silent
fi

echo "  Frontend running on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  PriceHunt is running!"
echo "  Frontend: http://localhost:5173"
echo "  API:      http://localhost:8000/api"
echo "  API docs: http://localhost:8000/docs"
echo "=========================================="
echo "  Press Ctrl+C to stop"
echo ""

# Wait and clean up on exit
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

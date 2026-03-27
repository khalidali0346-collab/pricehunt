#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "=== PriceHunt Install ==="

# Backend
echo "[1/2] Setting up Python backend..."
cd "$ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "  Backend ready."

# Frontend
echo "[2/2] Setting up React frontend..."
cd "$ROOT/frontend"
npm install
echo "  Frontend ready."

echo ""
echo "Installation complete! Run ./start.sh to launch PriceHunt."

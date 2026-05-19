#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== Starting LiveHappy locally (no Docker) ==="

# 1. Install Python deps if needed
if [ ! -d "backend/.venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv backend/.venv
  source backend/.venv/bin/activate
  pip install -e backend/
else
  source backend/.venv/bin/activate
fi

# 2. Run database migrations
echo "Running migrations..."
cd backend && PYTHONPATH=. alembic upgrade head && cd ..

# 3. Start backend (port 8001, serves frontend static files)
echo "Starting backend on :8001..."
cd backend && PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
cd ..

echo ""
echo "✅ LiveHappy: http://localhost:8001"
echo "   (API 文档: http://localhost:8001/docs)"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait

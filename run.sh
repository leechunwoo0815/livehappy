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
PYTHONPATH=backend alembic upgrade head

# 3. Start backend (port 8001)
echo "Starting backend on :8001..."
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

# 4. Start frontend (port 3001)
echo "Starting frontend on :3001..."
python3 -m http.server 3001 -d frontend/ &
FRONTEND_PID=$!

echo ""
echo "✅ Backend:  http://localhost:8001"
echo "✅ Frontend: http://localhost:3001"
echo "   (Swagger: http://localhost:8001/docs)"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait

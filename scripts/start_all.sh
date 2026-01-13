#!/bin/bash

# Start all services in separate terminal windows/tabs
# Usage: ./scripts/start_all.sh

set -e

echo "🚀 Starting Structural Health Monitoring System..."
echo ""

# Check dependencies
command -v python3 &> /dev/null || { echo "❌ Python3 required"; exit 1; }
command -v npm &> /dev/null || { echo "❌ npm required"; exit 1; }

echo "✓ Python3 installed"
echo "✓ npm installed"
echo ""

# Determine OS
OS="$(uname -s)"

# Terminal 1: Backend
echo "📡 Starting backend on port 8000..."
if [ "$OS" == "Darwin" ]; then
  # macOS
  open -a Terminal --args bash -c "cd backend && python3 app.py; exec bash" &
elif [ "$OS" == "Linux" ]; then
  # Linux (GNOME Terminal)
  gnome-terminal -- bash -c "cd backend && python3 app.py; exec bash" &
else
  # Windows or other
  python3 backend/app.py &
fi
BACKEND_PID=$!

sleep 3

# Terminal 2: Frontend
echo "🎨 Starting frontend on port 5173..."
if [ "$OS" == "Darwin" ]; then
  open -a Terminal --args bash -c "cd frontend && npm run dev; exec bash" &
elif [ "$OS" == "Linux" ]; then
  gnome-terminal -- bash -c "cd frontend && npm run dev; exec bash" &
else
  cd frontend && npm run dev &
fi
FRONTEND_PID=$!

sleep 5

# Terminal 3: Data collection (simulated)
echo "📊 Starting data collection (simulated)..."
if [ "$OS" == "Darwin" ]; then
  open -a Terminal --args bash -c "python3 tools/data_collect.py --stream ws://127.0.0.1:8000/ws/ingest --simulate; exec bash" &
elif [ "$OS" == "Linux" ]; then
  gnome-terminal -- bash -c "python3 tools/data_collect.py --stream ws://127.0.0.1:8000/ws/ingest --simulate; exec bash" &
else
  python3 tools/data_collect.py --stream ws://127.0.0.1:8000/ws/ingest --simulate &
fi
COLLECT_PID=$!

# Save PIDs for cleanup
mkdir -p /tmp
echo "$BACKEND_PID $FRONTEND_PID $COLLECT_PID" > /tmp/monitoring_pids.txt

echo ""
echo "✅ All services started!"
echo ""
echo "  📡 Backend: PID $BACKEND_PID (port 8000)"
echo "  🎨 Frontend: PID $FRONTEND_PID (port 5173)"
echo "  📊 Data Collection: PID $COLLECT_PID"
echo ""
echo "🌐 Dashboard: http://localhost:5173/live-monitoring"
echo ""
echo "⏹️  To stop all services:"
echo "   bash scripts/stop_all.sh"
echo ""

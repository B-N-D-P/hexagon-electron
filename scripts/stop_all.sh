#!/bin/bash

# Stop all monitoring services
# Usage: ./scripts/stop_all.sh

echo "⏹️  Stopping all services..."
echo ""

# Try to read PIDs from file
if [ -f /tmp/monitoring_pids.txt ]; then
  read BACKEND_PID FRONTEND_PID COLLECT_PID < /tmp/monitoring_pids.txt
  
  echo "Killing Backend (PID $BACKEND_PID)..."
  kill $BACKEND_PID 2>/dev/null || echo "  (already stopped)"
  
  echo "Killing Frontend (PID $FRONTEND_PID)..."
  kill $FRONTEND_PID 2>/dev/null || echo "  (already stopped)"
  
  echo "Killing Data Collection (PID $COLLECT_PID)..."
  kill $COLLECT_PID 2>/dev/null || echo "  (already stopped)"
  
  rm -f /tmp/monitoring_pids.txt
fi

# Also try to kill by process name
echo ""
echo "Killing any remaining processes..."
pkill -f "python3 app.py" 2>/dev/null || echo "  (no backend found)"
pkill -f "npm run dev" 2>/dev/null || echo "  (no frontend found)"
pkill -f "data_collect.py" 2>/dev/null || echo "  (no data collection found)"

sleep 1

echo ""
echo "✅ All services stopped"

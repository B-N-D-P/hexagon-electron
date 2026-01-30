#!/bin/bash

echo "================================================================================"
echo "🏗️  STRUCTURAL HEALTH MONITORING SYSTEM"
echo "================================================================================"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🧹 Cleaning up old processes..."
pkill -f "uvicorn app:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1
echo ""

echo "🚀 Starting Backend (FastAPI)..."
cd backend
source venv/bin/activate
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 3
echo "✓ Backend started (PID: $BACKEND_PID)"
echo ""

echo "🎨 Starting Frontend (React + Vite)..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3
echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo ""

echo "================================================================================"
echo "✅ SYSTEM STARTED SUCCESSFULLY!"
echo "================================================================================"
echo ""
echo "📍 Access Points:"
echo "   • Backend API:          http://localhost:8000"
echo "   • API Documentation:    http://localhost:8000/docs"
echo "   • Health Monitoring:    http://localhost:8000/health_monitoring.html"
echo "   • React Frontend:       http://localhost:5173"
echo ""
echo "📊 Process IDs:"
echo "   • Backend PID:  $BACKEND_PID"
echo "   • Frontend PID: $FRONTEND_PID"
echo ""
echo "📋 Logs:"
echo "   • Backend:  logs/backend.log"
echo "   • Frontend: logs/frontend.log"
echo ""
echo "🛑 To stop all services, run:"
echo "   ./stop_all.sh"
echo "   or: pkill -f uvicorn && pkill -f vite"
echo ""
echo "================================================================================"
echo "🎉 Ready for use! Open http://localhost:5173"
echo "================================================================================"
echo ""

#!/bin/bash

echo "🛑 Stopping Structural Health Monitoring System..."

# Kill backend
lsof -ti:8000 | xargs kill -9 2>/dev/null
echo "✓ Backend stopped (port 8000)"

# Kill frontend
lsof -ti:5173 | xargs kill -9 2>/dev/null
echo "✓ Frontend stopped (port 5173)"

echo ""
echo "✅ All services stopped successfully!"

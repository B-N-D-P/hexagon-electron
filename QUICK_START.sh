#!/bin/bash

# ============================================================================
# ULTIMATE REAL-TIME VIBRATION MONITORING SYSTEM - QUICK START
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🚀 REAL-TIME VIBRATION MONITORING SYSTEM - QUICK START      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Function to print sections
print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Check Python
print_section "Checking Python Installation"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Check Node
print_section "Checking Node.js Installation"
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi
NODE_VERSION=$(node -v)
echo "✅ Node.js $NODE_VERSION found"

# Setup Backend
print_section "Setting Up Backend"
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "🔌 Activating virtual environment..."
source venv/bin/activate

echo "📥 Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✅ Backend dependencies installed"

# Setup Frontend
print_section "Setting Up Frontend"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "📥 Installing Node dependencies..."
    npm install -q
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Node dependencies already installed"
fi

# Create startup script
print_section "Creating Startup Scripts"

cat > "$SCRIPT_DIR/start_backend.sh" << 'BASHEOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
echo "🚀 Starting Backend Server..."
echo "   WebSocket: ws://localhost:8000/ws/monitor"
echo "   API: http://localhost:8000"
python realtime_monitor.py
BASHEOF

cat > "$SCRIPT_DIR/start_frontend.sh" << 'BASHEOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
echo "🚀 Starting Frontend Server..."
echo "   Dashboard: http://localhost:5173"
echo "   Route: http://localhost:5173/realtime"
npm run dev
BASHEOF

chmod +x "$SCRIPT_DIR/start_backend.sh"
chmod +x "$SCRIPT_DIR/start_frontend.sh"

echo "✅ Startup scripts created"

# Summary
print_section "🎉 Setup Complete!"

echo ""
echo "Your system is ready! Follow these steps to start:"
echo ""
echo "STEP 1: Start Backend (Terminal 1)"
echo "────────────────────────────────────"
echo "./start_backend.sh"
echo ""
echo "STEP 2: Start Frontend (Terminal 2)"
echo "──────────────────────────────────────"
echo "./start_frontend.sh"
echo ""
echo "STEP 3: Open Dashboard"
echo "─────────────────────────"
echo "Browser: http://localhost:5173/realtime"
echo ""
echo "✨ System is ready for demonstration!"
echo ""

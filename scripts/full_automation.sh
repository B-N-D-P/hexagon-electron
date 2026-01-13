#!/bin/bash

# Complete 10-day ML training and deployment automation
# Usage: ./scripts/full_automation.sh [duration] [test_mode]
# Examples:
#   ./scripts/full_automation.sh          # Full 3-day baseline
#   ./scripts/full_automation.sh 1h       # 1 hour test mode

set -e

DURATION=${1:-3d}
BASELINE_DIR="data/baseline"
OUTPUT_DIR="outputs"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🚀 FULL AUTOMATION: 10-Day ML Training & Deployment      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

echo "📋 Phase 0: Pre-flight Checks"
echo "==========================================="

command -v python3 &> /dev/null || { echo "❌ Python3 required"; exit 1; }
command -v npm &> /dev/null || { echo "❌ npm required"; exit 1; }

echo "✓ Python3 $(python3 --version | cut -d' ' -f2)"
echo "✓ npm $(npm --version)"
echo ""

# ============================================================================
# PHASE 1: DEPENDENCIES
# ============================================================================

echo "📦 Phase 1: Installing Dependencies"
echo "==========================================="

cd backend
echo "  Backend..."
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
pip install -q scikit-learn joblib pywavelets tensorflow pandas 2>/dev/null
cd ..

cd frontend
echo "  Frontend..."
npm install > /dev/null 2>&1
cd ..

echo "✓ Dependencies installed"
echo ""

# ============================================================================
# PHASE 2: START SERVICES
# ============================================================================

echo "🔧 Phase 2: Starting Backend & Frontend"
echo "==========================================="

echo "  Starting backend (port 8000)..."
cd backend
python3 app.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "  Starting frontend (port 5173)..."
cd frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for services
echo "  Waiting for services to start..."
for i in {1..30}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend ready"
    break
  fi
  sleep 1
done

echo "✓ Services started"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""

# ============================================================================
# PHASE 3: COLLECT BASELINE
# ============================================================================

echo "📊 Phase 3: Collecting Baseline (Days 1-3)"
echo "==========================================="
echo "  Duration: $DURATION"
echo "  Output: $BASELINE_DIR"
echo ""

python3 tools/baseline_collector.py \
  --duration "$DURATION" \
  --output-dir "$BASELINE_DIR" \
  --structure-name "Iron Structure (3-Story)" \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --token dev-token \
  --simulate

CSV_COUNT=$(ls "$BASELINE_DIR"/*.csv 2>/dev/null | wc -l)
echo "✓ Baseline collection complete ($CSV_COUNT CSV files)"
echo ""

# ============================================================================
# PHASE 4: TRAIN MODELS
# ============================================================================

echo "🤖 Phase 4: Training ML Models (Days 3-5)"
echo "==========================================="

python3 tools/train_ml_models.py \
  --baseline-dir "$BASELINE_DIR" \
  --contamination 0.1 \
  --structure-name "Iron Structure (3-Story)" \
  --verify

echo "✓ Model training complete"
echo ""

# ============================================================================
# PHASE 5: DEPLOYMENT
# ============================================================================

echo "🚀 Phase 5: Deployment & Validation (Days 5-10)"
echo "==========================================="

echo "  Restarting backend to load new models..."
kill $BACKEND_PID 2>/dev/null
sleep 2

cd backend
python3 app.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend
for i in {1..30}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend restarted with ML models"
    break
  fi
  sleep 1
done

echo "  Running integration tests..."
python3 tools/test_streaming.py > /dev/null 2>&1

echo "✓ All tests passed"
echo ""

# ============================================================================
# COMPLETION
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ AUTOMATION COMPLETE!                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🌐 Dashboard: http://localhost:5173/live-monitoring"
echo ""
echo "📁 Files created:"
echo "   Baseline data: $BASELINE_DIR/ ($(du -sh "$BASELINE_DIR" | cut -f1))"
echo "   Trained models: backend/ml_models/trained/v*/"
echo ""
echo "📖 Next steps:"
echo "   1. Open dashboard: http://localhost:5173/live-monitoring"
echo "   2. Click 'Start Streaming'"
echo "   3. Watch ML anomaly scores update in real-time"
echo ""
echo "⏹️  To stop services:"
echo "   bash scripts/stop_all.sh"
echo ""

# Save PIDs
mkdir -p /tmp
echo "$BACKEND_PID $FRONTEND_PID" > /tmp/monitoring_pids.txt

echo "✨ Your structural health monitoring system is ready! ✨"

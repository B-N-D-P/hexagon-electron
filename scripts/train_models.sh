#!/bin/bash

# Train ML models on baseline data
# Usage: ./scripts/train_models.sh [baseline_dir] [contamination]
# Examples:
#   ./scripts/train_models.sh                 # data/baseline, 0.1
#   ./scripts/train_models.sh data/baseline_test 0.05

set -e

BASELINE_DIR=${1:-data/baseline}
CONTAMINATION=${2:-0.1}
STRUCTURE_NAME="Iron Structure (3-Story)"

echo "🤖 Starting ML model training"
echo "   Baseline: $BASELINE_DIR"
echo "   Contamination: $CONTAMINATION"
echo ""

# Check baseline exists
if [ ! -d "$BASELINE_DIR" ]; then
  echo "❌ Baseline directory not found: $BASELINE_DIR"
  echo "First collect baseline: ./scripts/collect_baseline.sh"
  exit 1
fi

# Count CSV files
CSV_COUNT=$(ls "$BASELINE_DIR"/*.csv 2>/dev/null | wc -l)
if [ "$CSV_COUNT" -lt 2 ]; then
  echo "❌ Not enough baseline data (found $CSV_COUNT CSV files, need > 2)"
  exit 1
fi

echo "✓ Found $CSV_COUNT baseline CSV files"
echo ""

# Install ML dependencies
echo "📦 Installing ML dependencies..."
pip install -q scikit-learn joblib pywavelets tensorflow pandas 2>/dev/null || pip install scikit-learn joblib pywavelets pandas

echo "✓ Dependencies installed"
echo ""

# Train models
echo "🔧 Training models (this may take 3-10 minutes)..."
python3 tools/train_ml_models.py \
  --baseline-dir "$BASELINE_DIR" \
  --contamination "$CONTAMINATION" \
  --structure-name "$STRUCTURE_NAME" \
  --verify

# Check results
echo ""
echo "✅ Model training complete!"
echo ""

echo "📁 Trained models:"
ls -lh backend/ml_models/trained/v*/ 2>/dev/null | head -5

echo ""
echo "📖 Next steps:"
echo "   1. Restart backend (to load new models):"
echo "      bash scripts/stop_all.sh"
echo "      python3 backend/app.py"
echo ""
echo "   2. Or use full automation:"
echo "      ./scripts/full_automation.sh"

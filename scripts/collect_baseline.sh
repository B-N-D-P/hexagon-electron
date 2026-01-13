#!/bin/bash

# Automated baseline collection
# Usage: ./scripts/collect_baseline.sh [duration] [output_dir]
# Examples:
#   ./scripts/collect_baseline.sh              # 3 days, data/baseline
#   ./scripts/collect_baseline.sh 1h           # 1 hour, data/baseline
#   ./scripts/collect_baseline.sh 3d data/my_baseline  # 3 days, custom dir

set -e

DURATION=${1:-3d}
OUTPUT_DIR=${2:-data/baseline}
STRUCTURE_NAME="Iron Structure (3-Story)"

echo "🔍 Starting baseline collection"
echo "   Duration: $DURATION"
echo "   Output: $OUTPUT_DIR"
echo "   Structure: $STRUCTURE_NAME"
echo ""

# Check prerequisites
if ! pgrep -f "python3 backend/app.py" > /dev/null; then
  echo "❌ Backend not running!"
  echo "Start with: python3 backend/app.py"
  exit 1
fi

echo "✓ Backend is running"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Start baseline collection
python3 tools/baseline_collector.py \
  --duration "$DURATION" \
  --output-dir "$OUTPUT_DIR" \
  --structure-name "$STRUCTURE_NAME" \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --token dev-token \
  --simulate

# Show results
echo ""
echo "✅ Baseline collection complete!"
echo ""

CSV_COUNT=$(ls "$OUTPUT_DIR"/*.csv 2>/dev/null | wc -l)
echo "📊 Statistics:"
echo "   CSV files: $CSV_COUNT"
echo "   Directory: $OUTPUT_DIR"
du -sh "$OUTPUT_DIR"

echo ""
echo "📖 Next step: Train ML models"
echo "   ./scripts/train_models.sh $OUTPUT_DIR"

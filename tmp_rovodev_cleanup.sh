#!/bin/bash
# Cleanup temporary files created during development

echo "🧹 Cleaning up temporary files..."
echo ""

# Remove temporary scripts and files
rm -f tmp_rovodev_*.py tmp_rovodev_*.sh tmp_rovodev_*.txt 2>/dev/null
rm -rf tmp_rovodev_*/ 2>/dev/null

# Remove training temporary data
rm -rf /tmp/ml_training_data* 2>/dev/null

# Remove build logs (keep the main one)
rm -f training_log.txt 2>/dev/null

echo "✓ Temporary files cleaned up!"
echo ""
echo "Kept important files:"
echo "  • build.log"
echo "  • WINDOWS_DEPLOYMENT_GUIDE.md"
echo "  • FILE_PERSISTENCE_FIX.md"

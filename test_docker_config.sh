#!/bin/bash
# Quick validation script for Docker configuration

echo "🧪 Validating Docker Configuration"
echo "=================================="
echo ""

# Check files exist
echo "✓ Checking files..."
for file in docker-compose.yml Dockerfile.backend Dockerfile.frontend .dockerignore docker-start.sh docker-stop.sh; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
    fi
done

echo ""
echo "✓ Configuration validation complete!"
echo ""
echo "Next steps:"
echo "  1. Run: ./docker-start.sh"
echo "  2. Access: http://localhost:3000"
echo ""

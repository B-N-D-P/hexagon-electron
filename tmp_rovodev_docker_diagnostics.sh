#!/bin/bash
# Comprehensive Docker System Diagnostics and Health Check

echo "============================================================================"
echo "🔍 DOCKER SYSTEM DIAGNOSTICS - Structural Health Monitoring"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
ISSUES=0
WARNINGS=0

echo "📊 1. CONTAINER STATUS"
echo "============================================================================"
sudo docker compose ps
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to get container status${NC}"
    ((ISSUES++))
else
    echo -e "${GREEN}✓ Container status retrieved${NC}"
fi
echo ""

echo "📦 2. IMAGE INFORMATION"
echo "============================================================================"
sudo docker compose images
echo ""

echo "🔌 3. NETWORK CONNECTIVITY"
echo "============================================================================"
echo "Testing backend health endpoint..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1)
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ Backend health check: OK (HTTP 200)${NC}"
    curl -s http://localhost:8000/health | jq '.' 2>/dev/null || curl -s http://localhost:8000/health
else
    echo -e "${RED}❌ Backend health check failed: HTTP $BACKEND_HEALTH${NC}"
    ((ISSUES++))
fi
echo ""

echo "Testing frontend accessibility..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>&1)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Frontend accessible: OK (HTTP 200)${NC}"
else
    echo -e "${RED}❌ Frontend not accessible: HTTP $FRONTEND_STATUS${NC}"
    ((ISSUES++))
fi
echo ""

echo "💾 4. VOLUME MOUNTS"
echo "============================================================================"
echo "Checking backend volumes..."
sudo docker compose exec backend ls -la /app/uploads /app/outputs /app/ml_models 2>&1 | head -20
echo ""

echo "Checking ML456 mount..."
sudo docker compose exec backend ls -la /home/itachi/ml456_advanced 2>&1 | head -10
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ML456 directory mounted${NC}"
else
    echo -e "${RED}❌ ML456 directory NOT mounted${NC}"
    ((ISSUES++))
fi
echo ""

echo "Checking trained models..."
sudo docker compose exec backend ls -lh /home/itachi/ml456_advanced/checkpoints/advanced/*.pkl 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Trained models accessible${NC}"
else
    echo -e "${YELLOW}⚠ Trained models not found${NC}"
    ((WARNINGS++))
fi
echo ""

echo "📝 5. BACKEND LOGS (Last 30 lines)"
echo "============================================================================"
sudo docker compose logs backend --tail=30
echo ""

echo "🔍 6. ERROR DETECTION"
echo "============================================================================"
echo "Checking for errors in backend logs..."
ERROR_COUNT=$(sudo docker compose logs backend --tail=100 | grep -i "error\|exception\|traceback\|failed" | wc -l)
if [ $ERROR_COUNT -gt 0 ]; then
    echo -e "${RED}❌ Found $ERROR_COUNT error entries${NC}"
    echo "Recent errors:"
    sudo docker compose logs backend --tail=100 | grep -i "error\|exception\|traceback" | tail -10
    ((ISSUES++))
else
    echo -e "${GREEN}✓ No errors detected in recent logs${NC}"
fi
echo ""

echo "🔍 7. FRONTEND LOGS (Last 20 lines)"
echo "============================================================================"
sudo docker compose logs frontend --tail=20
echo ""

echo "🧪 8. API ENDPOINT TESTS"
echo "============================================================================"

# Test file upload endpoint
echo "Testing upload endpoint..."
UPLOAD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/upload 2>&1)
if [ "$UPLOAD_STATUS" = "405" ] || [ "$UPLOAD_STATUS" = "422" ]; then
    echo -e "${GREEN}✓ Upload endpoint responding (expected 405/422 without POST data)${NC}"
else
    echo -e "${YELLOW}⚠ Upload endpoint returned: HTTP $UPLOAD_STATUS${NC}"
    ((WARNINGS++))
fi

# Test ML456 availability
echo "Testing ML456 availability endpoint..."
ML456_STATUS=$(curl -s http://localhost:8000/api/ml456/status 2>&1)
echo "ML456 Status: $ML456_STATUS"
echo ""

echo "🔧 9. METADATA PERSISTENCE CHECK"
echo "============================================================================"
sudo docker compose exec backend ls -la /app/uploads/uploaded_files_metadata.json 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Metadata file exists${NC}"
    echo "Contents:"
    sudo docker compose exec backend cat /app/uploads/uploaded_files_metadata.json 2>&1 | head -20
else
    echo -e "${YELLOW}⚠ No metadata file yet (will be created on first upload)${NC}"
    ((WARNINGS++))
fi
echo ""

echo "🐍 10. PYTHON ENVIRONMENT CHECK"
echo "============================================================================"
echo "Checking Python version and key packages..."
sudo docker compose exec backend python --version
echo ""
echo "Checking TensorFlow..."
sudo docker compose exec backend python -c "import tensorflow as tf; print(f'TensorFlow: {tf.__version__}')" 2>&1
echo ""
echo "Checking PyTorch..."
sudo docker compose exec backend python -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>&1
echo ""
echo "Checking scikit-learn..."
sudo docker compose exec backend python -c "import sklearn; print(f'scikit-learn: {sklearn.__version__}')" 2>&1
echo ""

echo "============================================================================"
echo "📊 DIAGNOSTIC SUMMARY"
echo "============================================================================"
echo -e "${RED}Critical Issues: $ISSUES${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 All systems operational!${NC}"
    echo ""
    echo "✅ Backend: http://localhost:8000"
    echo "✅ Frontend: http://localhost:3000"
    echo "✅ API Docs: http://localhost:8000/docs"
elif [ $ISSUES -eq 0 ]; then
    echo -e "${YELLOW}⚠ System operational with minor warnings${NC}"
else
    echo -e "${RED}❌ Critical issues detected - review errors above${NC}"
fi

echo ""
echo "============================================================================"
echo "💡 RECOMMENDATIONS"
echo "============================================================================"

if [ $ISSUES -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo "Run this to see live logs:"
    echo "  sudo docker compose logs -f"
    echo ""
    echo "Restart containers if needed:"
    echo "  sudo docker compose restart"
    echo ""
    echo "Full rebuild if major issues:"
    echo "  sudo docker compose down"
    echo "  sudo docker compose build --no-cache"
    echo "  sudo docker compose up -d"
fi

echo ""
echo "Diagnostic complete! Review output above for details."

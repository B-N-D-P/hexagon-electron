#!/bin/bash
# HEXAGON Setup Verification Script

echo "========================================"
echo "HEXAGON Setup Verification"
echo "========================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ERRORS=0

# Check Python
echo -n "Checking Python... "
if command -v python &> /dev/null; then
    PY_VERSION=$(python --version 2>&1)
    echo -e "${GREEN}✓ $PY_VERSION${NC}"
else
    echo -e "${RED}✗ Python not found${NC}"
    ((ERRORS++))
fi

# Check Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js not found${NC}"
    ((ERRORS++))
fi

# Check npm
echo -n "Checking npm... "
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm $NPM_VERSION${NC}"
else
    echo -e "${RED}✗ npm not found${NC}"
    ((ERRORS++))
fi

# Check backend directory
echo -n "Checking backend directory... "
if [ -d "$SCRIPT_DIR/../backend" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    ((ERRORS++))
fi

# Check frontend directory
echo -n "Checking frontend directory... "
if [ -d "$SCRIPT_DIR/../frontend" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    ((ERRORS++))
fi

# Check ML models
echo -n "Checking ML models... "
if [ -d "$SCRIPT_DIR/../backend/ml_models" ]; then
    MODEL_COUNT=$(find "$SCRIPT_DIR/../backend/ml_models" -type f \( -name "*.pkl" -o -name "*.pth" -o -name "*.h5" \) | wc -l)
    echo -e "${GREEN}✓ Found $MODEL_COUNT model files${NC}"
else
    echo -e "${YELLOW}⚠ ML models directory not found${NC}"
fi

# Check ML456
echo -n "Checking ML456 (optional)... "
if [ -d "$HOME/ml456_advanced" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${YELLOW}⚠ Not found (will build without ML456)${NC}"
fi

# Check icons
echo -n "Checking icons... "
if [ -f "$SCRIPT_DIR/resources/icon.png" ]; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${YELLOW}⚠ Icons missing (run create-simple-icon.py)${NC}"
fi

# Check required Python packages
echo -n "Checking Python dependencies... "
MISSING_DEPS=()
for pkg in flask numpy pandas scikit-learn torch; do
    if ! python -c "import $pkg" 2>/dev/null; then
        MISSING_DEPS+=($pkg)
    fi
done

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All required packages installed${NC}"
else
    echo -e "${YELLOW}⚠ Missing: ${MISSING_DEPS[*]}${NC}"
    echo "  Install with: pip install ${MISSING_DEPS[*]}"
fi

# Check PyInstaller
echo -n "Checking PyInstaller... "
if python -c "import PyInstaller" 2>/dev/null; then
    echo -e "${GREEN}✓ Installed${NC}"
else
    echo -e "${YELLOW}⚠ Not installed (will auto-install during build)${NC}"
fi

# Summary
echo ""
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Setup verified! Ready to build.${NC}"
    echo ""
    echo "To build HEXAGON:"
    echo "  cd hexagon-electron"
    echo "  ./build.sh"
    echo ""
    echo "To test in development:"
    echo "  cd hexagon-electron"
    echo "  ./dev.sh"
else
    echo -e "${RED}✗ $ERRORS critical error(s) found${NC}"
    echo "Please fix the errors above before building."
fi
echo "========================================"

#!/bin/bash
# HEXAGON Build Script for Arch Linux

set -e

echo "========================================"
echo "HEXAGON - Complete Build Script"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"
BACKEND_DIR="$SCRIPT_DIR/../backend"

echo -e "${BLUE}[1/6] Installing Electron dependencies...${NC}"
cd "$SCRIPT_DIR"
npm install
echo -e "${GREEN}✓ Electron dependencies installed${NC}"

echo -e "\n${BLUE}[2/6] Building frontend...${NC}"
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
npm run build
echo -e "${GREEN}✓ Frontend built${NC}"

echo -e "\n${BLUE}[3/6] Copying frontend build to Electron...${NC}"
rm -rf "$SCRIPT_DIR/dist"
cp -r "$FRONTEND_DIR/dist" "$SCRIPT_DIR/dist"
echo -e "${GREEN}✓ Frontend copied${NC}"

echo -e "\n${BLUE}[4/6] Building Python backend...${NC}"
cd "$SCRIPT_DIR"

# Activate venv if exists
if [ -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}Using virtual environment...${NC}"
    source venv/bin/activate
elif [ -f "$BACKEND_DIR/venv/bin/activate" ]; then
    echo -e "${YELLOW}Using backend virtual environment...${NC}"
    source "$BACKEND_DIR/venv/bin/activate"
fi

# Check if PyInstaller is available
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}Installing PyInstaller...${NC}"
    pip install pyinstaller
fi

python build_backend.py
echo -e "${GREEN}✓ Backend built${NC}"

echo -e "\n${BLUE}[5/6] Building Electron app...${NC}"
cd "$SCRIPT_DIR"
npm run build:electron
echo -e "${GREEN}✓ Electron app built${NC}"

echo -e "\n${BLUE}[6/6] Finalizing...${NC}"
RELEASE_DIR="$SCRIPT_DIR/release"
if [ -d "$RELEASE_DIR" ]; then
    echo -e "${GREEN}✓ Build complete!${NC}"
    echo ""
    echo "========================================"
    echo "Build Output:"
    echo "========================================"
    ls -lh "$RELEASE_DIR"
    echo ""
    echo -e "${GREEN}Your HEXAGON app is ready!${NC}"
    echo -e "Location: ${YELLOW}$RELEASE_DIR${NC}"
    echo ""
    echo "To run the AppImage:"
    echo -e "  ${BLUE}cd $RELEASE_DIR${NC}"
    echo -e "  ${BLUE}chmod +x HEXAGON-*.AppImage${NC}"
    echo -e "  ${BLUE}./HEXAGON-*.AppImage${NC}"
    echo ""
else
    echo -e "${RED}✗ Build directory not found${NC}"
    exit 1
fi

echo "========================================"
echo -e "${GREEN}HEXAGON Build Complete! 🎉${NC}"
echo "========================================"

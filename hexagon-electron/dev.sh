#!/bin/bash
# HEXAGON Development Mode - Quick Start

set -e

echo "========================================"
echo "HEXAGON - Development Mode"
echo "========================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install dependencies if needed
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
    echo "Installing Electron dependencies..."
    cd "$SCRIPT_DIR"
    npm install
fi

echo ""
echo "Starting HEXAGON in development mode..."
echo "- Frontend: http://localhost:5173"
echo "- Backend: http://localhost:5000"
echo "- Electron will open automatically"
echo ""

cd "$SCRIPT_DIR"
npm run dev

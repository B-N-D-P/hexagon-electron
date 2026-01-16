#!/bin/bash
# HEXAGON Structural Health - UI Launcher Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     HEXAGON Structural Health - Real-Time Monitoring IDE       ║"
echo "║              Professional Desktop Application                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Remove old environment if it exists (for Python version compatibility)
if [ -d "ui_env" ]; then
    echo "🔄 Cleaning old environment..."
    rm -rf ui_env
fi

# Create fresh virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv ui_env

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source ui_env/bin/activate

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel 2>/dev/null

# Install requirements
echo "📥 Installing dependencies (this may take a minute)..."
pip install -r ui_requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Installation failed!"
    echo "Trying alternative installation method..."
    pip install --upgrade pip
    pip install -r ui_requirements.txt
fi

# Launch application
echo ""
echo "🚀 Launching HEXAGON UI..."
echo ""
python3 ui_main.py

# Deactivate virtual environment on exit
deactivate

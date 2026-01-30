#!/bin/bash
# Fix GitHub repo structure and push

cd /mnt/storage/structural-repair-web

echo "Step 1: Remove nested git repo in hexagon-electron..."
rm -rf hexagon-electron/.git

echo "Step 2: Add SSH key to agent..."
ssh-add ~/.ssh/id_ed25519

echo "Step 3: Reset and recommit everything..."
git reset --soft HEAD~1

echo "Step 4: Add all source files..."
git add .github/ .gitignore
git add backend/*.py backend/*.html backend/requirements.txt backend/config.py backend/ml_models/*.py backend/backend_models/ backend/services/*.py
git add frontend/src/ frontend/vite.config.js frontend/index.html frontend/.env.electron frontend/package.json
git add hexagon-electron/*.py hexagon-electron/*.sh hexagon-electron/*.js hexagon-electron/*.json hexagon-electron/*.md hexagon-electron/electron/ hexagon-electron/resources/

echo "Step 5: Commit..."
git commit -m "Complete monorepo with backend, frontend, and electron app

Features:
- Backend: Python FastAPI + ML models
- Frontend: React + Vite
- Electron: Desktop app wrapper
- GitHub Actions: Auto-build for Windows/Linux/macOS"

echo "Step 6: Force push..."
git push -f origin main

echo "Step 7: Create release tag..."
git tag -fa v1.0.0 -m "Version 1.0.0 - First complete release"
git push -f origin v1.0.0

echo "✅ Done! Check: https://github.com/B-N-D-P/hexagon-electron/actions"

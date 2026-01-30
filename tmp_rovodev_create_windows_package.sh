#!/bin/bash
# Create deployment package for Windows

PACKAGE_DIR="structural-repair-windows-deployment"
mkdir -p "$PACKAGE_DIR"

echo "============================================================================"
echo "📦 Creating Windows Deployment Package"
echo "============================================================================"
echo ""

# 1. Export Docker images
echo "Step 1/7: Exporting backend Docker image (this may take 5-10 minutes)..."
sudo docker save structural-health-monitoring-backend:latest | gzip > "$PACKAGE_DIR/shm-backend.tar.gz"
echo "✓ Backend image exported"

echo ""
echo "Step 2/7: Exporting frontend Docker image..."
sudo docker save structural-health-monitoring-frontend:latest | gzip > "$PACKAGE_DIR/shm-frontend.tar.gz"
echo "✓ Frontend image exported"

# 2. Copy configuration files
echo ""
echo "Step 3/7: Copying configuration files..."
cp docker-compose.yml "$PACKAGE_DIR/"
cp .env.docker "$PACKAGE_DIR/.env"
cp .dockerignore "$PACKAGE_DIR/" 2>/dev/null || true
echo "✓ Configuration copied"

# 3. Copy ML models
echo ""
echo "Step 4/7: Copying ML models..."
mkdir -p "$PACKAGE_DIR/backend/ml_models"
cp -r backend/ml_models/* "$PACKAGE_DIR/backend/ml_models/" 2>/dev/null || true
echo "✓ ML models copied"

# 4. Copy ML456 trained models
echo ""
echo "Step 5/7: Copying ML456 trained models..."
mkdir -p "$PACKAGE_DIR/ml456_advanced"
if [ -d "/home/itachi/ml456_advanced/checkpoints" ]; then
    cp -r /home/itachi/ml456_advanced/checkpoints "$PACKAGE_DIR/ml456_advanced/"
    echo "✓ ML456 models copied"
else
    echo "⚠ ML456 models not found, skipping..."
fi

# 5. Update docker-compose for Windows
echo ""
echo "Step 6/7: Creating Windows-compatible docker-compose.yml..."
cat > "$PACKAGE_DIR/docker-compose.yml" << 'EOF'
# Docker Compose configuration for Structural Health Monitoring System

services:
  backend:
    image: structural-health-monitoring-backend:latest
    container_name: shm-backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - TF_CPP_MIN_LOG_LEVEL=2
    volumes:
      - uploads_data:/app/uploads
      - outputs_data:/app/outputs
      - ml_models_data:/app/ml_models
      # Mount ML456 models (Windows path - adjust if needed)
      - ./ml456_advanced:/home/itachi/ml456_advanced:ro
    networks:
      - shm-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  frontend:
    image: structural-health-monitoring-frontend:latest
    container_name: shm-frontend
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - shm-network
    restart: unless-stopped

networks:
  shm-network:
    driver: bridge

volumes:
  uploads_data:
  outputs_data:
  ml_models_data:
EOF
echo "✓ Windows docker-compose created"

# 6. Create Windows batch scripts
echo ""
echo "Step 7/7: Creating Windows setup scripts..."

cat > "$PACKAGE_DIR/SETUP_WINDOWS.bat" << 'EOFBAT'
@echo off
echo ============================================================================
echo   Structural Health Monitoring System - Windows Setup
echo ============================================================================
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not running!
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [1/4] Loading backend Docker image (this may take 5-10 minutes)...
docker load -i shm-backend.tar.gz
if %errorlevel% neq 0 (
    echo ERROR: Failed to load backend image
    pause
    exit /b 1
)

echo [2/4] Loading frontend Docker image...
docker load -i shm-frontend.tar.gz
if %errorlevel% neq 0 (
    echo ERROR: Failed to load frontend image
    pause
    exit /b 1
)

echo [3/4] Creating required directories...
mkdir uploads 2>nul
mkdir outputs 2>nul

echo [4/4] Starting containers...
docker compose up -d

echo.
echo ============================================================================
echo   Setup Complete!
echo ============================================================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo To view logs: docker compose logs -f
echo To stop:      docker compose down
echo.
pause
EOFBAT

cat > "$PACKAGE_DIR/START.bat" << 'EOFBAT'
@echo off
echo Starting Structural Health Monitoring System...
docker compose up -d
timeout /t 3 >nul
docker compose ps
echo.
echo System started!
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo.
start http://localhost:3000
pause
EOFBAT

cat > "$PACKAGE_DIR/STOP.bat" << 'EOFBAT'
@echo off
echo Stopping Structural Health Monitoring System...
docker compose down
echo System stopped!
pause
EOFBAT

cat > "$PACKAGE_DIR/VIEW_LOGS.bat" << 'EOFBAT'
@echo off
echo Viewing logs (Press Ctrl+C to exit)...
docker compose logs -f
EOFBAT

cat > "$PACKAGE_DIR/README_WINDOWS.txt" << 'EOFTXT'
STRUCTURAL HEALTH MONITORING SYSTEM - WINDOWS DEPLOYMENT
============================================================================

QUICK START:
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
   - Enable WSL 2 during installation
   - Restart computer if prompted
2. Extract this ZIP file to a folder
3. Double-click "SETUP_WINDOWS.bat" to install
4. Open browser: http://localhost:3000

SYSTEM REQUIREMENTS:
- Windows 10/11 (64-bit)
- Docker Desktop with WSL 2
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

FILES INCLUDED:
- shm-backend.tar.gz      : Backend Docker image (~2 GB)
- shm-frontend.tar.gz     : Frontend Docker image (~500 MB)
- docker-compose.yml      : Container configuration
- backend/ml_models/      : Machine learning models
- ml456_advanced/         : Trained ML456 models

USAGE:
- SETUP_WINDOWS.bat : First-time setup (run once)
- START.bat         : Start the system
- STOP.bat          : Stop the system
- VIEW_LOGS.bat     : View system logs

FEATURES:
✓ Upload accelerometer data (CSV files)
✓ Baseline prediction using ML
✓ Damage classification (AI-powered)
✓ Repair quality analysis
✓ Professional PDF reports
✓ 2-sensor damage localization

TROUBLESHOOTING:

Problem: "Docker is not running"
Solution: Open Docker Desktop app and wait for it to start

Problem: "Port 3000 already in use"
Solution: 
  1. Open PowerShell as Administrator
  2. Run: Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force

Problem: "Cannot load image"
Solution: Make sure you extracted ALL files from the ZIP

Problem: Slow performance
Solution:
  1. Open Docker Desktop → Settings → Resources
  2. Increase Memory to 8GB or more
  3. Click "Apply & Restart"

For more help, see WINDOWS_DEPLOYMENT_GUIDE.md

============================================================================
Contact: [Your contact information]
Version: 1.0 (January 2026)
EOFTXT

echo "✓ Windows scripts created"

# 7. Copy documentation
echo ""
echo "Copying documentation..."
cp WINDOWS_DEPLOYMENT_GUIDE.md "$PACKAGE_DIR/" 2>/dev/null || echo "⚠ Deployment guide not found"
cp README.md "$PACKAGE_DIR/" 2>/dev/null || echo "⚠ README not found"

# 8. Calculate size
echo ""
echo "============================================================================"
echo "📊 Package Summary"
echo "============================================================================"
du -sh "$PACKAGE_DIR"
echo ""
echo "File breakdown:"
du -sh "$PACKAGE_DIR"/* | sort -h

echo ""
echo "============================================================================"
echo "✅ Package Created Successfully!"
echo "============================================================================"
echo ""
echo "Location: $PACKAGE_DIR"
echo ""
echo "Next steps:"
echo ""
echo "1. Compress the package:"
echo "   zip -r structural-repair-windows.zip $PACKAGE_DIR"
echo "   OR"
echo "   tar -czf structural-repair-windows.tar.gz $PACKAGE_DIR"
echo ""
echo "2. Send to your friend via:"
echo "   • Google Drive / OneDrive (recommended for large files)"
echo "   • WeTransfer (free up to 2GB)"
echo "   • Mega.nz (free up to 20GB)"
echo "   • USB drive"
echo ""
echo "3. Your friend should:"
echo "   • Install Docker Desktop for Windows"
echo "   • Extract the ZIP file"
echo "   • Run SETUP_WINDOWS.bat"
echo "   • Open http://localhost:3000"
echo ""
echo "============================================================================"

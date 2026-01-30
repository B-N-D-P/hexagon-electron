# Windows Deployment Guide - Structural Health Monitoring System

This guide will help you deploy the complete system on a Windows laptop using Docker.

## 📋 Prerequisites

Your friend needs to install these on their Windows laptop:

### 1. Docker Desktop for Windows
- Download: https://www.docker.com/products/docker-desktop/
- System Requirements:
  - Windows 10/11 (64-bit)
  - WSL 2 (Windows Subsystem for Linux)
  - At least 8GB RAM (16GB recommended)
  - 20GB free disk space

### 2. Git for Windows (Optional, for updates)
- Download: https://git-scm.com/download/win

---

## 📦 What to Package and Send

You need to send these files to your friend:

### Option 1: Docker Images (Recommended - No Build Required)
```bash
# Export Docker images on your Arch Linux system
sudo docker save structural-health-monitoring-backend:latest | gzip > shm-backend.tar.gz
sudo docker save structural-health-monitoring-frontend:latest | gzip > shm-frontend.tar.gz

# Total size: ~2-4 GB compressed
```

### Option 2: Source Code + Data (Build Required)
Package the entire project directory excluding unnecessary files.

---

## 🎯 Deployment Method 1: Pre-built Docker Images (EASIEST)

This is the fastest method - no compilation needed!

### Step 1: Package Everything on Your System

Run this script on your Arch Linux machine:

```bash
#!/bin/bash
# Create deployment package for Windows

PACKAGE_DIR="structural-repair-windows-deployment"
mkdir -p "$PACKAGE_DIR"

echo "📦 Creating Windows deployment package..."

# 1. Export Docker images
echo "Exporting backend image..."
sudo docker save structural-health-monitoring-backend:latest | gzip > "$PACKAGE_DIR/shm-backend.tar.gz"

echo "Exporting frontend image..."
sudo docker save structural-health-monitoring-frontend:latest | gzip > "$PACKAGE_DIR/shm-frontend.tar.gz"

# 2. Copy configuration files
echo "Copying configuration files..."
cp docker-compose.yml "$PACKAGE_DIR/"
cp .env.docker "$PACKAGE_DIR/.env"
cp Dockerfile.backend "$PACKAGE_DIR/"
cp Dockerfile.frontend "$PACKAGE_DIR/"

# 3. Copy ML models
echo "Copying ML models..."
mkdir -p "$PACKAGE_DIR/ml_models"
cp -r backend/ml_models/* "$PACKAGE_DIR/ml_models/" 2>/dev/null || true

# 4. Copy ML456 trained models
echo "Copying ML456 trained models..."
mkdir -p "$PACKAGE_DIR/ml456_advanced"
cp -r /home/itachi/ml456_advanced/checkpoints "$PACKAGE_DIR/ml456_advanced/" 2>/dev/null || true
cp -r /home/itachi/ml456_advanced/config "$PACKAGE_DIR/ml456_advanced/" 2>/dev/null || true

# 5. Create Windows setup scripts
cat > "$PACKAGE_DIR/SETUP_WINDOWS.bat" << 'EOF'
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

echo [1/4] Loading backend Docker image...
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
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo To view logs: docker compose logs -f
echo To stop:      docker compose down
echo.
pause
EOF

cat > "$PACKAGE_DIR/START.bat" << 'EOF'
@echo off
echo Starting Structural Health Monitoring System...
docker compose up -d
echo.
echo System started!
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo.
pause
EOF

cat > "$PACKAGE_DIR/STOP.bat" << 'EOF'
@echo off
echo Stopping Structural Health Monitoring System...
docker compose down
echo System stopped!
pause
EOF

cat > "$PACKAGE_DIR/VIEW_LOGS.bat" << 'EOF'
@echo off
echo Viewing logs (Press Ctrl+C to exit)...
docker compose logs -f
EOF

# 6. Create README
cat > "$PACKAGE_DIR/README_WINDOWS.txt" << 'EOF'
STRUCTURAL HEALTH MONITORING SYSTEM - WINDOWS DEPLOYMENT
============================================================================

QUICK START:
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Double-click "SETUP_WINDOWS.bat" to install
3. Open browser: http://localhost:3000

SYSTEM REQUIREMENTS:
- Windows 10/11 (64-bit)
- Docker Desktop with WSL 2
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

FILES INCLUDED:
- shm-backend.tar.gz    : Backend Docker image
- shm-frontend.tar.gz   : Frontend Docker image
- docker-compose.yml    : Container orchestration
- ml_models/            : Machine learning models
- ml456_advanced/       : Trained ML456 models

USAGE:
- START.bat       : Start the system
- STOP.bat        : Stop the system
- VIEW_LOGS.bat   : View system logs

TROUBLESHOOTING:
1. Make sure Docker Desktop is running
2. Check ports 3000 and 8000 are not in use
3. Run: docker compose logs -f

For support, contact: [your email]
EOF

# 7. Calculate size
echo ""
echo "Calculating package size..."
du -sh "$PACKAGE_DIR"

echo ""
echo "✅ Package created: $PACKAGE_DIR"
echo ""
echo "Next steps:"
echo "1. Compress the folder:"
echo "   zip -r structural-repair-windows.zip $PACKAGE_DIR"
echo ""
echo "2. Send to your friend via:"
echo "   - Google Drive / Dropbox"
echo "   - USB drive"
echo "   - File transfer service"
echo ""
echo "3. Your friend should:"
echo "   - Extract the ZIP file"
echo "   - Run SETUP_WINDOWS.bat"
echo "   - Open http://localhost:3000"
```

Save this as `create_windows_package.sh` and run it.

### Step 2: Send the Package

Compress and send:
```bash
cd /mnt/storage/structural-repair-web
chmod +x create_windows_package.sh
./create_windows_package.sh

# Compress
zip -r structural-repair-windows.zip structural-repair-windows-deployment/

# Or use tar
tar -czf structural-repair-windows.tar.gz structural-repair-windows-deployment/
```

Upload to:
- **Google Drive / OneDrive** (if < 15GB)
- **WeTransfer** (free up to 2GB)
- **Mega.nz** (free up to 20GB)
- **Physical USB drive**

---

## 🎯 Deployment Method 2: Source Code + Build (Smaller Download)

### Step 1: Package Source Code

```bash
#!/bin/bash
# Package source code for Windows

PACKAGE_DIR="structural-repair-source"
mkdir -p "$PACKAGE_DIR"

# Copy essential files
cp -r backend "$PACKAGE_DIR/"
cp -r frontend "$PACKAGE_DIR/"
cp docker-compose.yml Dockerfile.* .dockerignore .env.docker "$PACKAGE_DIR/"

# Copy ML models
cp -r backend/ml_models "$PACKAGE_DIR/backend/" 2>/dev/null || true

# Create Windows build script
cat > "$PACKAGE_DIR/BUILD_AND_RUN.bat" << 'EOF'
@echo off
echo Building and starting system...
docker compose build
docker compose up -d
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
pause
EOF

# Compress
tar -czf structural-repair-source.tar.gz "$PACKAGE_DIR/"
```

**Note:** This requires building on Windows, which takes longer but is a smaller download.

---

## 🪟 Windows-Specific Configuration

### Update docker-compose.yml for Windows

If your friend needs to change paths, edit `docker-compose.yml`:

```yaml
# Windows path for ML456 (if needed)
volumes:
  # Windows style path
  - C:/Users/YourFriend/ml456_advanced:/home/itachi/ml456_advanced:ro
  
  # Or use relative path (put ml456_advanced in same folder)
  - ./ml456_advanced:/home/itachi/ml456_advanced:ro
```

---

## 📝 Instructions for Your Friend (Windows User)

### Setup Steps:

1. **Install Docker Desktop**
   - Download from https://www.docker.com/products/docker-desktop/
   - During installation, enable WSL 2
   - Restart computer if prompted

2. **Extract the Package**
   - Right-click the ZIP → Extract All
   - Choose a location (e.g., `C:\structural-health-monitoring`)

3. **Run Setup**
   - Open the extracted folder
   - Double-click `SETUP_WINDOWS.bat`
   - Wait for images to load (5-10 minutes)

4. **Access the System**
   - Open browser: http://localhost:3000
   - Backend API: http://localhost:8000/docs

5. **Daily Usage**
   - Start: Double-click `START.bat`
   - Stop: Double-click `STOP.bat`
   - View Logs: Double-click `VIEW_LOGS.bat`

---

## 🔧 Troubleshooting on Windows

### Common Issues:

**Issue 1: Docker not running**
```
Solution: Open Docker Desktop and wait for it to start
```

**Issue 2: Port already in use**
```
Solution: 
1. Open PowerShell as Administrator
2. Run: netstat -ano | findstr :3000
3. Kill process: taskkill /PID <PID> /F
```

**Issue 3: WSL 2 not installed**
```
Solution:
1. Open PowerShell as Administrator
2. Run: wsl --install
3. Restart computer
```

**Issue 4: Slow performance**
```
Solution:
- Allocate more RAM in Docker Desktop settings
- Settings → Resources → Memory (set to 8GB+)
```

---

## 📊 Package Size Estimates

| Method | Size | Build Time | User Effort |
|--------|------|------------|-------------|
| Pre-built Images | 3-5 GB | None | Low ⭐⭐⭐ |
| Source Code | 500 MB | 20-30 min | Medium ⭐⭐ |
| Source + Models | 1-2 GB | 15-20 min | Medium ⭐⭐ |

**Recommendation:** Use pre-built images for easiest deployment!

---

## ✅ Testing Checklist (For Your Friend)

After setup, test these:

- [ ] Frontend loads at http://localhost:3000
- [ ] Backend health check: http://localhost:8000/health
- [ ] Upload a CSV file
- [ ] Run baseline prediction
- [ ] Run damage classification
- [ ] Generate PDF report
- [ ] View previous analyses

---

## 🆘 Support

If your friend encounters issues, they can:

1. **Check logs:**
   ```
   docker compose logs -f
   ```

2. **Restart containers:**
   ```
   docker compose restart
   ```

3. **Full reset:**
   ```
   docker compose down
   docker compose up -d
   ```

4. **Contact you with:**
   - Error messages
   - Screenshots
   - Log output

---

## 🔐 Security Notes

- Change default passwords in `.env` file
- Don't expose ports to internet without firewall
- Keep Docker Desktop updated
- Regular backups of uploads/outputs folders

---

## 📚 Additional Resources

- Docker Desktop Docs: https://docs.docker.com/desktop/windows/
- WSL 2 Guide: https://learn.microsoft.com/en-us/windows/wsl/install
- Project Documentation: See README.md files in package

---

**Created:** 2026-01-30  
**Version:** 1.0  
**Platform:** Windows 10/11 with Docker Desktop

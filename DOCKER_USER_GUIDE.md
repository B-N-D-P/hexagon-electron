# 📦 User Guide - Docker Deployment Package

## 🎯 For End Users (Non-Technical)

This guide helps you install and use the **Structural Health Monitoring System** on your computer using Docker.

---

## 📥 What is Docker?

Docker is like a **virtual container** that packages all the software you need to run the application. Think of it as:

- ✅ **No installation hassle**: Everything works out-of-the-box
- ✅ **No conflicts**: Isolated from other software on your computer
- ✅ **Easy updates**: Just download and run the new version
- ✅ **Portable**: Works the same on Windows, Mac, and Linux

---

## 🖥️ Step 1: Install Docker

### Windows

1. Download **Docker Desktop**: https://www.docker.com/products/docker-desktop/
2. Run the installer (Docker Desktop Installer.exe)
3. Follow the installation wizard
4. **Restart your computer**
5. Open Docker Desktop (you'll see a whale icon in the system tray)

### Mac

1. Download **Docker Desktop**: https://www.docker.com/products/docker-desktop/
2. Open the .dmg file
3. Drag Docker to Applications
4. Launch Docker from Applications
5. Grant permissions when asked

### Linux (Ubuntu/Debian)

```bash
# Run these commands in Terminal
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER

# Logout and login again
```

### Verify Installation

Open **Terminal** (Mac/Linux) or **PowerShell** (Windows) and type:

```bash
docker --version
```

You should see something like: `Docker version 24.0.6`

---

## 📦 Step 2: Download the Application

### Option A: Download Package (Easiest)

1. Download the `structural-health-monitoring.zip` file
2. Extract to a folder (e.g., `Documents/structural-health-monitoring`)
3. Open Terminal/PowerShell in that folder

### Option B: Git Clone (If you have Git)

```bash
git clone https://github.com/your-repo/structural-health-monitoring.git
cd structural-health-monitoring
```

---

## 🚀 Step 3: Start the Application

### Automatic Method (Recommended)

**Mac/Linux:**
```bash
./docker-start.sh
```

**Windows (PowerShell):**
```powershell
bash docker-start.sh
```

Or manually:
```powershell
docker-compose up -d
```

### What Happens?

The script will:
1. ✅ Check if Docker is running
2. ✅ Download required components (~2GB, first time only)
3. ✅ Build the application (~5-10 minutes, first time only)
4. ✅ Start the services
5. ✅ Show you the access URL

**First time**: Takes 5-10 minutes  
**Next times**: Takes 10-30 seconds

---

## 🌐 Step 4: Access the Application

Once started, open your web browser and go to:

**🔗 http://localhost:3000**

You should see the **Structural Health Monitoring** dashboard!

---

## 📊 How to Use

### Upload Files

1. Click **"Upload Data"** button
2. Select your CSV file containing sensor data
3. Wait for upload confirmation

### Run Analysis

1. Choose analysis type:
   - **Repair Quality**: Compare original → damaged → repaired
   - **Comparative**: Compare damaged → repaired
2. Configure parameters (or use defaults)
3. Click **"Analyze"**
4. Wait for results (1-5 minutes depending on data size)

### View Results

- 📈 **Interactive Graphs**: Frequency spectra, mode shapes
- 📊 **Quality Score**: 0-100% repair effectiveness
- 📄 **Download Reports**: PDF, JSON, HTML formats

---

## 🛑 Stop the Application

### Automatic Method

**Mac/Linux:**
```bash
./docker-stop.sh
```

**Windows (PowerShell):**
```powershell
bash docker-stop.sh
```

Or manually:
```powershell
docker-compose down
```

**Your data is safe!** All uploaded files and results are preserved.

---

## 🔄 Restart the Application

Just run the start script again:

```bash
./docker-start.sh
```

Your previous data and results will still be there!

---

## 💾 Your Data Location

All your data is stored in **Docker volumes**:

| Data Type | Location |
|-----------|----------|
| Uploaded CSV files | Docker volume `shm-uploads` |
| Analysis results | Docker volume `shm-outputs` |
| ML models | Docker volume `shm-ml-models` |

**Note**: Even if you restart your computer or update the application, your data is preserved.

---

## 🆘 Troubleshooting

### Problem: "Docker is not running"

**Solution**: 
- Open Docker Desktop application
- Wait for the whale icon to stop animating
- Try again

### Problem: "Port 3000 is already in use"

**Solution**:
```bash
# Stop other applications using port 3000
# Or change the port:
echo "FRONTEND_PORT=8080" > .env
./docker-start.sh
# Then access: http://localhost:8080
```

### Problem: "Cannot access http://localhost:3000"

**Solution**:
```bash
# Check if containers are running
docker ps

# Check logs
docker-compose logs

# Restart everything
docker-compose restart
```

### Problem: Application is slow

**Solution**:
- Give Docker more RAM: Docker Desktop → Settings → Resources → Memory (4GB+)
- Close other heavy applications
- Check your disk space (need 10GB+ free)

### Problem: "Permission denied"

**Linux only:**
```bash
# Add yourself to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

---

## 📱 Access from Other Devices

Want to use the app from your phone or another computer?

### On Same Network (WiFi/LAN)

1. Find your computer's IP address:
   - **Windows**: Open PowerShell → type `ipconfig` → look for "IPv4 Address"
   - **Mac**: System Preferences → Network → Look for IP address
   - **Linux**: Terminal → type `ip addr show` → look for "inet"

2. From other device, open browser and go to:
   ```
   http://YOUR_COMPUTER_IP:3000
   ```
   Example: `http://192.168.1.100:3000`

3. Make sure firewall allows connections on port 3000

---

## 🔧 Useful Commands

### Check if Application is Running

```bash
docker ps
```

You should see two containers: `shm-backend` and `shm-frontend`

### View Logs

```bash
docker-compose logs -f
```

Press `Ctrl+C` to exit

### Check Application Health

Open browser: http://localhost:8000/health

Should show: `{"status": "healthy"}`

### Update Application

```bash
# Stop current version
docker-compose down

# Download new version (if using git)
git pull

# Start new version
./docker-start.sh
```

---

## 🗑️ Uninstall

### Remove Application (Keep Data)

```bash
docker-compose down
docker rmi structural-health-monitoring-backend:latest
docker rmi structural-health-monitoring-frontend:latest
```

### Remove Everything (Including Data)

```bash
docker-compose down -v
docker volume rm shm-uploads shm-outputs shm-ml-models
```

Then delete the application folder.

---

## 📞 Getting Help

### 1. Check the Logs

```bash
docker-compose logs -f
```

Look for red error messages.

### 2. Check Status

```bash
docker ps
```

Both containers should show "healthy" status.

### 3. Test Connection

Open browser:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs

### 4. Restart Everything

```bash
docker-compose restart
```

---

## 📚 Additional Resources

- **Quick Start**: See `DOCKER_QUICK_START.md`
- **Full Guide**: See `DOCKER_DEPLOYMENT_GUIDE.md`
- **Docker Documentation**: https://docs.docker.com/

---

## ⚠️ Important Notes

### First Launch
- First time takes 5-10 minutes to download and build
- Need stable internet connection
- Need ~5GB disk space

### System Requirements
- **RAM**: 4GB minimum (8GB recommended)
- **CPU**: 2 cores minimum (4+ recommended)
- **Disk**: 10GB free space
- **Internet**: Required for first download only

### Data Backup
Your data is in Docker volumes. To backup:

```bash
# Create backup
docker run --rm -v shm-uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz -C /data .
```

---

## ✅ Quick Reference Card

```
╔════════════════════════════════════════════════════════╗
║           QUICK REFERENCE CARD                         ║
╠════════════════════════════════════════════════════════╣
║ START APP:        ./docker-start.sh                    ║
║ STOP APP:         ./docker-stop.sh                     ║
║ ACCESS UI:        http://localhost:3000                ║
║ CHECK LOGS:       docker-compose logs -f               ║
║ CHECK STATUS:     docker ps                            ║
║ RESTART:          docker-compose restart               ║
╚════════════════════════════════════════════════════════╝
```

---

**🎉 You're all set! Enjoy using the Structural Health Monitoring System!**

For technical support, see the full deployment guide or contact your system administrator.

# 🚀 Docker Quick Start - 2 Minutes to Running Application

## 📦 One-Command Installation

### Step 1: Make sure Docker is running

```bash
# Check Docker status
docker info
```

If Docker isn't running, start it:
- **Linux**: `sudo systemctl start docker`
- **Mac/Windows**: Open Docker Desktop

### Step 2: Run the deployment script

```bash
./docker-start.sh
```

**That's it!** The script will:
- ✅ Check Docker installation
- ✅ Build container images (~5-10 minutes first time)
- ✅ Start all services
- ✅ Wait for health checks
- ✅ Display access URLs

### Step 3: Access your application

Open your browser:

| Service | URL |
|---------|-----|
| **Frontend UI** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

---

## 🛠️ Basic Commands

```bash
# View logs (press Ctrl+C to exit)
docker-compose logs -f

# Stop services
./docker-stop.sh
# or
docker-compose down

# Restart services
docker-compose restart

# Check status
docker-compose ps
```

---

## 🔄 What Happens on First Run?

1. **Building images** (~5-10 minutes)
   - Downloads Python 3.11 base image
   - Installs backend dependencies (NumPy, PyTorch, TensorFlow, etc.)
   - Downloads Node.js base image
   - Builds React frontend
   - Downloads Nginx base image

2. **Starting services** (~30-60 seconds)
   - Starts backend API server
   - Starts frontend web server
   - Runs health checks

3. **Ready to use!**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

---

## 💡 Common Issues & Quick Fixes

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :3000
sudo lsof -i :8000

# Kill the process or change ports in .env file
```

### Docker Not Running

```bash
# Linux
sudo systemctl start docker

# Check status
docker info
```

### Build Failed

```bash
# Clean rebuild
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

### Can't Access Application

```bash
# Check if containers are running
docker-compose ps

# Check logs for errors
docker-compose logs backend
docker-compose logs frontend

# Check health
curl http://localhost:8000/health
```

---

## 📊 What's Running?

After deployment, you'll have:

| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| `shm-backend` | structural-health-monitoring-backend | 8000 | FastAPI + ML models |
| `shm-frontend` | structural-health-monitoring-frontend | 3000 | React UI + Nginx |

---

## 💾 Your Data is Safe

All your data is stored in Docker volumes:

| Volume | Contains |
|--------|----------|
| `shm-uploads` | Uploaded CSV files |
| `shm-outputs` | Analysis reports |
| `shm-ml-models` | ML models |

**Your data survives container restarts!**

To backup:
```bash
docker run --rm -v shm-uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz -C /data .
```

---

## 🌐 Access from Other Devices

### On Same Network (LAN)

1. Find your computer's IP:
   ```bash
   ip addr show  # Linux
   ipconfig      # Windows
   ifconfig      # macOS
   ```

2. Access from another device:
   ```
   http://YOUR_IP:3000
   ```

### From Internet

⚠️ **Not recommended without HTTPS!** See full guide: `DOCKER_DEPLOYMENT_GUIDE.md`

---

## 📚 Next Steps

- **Full documentation**: See `DOCKER_DEPLOYMENT_GUIDE.md`
- **Configuration**: Edit `.env` file
- **Monitoring**: Run `docker-compose logs -f`
- **Updates**: Run `docker-compose pull && docker-compose up -d`

---

## 🆘 Need Help?

```bash
# Check logs
docker-compose logs -f backend

# Check health
curl http://localhost:8000/health

# Restart everything
docker-compose restart
```

**Still stuck?** Open an issue or check the full deployment guide.

---

**🎉 Enjoy your containerized Structural Health Monitoring System!**

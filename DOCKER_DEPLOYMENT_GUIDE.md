# 🐳 Docker Deployment Guide - Structural Health Monitoring System

## 📦 What You'll Get

A **single-command deployment** that installs:
- ✅ Backend API (FastAPI + ML models)
- ✅ Frontend UI (React + Nginx)
- ✅ Persistent data storage (Docker volumes)
- ✅ Automatic health monitoring
- ✅ Production-ready configuration

**No manual setup required!** Just run one script and access the application.

---

## 🚀 Quick Start (1 Minute)

### Option 1: Automated Script (Recommended)

```bash
# 1. Start everything with one command
./docker-start.sh

# 2. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Option 2: Manual Docker Compose

```bash
# 1. Build and start services
docker-compose up -d

# 2. Check status
docker-compose ps

# 3. View logs
docker-compose logs -f
```

---

## 📋 Prerequisites

### Required Software

1. **Docker** (version 20.10 or later)
   - Download: https://docs.docker.com/get-docker/
   - Verify: `docker --version`

2. **Docker Compose** (usually included with Docker)
   - Verify: `docker-compose --version` or `docker compose version`

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space (5GB for images + 5GB for data)
- **OS**: Linux, macOS, or Windows (with WSL2)

---

## 📁 Project Structure

```
.
├── docker-compose.yml          # Main orchestration file
├── Dockerfile.backend          # Backend image definition
├── Dockerfile.frontend         # Frontend image definition
├── .dockerignore              # Files to exclude from build
├── .env.docker                # Environment configuration template
├── docker-start.sh            # Automated startup script
├── docker-stop.sh             # Graceful shutdown script
└── DOCKER_DEPLOYMENT_GUIDE.md # This file
```

---

## 🔧 Configuration

### Environment Variables

Copy `.env.docker` to `.env` and customize:

```bash
cp .env.docker .env
nano .env  # Edit configuration
```

**Key Settings:**

```bash
# Service Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Logging
LOG_LEVEL=INFO

# Analysis Parameters
DEFAULT_FS=1000
DEFAULT_MAX_MODES=5
DEFAULT_MIN_FREQ=1.0
DEFAULT_MAX_FREQ=450.0

# File Upload
MAX_FILE_SIZE=52428800  # 50 MB
```

### Port Configuration

If ports 3000 or 8000 are already in use:

```bash
# Edit .env file
BACKEND_PORT=8080
FRONTEND_PORT=8081

# Restart services
docker-compose down
docker-compose up -d
```

---

## 🎯 Usage Examples

### Start Services

```bash
# Using automated script
./docker-start.sh

# Or using docker-compose
docker-compose up -d
```

### Stop Services

```bash
# Graceful shutdown
./docker-stop.sh

# Or using docker-compose
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Check Status

```bash
# Service status
docker-compose ps

# Detailed inspection
docker inspect shm-backend
docker inspect shm-frontend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart backend only
docker-compose restart backend

# Restart frontend only
docker-compose restart frontend
```

---

## 💾 Data Persistence

Your data is stored in **Docker volumes** and persists across container restarts.

### Volumes Created

1. **`shm-uploads`** - User uploaded CSV files
2. **`shm-outputs`** - Generated reports and analysis results
3. **`shm-ml-models`** - Trained ML models

### Manage Volumes

```bash
# List volumes
docker volume ls | grep shm

# Inspect volume
docker volume inspect shm-uploads

# Backup volume
docker run --rm -v shm-uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/uploads-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v shm-uploads:/data -v $(pwd):/backup \
  alpine tar xzf /backup/uploads-backup.tar.gz -C /data

# Remove all data (WARNING: Irreversible!)
docker-compose down -v
```

---

## 🔍 Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker info

# Check for port conflicts
sudo lsof -i :3000
sudo lsof -i :8000

# Check logs for errors
docker-compose logs backend
docker-compose logs frontend
```

### Build Failures

```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Remove old images
docker system prune -a
```

### Health Check Failures

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:3000

# Inspect container
docker inspect shm-backend | grep -A 10 Health
```

### Container Keeps Restarting

```bash
# View last logs before crash
docker logs shm-backend --tail 50

# Run container interactively
docker-compose run --rm backend bash
```

### Out of Memory

```bash
# Increase Docker memory limit
# Docker Desktop: Settings → Resources → Memory → 4GB+

# Or reduce workers in docker-compose.yml:
# CMD ["uvicorn", "app:app", "--workers", "1"]
```

### Permission Errors

```bash
# Fix volume permissions (Linux)
sudo chown -R $USER:$USER ~/.docker

# Or run as root (not recommended for production)
docker-compose run --user root backend bash
```

---

## 🔐 Security Best Practices

### Production Deployment

1. **Change default ports**
   ```bash
   # Use non-standard ports
   BACKEND_PORT=8443
   FRONTEND_PORT=8444
   ```

2. **Enable HTTPS** (use reverse proxy like Nginx or Caddy)
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:3000;
       }
   }
   ```

3. **Restrict network access**
   ```yaml
   # In docker-compose.yml
   ports:
     - "127.0.0.1:8000:8000"  # Only localhost
   ```

4. **Use secrets for passwords**
   ```yaml
   # docker-compose.yml
   secrets:
     db_password:
       file: ./secrets/db_password.txt
   ```

5. **Enable firewall**
   ```bash
   # UFW (Ubuntu)
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

---

## 📊 Monitoring & Maintenance

### View Resource Usage

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Container resource limits
docker-compose config
```

### Regular Maintenance

```bash
# Clean up unused images/containers (weekly)
docker system prune

# Update images (monthly)
docker-compose pull
docker-compose up -d

# Backup data (daily/weekly)
./docker-backup.sh
```

---

## 🌐 Remote Access

### Access from Another Computer (LAN)

1. Find your server's IP:
   ```bash
   ip addr show  # Linux
   ipconfig      # Windows
   ifconfig      # macOS
   ```

2. Access from another device:
   ```
   http://YOUR_SERVER_IP:3000
   ```

3. Configure firewall:
   ```bash
   sudo ufw allow 3000/tcp
   sudo ufw allow 8000/tcp
   ```

### Access from Internet (Port Forwarding)

1. Forward ports on your router:
   - External: 80 → Internal: YOUR_SERVER_IP:3000
   - External: 443 → Internal: YOUR_SERVER_IP:3000

2. Use dynamic DNS (e.g., No-IP, DuckDNS)

3. **⚠️ IMPORTANT**: Use HTTPS with SSL certificates (Let's Encrypt)

---

## 🔄 Updates & Upgrades

### Update to New Version

```bash
# 1. Pull latest code
git pull

# 2. Rebuild images
docker-compose build --no-cache

# 3. Restart services
docker-compose down
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/health
```

### Rollback to Previous Version

```bash
# 1. Stop current version
docker-compose down

# 2. Checkout previous version
git checkout <previous-commit>

# 3. Rebuild and start
docker-compose build
docker-compose up -d
```

---

## 🧹 Complete Cleanup

### Remove Everything (Fresh Start)

```bash
# Stop and remove containers
docker-compose down -v

# Remove images
docker rmi structural-health-monitoring-backend:latest
docker rmi structural-health-monitoring-frontend:latest

# Remove volumes (WARNING: Deletes all data!)
docker volume rm shm-uploads shm-outputs shm-ml-models

# Remove network
docker network rm structural-health-monitoring

# Clean system
docker system prune -a --volumes
```

---

## 📞 Support & Help

### Getting Help

1. **Check logs**: `docker-compose logs -f`
2. **Health status**: `curl http://localhost:8000/health`
3. **System info**: `docker info && docker-compose version`

### Common Issues

| Issue | Solution |
|-------|----------|
| Port already in use | Change `BACKEND_PORT` or `FRONTEND_PORT` in `.env` |
| Out of disk space | Run `docker system prune` |
| Container won't start | Check logs with `docker-compose logs backend` |
| Can't access UI | Verify `http://localhost:3000` and check firewall |
| API errors | Check backend health: `curl localhost:8000/health` |

---

## 🎓 Advanced Topics

### Multi-Stage Production Deployment

```bash
# Development
docker-compose -f docker-compose.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Scale Services

```bash
# Run multiple backend workers
docker-compose up -d --scale backend=3
```

### Custom Network Configuration

```yaml
networks:
  shm-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Add PostgreSQL Database

```bash
# Uncomment postgres section in docker-compose.yml
# Then restart services
docker-compose up -d
```

---

## 📈 Performance Optimization

### Backend Optimization

```yaml
# docker-compose.yml
backend:
  command: ["uvicorn", "app:app", "--workers", "4", "--loop", "uvloop"]
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 8G
```

### Frontend Optimization

```yaml
# frontend/nginx.conf
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] Change default ports (optional)
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Test health checks
- [ ] Configure logging
- [ ] Set resource limits
- [ ] Document access URLs
- [ ] Test disaster recovery
- [ ] Set up monitoring alerts

---

## 📝 License & Credits

**Structural Health Monitoring System**  
Docker packaging by: Rovo Dev  
Version: 1.0.0  
Date: 2026-01-29

---

**🎉 You're all set! Enjoy your containerized deployment!**

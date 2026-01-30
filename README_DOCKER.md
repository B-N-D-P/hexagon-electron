# 🐳 Structural Health Monitoring System - Docker Package

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Production-ready Docker deployment** for Structural Health Monitoring and Repair Quality Analysis System

---

## 🎯 Overview

This Docker package provides a **complete, containerized solution** for structural health monitoring with:

- ✅ **Zero Configuration**: One command to deploy everything
- ✅ **Production Ready**: Multi-stage builds, health checks, security hardening
- ✅ **Data Persistence**: Automatic volume management for uploads, outputs, ML models
- ✅ **Scalable**: Easy to scale backend workers or add PostgreSQL
- ✅ **Portable**: Run on any system with Docker (Linux, macOS, Windows)
- ✅ **Secure**: Non-root users, resource limits, isolated networks

---

## 🚀 Quick Start (60 Seconds)

### Prerequisites

- **Docker** (20.10+): [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Usually included with Docker Desktop

### Installation

```bash
# 1. Clone repository (or extract package)
cd structural-health-monitoring

# 2. Start everything with one command
./docker-start.sh

# 3. Access application
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000/docs
```

**That's it!** 🎉

---

## 📦 What's Included

### Services

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| **Backend** | FastAPI + Python 3.11 | 8000 | API server, ML models, analysis engine |
| **Frontend** | React 18 + Vite + Nginx | 3000 | Web UI, visualizations, file upload |

### Features

- 🔬 **Modal Analysis**: Extract natural frequencies, mode shapes, damping ratios
- 🎯 **Repair Quality**: Assess structural repair effectiveness (0-100% score)
- 📊 **ML Predictions**: Neural network-based baseline prediction
- 📈 **Visualizations**: Interactive graphs, frequency spectra, mode shapes
- 📄 **Reports**: PDF, JSON, HTML reports with comprehensive analysis
- 🔄 **Real-time**: WebSocket support for live monitoring (optional)

---

## 📁 Project Structure

```
.
├── docker-compose.yml              # Service orchestration
├── Dockerfile.backend              # Backend image (Python + ML)
├── Dockerfile.frontend             # Frontend image (React + Nginx)
├── .dockerignore                   # Build optimization
├── .env.docker                     # Configuration template
│
├── docker-start.sh                 # Automated deployment script
├── docker-stop.sh                  # Graceful shutdown script
├── Makefile                        # Convenient shortcuts
│
├── DOCKER_QUICK_START.md          # 2-minute guide
├── DOCKER_DEPLOYMENT_GUIDE.md     # Complete documentation
└── README_DOCKER.md               # This file
```

---

## 🎮 Usage

### Basic Commands

```bash
# Start services
./docker-start.sh
# or
make start

# Stop services
./docker-stop.sh
# or
make stop

# View logs
docker-compose logs -f
# or
make logs

# Check status
docker-compose ps
# or
make status

# Restart services
docker-compose restart
# or
make restart
```

### Using Make (Recommended)

```bash
make help           # Show all commands
make start          # Start everything
make stop           # Stop everything
make logs           # View logs
make status         # Check health
make backup         # Backup data
make test           # Test deployment
make clean          # Remove containers
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file from template:

```bash
cp .env.docker .env
nano .env
```

**Key configurations:**

```bash
# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Analysis settings
DEFAULT_FS=1000              # Sampling frequency (Hz)
DEFAULT_MAX_MODES=5          # Maximum modes to extract
DEFAULT_MIN_FREQ=1.0         # Minimum frequency (Hz)
DEFAULT_MAX_FREQ=450.0       # Maximum frequency (Hz)

# File upload
MAX_FILE_SIZE=52428800       # 50 MB

# Logging
LOG_LEVEL=INFO
```

### Port Configuration

Change ports if defaults are in use:

```bash
# Edit .env
BACKEND_PORT=8080
FRONTEND_PORT=8081

# Restart
docker-compose down
docker-compose up -d
```

---

## 💾 Data Persistence

All data is stored in **Docker volumes** and persists across restarts:

| Volume | Purpose | Typical Size |
|--------|---------|--------------|
| `shm-uploads` | User uploaded CSV files | ~100MB-1GB |
| `shm-outputs` | Analysis reports, graphs | ~500MB-5GB |
| `shm-ml-models` | Trained ML models | ~10-50MB |

### Backup Data

```bash
# Automated backup
make backup

# Manual backup
docker run --rm -v shm-uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore Data

```bash
docker run --rm -v shm-uploads:/data -v $(pwd):/backup \
  alpine tar xzf /backup/backup-20260129.tar.gz -C /data
```

---

## 🔍 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Container health
docker inspect shm-backend | grep -A 10 Health
```

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100

# Follow with timestamps
docker-compose logs -f -t
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Container details
docker ps -a
```

---

## 🔐 Security

### Production Checklist

- ✅ **Non-root user**: Backend runs as `appuser` (UID 1000)
- ✅ **Resource limits**: CPU and memory constraints configured
- ✅ **Health checks**: Automatic container restart on failure
- ✅ **Network isolation**: Services in private Docker network
- ✅ **Volume permissions**: Proper ownership and access control

### Recommended for Production

```bash
# 1. Use HTTPS (with reverse proxy)
# See: DOCKER_DEPLOYMENT_GUIDE.md

# 2. Restrict network access
# Edit docker-compose.yml:
ports:
  - "127.0.0.1:8000:8000"  # Localhost only

# 3. Enable firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 4. Regular updates
docker-compose pull
docker-compose up -d
```

---

## 📊 Performance

### Specifications

**Backend Container:**
- Base: Python 3.11-slim (Debian)
- Size: ~1.2GB (with dependencies)
- CPU: 2 cores max, 0.5 reserved
- RAM: 4GB max, 1GB reserved
- Workers: 2 Uvicorn workers

**Frontend Container:**
- Base: Nginx 1.25-alpine
- Size: ~50MB
- CPU: 0.5 cores max
- RAM: 512MB max

### Optimization

```yaml
# Scale backend workers
backend:
  command: ["uvicorn", "app:app", "--workers", "4"]

# Increase resources
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
```

---

## 🌐 Remote Access

### LAN Access

```bash
# Find server IP
ip addr show  # Linux
ipconfig      # Windows
ifconfig      # macOS

# Access from other devices
http://YOUR_SERVER_IP:3000
```

### Internet Access

⚠️ **Security Warning**: Do not expose without HTTPS!

1. Set up reverse proxy (Nginx/Caddy)
2. Get SSL certificate (Let's Encrypt)
3. Configure firewall
4. Use strong authentication

See: `DOCKER_DEPLOYMENT_GUIDE.md` for details

---

## 🛠️ Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Check ports
sudo lsof -i :3000
sudo lsof -i :8000

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Permission Denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login, or:
newgrp docker

# Test
docker ps
```

### Out of Memory

```bash
# Increase Docker memory
# Docker Desktop: Settings → Resources → Memory → 4GB+

# Or reduce workers
# Edit docker-compose.yml: --workers 1
```

### Can't Access UI

```bash
# Check if container is running
docker ps | grep shm

# Check health
curl http://localhost:8000/health
curl http://localhost:3000

# Check firewall
sudo ufw status

# View nginx logs
docker-compose logs frontend
```

---

## 🔄 Updates

### Update to New Version

```bash
# 1. Pull latest
git pull

# 2. Rebuild
docker-compose build --no-cache

# 3. Restart
docker-compose down
docker-compose up -d

# 4. Verify
curl http://localhost:8000/health
```

### Rollback

```bash
# Stop current
docker-compose down

# Checkout previous version
git checkout v1.0.0

# Rebuild and start
docker-compose build
docker-compose up -d
```

---

## 🧪 Testing

### Automated Tests

```bash
# Run test suite
make test

# Manual health check
curl http://localhost:8000/health | jq

# Upload test file
curl -X POST -F "file=@test_data.csv" \
  http://localhost:8000/api/v1/upload
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test backend
ab -n 1000 -c 10 http://localhost:8000/health

# Test frontend
ab -n 1000 -c 10 http://localhost:3000/
```

---

## 🧹 Cleanup

### Remove Containers

```bash
docker-compose down
```

### Remove Images

```bash
docker-compose down
docker rmi structural-health-monitoring-backend:latest
docker rmi structural-health-monitoring-frontend:latest
```

### Remove Everything (Including Data)

```bash
# WARNING: Deletes all data!
docker-compose down -v
docker volume rm shm-uploads shm-outputs shm-ml-models
```

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| **DOCKER_QUICK_START.md** | 2-minute quick start guide |
| **DOCKER_DEPLOYMENT_GUIDE.md** | Complete deployment documentation |
| **README_DOCKER.md** | This file - overview and reference |

---

## 🎓 Advanced Topics

### Add PostgreSQL Database

```bash
# Uncomment postgres section in docker-compose.yml
# Then restart
docker-compose up -d
```

### Custom Network

```yaml
networks:
  shm-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### SSL/HTTPS Setup

```bash
# Use Caddy (automatic HTTPS)
caddy reverse-proxy --from example.com --to localhost:3000

# Or Nginx
# See: DOCKER_DEPLOYMENT_GUIDE.md
```

---

## 📞 Support

### Getting Help

1. **Check logs**: `make logs`
2. **Test deployment**: `make test`
3. **View documentation**: See guides above
4. **Check status**: `make status`

### Common Issues

| Issue | Solution |
|-------|----------|
| Port in use | Change `BACKEND_PORT`/`FRONTEND_PORT` in `.env` |
| Out of disk | Run `docker system prune` |
| Can't connect | Check firewall and Docker network |
| Build fails | Run `docker system prune -a && make build` |

---

## 📝 System Requirements

### Minimum

- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB free
- OS: Linux, macOS, Windows (WSL2)

### Recommended

- CPU: 4+ cores
- RAM: 8GB+
- Disk: 20GB+ free
- SSD for better performance

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🙏 Credits

**Structural Health Monitoring System**  
Docker Packaging: Rovo Dev  
Version: 1.0.0  
Date: 2026-01-29

**Built with:**
- Docker & Docker Compose
- FastAPI & Python
- React & Vite
- Nginx
- PyTorch & TensorFlow
- NumPy & SciPy

---

## 🎉 Quick Commands Reference

```bash
# Start
./docker-start.sh           # Automated script
make start                  # Using Makefile
docker-compose up -d        # Direct command

# Stop
./docker-stop.sh            # Automated script
make stop                   # Using Makefile
docker-compose down         # Direct command

# Monitor
make logs                   # View logs
make status                 # Check health
make test                   # Run tests

# Maintain
make backup                 # Backup data
make clean                  # Remove containers
docker system prune         # Clean unused resources
```

---

**🚀 Ready to deploy? Run `./docker-start.sh` and you're live in 60 seconds!**

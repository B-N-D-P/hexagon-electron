# 🚀 Quick Start Guide - Structural Repair Analysis Platform

Get up and running in **5 minutes** with Docker!

---

## Prerequisites

- **Docker Desktop** (https://www.docker.com/products/docker-desktop)
- **Git** (for cloning)
- **4GB RAM minimum** recommended
- **10GB disk space** for images and data

---

## 🐳 Docker Setup (Recommended)

### 1. Clone/Extract Project
```bash
cd structural-repair-web
```

### 2. Build and Start
```bash
# Build containers (first time only, ~2-3 minutes)
docker-compose build

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Output should show:**
```
CONTAINER ID   IMAGE                           STATUS
xxxxx          struct-repair-backend           Up (healthy)
xxxxx          struct-repair-frontend          Up (healthy)
```

### 3. Access the Application

| Component | URL | Purpose |
|-----------|-----|---------|
| **Frontend** | http://localhost:3000 | Upload data & view results |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | System status |

### 4. Upload Sample Data

1. Open http://localhost:3000 in your browser
2. Click "Repair Quality Analysis"
3. Upload sample CSV files:
   - Original: `backend/sample_data/original.csv`
   - Damaged: `backend/sample_data/damaged.csv`
   - Repaired: `backend/sample_data/repaired.csv`
4. Click "Run Analysis"
5. View results in dashboard!

---

## 🖥️ Local Development Setup

### Backend (Python)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
python app.py
```

**Backend runs on:** http://localhost:8000

### Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend runs on:** http://localhost:5173

---

## 🧪 Test the System

### Method 1: Using Web UI (Easiest)

1. Go to http://localhost:3000
2. Select "Repair Quality Analysis"
3. Upload sample files (or any CSV with accelerometer data)
4. Click "Run Analysis"
5. View results in real-time!

### Method 2: Using API (For Developers)

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Upload file
curl -X POST -F "file=@backend/sample_data/damaged.csv" \
  http://localhost:8000/api/v1/upload

# 3. Start analysis
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "damaged_file_id": "YOUR_FILE_ID",
    "analysis_type": "localization",
    "fs": 1000,
    "max_modes": 5
  }'

# 4. Get results
curl http://localhost:8000/api/v1/results/ANALYSIS_ID
```

---

## 📊 Understanding the Results

### Quality Score
- **95-100%**: Excellent repair
- **85-94%**: Very good repair
- **70-84%**: Good repair
- **50-69%**: Fair repair
- **<50%**: Poor repair

### Damage Localization
- **Confidence >80%**: High confidence in location
- **Confidence 65-80%**: Moderate confidence
- **Confidence <65%**: Low confidence (more data needed)

### Modal Parameters
- **Frequencies**: Natural vibration frequencies (Hz)
- **Damping**: Energy dissipation in the structure
- **Mode Shapes**: Deformation patterns during vibration

---

## 🔧 Common Operations

### View Live Logs
```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# All logs
docker-compose logs -f
```

### Rebuild and Restart
```bash
# Full rebuild (if you modify code)
docker-compose build --no-cache
docker-compose up -d

# Or for specific service
docker-compose build backend
docker-compose up -d backend
```

### Stop Services
```bash
# Stop all
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Access Container Shell
```bash
# Backend shell
docker exec -it struct-repair-backend /bin/bash

# Frontend shell
docker exec -it struct-repair-frontend /bin/sh
```

---

## 📁 Data Flow

```
User Upload (CSV)
        ↓
   [Backend API]
   - Load & Validate
   - Extract Modal Parameters
        ↓
   - Physics-based Analysis
   - ML-based Analysis
        ↓
   [Generate Results]
   - Quality Scores
   - Damage Location
   - Visualizations
        ↓
   [Frontend Display]
   - Interactive Dashboard
   - Charts & Heatmaps
   - PDF/JSON Reports
```

---

## 📱 Supported Data Formats

### Single-Axis (4 columns)
```csv
sensor1, sensor2, sensor3, sensor4
0.123,   0.456,   0.789,   0.234
0.124,   0.457,   0.790,   0.235
...
```

### 3-Axis (12 columns)
```csv
s1_x, s1_y, s1_z, s2_x, s2_y, s2_z, s3_x, s3_y, s3_z, s4_x, s4_y, s4_z
0.1,  0.2,  0.3,  0.4,  0.5,  0.6,  0.7,  0.8,  0.9,  1.0,  1.1,  1.2
...
```

### Requirements
- ✅ Minimum 512 samples
- ✅ Numeric data only
- ✅ No NaN or infinite values
- ✅ Consistent time intervals
- ✅ Max 50 MB file size

---

## 🎨 Customization

### Change Default Parameters

Edit `backend/config.py`:
```python
DEFAULT_FS = 1000.0        # Sampling rate
DEFAULT_MAX_MODES = 5       # Max frequency modes
DEFAULT_MIN_FREQ = 1.0      # Minimum frequency
DEFAULT_MAX_FREQ = 450.0    # Maximum frequency
```

### Change UI Theme

Edit `frontend/src/App.css`:
```css
/* Change color scheme */
:root {
  --primary: #3b82f6;      /* Blue */
  --success: #10b981;      /* Green */
  --danger: #ef4444;       /* Red */
}
```

---

## 🐛 Troubleshooting

### "Connection refused" error
**Problem**: Services not running
**Solution**: 
```bash
docker-compose up -d
docker-compose ps  # Verify all containers are "Up"
```

### "File not found" on upload
**Problem**: File path incorrect
**Solution**: 
- Use absolute paths
- Ensure file has .csv extension
- Check file size < 50MB

### Slow analysis
**Problem**: Low RAM or CPU intensive
**Solution**:
- Close other applications
- Increase Docker memory allocation
- Use smaller data files for testing

### Port already in use
**Problem**: 3000 or 8000 port in use
**Solution**:
```bash
# Kill process on port 3000
lsof -i :3000  # Find PID
kill -9 PID    # Kill it

# Or change port in docker-compose.yml
ports:
  - "3001:80"  # Changed from 3000
```

---

## ⚡ Performance Tips

1. **Use SSD storage** for faster file I/O
2. **Allocate 4GB+ RAM** to Docker
3. **Close unnecessary applications** during analysis
4. **Use Firefox or Chrome** for best UI performance
5. **Enable browser cache** for faster page loads

---

## 📊 Example Analysis Time

| Data Size | Computation Time | Total (incl. UI) |
|-----------|------------------|------------------|
| 10 sec data (10K samples) | 2-3s | 5-6s |
| 30 sec data (30K samples) | 4-5s | 7-9s |
| 60 sec data (60K samples) | 6-8s | 10-12s |

---

## 🎓 Next Steps

1. **Explore API Documentation**: http://localhost:8000/docs
2. **Try Different Analysis Types**: Repair Quality, Comparative, Localization
3. **Generate Reports**: Export JSON/PDF for presentations
4. **Modify Parameters**: Adjust fs, max_modes for your data
5. **Integrate with Your System**: Use REST API for automation

---

## 📚 Resources

- **Full Documentation**: See `README.md`
- **API Reference**: `backend/models/schemas.py`
- **Configuration**: `backend/config.py`
- **Core Algorithm**: `backend/services/damage_localizer.py`

---

## 💡 Tips for Judges

1. **Show the damage localization** - This is the most impressive feature
2. **Demonstrate real-time analysis** - Upload actual accelerometer data
3. **Highlight the hybrid approach** - Physics + ML combination
4. **Show professional UI/UX** - Dashboard with interactive charts
5. **Discuss scalability** - Docker deployment ready

---

## 🚀 Ready to Impress?

Your system is now running with:
- ✅ Professional web interface
- ✅ AI-powered damage detection
- ✅ Real-time analysis
- ✅ Production-grade architecture
- ✅ Scalable infrastructure

**Good luck with your presentation! 🎯**

---

**Questions?** Check the full README or API docs at `/docs`

# Quick Setup - Copy & Paste Commands

All the bash commands you need to automate everything, in one place.

---

## 🚀 Option 1: One-Command Full Automation (RECOMMENDED)

Runs everything automatically:

```bash
chmod +x scripts/full_automation.sh
./scripts/full_automation.sh
```

**What it does**:
- ✅ Installs all dependencies
- ✅ Starts backend + frontend
- ✅ Collects 3-day baseline (simulated)
- ✅ Trains ML models (Isolation Forest + Autoencoder)
- ✅ Validates everything
- ✅ Opens dashboard

**Duration**: ~10 min (simulated) or 3 days (real hardware)

---

## 🎯 Option 2: Step-by-Step (If You Want Control)

### Step 1: Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

### Step 2: Start All Services

```bash
./scripts/start_all.sh
```

This opens 3 terminals:
- Terminal 1: Backend (port 8000)
- Terminal 2: Frontend (port 5173)
- Terminal 3: Data Collection (simulated)

### Step 3: Collect Baseline (72 hours or 1 hour test)

**For testing (1 hour)**:
```bash
./scripts/collect_baseline.sh 1h
```

**For real (3 days)**:
```bash
./scripts/collect_baseline.sh 3d
```

### Step 4: Train Models

```bash
./scripts/train_models.sh data/baseline
```

### Step 5: Restart Backend & View Dashboard

```bash
# Stop old backend
bash scripts/stop_all.sh

# Start new backend (with ML models loaded)
python3 backend/app.py
```

**Open dashboard**: http://localhost:5173/live-monitoring

---

## 🛑 Stop Everything

```bash
./scripts/stop_all.sh
```

---

## 📖 Individual Commands (If You Need Custom Setup)

### Start Backend Only

```bash
cd backend
python3 app.py
```

### Start Frontend Only

```bash
cd frontend
npm run dev
```

### Stream Data (Simulated)

```bash
python3 tools/data_collect.py \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --simulate
```

### Stream Data (Real Arduino)

```bash
# First upload sketch to Arduino
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega arduino/DATA_COLLECTION.ino

# Then stream
python3 tools/data_collect.py \
  --stream ws://127.0.0.1:8000/ws/ingest
```

### Manual Baseline Collection

```bash
python3 tools/baseline_collector.py \
  --duration 1h \
  --output-dir data/baseline \
  --simulate
```

### Manual Model Training

```bash
python3 tools/train_ml_models.py \
  --baseline-dir data/baseline \
  --verify
```

### Run Tests

```bash
python3 tools/test_streaming.py
```

---

## 📊 Check Status

```bash
# Check processes
ps aux | grep -E "python3|npm" | grep -v grep

# Check ports
netstat -tulpn | grep -E "8000|5173"

# Check logs
tail -f /tmp/backend.log
tail -f /tmp/frontend.log

# List trained models
ls -lh backend/ml_models/trained/

# List baseline data
ls -lh data/baseline/
```

---

## 🔧 With Real Arduino Hardware

### 1. Upload Sketch

```bash
# Install Arduino CLI
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Find your Arduino
arduino-cli board list

# Upload (change port as needed)
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega arduino/DATA_COLLECTION.ino
```

### 2. Collect Real Data

```bash
python3 tools/data_collect.py \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --token dev-token
```

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check port 8000 is available
lsof -i :8000

# Kill anything using it
pkill -f "python3 app.py"

# Try again
python3 backend/app.py
```

### Frontend won't start

```bash
# Clear npm cache
npm cache clean --force

# Reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Models won't train

```bash
# Install ML dependencies
pip install scikit-learn joblib pywavelets tensorflow pandas

# Try training again
python3 tools/train_ml_models.py --baseline-dir data/baseline --verify
```

### Arduino not uploading

```bash
# Find port
ls /dev/ttyACM* /dev/ttyUSB*

# Try with explicit port
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega arduino/DATA_COLLECTION.ino
```

---

## 📱 Access Dashboard

After everything is running, open:

```
http://localhost:5173/live-monitoring
```

You should see:
- ✅ Live time-series chart
- ✅ ML Anomaly Meter with gauge
- ✅ Real-time anomaly scores
- ✅ Confidence indicator

---

## 🎯 10-Day Timeline with Bash Commands

### Days 1-3: Collect Baseline

```bash
./scripts/collect_baseline.sh 3d data/baseline
```

### Days 3-5: Train Models

```bash
./scripts/train_models.sh data/baseline
```

### Days 5-7: Deploy & Test

```bash
# Stop old backend
bash scripts/stop_all.sh

# Start new backend
python3 backend/app.py

# Run tests
python3 tools/test_streaming.py
```

### Days 7-10: Monitor & Fine-tune

```bash
# View dashboard
open http://localhost:5173/live-monitoring

# Monitor logs
tail -f /tmp/backend.log
```

---

## 💾 Save & Restore

### Backup your data

```bash
# Backup baseline
cp -r data/baseline data/baseline_backup

# Backup models
cp -r backend/ml_models/trained backend/ml_models/trained_backup
```

### Clean and restart

```bash
# Remove everything
rm -rf data/baseline/
rm -rf backend/ml_models/trained/
rm -rf frontend/node_modules/

# Start fresh
./scripts/full_automation.sh
```

---

## 🚀 Summary

| What | Command |
|------|---------|
| **Full automation** | `./scripts/full_automation.sh` |
| **Start all** | `./scripts/start_all.sh` |
| **Collect baseline** | `./scripts/collect_baseline.sh` |
| **Train models** | `./scripts/train_models.sh data/baseline` |
| **Stop all** | `./scripts/stop_all.sh` |
| **Dashboard** | http://localhost:5173/live-monitoring |
| **Logs** | `tail -f /tmp/backend.log` |

---

**You're all set!** 🎉

Start with:
```bash
chmod +x scripts/*.sh
./scripts/full_automation.sh
```


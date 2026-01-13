# Real-Time Monitoring - Quick Start Guide

Get up and running with real-time monitoring in 5 minutes!

## Prerequisites

- Python 3.8+
- Node.js 14+
- Git

## Installation

### 1. Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Frontend Dependencies
```bash
cd frontend
npm install
```

## Running the System

Open 3 terminals:

### Terminal 1: Start Backend
```bash
cd backend
python3 app.py
```

Expected output:
```
🚀 Structural Repair Quality Analysis API v1.0.0
✓ Upload directory: /path/to/uploads
✓ Output directory: /path/to/outputs
✓ CORS origins: ['http://localhost:3000', ...]

📡 Streaming Configuration:
   ✓ Buffer duration: 120 seconds
   ✓ PSD window: 8 seconds
   ✓ Update rate: 1 Hz
   ✓ Auth token: dev-token
   ✓ Live analysis engine initialized
   ✓ Baseline manager initialized
   ✓ Metrics publisher started
```

Backend ready at: `http://localhost:8000`

### Terminal 2: Start Frontend
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v5.0.8 ready in XXX ms

➜ Local: http://localhost:5173/
```

### Terminal 3: Start Data Collection
```bash
python3 tools/data_collect.py \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --simulate \
  --token dev-token
```

Expected output:
```
🔍 ADXL345 Real-Time Data Collection
📋 Configuration:
   Sampling rate: 1000 Hz
   Number of sensors: 5
   Sample interval: 1.00 ms

🎲 Using SYNTHETIC data (simulation mode)

▶ Starting collection... (press Ctrl+C to stop)
```

## Access Live Monitoring

1. Open browser: `http://localhost:5173`
2. Click "Live" in the navigation bar (red pulsing icon)
3. Click "Start Streaming" button

You should see:
- **Overview tab**: Live time-series chart updating in real-time
- **Spectrum tab**: Power spectral density with detected peaks
- **Controls tab**: "Mark as Baseline" button
- **Alerts**: Any QC warnings at the top

## Mode B: Without Baseline (First-Time Setup)

1. Let it stream for 5-10 seconds
2. Click **"Mark as Baseline"** button
3. Confirm in the popup
4. Check Controls tab - baseline is now marked

You've captured your first baseline!

## Mode A: With Baseline (Comparative Monitoring)

1. Baseline must be marked (see Mode B above)
2. Go to Controls tab
3. Select baseline from dropdown: "Current Baseline"
4. Switch to **Comparative tab**

You'll see:
- **Quality Score**: % match to baseline (0-100%)
- **Frequency Shifts**: Δf% for each modal peak
- **Energy Heatmap**: Per-sensor anomaly visualization (5 sensors shown)
- **Sensor Status**: Detail cards for each sensor

## Testing the Alerts

### Jitter Alert
- Should trigger if timing jitter > 5ms
- Usually shown as warning (yellow)

### Frequency Shift Alert
- Appears when modal frequencies shift > 5% vs baseline
- Typically triggered by damage or sensor issues

### Energy Anomaly
- Shows when a sensor's acceleration magnitude deviates > 70% from baseline
- Useful for localization (which sensor is abnormal)

### Clipping Alert
- Triggers if any sensor saturates the ADC
- Red alert - indicates sensor overload

## Using Real Hardware

When ADXL345 sensors are connected:

```bash
python3 tools/data_collect.py \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --token dev-token
  # Remove --simulate flag
```

The script will:
- Read raw SPI data from all 5 sensors
- Compute live QC metrics (jitter, clipping, SNR)
- Stream to backend
- Save rotating CSV files to `data/YYYYMMDD/`

## Stopping

Press `Ctrl+C` in each terminal:

1. **Data Collection**: Cleanly flushes CSV and metadata
2. **Frontend**: Stops dev server
3. **Backend**: Closes WebSocket connections

## Troubleshooting

### "Connected to stream" but no data

**Check**:
1. Is data_collect.py running?
2. Check browser console (F12 → Console tab)
3. Check backend output for errors
4. Verify WebSocket connection: F12 → Network → WS

### High jitter warnings

**Fix**:
1. Increase batch size: `--batch-size 200`
2. Check system CPU load
3. Verify USB/serial connection stability

### No peaks detected

**Fix**:
1. Ensure SNR > 30 dB (should be auto-generated in simulation)
2. Run for longer (8 second window needed)
3. Check PSD plot shape in Spectrum tab

### Baseline won't mark

**Check**:
1. Stream running? (play button should show "Stop")
2. At least 8 seconds of data? (needed for first PSD)
3. Check browser console for errors

## Data Storage

### Live Monitoring
- **In-memory buffer**: 120 seconds (cleared on backend restart)
- **Baseline profiles**: `backend/outputs/baseline_*.json`

### CSV Logging
- **Location**: `data/YYYYMMDD/data_YYYYMMDD_HHMMSS.csv`
- **Format**: Timestamp, then [S1_x, S1_y, S1_z, S2_x, ...] for each row
- **Metadata**: `data_YYYYMMDD_HHMMSS.json` with fs, num_sensors, sample count

## Configuration

### Adjust Buffer Size
Edit `backend/config.py`:
```python
LIVE_BUFFER_DURATION_SEC = 60  # Default 120
```

### Adjust Update Rate
```python
METRICS_UPDATE_RATE_HZ = 2  # Default 1 (faster updates, more CPU)
```

### Disable Streaming
```bash
export ENABLE_STREAMING=false
python3 app.py
```

### Change Auth Token
```bash
export STREAM_INGEST_AUTH_TOKEN=my-secret-key
python3 app.py
```

Then use in data_collect.py:
```bash
python3 tools/data_collect.py \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --token my-secret-key \
  --simulate
```

## Next Steps

1. **Production Deployment**: Check `REAL_TIME_MONITORING.md`
2. **Add Annotations**: Operator notes during monitoring
3. **Export Data**: Download incident windows as CSV/PDF
4. **Multi-user**: Connect multiple frontends
5. **Cloud**: Deploy to AWS/Azure for remote monitoring

## Support

- Check logs in backend console
- Review WebSocket in browser DevTools (Network tab)
- Run integration tests: `python3 tools/test_streaming.py`
- See `REAL_TIME_MONITORING.md` for full documentation

---

**Quick Links**:
- Live Monitoring: http://localhost:5173/live-monitoring
- API Docs: http://localhost:8000/docs
- Swagger UI: http://localhost:8000/docs

Happy monitoring! 🎉

# Real-Time Monitoring Implementation Guide

## Overview

This document describes the real-time monitoring system for the 5× ADXL345 SPI rig integrated with the structural-repair-web platform. The system supports two distinct modes:

- **Mode A**: With baseline/damage datasets (comparative metrics, localization heatmap)
- **Mode B**: Without baseline (streaming QC, absolute metrics, mark baseline capability)

## Architecture Components

### Backend Infrastructure

#### 1. Live Buffer Engine (`backend/services/live_buffer.py`)

The heart of real-time processing:

- **LiveSensorBuffer**: Circular in-memory buffer per sensor
  - Stores 120 seconds of raw data by default
  - Thread-safe with RLock
  - Automatic old data eviction

- **RollingPSDAnalyzer**: Welch PSD on sliding 8-second windows
  - Computes power spectral density at ~1 Hz update rate
  - Uses scipy.signal.welch with 50% overlap
  - Frequency range: 0.5 Hz to 450 Hz

- **PeakTracker**: Peak detection and matching
  - Identifies prominent spectral peaks
  - Tracks peak stability across windows
  - 2 Hz frequency tolerance for matching

- **DampingEstimator**: Damping ratio estimation
  - Direct method: impulse response envelope decay
  - Fallback method: 3dB bandwidth of spectral peak
  - Produces damping ratios in range [0, 0.5]

- **ComparativeEngine**: Comparative analysis vs baseline
  - Frequency shift computation (Δf%)
  - Energy anomaly scoring per sensor
  - Quality score calculation (0-1)
  - Simplified localization heatmap

- **LiveAnalysisEngine**: Orchestrator
  - Manages all above components
  - Ingests streaming frames
  - Computes and publishes metrics
  - Thread-safe global state

#### 2. Baseline Manager (`backend/services/baseline_manager.py`)

Handles baseline profiles:

- **BaselineProfile**: Dataclass for cached baseline
  - Spectral frequencies and damping
  - RMS baseline values per sensor
  - PSD profile
  - Metadata (name, creation time, source)

- **BaselineManager**: Central registry
  - Auto-scans outputs/ for existing baselines
  - Creates new baselines from live data
  - Supports multiple baselines (dropdown selection)
  - Thread-safe caching

#### 3. WebSocket Endpoints (app.py additions)

**Ingest Endpoint**: `/ws/ingest`
```
POST /ws/ingest?token=dev-token
Expected: JSON frames {ts, fs, sensors, mode, frame}
Rate: ~100-1000 frames/sec (configurable)
Auth: Query parameter token matching STREAM_INGEST_AUTH_TOKEN
```

**Stream Endpoint**: `/ws/stream`
```
GET /ws/stream
Publishes: Processed metrics at ~1 Hz
Format: {ts, qc, metrics, comparative}
Auth: None (frontend only)
```

**REST Endpoints**:
- `POST /api/baseline/mark?name=...` - Capture current buffer as baseline
- `GET /api/baseline/list` - List available baselines
- `POST /api/baseline/select?baseline_id=...` - Set comparison baseline

#### 4. Configuration (config.py)

Streaming parameters:
```python
LIVE_BUFFER_DURATION_SEC = 120       # Buffer window
PSD_WINDOW_SIZE_SEC = 8              # Welch window
METRICS_UPDATE_RATE_HZ = 1           # Publishing rate
ENABLE_STREAMING = True              # Feature flag
STREAM_INGEST_AUTH_TOKEN = "dev-token"

# Alert thresholds
JITTER_THRESHOLD_MS = 5.0
FREQ_SHIFT_ALERT_PERCENT = 5.0
ENERGY_ANOMALY_THRESHOLD = 0.7
```

### Frontend Components

#### 1. Main Page: `LiveMonitoring.jsx`

Four-tab interface:

**Overview Tab**:
- Live time-series chart (last 10 seconds)
- QC status badges (jitter, clipping, SNR)
- Real-time RMS values per sensor
- Recording status indicator

**Spectrum Tab**:
- Welch PSD plot (all sensors overlaid)
- Detected peaks with frequency labels (f1, f2, f3...)
- Interactive tooltips
- Peak stability indicators

**Comparative Tab** (enabled when baseline selected):
- Frequency shift table (Δf% vs baseline)
- Damping change table
- Quality score bar
- Energy anomaly heatmap (2D structure layout)
- Per-sensor anomaly status

**Controls Tab**:
- "Mark as Baseline" button (Mode B) → captures current state
- Baseline selector dropdown → loads for comparison
- "Capture Incident" button → pins N seconds pre/post
- Recording status display

#### 2. Supporting Components

**LiveChart.jsx**:
- Real-time time-series rendering
- 10-second rolling window
- Per-sensor RMS computation
- Recharts LineChart (optimized for performance)

**LivePSD.jsx**:
- Welch PSD visualization
- Reference lines at detected peaks
- Log-scale Y-axis
- Per-sensor legends

**QCBadges.jsx**:
- Jitter status (good/ok/warn/alert)
- Clipping indicators per sensor
- SNR display (dB)
- Health status dots

**ComparativeDashboard.jsx**:
- Comparison table (baseline vs current)
- Quality meter (0-100%)
- Heatmap with SVG visualization
- Per-sensor detail cards

**AlertBanner.jsx**:
- Auto-dismissing alert notifications
- Severity levels (warn/alert)
- Slide-in animation

#### 3. Styling: `LiveMonitoring.css`

Professional dark theme with responsive design.

### Host Data Collection

#### Data Collection Script (`tools/data_collect.py`)

Streaming from ADXL345 rig with async WebSocket and CSV rotating files.

**Usage**:
```bash
python3 tools/data_collect.py \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --token dev-token \
  --data-dir data/ \
  --simulate
```

## Data Contracts

### Host → Backend (WebSocket /ws/ingest)

```json
{
  "ts": "2026-01-11T22:00:00Z",
  "fs": 1000,
  "sensors": 5,
  "mode": "raw_xyz",
  "frame": [[x,y,z], [x,y,z], [x,y,z], [x,y,z], [x,y,z]]
}
```

### Backend → Frontend (WebSocket /ws/stream)

```json
{
  "ts": "2026-01-11T22:00:00Z",
  "qc": {"jitter_ms": 0.5, "clipping": [false]*5, "snr_db": 35.2},
  "metrics": {"psd": {...}, "peaks": [12.5, 24.3, 48.1], "rms": [...]},
  "comparative": {"delta_f": [...], "quality": 0.88, "heatmap": {...}}
}
```

## Integration Steps

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python3 app.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Start Data Collection
```bash
python3 tools/data_collect.py --stream ws://127.0.0.1:8000/ws/ingest --simulate
```

### 4. Open Live Monitoring
Navigate to http://localhost:5173/live-monitoring

## Testing

```bash
python3 tools/test_streaming.py
# Expected: 4 passed, 0 failed
```

## Mode-Specific Workflows

### Mode B: Without Baseline
1. Start streaming
2. View live PSD and peaks in Spectrum tab
3. Mark baseline when satisfied
4. Baseline saved to outputs/

### Mode A: With Baseline
1. Select baseline from dropdown
2. View comparative metrics (Δf%, quality score)
3. Monitor energy heatmap for anomalies
4. Alerts trigger on frequency shifts or anomalies

## Configuration

Edit `backend/config.py`:
```python
LIVE_BUFFER_DURATION_SEC = 120       # seconds
PSD_WINDOW_SIZE_SEC = 8              # seconds
METRICS_UPDATE_RATE_HZ = 1           # Hz
ENABLE_STREAMING = True
STREAM_INGEST_AUTH_TOKEN = "dev-token"
```

## Performance

- Latency: < 200 ms (ingest to frontend rendering)
- Throughput: 1000 Hz × 5 sensors
- Memory: ~5-10 MB per engine instance
- PSD update rate: ~1 Hz

---

**Version**: 1.0.0  
**Status**: Production Ready

# Real-Time Monitoring Integration Checklist

Use this checklist to ensure proper setup and deployment.

## Pre-Flight Checks

### System Requirements
- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] Node.js 14+ installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Git available (`git --version`)

### Dependencies
- [ ] Backend requirements reviewed: `backend/requirements.txt`
- [ ] Frontend dependencies reviewed: `frontend/package.json`
- [ ] All ports available (8000, 5173, optional 3000)

## Backend Setup

### Installation
- [ ] Run `pip install -r requirements.txt` in backend/
- [ ] Verify scipy, numpy, websockets installed
- [ ] Check imports: `python3 -c "from live_buffer import LiveAnalysisEngine"`

### Configuration
- [ ] Review `backend/config.py` streaming section
- [ ] Set environment variables if needed:
  ```bash
  export ENABLE_STREAMING=true
  export STREAM_INGEST_AUTH_TOKEN=dev-token
  ```
- [ ] Verify output directory exists: `backend/outputs/`
- [ ] Verify uploads directory exists: `backend/uploads/`

### Startup
- [ ] Start backend: `cd backend && python3 app.py`
- [ ] Verify output shows streaming initialization
- [ ] Verify WebSocket endpoints ready
- [ ] Access Swagger UI: http://localhost:8000/docs
- [ ] Check health endpoint: `curl http://localhost:8000/health`

### Verification
- [ ] Backend running on port 8000 ✓
- [ ] No error messages in console ✓
- [ ] "Live analysis engine initialized" message shown ✓
- [ ] "Baseline manager initialized" message shown ✓
- [ ] "Metrics publisher started" message shown ✓

## Frontend Setup

### Installation
- [ ] Run `npm install` in frontend/
- [ ] Verify all packages installed
- [ ] Check node_modules size > 500MB

### Configuration
- [ ] Review backend URL in `frontend/src/services/api.js`
- [ ] Verify CORS origins in `backend/config.py` include localhost:5173
- [ ] Check environment if using different backend URL

### Startup
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Verify Vite dev server started
- [ ] Check compilation completed without errors
- [ ] Note the Local URL (usually http://localhost:5173)

### Verification
- [ ] Frontend running on port 5173 ✓
- [ ] No compilation errors ✓
- [ ] Navigate to http://localhost:5173 - shows app ✓
- [ ] Header visible with navigation links ✓
- [ ] "Live" link visible in header ✓

## Data Collection Setup

### Script Preparation
- [ ] Review `tools/data_collect.py` for your use case
- [ ] Verify Python path: `python3 tools/data_collect.py --help`
- [ ] Check websockets installed: `python3 -c "import websockets"`

### Simulation Mode (Testing)
- [ ] Run: `python3 tools/data_collect.py --stream ws://127.0.0.1:8000/ws/ingest --simulate --token dev-token`
- [ ] Verify no connection errors
- [ ] Watch for sample output (every 5 seconds)

### Real Hardware Mode (When Ready)
- [ ] Connect ADXL345 SPI hardware to host
- [ ] Run: `python3 tools/data_collect.py --stream ws://127.0.0.1:8000/ws/ingest --token dev-token`
- [ ] Verify data is flowing (status output)
- [ ] Check CSV files created in `data/YYYYMMDD/`

### Verification
- [ ] Data collection running ✓
- [ ] Status output appearing every 5 seconds ✓
- [ ] No connection refused errors ✓
- [ ] Backend console shows frames arriving ✓

## Mode B: Basic Streaming (No Baseline)

### Access
- [ ] Navigate to http://localhost:5173/live-monitoring
- [ ] See "Real-Time Monitoring" header
- [ ] See 4 tabs: Overview, Spectrum, Comparative, Controls

### Start Streaming
- [ ] Click "Start Streaming" button
- [ ] Button changes to "Stop Streaming" (red)
- [ ] Backend console shows "[ingest client connected]"
- [ ] Frontend shows "Connected to stream" in console

### Monitor Data
- [ ] Go to Overview tab
- [ ] Live time-series chart appears and updates
- [ ] See 5 sensor lines (different colors)
- [ ] RMS values displayed below chart
- [ ] QC badges show (Jitter, Clipping, SNR)

### View Spectrum
- [ ] Go to Spectrum tab
- [ ] PSD plot displays
- [ ] Peaks detected and labeled (f1, f2, f3...)
- [ ] Peak list on right side

### Quality Control
- [ ] Jitter badge should be green (good)
- [ ] Clipping should show 0/5 sensors
- [ ] SNR should be > 30 dB

### Checklist
- [ ] [ ] Time-series updating
- [ ] [ ] PSD computing
- [ ] [ ] QC badges visible
- [ ] [ ] No error messages
- [ ] [ ] Backend receiving frames

## Mode A: Comparative Analysis (With Baseline)

### Mark Baseline (Mode B → Mode A)
- [ ] Stream for 5-10 seconds
- [ ] Go to Controls tab
- [ ] Click "Mark as Baseline"
- [ ] Confirm in popup
- [ ] Backend shows "Saved baseline to baseline_*.json"

### Select Baseline
- [ ] Controls tab shows baseline created
- [ ] Dropdown populated with baseline name
- [ ] Select baseline from dropdown
- [ ] Confirmation toast appears

### View Comparative
- [ ] Go to Comparative tab
- [ ] Tab becomes enabled (was disabled before)
- [ ] Quality score bar appears
- [ ] Frequency shift table shows
- [ ] Energy heatmap displays
- [ ] Per-sensor status cards visible

### Verify Metrics
- [ ] Quality score displayed (should be ~80-100% at start)
- [ ] Frequency shifts Δf% shown for each peak
- [ ] Heatmap shows 5 sensors
- [ ] Sensor colors: Green (normal), Yellow/Orange (caution), Red (alert)

### Test Anomaly Detection
- [ ] Let stream continue (synthetic data adds noise over time)
- [ ] Watch energy heatmap for changes
- [ ] Quality score should remain stable (synthetic data is well-behaved)
- [ ] If using real hardware: structural changes will show as anomalies

### Checklist
- [ ] [ ] Baseline marked successfully
- [ ] [ ] Comparative tab enabled
- [ ] [ ] Quality score shown
- [ ] [ ] Heatmap rendered
- [ ] [ ] Alerts trigger on anomalies

## Alert Testing

### Jitter Alert
- **Condition**: Timing jitter > 5ms for > 3 seconds
- **Expected**: Yellow WARN alert banner
- **Test**: (Typically automatic if system is under load)
- [ ] Jitter alert appears (may need to stress system)

### Clipping Alert
- **Condition**: ADC saturation on any sensor
- **Expected**: Red ALERT banner + badge changes
- **Test**: (Only with real hardware or modified simulator)
- [ ] Clipping detection working (verified in badge)

### Frequency Shift Alert
- **Condition**: Δf% > 5% vs baseline (Mode A only)
- **Expected**: Red ALERT banner with frequency shift message
- **Test**: (Would need physical damage or modified baseline)
- [ ] Frequency shift detection implemented (visible in table)

### Energy Anomaly
- **Condition**: Sensor energy > 70% anomaly score (Mode A)
- **Expected**: Sensor heatmap shows red zone
- **Test**: Should appear naturally with structural changes
- [ ] Energy anomaly detection working (heatmap visible)

## CSV Data Verification

### File Location
- [ ] Data saved to `data/YYYYMMDD/` directory
- [ ] Format: `data_YYYYMMDD_HHMMSS.csv`
- [ ] Metadata file: `data_YYYYMMDD_HHMMSS.json`

### CSV Contents
- [ ] Open latest CSV in editor
- [ ] Header shows: timestamp_iso, timestamp_unix, S1_x, S1_y, S1_z, S2_x, ...
- [ ] Data rows show numeric values
- [ ] No missing columns

### Metadata JSON
- [ ] Open corresponding .json file
- [ ] Contains: filename, start_time, fs, num_sensors, samples
- [ ] fs = 1000
- [ ] num_sensors = 5
- [ ] samples > 0

### Verification
- [ ] [ ] CSV files created
- [ ] [ ] CSV has correct columns
- [ ] [ ] Metadata JSON present
- [ ] [ ] Sample count reasonable

## Shutdown & Cleanup

### Graceful Stop
- [ ] Stop data collection (Ctrl+C in Terminal 3)
- [ ] Verify "Collection complete" message
- [ ] Frontend continues running (WebSocket will reconnect)
- [ ] Stop frontend (Ctrl+C in Terminal 2)
- [ ] Stop backend (Ctrl+C in Terminal 1)

### File Verification
- [ ] Latest CSV file finalized (not corrupted)
- [ ] Metadata JSON shows correct sample count
- [ ] No orphaned files in data/ directory

### Final Checks
- [ ] [ ] All processes stopped cleanly
- [ ] [ ] CSV files valid
- [ ] [ ] Backend logs show successful shutdown
- [ ] [ ] No hung processes (`ps aux | grep python`)

## Production Deployment

### Before Going Live
- [ ] All integration tests pass: `python3 tools/test_streaming.py`
- [ ] Baseline files created and loadable
- [ ] Historical data directory verified
- [ ] Backup existing baseline files
- [ ] ENABLE_STREAMING=true verified
- [ ] Auth token changed from "dev-token"
- [ ] CORS origins updated for production domain
- [ ] Database connections verified
- [ ] Error logging configured
- [ ] Monitoring/alerting setup (optional)

### Performance Tuning (Optional)
- [ ] Adjust LIVE_BUFFER_DURATION_SEC based on needs
- [ ] Tune PSD_WINDOW_SIZE_SEC (trade latency vs resolution)
- [ ] Adjust batch size in data_collect.py for your network
- [ ] Monitor backend CPU/memory under load

### Deployment Steps
1. [ ] Pull latest code
2. [ ] Install dependencies
3. [ ] Set environment variables
4. [ ] Run database migrations (if any)
5. [ ] Start backend service
6. [ ] Start frontend build/serve
7. [ ] Verify all endpoints responding
8. [ ] Run smoke tests
9. [ ] Monitor logs for errors

## Troubleshooting Checkpoints

### If Backend Won't Start
- [ ] Check Python version: `python3 --version` (need 3.8+)
- [ ] Verify requirements installed: `pip list | grep -E "fastapi|websockets|scipy"`
- [ ] Try: `python3 -c "from live_buffer import LiveAnalysisEngine"`
- [ ] Check port 8000 not in use: `lsof -i :8000`

### If Frontend Won't Load
- [ ] Check Node version: `node --version` (need 14+)
- [ ] Clear npm cache: `npm cache clean --force`
- [ ] Delete node_modules: `rm -rf frontend/node_modules`
- [ ] Reinstall: `cd frontend && npm install && npm run dev`
- [ ] Check port 5173 not in use: `lsof -i :5173`

### If No Data Appears
- [ ] Verify data_collect.py running
- [ ] Check backend console for "[ingest client connected]"
- [ ] Verify WebSocket: Browser F12 → Network → WS
- [ ] Check status output from data_collect.py
- [ ] Try with --simulate flag first

### If Peaks Not Detected
- [ ] Wait 8+ seconds (Welch window size)
- [ ] Check SNR > 30 dB (badge in QC)
- [ ] Review PSD plot shape (should have peaks, not flat)
- [ ] Verify fs=1000 matches data rate
- [ ] Check signal not DC-offset

### If Baseline Won't Mark
- [ ] Verify stream is active (button shows "Stop")
- [ ] Wait for 8+ seconds of data
- [ ] Check browser console (F12) for errors
- [ ] Verify backend has outputs/ directory
- [ ] Check backend logs for "mark baseline" messages

## Sign-Off

- [ ] All integration tests pass
- [ ] Mode B functionality verified
- [ ] Mode A functionality verified  
- [ ] Alerts working as expected
- [ ] Data persisting to CSV
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Documentation reviewed
- [ ] Ready for deployment

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Backend URL**: _______________  
**Frontend URL**: _______________  
**Notes**: _______________

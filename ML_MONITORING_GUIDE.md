# ML-Enhanced Real-Time Monitoring Guide

## 10-Day Implementation Timeline for Iron Structure

Your 3-story iron structure is complete today. Here's your ML-powered monitoring rollout:

---

## 📅 Days 1-3: Baseline Collection Phase

### Goal
Collect 72 hours of healthy structure vibration data to establish "normal" behavior.

### Setup

**Terminal 1: Backend**
```bash
cd backend
python3 app.py
```

**Terminal 2: Frontend**
```bash
cd frontend
npm run dev
```

**Terminal 3: Start Baseline Collection**
```bash
python3 tools/baseline_collector.py \
  --stream ws://127.0.0.1:8000/ws/ingest \
  --duration 3d \
  --structure-name "Iron Structure (3-Story)" \
  --output-dir data/baseline \
  --simulate
```

Expected output:
```
📊 BASELINE DATA COLLECTION FOR ML TRAINING
================================================================================
📋 Configuration:
   Sampling rate: 1000 Hz
   Number of sensors: 5
   Collection duration: 3.0 days
   Output directory: data/baseline

▶ Starting baseline collection... (press Ctrl+C to stop)
================================================================================
```

### During Collection

**What to do:**
1. Monitor the structure for any obvious issues
2. Let collection run continuously (can be background process)
3. Watch progress output (printed every 60 seconds)
4. Check `data/baseline/` fills with CSV files (hourly rotation)

**CSV Files Created:**
- `data/baseline/data_*.csv` - Hourly sensor data files
- `data/baseline/collection_metadata.json` - Session information

### Quality Checks

Monitor baseline collection quality:
- ✅ Jitter: Should be < 2ms (avg)
- ✅ Clipping: Should be 0 events
- ✅ SNR: Should be > 30 dB

If issues occur:
- **High jitter**: Check USB/serial connection stability
- **Clipping**: Reduce sensor gain (if hardware settable)
- **Low SNR**: Ensure sensors are properly mounted

---

## 📚 Days 3-5: ML Model Training Phase

### Goal
Train Isolation Forest + Autoencoder on baseline data to establish anomaly detection models.

### Step 1: Stop Baseline Collection

```bash
# In Terminal 3, press Ctrl+C
# Wait for "✓ BASELINE COLLECTION COMPLETE" message
```

### Step 2: Verify Baseline Data

```bash
ls -lh data/baseline/
# Should show multiple data_*.csv files (one per hour)
# Total should be ~20+ CSV files for 72 hours
```

### Step 3: Train Models

```bash
python3 tools/train_ml_models.py \
  --baseline-dir data/baseline \
  --contamination 0.1 \
  --structure-name "Iron Structure (3-Story)" \
  --verify
```

Expected output:
```
🤖 ML MODEL TRAINING PIPELINE
================================================================================

📂 Loading CSV files from data/baseline...
   Found 72 CSV files
   ✓ Loaded data_*.csv: 360000 samples
   ... (loading continues)
✓ Total data loaded: 2880000 samples, 15 columns

🔧 Extracting features from 2880000 samples...
✓ Features extracted: 360 windows, 156 features

🤖 TRAINING HYBRID ANOMALY DETECTION MODEL
================================================================================
📋 Configuration:
   Training samples: 360
   Features per sample: 156
   Contamination rate: 10.0%
   Baseline name: Iron Structure

Training Isolation Forest...
✓ Isolation Forest trained

Training Autoencoder...
✓ Autoencoder trained (50 epochs)

✓ Model trained successfully!
  Version: v20260112_090000
  Samples: 360
  Features: 156
  Location: backend/ml_models/trained/v20260112_090000

✅ MODEL TRAINING COMPLETE!
================================================================================

📦 Trained model:
   Version: v20260112_090000
   Location: backend/ml_models/trained/v20260112_090000

🚀 The model is now ready for deployment!
   - It will be automatically loaded when LiveMonitoring starts
   - Real-time anomaly scores will appear in the dashboard
```

### What's Happening Behind the Scenes

1. **Feature Extraction** (156 features per 8-second window):
   - Time-domain: RMS, Kurtosis, Skewness, Peak-to-Peak, etc.
   - Frequency-domain: Spectral centroid, entropy, band energies
   - Wavelet: Multi-level decomposition energies
   - Aggregated: Cross-sensor statistics

2. **Isolation Forest Training**:
   - Fast, lightweight anomaly detector
   - Learns normal data distribution
   - Runs in < 10ms per prediction

3. **Autoencoder Training**:
   - Deep neural network (layers: 156→128→64→32→64→128→156)
   - Learns to reconstruct normal data
   - High reconstruction error = anomaly
   - Runs in < 50ms per prediction

4. **Model Versions**:
   - Saved to `backend/ml_models/trained/v*`
   - Metadata in `info.json`
   - Models auto-load on backend restart

### Troubleshooting Training

**Error: "No CSV files found"**
- Check baseline collection completed: `ls data/baseline/data_*.csv`
- Verify path is correct

**Error: "TensorFlow not available"**
- Install: `pip install tensorflow>=2.13.0`
- Autoencoder will be skipped; only Isolation Forest used

**Error: "Memory error during feature extraction"**
- Increase available RAM or process in batches
- Reduce window size (currently 8 seconds)

---

## 🚀 Days 5-7: Model Deployment & Testing

### Step 1: Restart Backend with New Model

```bash
# Terminal 1: Kill previous backend (Ctrl+C)
# Then restart:
cd backend
python3 app.py

# Expected output:
✓ Live analysis engine initialized
✓ Baseline manager initialized
✓ ML anomaly detector loaded  ← NEW!
✓ Metrics publisher started
```

### Step 2: Verify Model in Live Dashboard

1. Open http://localhost:5173/live-monitoring
2. Start streaming: `python3 tools/data_collect.py --stream ws://127.0.0.1:8000/ws/ingest --simulate`
3. Click "Start Streaming" in frontend
4. Go to **Overview tab** → Check for **ML Anomaly Score** section

### Step 3: Test Anomaly Detection

Run test script to verify model:

```bash
python3 tools/test_streaming.py
# Should show: "Mode A: Comparative Analysis: PASSED"
```

---

## 🎯 Days 7-10: Live Monitoring & Refinement

### Phase 1: Normal Operation (Days 7-8)

**Monitor healthy structure:**
```bash
# Terminal 3: Switch to real data collection (when ready)
python3 tools/data_collect.py \
  --stream ws://127.0.0.1:8000/ws/ingest
  # Remove --simulate flag when using real hardware
```

**Watch dashboard:**
- **ML Anomaly Score**: Should stay low (~0.1-0.3) for healthy structure
- **Confidence**: Should be high (0.8+) when both detectors agree
- **Is Anomaly**: Should be `False` (green indicator)

Expected healthy state:
```json
{
  "anomaly_score": 0.15,
  "confidence": 0.85,
  "is_anomaly": false,
  "if_score": 0.12,
  "ae_score": 0.18,
  "threshold": 0.60
}
```

### Phase 2: Validation (Days 8-9)

**Introduce controlled test anomalies:**
1. **Light excitation**: Drop small weight from 1m height
2. **Moderate load**: Apply temporary load to structure
3. **Sensor movement**: Slightly adjust one sensor

**Watch anomaly scores increase:**
- IF score should increase first (instant response)
- AE score should follow (learns pattern)
- When ensemble > 0.60 → Alert triggered

### Phase 3: Fine-Tuning (Day 10)

**Adjust sensitivity if needed:**

Edit `backend/ml_models/anomaly_detector.py`:
```python
# Line ~235 in HybridAnomalyDetector.predict()
anomaly_threshold = 0.60  # Default moderate sensitivity

# Options:
# 0.40 = Aggressive (catch more anomalies, more false positives)
# 0.60 = Moderate (balanced, recommended)
# 0.80 = Conservative (fewer alerts, might miss issues)
```

---

## 📊 ML Anomaly Detection Explained

### How It Works

1. **Live Data Stream** (5 sensors @ 1000 Hz):
   ```
   S1, S2, S3, S4, S5 → Feature Extraction → 156 Features
   ```

2. **Two Detectors in Parallel**:
   ```
   Isolation Forest     Autoencoder
   (Fast statistical)   (Deep learning)
           ↓                  ↓
        Score [0-1]       Score [0-1]
           ↓                  ↓
        Ensemble Average: Final Anomaly Score
   ```

3. **Alert Threshold**:
   ```
   IF anomaly_score > 0.60 THEN
     is_anomaly = True
     Alert sent to dashboard
   ```

### Feature Matrix (156 total)

For each 8-second window:

**Per-Sensor Features (7 features × 5 sensors = 35 features):**
- RMS (energy level)
- Peak-to-Peak (max deviation)
- Kurtosis (impulsiveness)
- Skewness (asymmetry)
- Crest Factor (peak/RMS ratio)
- Shape Factor (RMS/mean)
- Impulse Factor (peak/mean)

**Frequency-Domain Features (9 features × 5 sensors = 45 features):**
- Spectral Centroid (center of mass)
- Spectral Entropy (disorder)
- Total Energy
- Energy in 4 frequency bands:
  - 0-5 Hz (low frequency)
  - 5-50 Hz (modal region)
  - 50-200 Hz (mid frequency)
  - 200-450 Hz (high frequency)
- Peak Frequency
- Peak Power

**Wavelet Features (4 features × 5 sensors = 20 features):**
- Energy in wavelet decomposition levels:
  - D1 (high frequency detail)
  - D2 (mid frequency detail)
  - D3 (low frequency detail)
  - A3 (approximation)

**Aggregated Features (4 features):**
- Mean RMS across sensors
- Std RMS across sensors
- Mean peak frequency
- Std peak frequency

### What Anomalies Look Like

**Normal Structure** (~8 hours after construction):
```
- Stable peaks at modal frequencies (12.5, 24.3, 48.1 Hz)
- Consistent RMS levels per sensor
- Low spectral entropy (organized)
- Anomaly Score: 0.1-0.3
```

**Potentially Anomalous**:
```
- Frequency shifts (> 5% change)
- RMS increase on specific sensors (> 1.5× baseline)
- High spectral entropy (chaotic)
- High kurtosis (impulsive impacts)
- Anomaly Score: 0.6-1.0
```

---

## 🔧 Production Configuration

### Recommended Settings for Iron Structure

```python
# backend/config.py

# ML Model Settings
LIVE_BUFFER_DURATION_SEC = 120
PSD_WINDOW_SIZE_SEC = 8
METRICS_UPDATE_RATE_HZ = 1

# Anomaly Detection
CONTAMINATION_RATE = 0.1  # 10% of training data as reference
ANOMALY_THRESHOLD = 0.60  # Moderate sensitivity

# Alert Thresholds
JITTER_THRESHOLD_MS = 5.0
FREQ_SHIFT_ALERT_PERCENT = 5.0
ENERGY_ANOMALY_THRESHOLD = 0.7
ML_ANOMALY_ALERT_THRESHOLD = 0.60
```

### Monitoring Checklist

Daily:
- [ ] Backend running with ML detector loaded
- [ ] Live dashboard accessible
- [ ] Anomaly scores in normal range (0.1-0.3)
- [ ] No false positive alerts

Weekly:
- [ ] Review alert history
- [ ] Check model predictions consistency
- [ ] Verify no sensor drift
- [ ] Validate against field observations

---

## 📈 Example Dashboard Output

### Overview Tab with ML Scores

```
Live Time-Series (Last 10s)
[Chart with 5 sensor lines]

Quality Control
├─ Jitter: 0.8ms ✓
├─ Clipping: 0/5 sensors ✓
└─ SNR: 36.2 dB ✓

🤖 ML ANOMALY DETECTION
├─ Anomaly Score: 0.18 (LOW RISK)
├─ Confidence: 0.85
├─ Isolation Forest: 0.15
├─ Autoencoder: 0.21
└─ Status: ✓ Normal
```

---

## 🚨 Alert Types & Actions

| Alert | Cause | Action |
|-------|-------|--------|
| **ML Anomaly** | Score > 0.60 | Investigate structure visually |
| **Frequency Shift** | Δf > 5% | Check for loose connections |
| **Energy Spike** | Sensor RMS > 1.5× | Verify sensor calibration |
| **Clipping** | ADC saturation | Reduce sensor gain |
| **High Jitter** | Timing variance | Check network/USB |

---

## 🎓 Next Steps After Day 10

1. **Continue Live Monitoring**: Model learns and adapts
2. **Document Anomalies**: Record any real issues with timestamps
3. **Retrain Periodically**: Every 30 days with new baseline
4. **Add Annotations**: Mark events in dashboard for learning
5. **Export Reports**: Download incident windows for analysis

---

## 📞 Support & Debugging

### Model Not Loading

```bash
# Check if models exist
ls -la backend/ml_models/trained/

# If empty, training failed
python3 tools/train_ml_models.py --baseline-dir data/baseline --verify
```

### Constant False Positives

```python
# backend/ml_models/anomaly_detector.py, line ~235
anomaly_threshold = 0.70  # Increase from 0.60 to be more conservative
```

### Constant False Negatives

```python
anomaly_threshold = 0.50  # Decrease to be more sensitive
```

### Retraining After Finding Issues

```bash
# Collect new 3-day baseline after structural repairs
python3 tools/baseline_collector.py --duration 3d --structure-name "After Repair"

# Train new model
python3 tools/train_ml_models.py --baseline-dir data/baseline
```

---

## Summary

✅ **Days 1-3**: Collect baseline (72 hours of healthy data)  
✅ **Days 3-5**: Train hybrid ML models (Isolation Forest + Autoencoder)  
✅ **Days 5-7**: Deploy models and verify in live dashboard  
✅ **Days 7-10**: Monitor, validate, and fine-tune  

**Result**: Production-ready anomaly detection system for your iron structure with ML-powered predictions! 🎉

---

**Last Updated**: January 12, 2026  
**Model Type**: Hybrid (Isolation Forest + Autoencoder)  
**Target Sensitivity**: Moderate  
**Structure**: Iron 3-Story Building

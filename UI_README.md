# HEXAGON Structural Health - Desktop IDE

**Professional PyQt5 Real-Time Monitoring Application**

A standalone Python desktop application for real-time structural health monitoring with Arduino sensor data collection and analysis.

---

## 🚀 Features

### Real-Time Data Collection
- **Live Serial Connection**: Connect to Arduino via USB serial port
- **Multi-Sensor Support**: Monitor 2 sensors with XYZ accelerometers (6 channels)
- **Real-Time Visualization**: Live graphs with auto-scaling
- **50+ Computed Parameters**: Automatically calculated metrics displayed in real-time

### Parameter Categories

#### Time-Domain Parameters (Per Axis)
- RMS (Root Mean Square)
- Peak Value
- Mean & Standard Deviation
- Variance & Range
- Crest Factor
- Skewness & Kurtosis
- Energy

#### Frequency-Domain Parameters
- Dominant Frequency Detection
- Spectral Energy
- Peak Count
- Power Spectrum Analysis

#### Correlation Analysis
- Inter-axis correlation (XY, XZ, YZ)
- Cross-sensor correlation
- Magnitude correlation

### Data Recording & Export
- **CSV Export**: Clean CSV format WITHOUT timestamps (as requested)
  - Columns: S1_X, S1_Y, S1_Z, S2_X, S2_Y, S2_Z
  - One row per sample
  - Ready for analysis
  
- **JSON Export**: Complete analysis with all parameters
  - All 50+ parameters saved
  - With metadata and timestamps
  - For detailed post-processing

- **Flexible Export Location**: Choose where to save data

### Professional Interface
- **Dark theme** for extended monitoring sessions
- **Tabbed interface** organizing 50+ parameters
- **Real-time graphs** with pyqtgraph
- **Progress tracking** during recording
- **Session management** with sample counting

---

## 📋 System Requirements

- Python 3.8+
- PyQt5 (GUI framework)
- pyqtgraph (Real-time plotting)
- NumPy & SciPy (Signal processing)
- pySerial (Serial communication)
- Arduino with ADXL345 sensors or compatible accelerometer

---

## 🔧 Installation

### Option 1: Automatic Setup (Linux/Mac)

```bash
cd structural-repair-web
chmod +x launch_ui.sh
./launch_ui.sh
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv ui_env
source ui_env/bin/activate  # On Windows: ui_env\Scripts\activate

# Install dependencies
pip install -r ui_requirements.txt

# Run application
python3 ui_main.py
```

### Option 3: System-wide Installation

```bash
sudo pip install -r ui_requirements.txt
python3 ui_main.py
```

---

## 🎮 Usage Guide

### 1. Connect to Arduino

1. Connect Arduino via USB
2. Click **"🔄 Refresh"** to detect available ports
3. Select the correct COM port from dropdown
4. Verify baudrate (default: 115200)
5. Click **"🔌 Connect"** button
6. Status should show **"✅ Connected"**

### 2. Monitor Real-Time Data

The application automatically:
- Displays live sensor data in graphs (tab: "📈 Live Data")
- Calculates 50+ parameters continuously
- Updates every 100ms

**View parameters by category:**
- **⏱️ Time-Domain**: RMS, Peak, Mean, Std, Crest, etc.
- **📡 Frequency-Domain**: Dominant frequencies, spectral energy
- **🔗 Correlation**: Sensor-to-sensor and axis-to-axis relationships
- **📊 All Parameters**: Complete list of all 50+ metrics

### 3. Record Data

1. Click **"🔴 Start Recording"** to begin capture
2. Monitor:
   - Sample count (bottom left)
   - Recording duration (HH:MM:SS format)
   - Progress bar showing buffer usage
3. Click **"⏹️ Stop Recording"** when done

### 4. Export Data

#### Export CSV (No Timestamp)
1. Select export format: **"CSV (No Timestamp)"**
2. Choose export location (click **"📁 Browse"**)
3. Click **"💾 Export Data"**
4. CSV file created: `structural_health_YYYYMMDD_HHMMSS.csv`

**CSV Format:**
```
S1_X,S1_Y,S1_Z,S2_X,S2_Y,S2_Z
0.125,-0.087,0.234,0.156,-0.098,0.267
0.134,-0.092,0.241,0.162,-0.103,0.274
...
```

#### Export JSON (With Analysis)
1. Select format: **"JSON"**
2. Click **"💾 Export Data"**
3. JSON file created: `structural_health_YYYYMMDD_HHMMSS_analysis.json`

**JSON Format:**
```json
{
  "timestamp": "2026-01-16T13:45:30.123456",
  "samples": 5000,
  "parameters": {
    "s1_x_rms": 0.245,
    "s1_x_peak": 1.234,
    "s1_x_mean": -0.015,
    ...
    "corr_s1s2_mag": 0.782
  }
}
```

#### Export Both Formats
1. Select format: **"Both"**
2. Both CSV and JSON files will be created

### 5. Analyze Data

**Online Analysis:**
1. Export CSV file
2. Upload to HEXAGON website at `http://localhost:5174`
3. Website performs detailed analysis and generates reports

**Offline Analysis:**
- Use exported JSON for custom Python scripts
- Import CSV into Excel/Pandas for statistical analysis
- CSV format is Excel-compatible

---

## 📊 50+ Parameters Explained

### Time-Domain (Per Sensor, Per Axis)

| Parameter | Definition | Use Case |
|-----------|-----------|----------|
| RMS | Root mean square | Overall vibration energy |
| Peak | Maximum absolute value | Shock detection |
| Mean | Average value | Offset/bias |
| Std Dev | Standard deviation | Variability |
| Crest Factor | Peak / RMS | Impulsiveness detection |
| Skewness | Distribution asymmetry | Wear/damage indicator |
| Kurtosis | Distribution peakedness | Fault signatures |
| Energy | Sum of squared values | Total energy content |

### Frequency-Domain

| Parameter | Definition | Use Case |
|-----------|-----------|----------|
| Dominant Freq | Highest amplitude frequency | Resonance identification |
| Spectral Energy | Total power in spectrum | Frequency content |
| Num Peaks | Number of significant peaks | Pattern recognition |

### Correlation Metrics

| Parameter | Definition | Use Case |
|-----------|-----------|----------|
| Intra-axis Corr | XY, XZ, YZ correlation | Axis dependencies |
| Cross-sensor Corr | Sensor 1 vs Sensor 2 | Structural coherence |

---

## ⚙️ Configuration

### Arduino Serial Settings
- **Baudrate**: 115200 (default, adjustable)
- **Data Format**: Comma-separated values: `S1X,S1Y,S1Z,S2X,S2Y,S2Z\n`
- **Sampling Rate**: 50 Hz (configurable in code)

### Buffer Settings
- **Display Buffer**: 500 samples (shown on graph)
- **Calculation Buffer**: 1000 samples (for parameter computation)

### Update Rate
- **Display Update**: 100ms (10 Hz)
- **Graph Refresh**: Real-time

---

## 🔌 Arduino Integration

### Expected Serial Format

```
0.125,-0.087,0.234,0.156,-0.098,0.267\n
0.134,-0.092,0.241,0.162,-0.103,0.274\n
```

### Compatible Arduino Code
```cpp
void loop() {
  float s1x = readSensor1X();
  float s1y = readSensor1Y();
  float s1z = readSensor1Z();
  float s2x = readSensor2X();
  float s2y = readSensor2Y();
  float s2z = readSensor2Z();
  
  Serial.print(s1x); Serial.print(",");
  Serial.print(s1y); Serial.print(",");
  Serial.print(s1z); Serial.print(",");
  Serial.print(s2x); Serial.print(",");
  Serial.print(s2y); Serial.print(",");
  Serial.println(s2z);
  
  delay(20); // 50 Hz sampling
}
```

---

## 🐛 Troubleshooting

### No Ports Found
**Problem**: "No ports found" in port dropdown
**Solutions**:
- Check USB cable connection
- Install Arduino USB drivers
- Try different USB port
- Restart application

### Connection Fails
**Problem**: Status shows "❌ Disconnected"
**Solutions**:
- Verify baudrate matches Arduino (115200)
- Check if Arduino is properly programmed
- Try different baudrate (9600, 38400)
- Look at Arduino serial output with separate terminal

### Graphs Not Updating
**Problem**: Live data graph is empty
**Solutions**:
- Ensure Arduino is sending data
- Check serial port selection
- Verify data format matches expected format
- Monitor console for errors

### Export Fails
**Problem**: "Error exporting data"
**Solutions**:
- Check write permissions on export directory
- Ensure sufficient disk space
- Verify export path exists
- Try different export location

---

## 📈 Performance Notes

- Real-time updating at 100ms intervals
- 50+ parameters calculated in real-time
- Handles up to 1000 samples in memory buffer
- Efficient NumPy-based calculations
- Dark theme reduces eye strain for long sessions

---

## 🔗 Integration with Website

### Workflow

1. **Desktop App** (This UI)
   - Collects real-time data
   - Exports CSV file

2. **Website** (http://localhost:5174)
   - Upload CSV file
   - Performs advanced analysis
   - Generates comprehensive reports
   - Provides 3D visualizations

---

## 📝 File Outputs

### CSV Output Format (No Timestamp)
```
structural_health_20260116_134530.csv
- Size: ~2-5 MB per hour of data
- Columns: 6 (S1_X, S1_Y, S1_Z, S2_X, S2_Y, S2_Z)
- Rows: One per sample
```

### JSON Output Format
```
structural_health_20260116_134530_analysis.json
- Size: ~100-200 KB
- Contains: All 50+ parameters
- Metadata: Timestamp, sample count
```

---

## 🚀 Advanced Features

### Auto-Scaling Graphs
Enable in Display options for automatic Y-axis adjustment

### Show Magnitude
Toggle to display combined sensor magnitude (√(X² + Y² + Z²))

### Custom Export Location
Browse and select any directory for data export

---

## 📞 Support

For issues or feature requests, check:
1. Console output for error messages
2. Status bar for connection status
3. Parameter tables for data validation

---

## 📄 License

Part of HEXAGON Structural Health Monitoring System

---

## 🎯 Next Steps

1. ✅ Connect Arduino and verify data
2. ✅ Record baseline/reference data
3. ✅ Export and analyze on website
4. ✅ Compare structural conditions over time
5. ✅ Generate maintenance reports

**Happy monitoring! 🚀**

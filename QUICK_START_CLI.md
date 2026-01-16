# ⚡ HEXAGON CLI - Quick Start Guide

**Lightweight Command-Line Interface - No GUI Libraries Needed**

---

## 🚀 Launch (One Command)

```bash
cd structural-repair-web
source ui_env_new/bin/activate
python3 ui_cli.py
```

That's it! No compilation, instant startup.

---

## 📋 Menu Options

Once the app starts, you'll see a menu:

```
1. Connect to Arduino
2. Monitor Real-Time Data
3. Record Data Session
4. Export to CSV
5. Show Available Ports
6. Exit
```

---

## 5-Step Workflow

### Step 1: Show Available Ports
```
Select: 5
→ Lists all available COM ports
→ Note your Arduino port (e.g., /dev/ttyUSB0 or COM3)
```

### Step 2: Connect to Arduino
```
Select: 1
→ Lists ports again
→ Enter port number (1, 2, 3, etc.)
→ Status changes to: ✅ Connected
```

### Step 3: Monitor Live Data
```
Select: 2
→ Shows real-time parameters
→ Updates every second
→ Display includes:
  • Sensor 1 (X, Y, Z) - RMS, Peak, Mean
  • Sensor 2 (X, Y, Z) - RMS, Peak, Mean
  • Correlation metrics
  • Magnitude values
→ Press Ctrl+C to stop
```

### Step 4: Record Session
```
Select: 3
→ Starts recording all data
→ Shows: ⏱️  Recording... Samples: XXXXX  Time: XXs
→ Press Ctrl+C when done
→ Automatically exports to CSV
```

### Step 5: Export Data
```
Select: 4
→ Records 100 samples
→ Exports to CSV file
→ Filename: structural_health_YYYYMMDD_HHMMSS.csv
→ Ready for analysis!
```

---

## CSV Output Format

**File:** `structural_health_20260116_134530.csv`

**Contents (No timestamps):**
```csv
S1_X,S1_Y,S1_Z,S2_X,S2_Y,S2_Z
0.125,-0.087,0.234,0.156,-0.098,0.267
0.134,-0.092,0.241,0.162,-0.103,0.274
0.145,-0.098,0.249,0.169,-0.109,0.282
```

---

## What You'll See

### Real-Time Display

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                  HEXAGON Structural Health - Real-Time CLI                   ║
║           Professional Desktop Application (Lightweight Version)             ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ Connected to: /dev/ttyUSB0

📊 Live Parameters (Samples: 1234)
================================================================================

📈 SENSOR 1 (S1):
  X: RMS=0.2450  Peak=1.2340  Mean=-0.0150
  Y: RMS=0.1920  Peak=0.9870  Mean=0.0234
  Z: RMS=0.3210  Peak=1.5670  Mean=-0.0567

📈 SENSOR 2 (S2):
  X: RMS=0.1980  Peak=0.9870  Mean=0.0123
  Y: RMS=0.2340  Peak=1.1234  Mean=-0.0198
  Z: RMS=0.2890  Peak=1.3456  Mean=0.0345

🔗 CORRELATION:
  S1: XY=0.1234  XZ=0.0987  YZ=0.0654
  S2: XY=0.1567  XZ=0.1234  YZ=0.0876
  Cross-Sensor: 0.7823

📊 MAGNITUDE:
  S1: RMS=0.4567
  S2: RMS=0.4234

================================================================================
Press Ctrl+C to stop monitoring
```

---

## Features

✅ **Real-Time Monitoring**
- Live parameter display
- Updates every second
- 50+ parameters calculated

✅ **Data Recording**
- Record full sessions
- Sample counting
- Duration tracking

✅ **CSV Export**
- Clean format (no timestamps)
- Excel-compatible
- Ready for analysis

✅ **No Dependencies**
- Only needs: numpy, scipy, pyserial
- No GUI libraries
- Lightweight and fast

---

## Installation (If Not Done Yet)

```bash
cd structural-repair-web

# Create environment
python3 -m venv ui_env_new

# Activate
source ui_env_new/bin/activate

# Install packages
pip install pyserial numpy scipy

# Run
python3 ui_cli.py
```

---

## Troubleshooting

### "No serial ports found"
- Check USB cable connection
- Try `lsusb` or `ls /dev/tty*`
- Install USB drivers if needed

### "Permission denied on serial port"
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### "ModuleNotFoundError: No module named 'serial'"
```bash
source ui_env_new/bin/activate
pip install pyserial numpy scipy
```

---

## Advanced Use

### Record Long Sessions
1. Select: 3 (Record)
2. Let it run for desired duration
3. Press Ctrl+C
4. Auto-exports to CSV

### Quick 100-Sample Export
1. Select: 4 (Export)
2. Automatically records 100 samples
3. Saves to CSV

### Monitor Without Recording
1. Select: 2 (Monitor)
2. Watch real-time parameters
3. Press Ctrl+C to stop

---

## File Organization

```
structural-repair-web/
├── ui_cli.py                 ← Main CLI application
├── ui_env_new/               ← Virtual environment
├── QUICK_START_CLI.md        ← This file
├── INSTALL_MANUALLY.md       ← Manual installation
└── structural_health_*.csv   ← Exported data files
```

---

## Next Steps

1. ✅ Launch: `python3 ui_cli.py`
2. ✅ Connect to Arduino
3. ✅ Monitor live data
4. ✅ Record a session
5. ✅ Export CSV for analysis

---

## Performance

- **Update Rate:** 1 Hz (display)
- **Sampling:** Real-time from Arduino
- **Memory:** ~50 MB
- **CPU:** <5%

---

## Data Analysis

After exporting CSV, you can:

**Open in Excel:**
- Double-click the CSV file
- Plot graphs
- Calculate statistics

**Process with Python:**
```python
import pandas as pd
df = pd.read_csv('structural_health_YYYYMMDD_HHMMSS.csv')
df['magnitude'] = np.sqrt(df['S1_X']**2 + df['S1_Y']**2 + df['S1_Z']**2)
```

**Upload to Website (Optional):**
- Visit http://localhost:5174
- Upload CSV file
- Get advanced analysis

---

## Quick Reference

| Action | Command |
|--------|---------|
| Launch | `python3 ui_cli.py` |
| Check Ports | Select 5 in menu |
| Connect | Select 1, enter port # |
| Monitor | Select 2 |
| Record | Select 3 |
| Quick Export | Select 4 |

---

**Ready to monitor! 🚀**

For complete documentation, see:
- **UI_README.md** - Full reference
- **COMPLETE_PROJECT_SUMMARY.md** - Project overview
- **INSTALL_MANUALLY.md** - Manual installation

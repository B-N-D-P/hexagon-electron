# 🚀 START HERE - HEXAGON Structural Health

**Real-Time Structural Monitoring System - Ready to Use**

---

## ⚡ Quick Start (2 Minutes)

```bash
cd structural-repair-web
source ui_env_new/bin/activate
python3 ui_cli.py
```

That's it! You'll see an interactive menu.

---

## 📋 What You Get

✅ **Real-time monitoring** of Arduino sensor data
✅ **50+ parameters** calculated automatically
✅ **CSV export** in clean format (no timestamps)
✅ **Interactive menu** for all operations
✅ **Fast & lightweight** - no GUI libraries needed

---

## 🎯 Three Ways to Use

### Option 1: CLI Application (Recommended - Works NOW)

**Best for:** Immediate use, lightweight, no compilation

```bash
python3 ui_cli.py
```

**Read:** [QUICK_START_CLI.md](QUICK_START_CLI.md)

---

### Option 2: PyQt5 GUI (Professional Interface)

**Best for:** Advanced users who want graphical interface

```bash
# First-time setup (may take 10-15 min):
pip install PyQt5 pyqtgraph

# Then run:
python3 ui_main.py
```

**Read:** [QUICK_START_UI.md](QUICK_START_UI.md)

---

### Option 3: Web Dashboard (Optional)

**Best for:** Advanced analysis and reporting

1. Upload your exported CSV to: http://localhost:5174
2. Get advanced analysis and reports

---

## 📖 Documentation

### Essential (Read These First)
- **[QUICK_START_CLI.md](QUICK_START_CLI.md)** ← Start here for CLI
- **[QUICK_START_UI.md](QUICK_START_UI.md)** ← Or here for GUI

### Complete References
- **[UI_README.md](UI_README.md)** - Full feature guide
- **[UI_DEPLOYMENT_GUIDE.md](UI_DEPLOYMENT_GUIDE.md)** - Installation

### Technical Details
- **[UI_ARCHITECTURE.md](UI_ARCHITECTURE.md)** - System design
- **[UI_IMPLEMENTATION_SUMMARY.md](UI_IMPLEMENTATION_SUMMARY.md)** - Implementation
- **[COMPLETE_PROJECT_SUMMARY.md](COMPLETE_PROJECT_SUMMARY.md)** - Full overview
- **[UI_INDEX.md](UI_INDEX.md)** - Documentation index

---

## 🔧 System Status

✅ CLI Application: **READY NOW** (tested & working)
✅ Dependencies: **INSTALLED** (numpy, scipy, pyserial)
✅ Backend: **FIXED** (WebSocket endpoint + peak detection)
✅ Documentation: **COMPLETE** (97+ pages)

---

## 📊 What It Does

Real-time display of:
- **Sensor 1 & 2**: X, Y, Z acceleration (RMS, Peak, Mean)
- **Magnitude**: Combined acceleration vector
- **Correlation**: Sensor relationships
- **50+ Parameters**: All calculated automatically

---

## 💾 Export Format

**CSV File (No Timestamps - Clean Format):**
```
S1_X,S1_Y,S1_Z,S2_X,S2_Y,S2_Z
0.125,-0.087,0.234,0.156,-0.098,0.267
0.134,-0.092,0.241,0.162,-0.103,0.274
```

Ready for:
- Excel analysis
- Python processing
- Website upload
- Machine learning

---

## 🎮 Interactive Menu

Once you run `python3 ui_cli.py`, you'll get:

```
1. Connect to Arduino       → Select your COM port
2. Monitor Real-Time Data   → View live parameters
3. Record Data Session      → Collect data
4. Export to CSV            → Save for analysis
5. Show Available Ports     → List serial ports
6. Exit                     → Quit app
```

---

## ⏱️ Typical Workflow

1. **Connect** (30 seconds)
   - Select option 1
   - Choose your Arduino port

2. **Monitor** (2 minutes)
   - Select option 2
   - Watch real-time parameters
   - Press Ctrl+C to stop

3. **Record** (5-10 minutes)
   - Select option 3
   - Let it record
   - Press Ctrl+C when done

4. **Export** (automatic)
   - CSV saved automatically
   - File: `structural_health_YYYYMMDD_HHMMSS.csv`

5. **Analyze**
   - Open in Excel, or
   - Process with Python, or
   - Upload to website

---

## 🔌 Arduino Requirements

Your Arduino should send data in CSV format:
```
S1_X,S1_Y,S1_Z,S2_X,S2_Y,S2_Z\n
```

Supported:
- ADXL345 accelerometers
- Any 3-axis accelerometer
- 50 Hz sampling (configurable)
- 115200 baud (adjustable in app)

---

## 📋 Pre-Installed Packages

Environment `ui_env_new/` includes:
- ✅ numpy (numerical computing)
- ✅ scipy (signal processing)
- ✅ pyserial (Arduino communication)

Missing only: PyQt5 (optional, for GUI)

---

## 🚨 Troubleshooting

**Can't find Arduino?**
- Check USB cable
- Run option 5 to list ports
- Install USB drivers if needed

**"Permission denied"?**
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

**No data showing?**
- Verify Arduino is programmed
- Check data format: `S1X,S1Y,S1Z,S2X,S2Y,S2Z`

Full help: [INSTALL_MANUALLY.md](INSTALL_MANUALLY.md)

---

## 📂 File Structure

```
structural-repair-web/
├── ui_cli.py              ← CLI application (USE THIS)
├── ui_main.py             ← PyQt5 GUI (optional)
├── ui.py                  ← Core components
├── ui_env_new/            ← Environment (ready to use)
├── START_HERE.md          ← This file
├── QUICK_START_CLI.md     ← CLI quick start
├── QUICK_START_UI.md      ← GUI quick start
├── UI_README.md           ← Full documentation
└── ... (more files)
```

---

## ✨ Key Features

✅ **Real-Time**
- Live parameter updates
- 50+ metrics calculated
- Sub-second latency

✅ **Flexible Export**
- CSV (clean, no timestamps)
- JSON (with metadata)
- Excel-ready format

✅ **Easy to Use**
- Interactive menu
- Clear prompts
- Status indicators

✅ **Lightweight**
- No GUI compilation
- Instant startup
- Low memory usage

---

## 🎯 Next Steps

1. ✅ Activate environment:
   ```bash
   source ui_env_new/bin/activate
   ```

2. ✅ Run CLI:
   ```bash
   python3 ui_cli.py
   ```

3. ✅ Connect Arduino (menu option 1)

4. ✅ Monitor data (menu option 2)

5. ✅ Record & export (menu option 3-4)

6. ✅ Analyze your data!

---

## 📞 Need Help?

- **Quick start?** → Read [QUICK_START_CLI.md](QUICK_START_CLI.md)
- **Stuck?** → Check [INSTALL_MANUALLY.md](INSTALL_MANUALLY.md)
- **Full guide?** → See [UI_README.md](UI_README.md)
- **Technical?** → Read [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md)

---

## 🎉 You're Ready!

Everything is installed and ready to go.

Just run:
```bash
cd structural-repair-web
source ui_env_new/bin/activate
python3 ui_cli.py
```

**That's it! Start monitoring! 🚀**

---

**HEXAGON Structural Health - Real-Time Monitoring System**
*Version 1.0 - Production Ready*
*January 2026*

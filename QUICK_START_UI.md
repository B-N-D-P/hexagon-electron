# ⚡ HEXAGON UI - Quick Start (5 Minutes)

## Step 1: Install & Launch (1 min)

```bash
cd structural-repair-web
chmod +x launch_ui.sh
./launch_ui.sh
```

**On Windows:**
```bash
python -m venv ui_env
ui_env\Scripts\activate
pip install -r ui_requirements.txt
python ui_main.py
```

---

## Step 2: Connect Arduino (1 min)

1. **Plug in Arduino** via USB
2. Click **"🔄 Refresh"** → Select COM port
3. Click **"🔌 Connect"** → Wait for **"✅ Connected"**

✅ You should see live data in graphs

---

## Step 3: Monitor Live Data (1 min)

**Tabs show real-time parameters:**
- 📈 **Live Data**: Waveform graphs
- ⏱️ **Time-Domain**: RMS, Peak, Mean, Std, etc.
- 📡 **Frequency-Domain**: Dominant frequencies
- 🔗 **Correlation**: Sensor relationships
- 📊 **All Parameters**: Full list of 50+

---

## Step 4: Record Data (1 min)

1. Click **"🔴 Start Recording"**
2. Let it run (30 seconds to few minutes)
3. Click **"⏹️ Stop Recording"**

✅ Data saved in memory

---

## Step 5: Export CSV (1 min)

1. Select format: **"CSV (No Timestamp)"**
2. Click **"📁 Browse"** → Choose location (e.g., Desktop)
3. Click **"💾 Export Data"**

✅ File saved: `structural_health_YYYYMMDD_HHMMSS.csv`

**CSV Format (ready for analysis):**
```
S1_X,S1_Y,S1_Z,S2_X,S2_Y,S2_Z
0.125,-0.087,0.234,0.156,-0.098,0.267
0.134,-0.092,0.241,0.162,-0.103,0.274
```

---

## What's Happening?

| Component | What It Does |
|-----------|-------------|
| **Live Graphs** | Shows raw sensor data in real-time |
| **50+ Parameters** | Computed automatically every 100ms |
| **Time-Domain Tab** | RMS, Peak, Crest Factor, etc. |
| **Frequency Tab** | Dominant frequencies & power |
| **Correlation Tab** | How sensors relate to each other |
| **CSV Export** | Clean data for analysis |

---

## Next: Analyze Data

**Upload CSV to HEXAGON Website:**
1. Go to `http://localhost:5174`
2. Click "Upload Data"
3. Select your CSV file
4. Get detailed analysis & reports

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No COM ports | Restart Arduino, check drivers |
| Can't connect | Try different baudrate (115200) |
| No data in graphs | Verify Arduino is sending data |
| Export fails | Check write permissions on export folder |

---

## Key Features

✅ Real-time 50+ parameter calculation
✅ Professional dark theme UI
✅ Clean CSV export (no timestamps)
✅ Multi-sensor support
✅ Automatic frequency analysis
✅ Correlation analysis

---

**That's it! You're monitoring structural health in real-time! 🚀**

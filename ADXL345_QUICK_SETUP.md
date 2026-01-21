# ADXL345 Synchronized Dual Sensor - Quick Setup

## ⚡ 5-Minute Setup

### Hardware Checklist
- [ ] Arduino UNO
- [ ] 2x ADXL345 sensors
- [ ] 2x 4.7kΩ resistors (I2C pull-ups)
- [ ] 2x 0.1µF capacitors (decoupling)
- [ ] Breadboard & jumper wires
- [ ] USB cable

### Wiring (Essential)

```
ARDUINO UNO              ADXL345-1 (0x53)      ADXL345-2 (0x1D)
    5V ───────────────────→ VCC                  VCC ←───────
   GND ───────────────────→ GND                  GND ←───────
    A4 ───────────────────→ SDA                  SDA ←───────
    A5 ───────────────────→ SCL                  SCL ←───────
              ┌────────────→ SDO → GND
              │ 
              └────────────→ SDO → 5V
```

### Pull-up Resistors
```
    5V
     │
    [4.7kΩ]
     │
     ├─── A4 (SDA)
     │
    [4.7kΩ]
     │
     └─── A5 (SCL)
```

### Quick Connection Steps

1. **Power the sensors:**
   - VCC from both sensors → 5V pin (Arduino)
   - GND from both sensors → GND pin (Arduino)

2. **Connect I2C bus (shared):**
   - SDA from both sensors → A4 (Arduino)
   - SCL from both sensors → A5 (Arduino)
   - Add 4.7kΩ pull-up resistors on SDA and SCL

3. **Set I2C addresses (different SDO levels):**
   - Sensor 1: SDO → GND (address will be 0x53)
   - Sensor 2: SDO → 5V (address will be 0x1D)

4. **Add capacitors (recommended):**
   - 0.1µF capacitor between VCC and GND of each sensor

5. **Verify connections:**
   - No loose wires
   - Proper I2C addresses set by SDO pins
   - All ground connections solid

---

## 🚀 Upload & Test

### Step 1: Upload Code
```
1. Open Arduino IDE
2. Paste code from: arduino_sketch_dual_adxl345_synchronized.ino
3. Tools → Board → Arduino UNO
4. Tools → Port → (select your COM port)
5. Click Upload
```

### Step 2: Test Sensors
```
1. Tools → Serial Monitor
2. Set baud to 115200 (bottom right)
3. Should see: "✓ Connected" for both sensors
4. Type any character and press Enter to start
5. Watch data flow for 30 seconds
```

### Step 3: Expected Output
```
Sensor Status:
  Sensor 1 (0x53): ✓ Connected
  Sensor 2 (0x1D): ✓ Connected

Timestamp_ms,S1_X_g,S1_Y_g,S1_Z_g,S2_X_g,S2_Y_g,S2_Z_g
0,0.0234,0.0145,-0.9854,0.0198,0.0167,-0.9897
20,0.0267,0.0156,-0.9823,0.0212,0.0178,-0.9876
40,0.0245,0.0134,-0.9876,0.0189,0.0156,-0.9898
```

---

## 📊 Collect Data

### Method 1: Copy from Serial Monitor (Easiest)
```
1. Run for 30 seconds (data will auto-collect)
2. Right-click in Serial Monitor → Select All
3. Ctrl+C to copy
4. Open Notepad
5. Paste and save as "data.csv"
```

### Method 2: Save Directly (Advanced)
```bash
# Windows
mode COM3:115200,N,8,1
```

---

## ✅ Validate Data

```bash
# Run validator
python3 pre_analysis_validator.py data.csv

# Should show:
# ✅ Status: PASSED
```

---

## 🔧 Troubleshooting Quick Fix

| Problem | Fix |
|---------|-----|
| "Sensors not detected" | Check I2C wires on A4/A5, verify SDO pins |
| Noisy data | Add 0.1µF capacitors near sensor power |
| Data gaps | Ensure 115200 baud rate in serial monitor |
| Still getting sync error | Check both sensors in SAME loop (they are!) |

---

## 📋 Configuration Options

### Change Sampling Rate
Find in code:
```cpp
#define SAMPLE_INTERVAL_MS 20   // Change this for different Hz
```

Common rates:
- 20 ms = 50 Hz (default) ✅ RECOMMENDED
- 10 ms = 100 Hz
- 40 ms = 25 Hz

### Change Duration
Find in code:
```cpp
#define COLLECTION_TIME_MS 30000   // Change to different duration
```

- 30000 = 30 seconds (default) ✅ RECOMMENDED
- 60000 = 60 seconds
- 10000 = 10 seconds

---

## 📝 Wiring Checklist

```
Arduino UNO Pins:
[ ] 5V connected to sensor VCC
[ ] GND connected to sensor GND  
[ ] A4 (SDA) connected to both sensors SDA + 4.7kΩ pull-up
[ ] A5 (SCL) connected to both sensors SCL + 4.7kΩ pull-up

ADXL345 Sensor 1:
[ ] VCC → 5V
[ ] GND → GND
[ ] SDA → A4
[ ] SCL → A5
[ ] SDO → GND (sets address to 0x53)

ADXL345 Sensor 2:
[ ] VCC → 5V
[ ] GND → GND
[ ] SDA → A4
[ ] SCL → A5
[ ] SDO → 5V (sets address to 0x1D)

Additional:
[ ] 0.1µF capacitor on Sensor 1 (VCC-GND)
[ ] 0.1µF capacitor on Sensor 2 (VCC-GND)
[ ] 4.7kΩ resistor on SDA pull-up
[ ] 4.7kΩ resistor on SCL pull-up
```

---

## 🎯 Complete Workflow

```
1. WIRE hardware ──→ 2. UPLOAD code ──→ 3. TEST sensors ──→ 4. COLLECT data
                                ↓
                        ✓ Connected?
                        │    │
                       YES   NO → Fix wiring
                        │
5. SAVE CSV ──→ 6. VALIDATE ──→ 7. UPLOAD ──→ 8. ANALYZE
                      ↓
                  ✅ PASSED? 
                   │    │
                  YES   NO → Check issues
                   │
                SUCCESS! 🎉
```

---

## 📞 I2C Addresses Explained

```
ADXL345 Has 7 possible I2C addresses:
All use same SDA/SCL bus
Differentiated by SDO pin:

SDO → GND     = 0x53  (Sensor 1 in this setup) ✓
SDO → 5V      = 0x1D  (Sensor 2 in this setup) ✓
SDO → SDA     = 0x1D
SDO → Floating= 0x53

This sketch uses:
  Sensor 1: SDO → GND (0x53)
  Sensor 2: SDO → 5V  (0x1D)
```

---

## 🎓 What This Solves

**Problem You Had:**
```
Analysis failed: Multi-Channel Synchronization Issue Detected.
Peak frequencies appear at different FFT bins.
This suggests channels are sampled asynchronously.
```

**Why This Sketch Fixes It:**
✅ Both sensors read in SAME loop iteration
✅ Fixed 20ms interval (50 Hz) = synchronized sampling
✅ CSV includes timestamps to verify timing
✅ Same I2C bus = same clock source
✅ Data comes out perfectly aligned

**Result:** No more synchronization errors! 🎉

---

## ✨ Key Features

| Feature | Benefit |
|---------|---------|
| Dual I2C addresses | No address conflicts |
| Same I2C bus | Synchronized clock |
| Fixed sample interval | Precise timing |
| Timestamps | Verify synchronization |
| 115200 baud | Fast data transfer |
| CSV output | Ready for analysis |
| Error checking | Sensor verification |

---

## 💾 Next: Process Data

Once you have data.csv:

```bash
# 1. Validate
python3 pre_analysis_validator.py data.csv

# 2. If PASSED, use in analysis
python3 backend/app.py --file data.csv

# 3. Get structural analysis results!
```

---

## 🆘 Common Mistakes

❌ **Don't do:**
- Mix up SDO pins (reversed addresses)
- Forget pull-up resistors (data corruption)
- Use wrong baud rate (garbled serial)
- Skip decoupling caps (noise in data)
- Use loose connections (intermittent failures)

✅ **Do:**
- Double-check all wiring
- Use 4.7kΩ pull-ups
- Set 115200 baud
- Add 0.1µF caps
- Keep connections tight

---

## 📞 Still Having Issues?

1. **Check initialization message** - Are both sensors ✓ Connected?
2. **Verify baud rate** - Must be 115200
3. **Inspect wiring** - Check SDO pins especially
4. **Run I2C scanner** - Verify addresses are 0x53 and 0x1D
5. **Use validator** - Run: `python3 pre_analysis_validator.py data.csv`

---

**Ready to go! Follow the steps above and you'll have synchronized sensor data in minutes.** 🚀

For detailed info, see: `ADXL345_SYNCHRONIZED_SETUP_GUIDE.md`

# Synchronized Dual ADXL345 Sensor Setup Guide

## Overview

This guide explains how to use the **synchronized dual ADXL345 sensor sketch** to collect properly synchronized accelerometer data. This is critical for avoiding the "Multi-Channel Synchronization Issue" in your structural analysis.

---

## Hardware Setup

### Component List

- Arduino UNO microcontroller
- 2x ADXL345 accelerometer modules
- Breadboard or PCB
- I2C pull-up resistors: 2x 4.7kΩ (for SDA and SCL)
- Decoupling capacitors: 2x 0.1µF (near each sensor power pin)
- USB cable for programming and power
- Jumper wires

### Wiring Diagram

```
Arduino UNO                ADXL345 Sensor 1       ADXL345 Sensor 2
─────────                  ──────────────         ──────────────
5V         ─────────────┬─────→ VCC               VCC ←─────┬
                        │
GND        ─────────────┼─────→ GND               GND ←─────┼
                        │
A4 (SDA)   ─────────────┼─────→ SDA               SDA ←─────┼
           (with 4.7kΩ  │
           pull-up)     │
           
A5 (SCL)   ─────────────┼─────→ SCL               SCL ←─────┼
           (with 4.7kΩ  │
           pull-up)     │
                        │
           ─────────→ SDO              GND    (Address: 0x53)
           
           ─────────→ INT1/INT2
           
           ─────────→ SDO              5V     (Address: 0x1D)
           
           ─────────→ INT1/INT2
```

### Pin Connections Detail

**ADXL345 Sensor 1 (Address 0x53):**
- VCC → 5V (Arduino)
- GND → GND (Arduino)
- SDA → A4 (Arduino)
- SCL → A5 (Arduino)
- SDO → GND (Sets I2C address to 0x53)

**ADXL345 Sensor 2 (Address 0x1D):**
- VCC → 5V (Arduino)
- GND → GND (Arduino)
- SDA → A4 (Arduino)
- SCL → A5 (Arduino)
- SDO → 5V (Sets I2C address to 0x1D)

### Important Notes

✅ **Both sensors share the same I2C bus** (SDA, SCL, VCC, GND)
✅ **Different I2C addresses** achieved by different SDO levels
✅ **Pull-up resistors required** on SDA and SCL (4.7kΩ typical)
✅ **Decoupling capacitors** near power pins reduce noise
✅ **All connections must be solid** for synchronization to work

---

## Software Setup

### Step 1: Install Arduino IDE

Download from: https://www.arduino.cc/en/software

### Step 2: Select Board and Port

1. Open Arduino IDE
2. Tools → Board → Select "Arduino UNO"
3. Tools → Port → Select your COM port (e.g., COM3 or /dev/ttyUSB0)
4. Tools → Serial Monitor Speed → 115200

### Step 3: Upload the Sketch

1. Copy the code from `arduino_sketch_dual_adxl345_synchronized.ino`
2. Paste into Arduino IDE
3. Click Upload (or Ctrl+U)
4. Wait for "Done uploading" message

### Step 4: Open Serial Monitor

1. Tools → Serial Monitor
2. Select 115200 baud rate (bottom right)
3. You should see initialization messages

---

## Using the System

### Starting Data Collection

1. **Open Serial Monitor** (Tools → Serial Monitor, 115200 baud)

2. **Wait for initialization message:**
   ```
   ==========================================
   SYNCHRONIZED DUAL ADXL345 SENSOR SYSTEM
   ==========================================
   
   Initializing sensors...
   
   Sensor Status:
     Sensor 1 (0x53): ✓ Connected
     Sensor 2 (0x1D): ✓ Connected
   
   Configuration:
     Sampling Rate: 50 Hz
     Sample Interval: 20 ms
     Range: ±16g
     Resolution: Full (13-bit)
   
   Ready to record!
   Send any character via serial to START recording (30 seconds)
   ```

3. **Send any character** to start recording (type anything and press Enter)

4. **Data collection begins:**
   ```
   ==========================================
   RECORDING STARTED
   Duration: 30 seconds
   Expected samples: ~1500
   ==========================================
   
   Timestamp_ms,S1_X_g,S1_Y_g,S1_Z_g,S2_X_g,S2_Y_g,S2_Z_g
   0,0.0234,0.0145,-0.9854,0.0198,0.0167,-0.9897
   20,0.0267,0.0156,-0.9823,0.0212,0.0178,-0.9876
   40,0.0245,0.0134,-0.9876,0.0189,0.0156,-0.9898
   ...
   ```

5. **Collection completes after 30 seconds:**
   ```
   ==========================================
   RECORDING STOPPED
   Total samples: 1500
   Total time: 30020 ms
   Actual sample rate: 49.98 Hz
   ==========================================
   
   Ready for next recording. Send any character to start...
   ```

### Capturing Data

**Option 1: Copy from Serial Monitor**
- Right-click in Serial Monitor → Select All
- Ctrl+C to copy
- Paste into text file
- Save as CSV

**Option 2: Redirect to File (Windows)**
```bash
# In Command Prompt
cd C:\Users\YourName\Documents
```
Then copy-paste data from serial monitor to file

**Option 3: Redirect to File (Linux/Mac)**
```bash
# Terminal command
cat /dev/ttyUSB0 > sensor_data.csv
# Stop with Ctrl+C
```

---

## Output Format

### CSV Header
```
Timestamp_ms,S1_X_g,S1_Y_g,S1_Z_g,S2_X_g,S2_Y_g,S2_Z_g
```

### Column Meanings

| Column | Meaning | Units | Range |
|--------|---------|-------|-------|
| Timestamp_ms | Time since recording started | milliseconds | 0-30000 |
| S1_X_g | Sensor 1 X acceleration | g-forces | ±16 |
| S1_Y_g | Sensor 1 Y acceleration | g-forces | ±16 |
| S1_Z_g | Sensor 1 Z acceleration | g-forces | ±16 |
| S2_X_g | Sensor 2 X acceleration | g-forces | ±16 |
| S2_Y_g | Sensor 2 Y acceleration | g-forces | ±16 |
| S2_Z_g | Sensor 2 Z acceleration | g-forces | ±16 |

### Example Data
```
Timestamp_ms,S1_X_g,S1_Y_g,S1_Z_g,S2_X_g,S2_Y_g,S2_Z_g
0,0.0234,0.0145,-0.9854,0.0198,0.0167,-0.9897
20,0.0267,0.0156,-0.9823,0.0212,0.0178,-0.9876
40,0.0245,0.0134,-0.9876,0.0189,0.0156,-0.9898
60,0.0278,0.0189,-0.9912,0.0234,0.0201,-0.9834
80,0.0256,0.0167,-0.9867,0.0219,0.0176,-0.9876
100,0.0289,0.0198,-0.9823,0.0267,0.0212,-0.9798
```

---

## Verifying Synchronization

### Check 1: Sample Rate
- Expected: 1500 samples in ~30 seconds
- Actual rate shown: Should be ~50 Hz (49-51 Hz is acceptable)

### Check 2: Timestamp Intervals
- Open CSV in Excel or text editor
- Timestamps should increment by ~20 ms
- Pattern: 0, 20, 40, 60, 80, 100, ...
- Gaps or irregular intervals = potential sync problem

### Check 3: Data Consistency
- Both sensors should show similar patterns
- If Sensor 2 leads/lags Sensor 1 = sync issue
- Both should respond to same motion at same time

### Check 4: Use Pre-Analysis Validator
```bash
python3 pre_analysis_validator.py your_sensor_data.csv
```

This will check FFT alignment and confirm synchronization is working!

---

## Troubleshooting

### Problem: "Sensors not detected" error

**Causes:**
- I2C connection loose
- Wrong pin assignments
- Missing pull-up resistors
- Sensor not powered

**Solutions:**
1. Check all wires are firmly connected
2. Verify Arduino is using A4 (SDA) and A5 (SCL)
3. Add 4.7kΩ pull-up resistors if missing
4. Check 5V power to sensors
5. Try I2C Scanner sketch to verify addresses:
   ```cpp
   #include <Wire.h>
   void setup() {
     Serial.begin(115200);
     Wire.begin();
   }
   void loop() {
     for (int addr = 1; addr < 127; addr++) {
       Wire.beginTransmission(addr);
       if (Wire.endTransmission() == 0) {
         Serial.print("Found device at 0x");
         Serial.println(addr, HEX);
       }
     }
     delay(5000);
   }
   ```

### Problem: Erratic or noisy data

**Causes:**
- Loose connections
- Electrical interference
- Inadequate power supply
- Missing decoupling capacitors

**Solutions:**
1. Add 0.1µF capacitors near sensor power pins
2. Use shorter, shielded cables
3. Keep away from power supplies and RF sources
4. Check ground connections are solid
5. Use a regulated 5V power supply

### Problem: Data gaps or irregular timestamps

**Causes:**
- Serial buffer overflow
- I2C communication timing issues
- Baud rate mismatch

**Solutions:**
1. Ensure 115200 baud rate in Serial Monitor
2. Reduce sampling rate temporarily
3. Check USB cable quality
4. Try a different USB port
5. Verify I2C pull-up resistor values

### Problem: Still getting "Multi-Channel Synchronization Issue" in analysis

**Causes:**
- Sensors still not synchronized
- Different sampling rates between sensors
- Timestamps not matching
- Data collection interrupted

**Solutions:**
1. Verify this sketch is uploaded (check Serial output)
2. Confirm both sensors are reading data
3. Check CSV has same number of samples for both sensors
4. Look at timestamps - should increment uniformly
5. Inspect raw data - both sensors should respond together
6. Run pre_analysis_validator.py to get specific feedback

---

## Advanced Configuration

### Changing Sampling Rate

In the sketch, find:
```cpp
#define SAMPLE_RATE_HZ     50      // 50 Hz sampling rate
#define SAMPLE_INTERVAL_MS 20      // 20 ms between samples (1000/50)
```

Change to desired rate:
- 100 Hz → SAMPLE_INTERVAL_MS = 10
- 25 Hz → SAMPLE_INTERVAL_MS = 40
- 200 Hz → SAMPLE_INTERVAL_MS = 5

**Note:** Higher rates may cause I2C communication issues. Stick with 50 Hz unless you have a specific reason.

### Changing Collection Duration

In the sketch, find:
```cpp
#define COLLECTION_TIME_MS 30000   // 30 seconds total
```

Change to desired duration (in milliseconds):
- 60 seconds → 60000
- 10 seconds → 10000
- 5 minutes → 300000

### Changing Range/Resolution

In the sketch, find in `initializeADXL345()`:
```cpp
writeRegister(address, REG_DATA_FORMAT, 0x0B);  // ±16g, 13-bit resolution
```

Different values:
- 0x09 = ±4g, 10-bit resolution
- 0x0A = ±8g, 12-bit resolution
- 0x0B = ±16g, 13-bit resolution (current)

---

## Data Processing Workflow

### Step 1: Collect Data (This Sketch)
```
Arduino → Serial Monitor → Save as CSV
```

### Step 2: Validate Data
```bash
python3 pre_analysis_validator.py your_data.csv
```

### Step 3: Prepare for Analysis
- Remove header row if needed
- Ensure 6 columns (3 per sensor)
- Check for NaN values
- Verify synchronization

### Step 4: Upload to Analysis System
- Upload only VALIDATED files
- Confirm "PASSED" status
- Proceed with analysis

---

## Complete Example Session

```
[Arduino IDE Serial Monitor opens at 115200 baud]

==========================================
SYNCHRONIZED DUAL ADXL345 SENSOR SYSTEM
==========================================

Initializing sensors...

Sensor Status:
  Sensor 1 (0x53): ✓ Connected
  Sensor 2 (0x1D): ✓ Connected

Configuration:
  Sampling Rate: 50 Hz
  Sample Interval: 20 ms
  Range: ±16g
  Resolution: Full (13-bit)

Ready to record!
Send any character via serial to START recording (30 seconds)

[Type: 'a' and press Enter]

==========================================
RECORDING STARTED
Duration: 30 seconds
Expected samples: ~1500
==========================================

Timestamp_ms,S1_X_g,S1_Y_g,S1_Z_g,S2_X_g,S2_Y_g,S2_Z_g
0,0.0234,0.0145,-0.9854,0.0198,0.0167,-0.9897
20,0.0267,0.0156,-0.9823,0.0212,0.0178,-0.9876
40,0.0245,0.0134,-0.9876,0.0189,0.0156,-0.9898
... [1497 more lines of data] ...
29980,0.0289,0.0198,-0.9823,0.0267,0.0212,-0.9798

==========================================
RECORDING STOPPED
Total samples: 1500
Total time: 30020 ms
Actual sample rate: 49.98 Hz
==========================================

Ready for next recording. Send any character to start...

[Copy data and save to file: baseline_01.csv]

[Run validator]
$ python3 pre_analysis_validator.py baseline_01.csv
✅ Status: PASSED
   Rows: 1500 | Columns: 7 (timestamp + 6 accelerometer channels)
   FFT Synchronization: PASS

[Upload to analysis system]
```

---

## Specifications

| Parameter | Value |
|-----------|-------|
| Number of Sensors | 2 |
| Sensor Type | ADXL345 |
| I2C Addresses | 0x53, 0x1D |
| Sampling Rate | 50 Hz (configurable) |
| Sample Interval | 20 ms (configurable) |
| Range | ±16g (configurable) |
| Resolution | 13-bit (full resolution mode) |
| Scale Factor | 0.004 g/LSB |
| Recording Duration | 30 seconds (configurable) |
| Max Samples | ~1500 @ 50 Hz |
| Output Format | CSV with timestamps |
| Baud Rate | 115200 |

---

## Key Advantages of This Sketch

✅ **True Synchronization** - Both sensors read in same loop iteration
✅ **Timestamp Verification** - Includes millisecond timestamps to verify timing
✅ **Fixed Sample Rate** - 50 Hz ± 0.1% accuracy
✅ **Sensor Verification** - Checks both sensors are connected
✅ **Error Checking** - Validates I2C communication
✅ **CSV Output** - Direct compatible format with analysis system
✅ **No Buffering Needed** - Streams directly to serial
✅ **Clear Status Messages** - Real-time feedback during operation

---

## Next Steps

1. **Build the hardware** - Wire up both sensors with pull-up resistors
2. **Upload the sketch** - Program Arduino UNO
3. **Verify connections** - Check initialization message
4. **Collect test data** - Send serial command, wait 30 seconds
5. **Validate data** - Run pre_analysis_validator.py
6. **Upload to system** - Only if validator shows PASSED
7. **Run analysis** - Proceed with confidence!

---

## Support

If you encounter issues:

1. **Check hardware connections** - Most common cause
2. **Verify pull-up resistors** - Required for I2C
3. **Test with I2C scanner** - Find actual addresses
4. **Check baud rate** - Must be 115200
5. **Review serial output** - Look for error messages
6. **Run pre_analysis_validator.py** - Get detailed diagnostics

---

*This synchronized setup ensures you won't encounter the "Multi-Channel Synchronization Issue" error in your structural analysis!*

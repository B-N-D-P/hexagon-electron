# 🏗️ HEXAGON UI - System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    HEXAGON Structural Health                │
│              Real-Time Monitoring Desktop IDE               │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │     PyQt5 Application (ui_main.py)    │
        │                                       │
        │  Main Window & User Interface         │
        │  - Controls Panel                     │
        │  - Data Display (5 Tabs)              │
        │  - Live Graphs                        │
        │  - Parameter Tables                   │
        └───────────────────────────────────────┘
                    ↓          ↓          ↓
        ┌──────────────┬──────────────┬──────────────┐
        │              │              │              │
        ↓              ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Serial Thr  │ │  Parameter   │ │   Data Buf   │ │   Export    │
│  (Reader)    │ │  Calculator  │ │   (Buffer)   │ │   Manager   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        ↓                              
┌──────────────┐
│  Arduino/USB │
│   Serial     │
└──────────────┘
```

## Component Architecture

### 1. Main Application Layer (ui_main.py)

HexagonStructuralHealthUI manages:
- Left Control Panel (Connection, Recording, Export)
- Right Display Panel (5 Tabs with data)
- Event handlers for all user interactions
- GUI state management

### 2. Serial Communication Layer (ui.py - SerialDataThread)

- Runs in separate thread for non-blocking I/O
- Reads from Arduino serial port
- Parses CSV format: S1X,S1Y,S1Z,S2X,S2Y,S2Z
- Emits signals to main thread

### 3. Parameter Calculation Layer (ui.py - ParameterCalculator)

Computes 50+ parameters:
- Time-domain: RMS, Peak, Mean, Std, Crest, Skew, Kurt, Energy
- Frequency-domain: Dominant freq, Spectral energy, Peak count
- Correlation: Intra-axis and cross-sensor

## Data Flow

```
Arduino → Serial Port → SerialDataThread
   ↓
Parse CSV [S1X,S1Y,S1Z,S2X,S2Y,S2Z]
   ↓
Emit data_received signal
   ↓
Main Thread receives data
   ↓
Store in data_buffer (deque, max 500)
   ↓
Add to param_calculator (max 1000)
   ↓
Every 100ms: compute_parameters()
   ↓
Update GUI:
├─ Live Graphs
├─ Time-Domain Table
├─ Frequency-Domain Table
├─ Correlation Table
└─ All Parameters Table
```

## GUI Layout

```
┌─────────────────────────────────────────────────────┐
│        HEXAGON Structural Health IDE                │
├──────────┬────────────────────────────────────────┤
│          │                                        │
│ LEFT     │  📈 Live Data  ⏱️ Time  📡 Freq      │
│ PANEL    │  🔗 Corr       📊 All Params         │
│          │                                        │
│ Controls │  ┌───────────────────────────────┐   │
│ • Port   │  │ Live Graphs & Parameter Tabs  │   │
│ • Baud   │  │ (Real-time updates)           │   │
│ • Conn   │  │                               │   │
│ • Rec    │  │ Tables show 50+ parameters    │   │
│ • Export │  │                               │   │
│ • Status │  └───────────────────────────────┘   │
│          │                                        │
└──────────┴────────────────────────────────────────┘
│ 🔴 Disconnected | Port: COM3 | Status: Ready    │
└──────────────────────────────────────────────────┘
```

## Thread Architecture

**Main Thread:**
- Handles all GUI operations
- Updates every 100ms
- Receives signals from SerialDataThread

**SerialDataThread (Worker):**
- Runs independently
- Reads from serial port continuously
- Emits data_received signals (thread-safe)
- No GUI modifications

**ParameterCalculator:**
- Runs in main thread on demand
- Vectorized NumPy operations (fast)
- Processes buffered data
- Returns 50+ parameters

## Parameter Computation

**Per Sensor, Per Axis (8 metrics each):**
- RMS: Root mean square vibration
- Peak: Maximum acceleration
- Mean: Average value
- Std: Standard deviation
- Crest: Peak/RMS ratio
- Skew: Distribution asymmetry
- Kurt: Distribution peakedness
- Energy: Total power

**Magnitude (2 sensors):**
- Combined XYZ magnitude
- Same 8 metrics

**Frequency Domain:**
- Dominant frequency
- Spectral energy
- Peak count

**Correlations (7 metrics):**
- Intra-axis (XY, XZ, YZ per sensor)
- Cross-sensor magnitude

**Total: 50+ parameters displayed real-time**

## Export Architecture

**CSV Export (No Timestamp):**
```
S1_X,S1_Y,S1_Z,S2_X,S2_Y,S2_Z
0.125,-0.087,0.234,0.156,-0.098,0.267
0.134,-0.092,0.241,0.162,-0.103,0.274
```

**JSON Export (With Analysis):**
```json
{
  "timestamp": "2026-01-16T13:45:30",
  "samples": 5000,
  "parameters": {
    "s1_x_rms": 0.245,
    ...
    "corr_s1s2_mag": 0.782
  }
}
```

## Performance Characteristics

- Update Rate: 10 Hz (100ms)
- Parameter Calc: <50ms
- Memory: ~150 MB
- CPU: <10% idle, <30% active
- Buffer: 1000 samples
- Display: 500 samples

## State Management

```
Idle → Connecting → Connected → Recording → Export → Idle
```

## File Structure

```
structural-repair-web/
├─ ui.py (Core components)
│  ├─ SerialDataThread
│  └─ ParameterCalculator
├─ ui_main.py (Main application)
│  └─ HexagonStructuralHealthUI
├─ launch_ui.sh (Launcher)
├─ ui_requirements.txt (Dependencies)
├─ UI_README.md (Complete guide)
├─ QUICK_START_UI.md (Quick start)
└─ UI_ARCHITECTURE.md (This file)
```

---

**Professional, real-time desktop application for structural health monitoring!**

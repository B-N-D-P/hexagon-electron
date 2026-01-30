# Current Repair Quality Formula Analysis

## Location
File: `backend/repair_analyzer.py` (lines 723-840)
Function: `calculate_repair_quality()`

## Current Formula (Lines 754-756)

```python
denom = (fO - fD)  # Original - Damaged
denom = np.where(np.abs(denom) < 1e-6, np.sign(denom) * 1e-6 + 1e-6, denom)
Q_freq_i = np.clip((fR - fD) / denom, 0.0, 1.0)
```

Where:
- `fO` = Original frequency
- `fD` = Damaged frequency  
- `fR` = Repaired frequency

Expanded formula:
```
Q_freq = (fR - fD) / (fO - fD)
```

## The Fundamental Flaw

### Restoration Scenario (WORKS CORRECTLY ✓)
- **Goal**: Return to original state
- **Example**: Original=100 Hz, Damaged=80 Hz, Repaired=100 Hz
- **Formula**: Q = (100-80)/(100-80) = 20/20 = **1.0** ✓ Correct!

### Retrofitting/Strengthening Scenario (FAILS ✗)
- **Goal**: Improve beyond original (add FRP, steel plates, carbon fiber)
- **Example**: Original=100 Hz, Damaged=80 Hz, Repaired=110 Hz (strengthened)
- **Formula**: Q = (110-80)/(100-80) = 30/20 = **1.5** → Clipped to 1.0
- **Problem**: System sees 1.0, not distinguishing between:
  - Perfect restoration (100 Hz) = 1.0
  - 10% strengthening (110 Hz) = 1.0 (clipped)
  - 50% strengthening (150 Hz) = 1.0 (clipped)

## Impact

### What Gets Penalized:
1. **Fiber-Reinforced Polymer (FRP) wraps** - Intentionally increases stiffness
2. **Steel plate bonding** - Adds stiffness beyond original
3. **Carbon fiber reinforcement** - Strengthens structure
4. **Additional bracing** - Improves lateral stiffness

### Why This is Wrong:
- These are **valid, often superior repair strategies**
- Standards (ACI, ASCE, Eurocode) **encourage** strengthening
- Current system treats strengthening same as perfect restoration
- Cannot differentiate quality levels in retrofitting projects

## The Dataset Evidence

Check existing repair data:
```bash
ls -la datas/repaired/good_repair/
ls -la datas/repaired/bad_repair/
ls -la datas/repaired/verybad_repair/
```

These datasets likely contain both restoration and retrofitting examples.

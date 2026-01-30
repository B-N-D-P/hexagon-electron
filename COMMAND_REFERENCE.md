# 🎯 Command Reference - Improved Repair Quality System

## Quick Commands

### 1. Test the Implementation
```bash
cd backend
python test_improved_quality.py
```
**Expected:** All synthetic tests pass, showing OLD vs NEW formula differences.

---

### 2. Run Integration Example
```bash
cd backend
python INTEGRATION_EXAMPLE.py
```
**Shows:** Detailed comparison of restoration vs retrofitting scenarios.

---

### 3. Deploy to Backend
```bash
# Edit backend/app.py line ~611
# Change:
#   from python123.repair_analyzer import calculate_repair_quality
# To:
#   from improved_repair_quality import calculate_repair_quality_smart as calculate_repair_quality

# Then restart backend:
cd backend
source venv/bin/activate
python app.py
```

---

### 4. Test with Real Data
```bash
# Start backend
cd backend && python app.py &

# Upload files via UI or curl
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@path/to/your/repair.csv"

# Analyze
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"damaged_file_id":"xxx", "repaired_file_id":"yyy", "analysis_type":"repair_quality"}'
```

---

## File Locations

```
📁 Project Root
├── backend/
│   ├── improved_repair_quality.py      ← Main module
│   ├── test_improved_quality.py        ← Test suite  
│   ├── INTEGRATION_EXAMPLE.py          ← Examples
│   └── REPAIR_QUALITY_ANALYSIS.md      ← Technical docs
│
├── IMPROVED_REPAIR_QUALITY_GUIDE.md    ← User guide
├── IMPLEMENTATION_COMPLETE_REPAIR_QUALITY.md
├── QUICK_DEPLOY_REPAIR_QUALITY.md
└── COMMAND_REFERENCE.md                ← This file
```

---

## Python API Quick Reference

### Basic Usage (Drop-in Replacement)
```python
from improved_repair_quality import calculate_repair_quality_smart

quality = calculate_repair_quality_smart(modal_original, modal_damaged, modal_repaired)

print(f"Score: {quality.overall_score:.3f}")
print(f"Type: {quality.breakdown.repair_type}")
```

### With Manual Override
```python
quality = calculate_repair_quality_smart(
    modal_original, modal_damaged, modal_repaired,
    repair_type='retrofitting'  # or 'restoration'
)
```

### Access New Fields
```python
# Repair type: 'restoration', 'retrofitting', or 'mixed'
repair_type = quality.breakdown.repair_type

# Strengthening factor: 1.0 = original, 1.15 = 15% stronger
strength = quality.breakdown.strengthening_factor

# Enhanced interpretation
strategy = quality.repair_strategy
```

---

## Key Metrics

### Restoration Repairs
- **Score 1.0:** Perfect restoration to original state
- **Score 0.8:** 80% restoration (good)
- **Score 0.5:** 50% restoration (fair)

### Retrofitting Repairs
- **Score 1.0:** 20% strengthening (excellent)
- **Score 0.88:** 15% strengthening (very good)
- **Score 0.75:** 10% strengthening (good)
- **Score 0.5:** Restored to original only (baseline)

---

## Troubleshooting

### Test Failures
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
cd backend
pip install -r requirements-no-tf.txt

# Run tests with verbose output
python -v test_improved_quality.py
```

### Import Errors
```bash
# Verify file exists
ls -la backend/improved_repair_quality.py

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Wrong Scores
```bash
# Check repair type detection
python -c "
from improved_repair_quality import detect_repair_type
import numpy as np

fO = np.array([100.0])
fD = np.array([80.0])
fR = np.array([110.0])

repair_type, strength = detect_repair_type(fO, fD, fR)
print(f'Type: {repair_type}, Strength: {strength:.2f}x')
"
```

---

## Documentation Links

| Document | Purpose | Location |
|----------|---------|----------|
| **User Guide** | Complete usage instructions | `IMPROVED_REPAIR_QUALITY_GUIDE.md` |
| **Deploy Guide** | 5-minute deployment | `QUICK_DEPLOY_REPAIR_QUALITY.md` |
| **Summary** | Project overview | `IMPLEMENTATION_COMPLETE_REPAIR_QUALITY.md` |
| **Examples** | Code samples | `backend/INTEGRATION_EXAMPLE.py` |
| **Tests** | Validation suite | `backend/test_improved_quality.py` |

---

## Status Check

```bash
# Verify all files present
ls -la backend/improved_repair_quality.py \
      backend/test_improved_quality.py \
      IMPROVED_REPAIR_QUALITY_GUIDE.md \
      QUICK_DEPLOY_REPAIR_QUALITY.md

# Expected: All files exist (no errors)
```

---

**Last Updated:** 2026-01-29  
**Status:** ✅ Ready for deployment

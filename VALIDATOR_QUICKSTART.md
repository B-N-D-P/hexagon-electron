# Pre-Analysis Validator - Quick Start

## What is it?
A Python script that validates sensor data BEFORE uploading to catch errors like:
- ❌ Multi-Channel Synchronization Issues
- ❌ Missing/corrupted data
- ❌ Data type problems
- ❌ Signal clipping/saturation

## Install (one-time)
```bash
pip install pandas numpy scipy
```

## Quick Usage

### Validate a single file
```bash
python3 pre_analysis_validator.py your_data.csv
```

### Validate entire folder
```bash
python3 pre_analysis_validator.py /path/to/folder
```

### Save detailed report
```bash
python3 pre_analysis_validator.py /path/to/folder --report report.txt
```

## What to expect

**✅ PASSED** = Safe to upload
**⚠️ WARNING** = Review before uploading  
**❌ FAILED** = Fix issues first

## Example

```bash
$ python3 pre_analysis_validator.py ./datas/baseline

====================================================================================================
PRE-ANALYSIS DATA VALIDATION
====================================================================================================
Folder: datas/baseline
Files found: 20
====================================================================================================

  1. ✅ baseline_01.csv
     Status: PASSED
     Rows: 2000 | Columns: 6

  2. ✅ baseline_02.csv
     Status: PASSED
     Rows: 2000 | Columns: 6

[... more files ...]

🎉 ALL FILES PASSED VALIDATION - Safe to upload and analyze!
```

## Common Issues & Quick Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Multi-Channel Sync | Different clock sources | Use same power/clock for all sensors |
| NaN values | Data corruption | Re-collect the data |
| Non-numeric | Text in sensor columns | Clean CSV, remove headers |
| Extreme values | Sensor error | Check connections, recalibrate |
| Signal saturation | ADC overflow | Reduce gain, rescale |

## Full Documentation
See `PRE_ANALYSIS_VALIDATOR_GUIDE.md` for complete details

## Common Commands

```bash
# Validate and see results
python3 pre_analysis_validator.py ./my_data

# Validate and save report
python3 pre_analysis_validator.py ./my_data --report validation_report.txt

# Validate and save as JSON
python3 pre_analysis_validator.py ./my_data --json validation_results.json

# Validate multiple folders
for folder in data_*; do
  python3 pre_analysis_validator.py "$folder" --report "${folder}_report.txt"
done
```

## Why use it?
✅ Catch errors before they fail in analysis
✅ Save time debugging upload errors
✅ Document data quality
✅ Automate quality assurance

**Start using it now!**

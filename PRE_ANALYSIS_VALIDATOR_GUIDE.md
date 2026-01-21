# Pre-Analysis Data Validator Guide

## Overview

The **Pre-Analysis Validator** (`pre_analysis_validator.py`) is a comprehensive tool designed to catch data issues **BEFORE** uploading to the analysis system. It prevents failures like the "Multi-Channel Synchronization Issue" error that can occur after upload.

## Key Features

✅ **Multi-Channel Synchronization Check** - Detects asynchronous sampling (the main error you showed)
✅ **Data Quality Validation** - NaN values, data types, range consistency
✅ **Extreme Value Detection** - Flags suspicious sensor readings
✅ **Signal Saturation Detection** - Identifies clipping and overflow
✅ **Batch Processing** - Validate entire folders at once
✅ **Detailed Reports** - Console + file output with actionable fixes
✅ **JSON Export** - For programmatic analysis

---

## Installation

No additional dependencies needed! The script uses standard Python libraries:
- pandas
- numpy
- scipy

Make sure you have these installed:
```bash
pip install pandas numpy scipy
```

---

## Usage

### 1. Validate a Single File

```bash
python3 pre_analysis_validator.py /path/to/data.csv
```

**Example:**
```bash
python3 pre_analysis_validator.py ./datas/baseline/baseline_01.csv
```

**Output:**
```
====================================================================================================
FILE VALIDATION RESULT
====================================================================================================

File: baseline_01.csv
Status: PASSED
Rows: 2000 | Columns: 6

✅ File is safe to upload and analyze!
```

---

### 2. Validate an Entire Folder

Batch validate all CSV files in a folder:

```bash
python3 pre_analysis_validator.py /path/to/folder
```

**Example:**
```bash
python3 pre_analysis_validator.py ./datas/baseline
```

**Output:**
```
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
```

---

### 3. Save Report to File

Generate a detailed text report:

```bash
python3 pre_analysis_validator.py /path/to/folder --report validation_report.txt
```

**Example:**
```bash
python3 pre_analysis_validator.py ./datas/baseline --report baseline_validation.txt
```

The report will include:
- Summary statistics
- Detailed results for each file
- Issues and warnings with recommended fixes
- Data characteristics

---

### 4. Export to JSON

For programmatic analysis or integration:

```bash
python3 pre_analysis_validator.py /path/to/folder --json results.json
```

**Example:**
```bash
python3 pre_analysis_validator.py ./datas/baseline --json validation_results.json
```

---

## Validation Checks

The validator performs these checks on each file:

| Check | Description | What It Catches |
|-------|-------------|-----------------|
| **File Load** | Can the CSV be opened? | Corrupted files, permission issues |
| **Empty File** | Does the file have data? | Empty uploads |
| **Sample Count** | Enough samples? | Too few data points (< 100) |
| **NaN Values** | Missing data? | Incomplete or corrupted datasets |
| **Numeric Data** | All columns numeric? | Text in sensor columns |
| **FFT Synchronization** | Are channels synchronized? | **Multi-Channel Synchronization Issue** ⚠️ |
| **Extreme Values** | Suspicious readings? | Sensor errors, calibration issues |
| **Range Consistency** | Similar data ranges? | Asynchronous sampling |
| **Signal Saturation** | Clipping detected? | ADC overflow, overrange values |
| **Sampling Regularity** | Regular intervals? | Timing inconsistencies |

---

## Understanding Results

### ✅ PASSED
- File has no errors
- All checks passed
- **Safe to upload and analyze**

### ⚠️ WARNING
- File has warnings but no critical errors
- May affect analysis quality
- **Review before uploading** or **proceed with caution**

### ❌ FAILED
- File has critical errors
- **Cannot be used for analysis**
- **Fix issues before uploading**

---

## Common Issues & Fixes

### Issue: "Multi-Channel Synchronization Issue"

**Problem:** Peak frequencies appear at different FFT bins (channels sampled asynchronously)

**Causes:**
- Sensors connected to different power sources
- Different clock sources or USB hubs
- Timing jitter in data collection
- Different sampling rates

**Fix:**
1. Ensure all sensors use the same clock source
2. Connect all sensors to the same power supply
3. Use a single USB hub or direct connection
4. Verify sampling rate is consistent across all channels
5. Re-collect data with synchronized timing

---

### Issue: "Contains X NaN values"

**Problem:** Missing or corrupted data points

**Causes:**
- Sensor disconnection during collection
- Data transmission errors
- File corruption

**Fix:**
1. Verify sensor connections
2. Re-collect the data
3. Check file integrity

---

### Issue: "Non-numeric columns"

**Problem:** Text or non-numeric values in sensor columns

**Causes:**
- Headers in data rows
- Formatting issues
- Corrupted data

**Fix:**
1. Clean the CSV file
2. Remove header rows from data
3. Re-export from sensor software

---

### Issue: "Extreme values detected"

**Problem:** Values much larger than expected (e.g., > 100)

**Causes:**
- Sensor disconnection
- Electrical interference
- Calibration error
- Wrong units

**Fix:**
1. Check sensor connections
2. Verify sensor calibration
3. Check for electrical noise
4. Re-collect the data

---

### Issue: "Possible signal saturation"

**Problem:** Many repeated min/max values (clipping)

**Causes:**
- ADC overflow
- Sensor overrange
- Gain set too high

**Fix:**
1. Reduce sensor gain
2. Check ADC range settings
3. Re-collect with appropriate scaling

---

## Usage Examples

### Workflow 1: Single File Validation

```bash
# Validate a file before uploading
python3 pre_analysis_validator.py sensor_data.csv

# If PASSED, upload to system
# If FAILED, fix issues and retry
```

### Workflow 2: Batch Folder Validation

```bash
# Validate all files in a folder
python3 pre_analysis_validator.py ./sensor_data_batch --report batch_report.txt

# Review batch_report.txt
# Upload only PASSED files
# Fix or re-collect FAILED files
```

### Workflow 3: Quality Assurance

```bash
# Validate and archive results
python3 pre_analysis_validator.py ./collected_data \
  --report qa_report_$(date +%Y%m%d).txt \
  --json qa_results_$(date +%Y%m%d).json

# Store reports with data for audit trail
```

### Workflow 4: Automated Pipeline

```bash
# In a bash script - stop if validation fails
python3 pre_analysis_validator.py ./data || {
  echo "Validation failed!"
  exit 1
}

# Continue with analysis
python3 ./backend/app.py
```

---

## Output Formats

### Console Output
Real-time status with color indicators:
- ✅ = Passed
- ⚠️ = Warning
- ❌ = Failed

### Text Report (`--report`)
Comprehensive report with:
- Summary statistics
- Detailed file-by-file results
- Issues and recommendations
- Data characteristics

### JSON Output (`--json`)
Machine-readable format for integration:
```json
[
  {
    "file": "baseline_01.csv",
    "status": "PASSED",
    "data_info": {
      "rows": 2000,
      "columns": 6,
      "column_names": ["S1_X_g", "S1_Y_g", "S1_Z_g", "S2_X_g", "S2_Y_g", "S2_Z_g"]
    },
    "issues": [],
    "warnings": []
  }
]
```

---

## Tips & Best Practices

1. **Always validate before uploading** - Catch errors early
2. **Keep validation reports** - Document data quality history
3. **Batch validate folders** - Process multiple files efficiently
4. **Review warnings** - Even "warning" status may need investigation
5. **Fix at source** - Address issues in data collection, not cleanup
6. **Automate validation** - Integrate into your data pipeline

---

## Troubleshooting

### Script won't run
```bash
# Make sure dependencies are installed
pip install pandas numpy scipy

# Run with explicit Python path
python3 pre_analysis_validator.py /path/to/folder
```

### "File not found" error
```bash
# Use absolute paths
python3 pre_analysis_validator.py /full/path/to/file.csv

# Or full path to folder
python3 pre_analysis_validator.py /full/path/to/folder
```

### Too many warnings/errors
- Check data collection setup
- Verify sensor connections
- Re-collect the data with proper synchronization
- Contact system administrator

---

## Summary

The Pre-Analysis Validator helps you:
✅ Catch synchronization issues before analysis fails
✅ Validate data quality before upload
✅ Generate audit reports
✅ Automate quality assurance

**Use it on every dataset before uploading to prevent analysis failures!**

---

For more information, see the inline comments in `pre_analysis_validator.py`

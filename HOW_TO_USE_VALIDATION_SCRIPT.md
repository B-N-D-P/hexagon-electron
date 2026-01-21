# CSV Folder Validation Script - Complete Guide

## What You Have

A universal Python script: `validate_csv_folder.py`

This script can validate ANY folder containing CSV sensor data files.

## Quick Start

### 1. **Simple Validation (No Baseline)**
```bash
python3 validate_csv_folder.py "/path/to/your/csv/folder"
```

**Example:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/datas/baseline 2082-10-3"
```

### 2. **Validation WITH Baseline Comparison**
```bash
python3 validate_csv_folder.py "/path/to/folder" \
  --baseline "/path/to/baseline.csv"
```

**Example:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/repaired_classified/20_good_repair" \
  --baseline "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv"
```

### 3. **Save Report to File**
```bash
python3 validate_csv_folder.py "/path/to/folder" \
  --report "report_name.txt"
```

**Example:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/datas/damaged B1 removed" \
  --report "damage_validation.txt"
```

### 4. **Full Command (Baseline + Report)**
```bash
python3 validate_csv_folder.py "/path/to/folder" \
  --baseline "/path/to/baseline.csv" \
  --report "output.txt"
```

## What Gets Checked

✅ **NaN Values** - No missing data  
✅ **Data Types** - All numeric  
✅ **Row Count** - Matches baseline (if provided)  
✅ **Column Count** - Matches baseline (if provided)  
✅ **Column Names** - Correct sensor structure  
✅ **Extreme Values** - No outliers > ±1000  
✅ **Quality Metrics** - Mean, Std, Quality Score  
✅ **Statistics** - Aggregated across all files  

## Output Interpretation

### Status Codes
- **✅ PASSED** - All checks passed, file is valid
- **❌ FAILED** - File has issues
- **⚠️ WARNINGS** - File is valid but has minor issues

### Quality Scores
- **80-100%** - GOOD REPAIR (well recovered)
- **40-70%** - BAD REPAIR (partially recovered)
- **<40%** - VERY BAD REPAIR (minimal recovery)

## Ready-to-Use Commands for Your Data

### Test Original Data Folders

**Baseline:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/datas/baseline 2082-10-3"
```

**Damaged:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/datas/damaged B1 removed" \
  --baseline "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv"
```

**Repaired:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/datas/repaired" \
  --baseline "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv"
```

### Test Synthetic Data Folders

**Good Repair:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/repaired_classified/20_good_repair" \
  --baseline "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv" \
  --report "good_repair_validation.txt"
```

**Bad Repair:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/repaired_classified/20_bad_repair" \
  --baseline "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv" \
  --report "bad_repair_validation.txt"
```

**Very Bad Repair:**
```bash
python3 validate_csv_folder.py "/home/itachi/data raw/repaired_classified/20_verybad_repair" \
  --baseline "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv" \
  --report "verybad_repair_validation.txt"
```

## Example Output

```
================================================================================
CSV FOLDER VALIDATION
================================================================================
✅ Baseline loaded: baseline 2082-10-3 1st.csv
   Rows: 2006, Columns: 6
✅ Found 20 CSV files
📁 Folder: /home/itachi/data raw/repaired_classified/20_good_repair
📊 Files to validate: 20

#    Status   File Name                                Rows     Checks    
────────────────────────────────────────────────────────────────────────────
1    ✅       good_repair_01.csv                       2006     8/8       
2    ✅       good_repair_02.csv                       2006     8/8       
...

✅ PASSED FILES (20)
────────────────────────────────────────────────────────────────────────────
  good_repair_01.csv    | Mean Dev:   4.06% | Quality: 93.9%
  good_repair_02.csv    | Mean Dev:   3.95% | Quality: 94.1%
  ...

📈 STATISTICS
────────────────────────────────────────────────────────────────────────────
Average Mean: -0.400161 (±0.002177)
Average Std: 0.036108 (±0.000059)
Quality Scores:
  Average: 94.3%
  Min: 92.8%
  Max: 95.6%

✅ ALL FILES PASSED VALIDATION - Ready for analysis
```

## Key Features

🎯 **Universal** - Works with any CSV folder  
📊 **Comprehensive** - Checks 8 different aspects  
📈 **Statistical** - Calculates aggregated metrics  
🔍 **Detailed** - Shows individual file and aggregate statistics  
💾 **Exportable** - Saves reports to file  
✅ **Clear** - Color-coded status indicators  

## Tips

1. **Always use baseline comparison** for repair data to see quality scores
2. **Save reports** for documentation and comparison
3. **Run on all your folders** to verify data integrity before uploading to the website
4. **Quality scores** help identify which repair category each file belongs to

## Next Steps

Run the validation on your folders to confirm all data is ready:
- Test your original data (baseline, damaged, repaired)
- Test your synthetic data (good_repair, bad_repair, verybad_repair)
- All files should show ✅ PASSED status
- Quality scores should match expected ranges

Then you can safely upload the validated files to your website for analysis!

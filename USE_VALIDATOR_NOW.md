# Use the Pre-Analysis Validator NOW

## 🚀 Quick Start (30 seconds)

```bash
# Validate your data before uploading
python3 pre_analysis_validator.py /path/to/your/data.csv
```

That's it! You'll see:
- ✅ PASSED = Upload safely
- ⚠️ WARNING = Review first
- ❌ FAILED = Fix before uploading

---

## 📋 Your Specific Use Case

Based on your request for **batch folder validation**:

### Validate Entire Folder
```bash
python3 pre_analysis_validator.py ./datas/baseline
```

Output:
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
     
[... all 20 files ...]

🎉 ALL FILES PASSED VALIDATION - Safe to upload and analyze!
```

### Save Detailed Report
```bash
python3 pre_analysis_validator.py ./datas/baseline --report baseline_validation.txt
```

This creates a file with:
- Summary statistics
- File-by-file results
- Issues and warnings
- Recommended fixes

---

## 🎯 The Error You're Trying to Prevent

The validator catches this error **BEFORE** it happens:

```
Analysis failed: Data: Multi-Channel Synchronization Issue Detected. 
Peak frequencies appear at different FFT bins: 
[np.int64(0), np.int64(0), np.int64(268), np.int64(0), np.int64(144), np.int64(726)]. 
This suggests channels are sampled asynchronously. Mode shapes will be corrupted. 
FIX: Ensure all sensors are sampled simultaneously with the same clock.
```

**How it works:**
1. Loads your CSV file
2. Computes FFT for each sensor channel
3. Checks if peak frequencies align
4. If they don't → Flags the issue
5. Gives you the exact fix

---

## 📊 Typical Workflow

### Workflow 1: Single File
```bash
# Step 1: Validate
python3 pre_analysis_validator.py sensor_data.csv

# Step 2: Check output
# If ✅ PASSED:
#   Upload to system
# If ❌ FAILED:
#   Read error message
#   Fix the issue
#   Re-collect data
#   Retry validation
```

### Workflow 2: Batch Folder
```bash
# Step 1: Validate entire folder
python3 pre_analysis_validator.py ./collected_data --report report.txt

# Step 2: Check report.txt
# Review which files passed/failed

# Step 3: Upload only PASSED files
# Fix or re-collect FAILED files

# Step 4: Keep report for audit trail
```

### Workflow 3: Automated (For Scripts)
```bash
#!/bin/bash
# In your data collection script

# Collect data
python3 collect_sensor_data.py

# Validate immediately
python3 pre_analysis_validator.py ./new_data || {
    echo "❌ Validation failed!"
    exit 1
}

# Upload to analysis
curl -F "file=@./new_data.csv" http://localhost:8000/upload
```

---

## 🔧 Common Commands

### Validate and see results immediately
```bash
python3 pre_analysis_validator.py ./my_folder
```

### Validate and save report for later
```bash
python3 pre_analysis_validator.py ./my_folder --report my_report.txt
```

### Validate and export as JSON (for processing)
```bash
python3 pre_analysis_validator.py ./my_folder --json results.json
```

### Validate multiple folders
```bash
for folder in baseline damaged repaired; do
  echo "Validating $folder..."
  python3 pre_analysis_validator.py ./data/$folder --report ${folder}_report.txt
done
```

### Validate and upload only good files
```bash
python3 pre_analysis_validator.py ./data

# Then manually upload files marked as PASSED
# Or integrate with API:
python3 upload_validated_files.py
```

---

## 📁 What You Need

**Already in your workspace:**
- ✅ `pre_analysis_validator.py` - Main script
- ✅ `PRE_ANALYSIS_VALIDATOR_GUIDE.md` - Full documentation
- ✅ `VALIDATOR_QUICKSTART.md` - Quick reference
- ✅ `VALIDATOR_IMPLEMENTATION_SUMMARY.md` - Technical details

**Dependencies (one-time install):**
```bash
pip install pandas numpy scipy
```

These are standard data science libraries - likely already installed.

---

## 🎓 Understanding the Output

### When File PASSES ✅
```
Status: PASSED
✅ File is safe to upload and analyze!
```
→ Upload immediately

### When File Has WARNINGS ⚠️
```
Status: WARNING
⚠️ WARNING: Extreme values detected: Columns with extreme values: S1_X_g: 500.00
```
→ Review the warning, decide if acceptable

### When File FAILS ❌
```
Status: FAILED
❌ ISSUE: Multi-Channel Synchronization Issue: Peak frequencies appear at different FFT bins...
   FIX: Ensure all sensors are sampled simultaneously with the same clock.
```
→ Fix the issue before uploading

---

## 💡 Pro Tips

1. **Validate After Collection** - Run validator immediately after collecting data
2. **Batch Process** - Validate entire folders instead of one file at a time
3. **Keep Reports** - Save reports to document data quality over time
4. **Automate** - Add validator to your data pipeline
5. **Review Warnings** - Even warnings can affect analysis quality

---

## 🆘 Quick Troubleshooting

### "File not found"
```bash
# Use full path
python3 pre_analysis_validator.py /full/path/to/file.csv
```

### "Module not found: pandas"
```bash
# Install dependencies
pip install pandas numpy scipy
```

### "FAILED - Multi-Channel Sync Issue"
```bash
# Fix: Ensure sensors use the same clock source
# 1. Check all sensors connected to same power supply
# 2. Verify all using same USB hub
# 3. Re-collect data with synchronized timing
# 4. Try validation again
```

### "Too many NaN values"
```bash
# Fix: Re-collect the data with proper sensor connections
```

---

## 📞 Next Steps

1. **Try it now:**
   ```bash
   python3 pre_analysis_validator.py ./datas/baseline
   ```

2. **Read the full guide** (if needed):
   ```bash
   cat PRE_ANALYSIS_VALIDATOR_GUIDE.md
   ```

3. **Integrate into your workflow:**
   - Add to collection scripts
   - Run before every upload
   - Keep reports

4. **Automate it:**
   - Use in CI/CD pipelines
   - Integrate with upload system
   - Set up automatic reports

---

## ✨ Summary

You now have a tool that:
- ✅ Validates data BEFORE upload (saves time!)
- ✅ Catches the "Multi-Channel Synchronization Issue"
- ✅ Works on single files or entire folders
- ✅ Gives clear error messages with fixes
- ✅ Ready to use right now!

**Start using it on your next dataset!**

```bash
python3 pre_analysis_validator.py your_data_folder
```

That's it! 🚀

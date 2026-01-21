#!/usr/bin/env python3
"""
Data Validation & Analysis Testing Script
Tests CSV data for issues before uploading to Structural Health Monitoring System
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.fft import fft
from scipy.signal import find_peaks
import sys

class DataValidator:
    def __init__(self, baseline_file, test_file, name="Test Data"):
        self.name = name
        self.baseline_file = Path(baseline_file)
        self.test_file = Path(test_file)
        self.df_baseline = None
        self.df_test = None
        self.issues = []
        self.warnings = []
        self.passed_checks = []
        
    def load_files(self):
        """Load CSV files"""
        print(f"\n1️⃣  LOADING FILES")
        print("-" * 80)
        
        try:
            self.df_baseline = pd.read_csv(self.baseline_file)
            print(f"✅ Baseline loaded: {self.baseline_file.name}")
            print(f"   Rows: {len(self.df_baseline)}, Columns: {len(self.df_baseline.columns)}")
        except Exception as e:
            self.issues.append(f"Failed to load baseline: {e}")
            print(f"❌ Baseline load failed: {e}")
            return False
        
        try:
            self.df_test = pd.read_csv(self.test_file)
            print(f"✅ Test data loaded: {self.test_file.name}")
            print(f"   Rows: {len(self.df_test)}, Columns: {len(self.df_test.columns)}")
        except Exception as e:
            self.issues.append(f"Failed to load test data: {e}")
            print(f"❌ Test data load failed: {e}")
            return False
        
        return True
    
    def check_nan_values(self):
        """Check for NaN values"""
        print(f"\n2️⃣  CHECKING FOR NaN VALUES")
        print("-" * 80)
        
        # Baseline
        baseline_nans = self.df_baseline.isna().sum().sum()
        if baseline_nans > 0:
            self.issues.append(f"Baseline has {baseline_nans} NaN values")
            print(f"❌ Baseline has {baseline_nans} NaN values")
        else:
            print(f"✅ Baseline: No NaN values")
            self.passed_checks.append("Baseline NaN check")
        
        # Test data
        test_nans = self.df_test.isna().sum().sum()
        if test_nans > 0:
            self.issues.append(f"Test data has {test_nans} NaN values")
            print(f"❌ Test data has {test_nans} NaN values")
            print(f"   Columns with NaN:")
            for col in self.df_test.columns:
                nan_count = self.df_test[col].isna().sum()
                if nan_count > 0:
                    print(f"     • {col}: {nan_count} NaN values")
        else:
            print(f"✅ Test data: No NaN values")
            self.passed_checks.append("Test data NaN check")
        
        return baseline_nans == 0 and test_nans == 0
    
    def check_data_types(self):
        """Check if all columns are numeric"""
        print(f"\n3️⃣  CHECKING DATA TYPES")
        print("-" * 80)
        
        # Baseline
        baseline_numeric = True
        for col in self.df_baseline.columns:
            try:
                pd.to_numeric(self.df_baseline[col])
            except:
                baseline_numeric = False
                self.issues.append(f"Baseline column '{col}' is not numeric")
                print(f"❌ Baseline column '{col}' is not numeric")
        
        if baseline_numeric:
            print(f"✅ Baseline: All columns numeric")
            self.passed_checks.append("Baseline data types")
        
        # Test data
        test_numeric = True
        for col in self.df_test.columns:
            try:
                pd.to_numeric(self.df_test[col])
            except:
                test_numeric = False
                self.issues.append(f"Test data column '{col}' is not numeric")
                print(f"❌ Test data column '{col}' is not numeric")
        
        if test_numeric:
            print(f"✅ Test data: All columns numeric")
            self.passed_checks.append("Test data types")
        
        return baseline_numeric and test_numeric
    
    def check_row_count(self):
        """Check if row counts match"""
        print(f"\n4️⃣  CHECKING ROW COUNT")
        print("-" * 80)
        
        baseline_rows = len(self.df_baseline)
        test_rows = len(self.df_test)
        
        print(f"Baseline rows: {baseline_rows}")
        print(f"Test data rows: {test_rows}")
        
        if baseline_rows != test_rows:
            self.warnings.append(f"Row count mismatch: baseline={baseline_rows}, test={test_rows}")
            print(f"⚠️  WARNING: Row counts don't match")
        else:
            print(f"✅ Row counts match: {baseline_rows}")
            self.passed_checks.append("Row count check")
        
        return baseline_rows == test_rows
    
    def check_column_count(self):
        """Check if column counts match"""
        print(f"\n5️⃣  CHECKING COLUMN COUNT")
        print("-" * 80)
        
        baseline_cols = len(self.df_baseline.columns)
        test_cols = len(self.df_test.columns)
        
        print(f"Baseline columns: {baseline_cols}")
        print(f"Test data columns: {test_cols}")
        print(f"Baseline columns: {list(self.df_baseline.columns)}")
        print(f"Test columns: {list(self.df_test.columns)}")
        
        if baseline_cols != test_cols:
            self.issues.append(f"Column count mismatch: baseline={baseline_cols}, test={test_cols}")
            print(f"❌ Column count mismatch")
        else:
            print(f"✅ Column counts match: {baseline_cols}")
            self.passed_checks.append("Column count check")
        
        return baseline_cols == test_cols
    
    def check_column_names(self):
        """Check if column names match"""
        print(f"\n6️⃣  CHECKING COLUMN NAMES")
        print("-" * 80)
        
        baseline_names = set(self.df_baseline.columns)
        test_names = set(self.df_test.columns)
        
        if baseline_names != test_names:
            missing = baseline_names - test_names
            extra = test_names - baseline_names
            if missing:
                self.warnings.append(f"Missing columns in test: {missing}")
                print(f"⚠️  Missing columns: {missing}")
            if extra:
                self.warnings.append(f"Extra columns in test: {extra}")
                print(f"⚠️  Extra columns: {extra}")
        else:
            print(f"✅ Column names match")
            self.passed_checks.append("Column names check")
        
        return baseline_names == test_names
    
    def check_value_ranges(self):
        """Check for extreme values"""
        print(f"\n7️⃣  CHECKING VALUE RANGES")
        print("-" * 80)
        
        print(f"Baseline value ranges:")
        for col in self.df_baseline.columns:
            min_val = self.df_baseline[col].min()
            max_val = self.df_baseline[col].max()
            mean_val = self.df_baseline[col].mean()
            print(f"  {col}: min={min_val:.6f}, max={max_val:.6f}, mean={mean_val:.6f}")
        
        print(f"\nTest data value ranges:")
        for col in self.df_test.columns:
            min_val = self.df_test[col].min()
            max_val = self.df_test[col].max()
            mean_val = self.df_test[col].mean()
            print(f"  {col}: min={min_val:.6f}, max={max_val:.6f}, mean={mean_val:.6f}")
            
            # Check for extreme values
            if abs(max_val) > 1000 or abs(min_val) > 1000:
                self.warnings.append(f"Column '{col}' has extreme values: [{min_val}, {max_val}]")
                print(f"  ⚠️  Extreme values detected in {col}")
        
        self.passed_checks.append("Value range check")
    
    def check_synchronization(self):
        """Check if data is properly synchronized (all columns present)"""
        print(f"\n8️⃣  CHECKING SYNCHRONIZATION")
        print("-" * 80)
        
        expected_cols = ['S1_X_g', 'S1_Y_g', 'S1_Z_g', 'S2_X_g', 'S2_Y_g', 'S2_Z_g']
        test_cols = list(self.df_test.columns)
        
        # Check if we have 2-sensor data (6 columns)
        if len(test_cols) == 6:
            print(f"✅ 2-Sensor data detected (6 columns)")
            self.passed_checks.append("Sensor count check")
        elif len(test_cols) == 15:
            print(f"✅ 5-Sensor data detected (15 columns)")
            self.passed_checks.append("Sensor count check")
        else:
            self.warnings.append(f"Unexpected column count: {len(test_cols)} (expected 6 or 15)")
            print(f"⚠️  Unexpected column count: {len(test_cols)}")
    
    def fft_analysis(self):
        """Perform FFT analysis to check for synchronization issues"""
        print(f"\n9️⃣  FFT SYNCHRONIZATION ANALYSIS")
        print("-" * 80)
        
        try:
            # Get first two sensor X channels
            if 'S1_X_g' in self.df_test.columns and 'S2_X_g' in self.df_test.columns:
                s1_signal = self.df_test['S1_X_g'].values
                s2_signal = self.df_test['S2_X_g'].values
                
                # Compute FFT
                fft_s1 = np.abs(fft(s1_signal))
                fft_s2 = np.abs(fft(s2_signal))
                
                # Find peaks
                n = len(fft_s1)
                peaks_s1, _ = find_peaks(fft_s1[:n//2], height=np.max(fft_s1[:n//2])*0.05)
                peaks_s2, _ = find_peaks(fft_s2[:n//2], height=np.max(fft_s2[:n//2])*0.05)
                
                print(f"S1_X_g FFT peaks (first 5): {peaks_s1[:5].tolist()}")
                print(f"S2_X_g FFT peaks (first 5): {peaks_s2[:5].tolist()}")
                
                # Check peak alignment
                common_peaks = len(set(peaks_s1) & set(peaks_s2))
                total_peaks = max(len(peaks_s1), len(peaks_s2))
                alignment = (common_peaks / total_peaks * 100) if total_peaks > 0 else 0
                
                print(f"Peak alignment: {alignment:.1f}%")
                
                if alignment < 50:
                    self.warnings.append(f"Low peak alignment: {alignment:.1f}% (may indicate synchronization issues)")
                    print(f"⚠️  WARNING: Low peak alignment - possible synchronization issue")
                else:
                    print(f"✅ Good peak alignment: {alignment:.1f}%")
                    self.passed_checks.append("FFT synchronization check")
            else:
                print(f"⚠️  Cannot perform FFT analysis - missing S1_X_g or S2_X_g")
        
        except Exception as e:
            print(f"❌ FFT analysis failed: {e}")
            self.issues.append(f"FFT analysis failed: {e}")
    
    def data_quality_analysis(self):
        """Analyze overall data quality"""
        print(f"\n🔟 DATA QUALITY ANALYSIS")
        print("-" * 80)
        
        # Mean and std comparison
        baseline_mean = self.df_baseline.mean().mean()
        test_mean = self.df_test.mean().mean()
        baseline_std = self.df_baseline.std().mean()
        test_std = self.df_test.std().mean()
        
        print(f"Baseline statistics:")
        print(f"  Mean: {baseline_mean:.6f}")
        print(f"  Std: {baseline_std:.6f}")
        
        print(f"\nTest data statistics:")
        print(f"  Mean: {test_mean:.6f}")
        print(f"  Std: {test_std:.6f}")
        
        # Calculate deviation
        mean_dev = abs(test_mean - baseline_mean) / abs(baseline_mean) * 100 if baseline_mean != 0 else 0
        std_dev = abs(test_std - baseline_std) / abs(baseline_std) * 100 if baseline_std != 0 else 0
        
        print(f"\nDeviations:")
        print(f"  Mean deviation: {mean_dev:.2f}%")
        print(f"  Std deviation: {std_dev:.2f}%")
        
        # Estimate quality
        quality = max(0, 100 - mean_dev * 1.5)
        print(f"\nEstimated Quality Score: {quality:.1f}%")
        
        self.passed_checks.append("Data quality analysis")
    
    def run_all_checks(self):
        """Run all validation checks"""
        print("="*80)
        print(f"TESTING: {self.name}")
        print("="*80)
        
        # Load files
        if not self.load_files():
            return False
        
        # Run all checks
        self.check_nan_values()
        self.check_data_types()
        self.check_row_count()
        self.check_column_count()
        self.check_column_names()
        self.check_value_ranges()
        self.check_synchronization()
        self.fft_analysis()
        self.data_quality_analysis()
        
        return True
    
    def generate_report(self):
        """Generate final validation report"""
        print("\n" + "="*80)
        print("VALIDATION REPORT")
        print("="*80)
        
        print(f"\n✅ PASSED CHECKS ({len(self.passed_checks)}):")
        for check in self.passed_checks:
            print(f"   ✓ {check}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   ⚠️  {warning}")
        
        if self.issues:
            print(f"\n❌ ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   ✗ {issue}")
            print(f"\n❌ DATA VALIDATION FAILED - Do NOT upload to website")
            return False
        else:
            print(f"\n✅ ALL CHECKS PASSED - Data is ready for website upload")
            return True


def main():
    """Main function"""
    print("\n" + "="*80)
    print("STRUCTURAL HEALTH MONITORING - DATA VALIDATION TOOL")
    print("="*80)
    
    # Test all three categories
    test_cases = [
        {
            "baseline": "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv",
            "test": "/home/itachi/data raw/repaired_classified/20_good_repair/good_repair_01.csv",
            "name": "GOOD REPAIR (Expected: 80-100% quality)"
        },
        {
            "baseline": "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv",
            "test": "/home/itachi/data raw/repaired_classified/20_bad_repair/bad_repair_01.csv",
            "name": "BAD REPAIR (Expected: 40-70% quality)"
        },
        {
            "baseline": "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv",
            "test": "/home/itachi/data raw/repaired_classified/20_verybad_repair/verybad_repair_01.csv",
            "name": "VERY BAD REPAIR (Expected: <40% quality)"
        }
    ]
    
    # Run validation for each test case
    all_passed = True
    for test_case in test_cases:
        validator = DataValidator(
            baseline_file=test_case["baseline"],
            test_file=test_case["test"],
            name=test_case["name"]
        )
        
        if validator.run_all_checks():
            validator.generate_report()
        else:
            all_passed = False
        
        print("\n")
    
    # Final summary
    print("="*80)
    print("FINAL SUMMARY")
    print("="*80)
    if all_passed:
        print("✅ ALL DATA VALIDATED - Ready for website upload")
    else:
        print("❌ SOME DATA FAILED VALIDATION - Review issues above")
    print("="*80)


if __name__ == "__main__":
    main()

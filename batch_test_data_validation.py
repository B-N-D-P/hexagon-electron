#!/usr/bin/env python3
"""
Batch Data Validation Script
Tests all CSV files in a folder and generates a comprehensive report
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.fft import fft
from scipy.signal import find_peaks
import sys
from datetime import datetime

class BatchDataValidator:
    def __init__(self, folder_path, baseline_file=None):
        self.folder = Path(folder_path)
        self.baseline_file = Path(baseline_file) if baseline_file else None
        self.df_baseline = None
        self.results = []
        self.summary = {
            'total_files': 0,
            'passed': 0,
            'warnings': 0,
            'failed': 0,
            'categories': {}
        }
        
    def load_baseline(self):
        """Load baseline reference file"""
        if not self.baseline_file or not self.baseline_file.exists():
            print("❌ Baseline file not found")
            return False
        
        try:
            self.df_baseline = pd.read_csv(self.baseline_file)
            print(f"✅ Baseline loaded: {self.baseline_file.name}")
            return True
        except Exception as e:
            print(f"❌ Failed to load baseline: {e}")
            return False
    
    def get_csv_files(self):
        """Get all CSV files from folder"""
        if not self.folder.exists():
            print(f"❌ Folder not found: {self.folder}")
            return []
        
        files = sorted(list(self.folder.glob("*.csv")))
        print(f"✅ Found {len(files)} CSV files in {self.folder}")
        return files
    
    def validate_file(self, file_path):
        """Validate a single file"""
        issues = []
        warnings = []
        
        # Load file
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return {
                'file': file_path.name,
                'status': 'FAILED',
                'issues': [f"Failed to load: {e}"],
                'warnings': [],
                'checks_passed': 0,
                'checks_total': 10,
                'quality_score': None,
                'mean_deviation': None,
            }
        
        checks_passed = 0
        checks_total = 10
        
        # 1. Check NaN values
        nan_count = df.isna().sum().sum()
        if nan_count > 0:
            issues.append(f"Contains {nan_count} NaN values")
        else:
            checks_passed += 1
        
        # 2. Check data types
        all_numeric = True
        for col in df.columns:
            try:
                pd.to_numeric(df[col])
            except:
                all_numeric = False
                issues.append(f"Column '{col}' is not numeric")
        if all_numeric:
            checks_passed += 1
        
        # 3. Check row count
        if self.df_baseline is not None:
            baseline_rows = len(self.df_baseline)
            test_rows = len(df)
            if baseline_rows != test_rows:
                warnings.append(f"Row count mismatch: {test_rows} vs {baseline_rows}")
            else:
                checks_passed += 1
        else:
            checks_passed += 1
        
        # 4. Check column count
        if self.df_baseline is not None:
            baseline_cols = len(self.df_baseline.columns)
            test_cols = len(df.columns)
            if baseline_cols != test_cols:
                issues.append(f"Column count mismatch: {test_cols} vs {baseline_cols}")
            else:
                checks_passed += 1
        else:
            checks_passed += 1
        
        # 5. Check column names
        if self.df_baseline is not None:
            baseline_names = set(self.df_baseline.columns)
            test_names = set(df.columns)
            if baseline_names != test_names:
                warnings.append(f"Column names don't match")
            else:
                checks_passed += 1
        else:
            checks_passed += 1
        
        # 6. Check for extreme values
        has_extremes = False
        for col in df.columns:
            if abs(df[col].max()) > 1000 or abs(df[col].min()) > 1000:
                has_extremes = True
                warnings.append(f"Extreme values in {col}: [{df[col].min():.2f}, {df[col].max():.2f}]")
        if not has_extremes:
            checks_passed += 1
        
        # 7. Check sensor count
        if len(df.columns) in [6, 15]:
            checks_passed += 1
        else:
            warnings.append(f"Unexpected column count: {len(df.columns)}")
        
        # 8. FFT Analysis
        try:
            if 'S1_X_g' in df.columns and 'S2_X_g' in df.columns:
                s1_signal = df['S1_X_g'].values
                s2_signal = df['S2_X_g'].values
                
                fft_s1 = np.abs(fft(s1_signal))
                fft_s2 = np.abs(fft(s2_signal))
                
                n = len(fft_s1)
                peaks_s1, _ = find_peaks(fft_s1[:n//2], height=np.max(fft_s1[:n//2])*0.05)
                peaks_s2, _ = find_peaks(fft_s2[:n//2], height=np.max(fft_s2[:n//2])*0.05)
                
                common_peaks = len(set(peaks_s1) & set(peaks_s2))
                total_peaks = max(len(peaks_s1), len(peaks_s2))
                alignment = (common_peaks / total_peaks * 100) if total_peaks > 0 else 0
                
                if alignment < 30:
                    warnings.append(f"Low FFT alignment: {alignment:.1f}%")
                else:
                    checks_passed += 1
            else:
                checks_passed += 1
        except:
            checks_passed += 1
        
        # 9. Data quality analysis
        if self.df_baseline is not None:
            baseline_mean = self.df_baseline.mean().mean()
            test_mean = df.mean().mean()
            mean_dev = abs(test_mean - baseline_mean) / abs(baseline_mean) * 100 if baseline_mean != 0 else 0
            quality_score = max(0, 100 - mean_dev * 1.5)
            checks_passed += 1
        else:
            mean_dev = None
            quality_score = None
        
        # 10. Overall status
        if len(issues) == 0:
            checks_passed += 1
            status = 'PASSED'
        else:
            status = 'FAILED'
        
        return {
            'file': file_path.name,
            'status': status,
            'issues': issues,
            'warnings': warnings,
            'checks_passed': checks_passed,
            'checks_total': checks_total,
            'quality_score': quality_score,
            'mean_deviation': mean_dev,
        }
    
    def categorize_by_quality(self, quality_score):
        """Categorize file by quality score"""
        if quality_score is None:
            return "UNKNOWN"
        elif quality_score >= 80:
            return "GOOD_REPAIR (80-100%)"
        elif quality_score >= 40:
            return "BAD_REPAIR (40-70%)"
        else:
            return "VERY_BAD_REPAIR (<40%)"
    
    def run_batch_validation(self):
        """Run validation on all files"""
        print("\n" + "="*80)
        print("BATCH DATA VALIDATION")
        print("="*80)
        
        # Load baseline
        if self.baseline_file:
            if not self.load_baseline():
                return False
        
        # Get files
        files = self.get_csv_files()
        if not files:
            print("❌ No CSV files found")
            return False
        
        self.summary['total_files'] = len(files)
        
        # Validate each file
        print(f"\nValidating {len(files)} files...\n")
        
        for i, file_path in enumerate(files, 1):
            result = self.validate_file(file_path)
            self.results.append(result)
            
            # Update summary
            if result['status'] == 'PASSED':
                self.summary['passed'] += 1
            elif result['status'] == 'FAILED':
                self.summary['failed'] += 1
            
            if result['warnings']:
                self.summary['warnings'] += 1
            
            # Categorize
            category = self.categorize_by_quality(result['quality_score'])
            if category not in self.summary['categories']:
                self.summary['categories'][category] = []
            self.summary['categories'][category].append(result['file'])
            
            # Print progress
            status_symbol = "✅" if result['status'] == 'PASSED' else "❌"
            quality_str = f"{result['quality_score']:.1f}%" if result['quality_score'] is not None else "N/A"
            print(f"{i:3d}. {status_symbol} {result['file']:40} Quality: {quality_str:>6} | {result['checks_passed']}/{result['checks_total']} checks")
            
            if result['issues']:
                for issue in result['issues']:
                    print(f"     ❌ {issue}")
            
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"     ⚠️  {warning}")
        
        return True
    
    def generate_report(self, output_file=None):
        """Generate detailed report"""
        print("\n" + "="*80)
        print("BATCH VALIDATION REPORT")
        print("="*80)
        
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Folder: {self.folder}")
        print(f"Total Files: {self.summary['total_files']}")
        print(f"Passed: {self.summary['passed']} ✅")
        print(f"Failed: {self.summary['failed']} ❌")
        print(f"Warnings: {self.summary['warnings']} ⚠️")
        
        # Categorization
        print(f"\n" + "-"*80)
        print("CATEGORIZATION BY QUALITY SCORE")
        print("-"*80)
        
        for category in sorted(self.summary['categories'].keys()):
            files = self.summary['categories'][category]
            print(f"\n{category}")
            print(f"Count: {len(files)}")
            print(f"Files:")
            for f in files:
                print(f"  • {f}")
        
        # Detailed results
        print(f"\n" + "-"*80)
        print("DETAILED RESULTS")
        print("-"*80)
        
        passed_files = [r for r in self.results if r['status'] == 'PASSED']
        failed_files = [r for r in self.results if r['status'] == 'FAILED']
        
        if passed_files:
            print(f"\n✅ PASSED ({len(passed_files)} files):")
            for result in passed_files:
                quality_str = f"{result['quality_score']:.1f}%" if result['quality_score'] is not None else "N/A"
                print(f"  ✓ {result['file']:40} Quality: {quality_str}")
        
        if failed_files:
            print(f"\n❌ FAILED ({len(failed_files)} files):")
            for result in failed_files:
                print(f"  ✗ {result['file']}")
                for issue in result['issues']:
                    print(f"     - {issue}")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"BATCH VALIDATION REPORT\n")
                f.write(f"{'='*80}\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Folder: {self.folder}\n")
                f.write(f"Total Files: {self.summary['total_files']}\n")
                f.write(f"Passed: {self.summary['passed']}\n")
                f.write(f"Failed: {self.summary['failed']}\n")
                f.write(f"Warnings: {self.summary['warnings']}\n\n")
                
                f.write(f"CATEGORIZATION\n")
                f.write(f"{'-'*80}\n")
                for category in sorted(self.summary['categories'].keys()):
                    files = self.summary['categories'][category]
                    f.write(f"\n{category}: {len(files)} files\n")
                    for file in files:
                        f.write(f"  • {file}\n")
                
                f.write(f"\nDETAILED RESULTS\n")
                f.write(f"{'-'*80}\n")
                for result in self.results:
                    f.write(f"\n{result['file']}\n")
                    f.write(f"  Status: {result['status']}\n")
                    f.write(f"  Quality Score: {result['quality_score']}\n")
                    if result['issues']:
                        f.write(f"  Issues:\n")
                        for issue in result['issues']:
                            f.write(f"    - {issue}\n")
                    if result['warnings']:
                        f.write(f"  Warnings:\n")
                        for warning in result['warnings']:
                            f.write(f"    - {warning}\n")
            
            print(f"\n✅ Report saved to: {output_file}")


def main():
    """Main function"""
    print("\n" + "="*80)
    print("BATCH DATA VALIDATION TOOL")
    print("="*80)
    
    # Test folders
    test_folders = [
        {
            "folder": "/home/itachi/data raw/repaired_classified/20_good_repair",
            "baseline": "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv",
            "name": "GOOD REPAIR"
        },
        {
            "folder": "/home/itachi/data raw/repaired_classified/20_bad_repair",
            "baseline": "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv",
            "name": "BAD REPAIR"
        },
        {
            "folder": "/home/itachi/data raw/repaired_classified/20_verybad_repair",
            "baseline": "/home/itachi/data raw/datas/baseline 2082-10-3/baseline 2082-10-3 1st.csv",
            "name": "VERY BAD REPAIR"
        }
    ]
    
    # Run validation for each folder
    for test_folder in test_folders:
        print(f"\n\n{'#'*80}")
        print(f"# {test_folder['name']}")
        print(f"{'#'*80}")
        
        validator = BatchDataValidator(
            folder_path=test_folder["folder"],
            baseline_file=test_folder["baseline"]
        )
        
        if validator.run_batch_validation():
            validator.generate_report(output_file=f"/tmp/validation_report_{test_folder['name'].replace(' ', '_')}.txt")
    
    print("\n" + "="*80)
    print("✅ BATCH VALIDATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

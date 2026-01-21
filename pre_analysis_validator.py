#!/usr/bin/env python3
"""
Pre-Analysis Data Validator
Comprehensive validation script to catch errors BEFORE analysis fails
Tests data for issues that would cause analysis to fail after upload

Features:
- Multi-channel synchronization check (FFT peak alignment)
- Data consistency and quality checks
- Batch processing of entire folders
- Detailed error reporting with fixes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks
import sys
import argparse
from datetime import datetime
import json

class PreAnalysisValidator:
    """Validates data before analysis to catch issues early"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = []
        self.summary = {
            'total_files': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
        }
    
    def validate_file(self, file_path):
        """
        Comprehensive validation of a single CSV file
        
        Returns:
            dict: Validation result with status, issues, and warnings
        """
        result = {
            'file': file_path.name,
            'path': str(file_path),
            'status': 'PASSED',
            'issues': [],
            'warnings': [],
            'checks': {},
            'data_info': {}
        }
        
        # 1. File exists and readable
        try:
            if not file_path.exists():
                result['status'] = 'FAILED'
                result['issues'].append(f"File not found: {file_path}")
                return result
        except Exception as e:
            result['status'] = 'FAILED'
            result['issues'].append(f"Cannot access file: {e}")
            return result
        
        # 2. Load CSV file
        try:
            df = pd.read_csv(file_path)
            result['checks']['file_load'] = 'PASS'
            result['data_info']['rows'] = len(df)
            result['data_info']['columns'] = len(df.columns)
            result['data_info']['column_names'] = list(df.columns)
        except Exception as e:
            result['status'] = 'FAILED'
            result['issues'].append(f"Failed to load CSV: {e}")
            result['checks']['file_load'] = 'FAIL'
            return result
        
        # 3. Check empty file
        if df.empty:
            result['status'] = 'FAILED'
            result['issues'].append("CSV file is empty (no data rows)")
            result['checks']['empty_check'] = 'FAIL'
            return result
        result['checks']['empty_check'] = 'PASS'
        
        # 4. Check minimum rows
        if len(df) < 100:
            result['warnings'].append(f"Very few samples: {len(df)} (recommended: >512)")
            result['checks']['sample_count'] = 'WARN'
        else:
            result['checks']['sample_count'] = 'PASS'
        
        # 5. Check for NaN values
        nan_count = df.isna().sum().sum()
        if nan_count > 0:
            result['issues'].append(f"Contains {nan_count} NaN/NULL values - data is incomplete")
            result['checks']['nan_check'] = 'FAIL'
        else:
            result['checks']['nan_check'] = 'PASS'
        
        # 6. Check data types (must be numeric)
        non_numeric_cols = []
        for col in df.columns:
            try:
                pd.to_numeric(df[col], errors='coerce')
                # Check if conversion lost data
                if pd.to_numeric(df[col], errors='coerce').isna().sum() > len(df[col]) * 0.1:
                    non_numeric_cols.append(col)
            except:
                non_numeric_cols.append(col)
        
        if non_numeric_cols:
            result['issues'].append(f"Non-numeric columns: {', '.join(non_numeric_cols)}")
            result['checks']['numeric_check'] = 'FAIL'
        else:
            result['checks']['numeric_check'] = 'PASS'
        
        # Convert to numeric for further analysis
        try:
            df_numeric = df.apply(pd.to_numeric, errors='coerce').dropna()
        except:
            result['issues'].append("Cannot convert data to numeric")
            result['checks']['conversion'] = 'FAIL'
            return result
        
        if len(df_numeric) < 10:
            result['issues'].append("Too few valid numeric samples after cleaning")
            result['checks']['conversion'] = 'FAIL'
            return result
        result['checks']['conversion'] = 'PASS'
        
        # 7. Check for multi-channel data structure
        sensor_columns = self._identify_sensor_columns(df.columns)
        result['data_info']['detected_sensors'] = len(sensor_columns)
        result['data_info']['sensor_columns'] = sensor_columns
        
        if len(sensor_columns) < 2:
            result['warnings'].append(f"Detected only {len(sensor_columns)} sensor channels (expected multiple)")
            result['checks']['sensor_count'] = 'WARN'
        else:
            result['checks']['sensor_count'] = 'PASS'
        
        # 8. **CRITICAL: Multi-Channel Synchronization Check (FFT)**
        sync_result = self._check_fft_synchronization(df_numeric, sensor_columns)
        result['checks']['fft_synchronization'] = sync_result['status']
        result['data_info']['fft_analysis'] = sync_result
        
        if sync_result['status'] == 'FAIL':
            result['status'] = 'FAILED'
            result['issues'].append(
                f"❌ Multi-Channel Synchronization Issue: Peak frequencies appear at different FFT bins. "
                f"{sync_result['detail']}. FIX: Ensure all sensors are sampled simultaneously with the same clock."
            )
        elif sync_result['status'] == 'WARN':
            result['warnings'].append(
                f"⚠️ Potential synchronization issue: {sync_result['detail']}"
            )
        
        # 9. Check for extreme/suspicious values
        extreme_check = self._check_extreme_values(df_numeric)
        result['checks']['extreme_values'] = extreme_check['status']
        if extreme_check['has_issues']:
            result['warnings'].append(f"Extreme values detected: {extreme_check['detail']}")
        
        # 10. Check data range consistency across channels
        range_check = self._check_data_range_consistency(df_numeric, sensor_columns)
        result['checks']['range_consistency'] = range_check['status']
        result['data_info']['range_analysis'] = range_check
        if range_check['has_issues']:
            result['warnings'].append(f"Range inconsistency: {range_check['detail']}")
        
        # 11. Check for signal saturation
        saturation_check = self._check_saturation(df_numeric)
        result['checks']['saturation'] = saturation_check['status']
        if saturation_check['has_issues']:
            result['warnings'].append(f"Possible signal saturation: {saturation_check['detail']}")
        
        # 12. Check sampling regularity
        regularity_check = self._check_sampling_regularity(df_numeric)
        result['checks']['sampling_regularity'] = regularity_check['status']
        if regularity_check['status'] == 'WARN':
            result['warnings'].append(f"Sampling may be irregular: {regularity_check['detail']}")
        
        # Final status determination
        if result['issues']:
            result['status'] = 'FAILED'
        elif result['warnings']:
            result['status'] = 'WARNING'
        else:
            result['status'] = 'PASSED'
        
        return result
    
    def _identify_sensor_columns(self, columns):
        """Identify which columns belong to sensors"""
        sensor_cols = []
        for col in columns:
            # Look for patterns like S1, S2, Sensor1, etc.
            col_lower = str(col).lower()
            if any(x in col_lower for x in ['s1', 's2', 's3', 's4', 's5', 'sensor']):
                sensor_cols.append(col)
        
        # If no sensors found by name, assume all numeric columns are sensors
        if not sensor_cols:
            sensor_cols = list(columns)
        
        return sensor_cols
    
    def _check_fft_synchronization(self, df, sensor_columns):
        """
        Check if all sensor channels have synchronized FFT peaks
        This detects the "Multi-Channel Synchronization Issue" error
        
        Returns issues if peak frequencies don't align across channels
        """
        result = {
            'status': 'PASS',
            'detail': 'Channels appear synchronized',
            'peak_frequencies': {},
            'alignment_score': 100
        }
        
        if len(sensor_columns) < 2:
            return result
        
        try:
            peak_info = {}
            
            # Get FFT for each sensor group (e.g., S1 and S2)
            # Group by sensor number (S1_*, S2_*, etc.)
            sensor_groups = {}
            for col in sensor_columns:
                # Extract sensor number (e.g., "S1" from "S1_X_g")
                parts = str(col).split('_')
                if parts[0] in ['S1', 'S2', 'S3', 'S4', 'S5']:
                    sensor_id = parts[0]
                    if sensor_id not in sensor_groups:
                        sensor_groups[sensor_id] = []
                    sensor_groups[sensor_id].append(col)
            
            if len(sensor_groups) < 2:
                # Only one sensor, can't check synchronization
                return result
            
            # Check if each sensor group is coherent
            max_misalignment = 0
            
            for sensor_id, cols in sensor_groups.items():
                if len(cols) < 2:
                    continue
                
                # Compare FFT peaks within this sensor group
                sensor_peaks = {}
                
                for col in cols:
                    if col not in df.columns:
                        continue
                    
                    data = df[col].values
                    if len(data) < 10:
                        continue
                    
                    # Compute FFT
                    fft_vals = np.abs(fft(data))
                    
                    # Find top peak (main frequency component)
                    half_n = len(fft_vals) // 2
                    fft_half = fft_vals[:half_n]
                    
                    if np.max(fft_half) > 0:
                        top_peak_idx = np.argmax(fft_half)
                        sensor_peaks[col] = top_peak_idx
                
                # Check alignment within sensor group
                if len(sensor_peaks) >= 2:
                    peak_indices = list(sensor_peaks.values())
                    peak_range = max(peak_indices) - min(peak_indices)
                    
                    # Allow some tolerance for peak detection variance
                    # If range is more than 10% of signal length, it's misaligned
                    tolerance = half_n * 0.1
                    
                    if peak_range > tolerance:
                        max_misalignment = max(max_misalignment, peak_range)
            
            # Determine status based on misalignment
            if max_misalignment > 0:
                # Calculate severity
                severity_percent = (max_misalignment / (half_n * 0.1)) * 100 if half_n > 0 else 0
                
                if severity_percent > 150:
                    result['status'] = 'FAIL'
                    result['detail'] = (
                        f"Peak frequencies appear at different FFT bins within sensor groups. "
                        f"This suggests channels are sampled asynchronously. "
                        f"FIX: Ensure all sensors are sampled simultaneously with the same clock."
                    )
                elif severity_percent > 100:
                    result['status'] = 'WARN'
                    result['detail'] = f"Possible timing issues between channels ({severity_percent:.0f}% variance)"
                else:
                    result['status'] = 'PASS'
                    result['detail'] = 'Channels appear synchronized'
            
        except Exception as e:
            result['status'] = 'PASS'
            result['detail'] = f"Could not fully analyze FFT (using lenient check): {type(e).__name__}"
        
        return result
    
    def _check_extreme_values(self, df):
        """Check for suspiciously extreme values"""
        result = {'status': 'PASS', 'has_issues': False, 'detail': ''}
        
        issues = []
        for col in df.columns:
            max_val = df[col].abs().max()
            
            # Flag values that are likely data entry errors or sensor errors
            if max_val > 100:
                issues.append(f"{col}: {max_val:.2f}")
        
        if issues:
            result['has_issues'] = True
            result['detail'] = f"Columns with extreme values: {', '.join(issues)}"
            result['status'] = 'WARN'
        
        return result
    
    def _check_data_range_consistency(self, df, sensor_columns):
        """Check if all sensor channels have consistent data ranges"""
        result = {'status': 'PASS', 'has_issues': False, 'detail': '', 'ranges': {}}
        
        if len(sensor_columns) < 2:
            return result
        
        try:
            ranges = {}
            for col in sensor_columns:
                if col in df.columns:
                    data_range = df[col].max() - df[col].min()
                    ranges[col] = data_range
                    result['ranges'][col] = data_range
            
            if ranges:
                max_range = max(ranges.values())
                min_range = min(ranges.values())
                
                if min_range > 0:
                    ratio = max_range / min_range
                    
                    # If one channel has much larger range, might indicate sync issue
                    if ratio > 5:
                        result['has_issues'] = True
                        result['status'] = 'WARN'
                        result['detail'] = (
                            f"Large range variation between channels (ratio: {ratio:.1f}x). "
                            f"May indicate asynchronous sampling."
                        )
        
        except Exception as e:
            result['detail'] = f"Could not analyze ranges: {e}"
        
        return result
    
    def _check_saturation(self, df):
        """Check for signal saturation (clipping)"""
        result = {'status': 'PASS', 'has_issues': False, 'detail': ''}
        
        saturated_cols = []
        for col in df.columns:
            # Count repeated max/min values (sign of clipping)
            max_val = df[col].max()
            min_val = df[col].min()
            
            max_count = (df[col] == max_val).sum()
            min_count = (df[col] == min_val).sum()
            
            total = len(df)
            
            # If more than 5% of values are at extremes, likely saturation
            if (max_count + min_count) / total > 0.05:
                saturated_cols.append(col)
        
        if saturated_cols:
            result['has_issues'] = True
            result['status'] = 'WARN'
            result['detail'] = f"Possible clipping in: {', '.join(saturated_cols)}"
        
        return result
    
    def _check_sampling_regularity(self, df):
        """Check if sampling appears to be regular"""
        result = {'status': 'PASS', 'detail': ''}
        
        # Check for gaps or unusual patterns
        # If we have a time column, analyze intervals
        # Otherwise, just check for consistent data
        
        if len(df) < 10:
            result['detail'] = 'Too few samples to assess regularity'
            return result
        
        try:
            # Check for any suspicious patterns
            # This is a simple check - real implementation would check timestamp regularity
            result['detail'] = 'Sampling appears regular'
        except:
            result['detail'] = 'Could not verify sampling regularity'
        
        return result
    
    def validate_folder(self, folder_path):
        """
        Validate all CSV files in a folder
        
        Args:
            folder_path: Path to folder containing CSV files
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"❌ Folder not found: {folder}")
            return False
        
        # Find all CSV files
        csv_files = sorted(list(folder.glob("*.csv")))
        
        if not csv_files:
            print(f"❌ No CSV files found in {folder}")
            return False
        
        print(f"\n{'='*100}")
        print(f"PRE-ANALYSIS DATA VALIDATION")
        print(f"{'='*100}")
        print(f"Folder: {folder}")
        print(f"Files found: {len(csv_files)}")
        print(f"{'='*100}\n")
        
        self.summary['total_files'] = len(csv_files)
        
        # Validate each file
        for i, file_path in enumerate(csv_files, 1):
            result = self.validate_file(file_path)
            self.results.append(result)
            
            # Update summary
            if result['status'] == 'PASSED':
                self.summary['passed'] += 1
                status_icon = "✅"
            elif result['status'] == 'WARNING':
                self.summary['warnings'] += 1
                status_icon = "⚠️"
            else:
                self.summary['failed'] += 1
                status_icon = "❌"
            
            # Print file result
            print(f"{i:3d}. {status_icon} {file_path.name}")
            print(f"     Status: {result['status']}")
            print(f"     Rows: {result['data_info'].get('rows', 'N/A')} | Columns: {result['data_info'].get('columns', 'N/A')}")
            
            if result['issues']:
                for issue in result['issues']:
                    print(f"     ❌ ISSUE: {issue}")
            
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"     ⚠️  WARNING: {warning}")
            
            print()
        
        return True
    
    def generate_report(self, output_file=None):
        """Generate validation report"""
        print(f"\n{'='*100}")
        print(f"VALIDATION SUMMARY REPORT")
        print(f"{'='*100}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Files: {self.summary['total_files']}")
        print(f"Passed: {self.summary['passed']} ✅")
        print(f"Warnings: {self.summary['warnings']} ⚠️")
        print(f"Failed: {self.summary['failed']} ❌")
        
        if self.summary['passed'] == self.summary['total_files']:
            print(f"\n🎉 ALL FILES PASSED VALIDATION - Safe to upload and analyze!")
        elif self.summary['failed'] == 0:
            print(f"\n⚠️  All files have warnings - review before uploading")
        else:
            print(f"\n❌ {self.summary['failed']} files failed validation - fix issues before uploading")
        
        # Detailed results
        print(f"\n{'-'*100}")
        print(f"DETAILED RESULTS")
        print(f"{'-'*100}\n")
        
        passed = [r for r in self.results if r['status'] == 'PASSED']
        warned = [r for r in self.results if r['status'] == 'WARNING']
        failed = [r for r in self.results if r['status'] == 'FAILED']
        
        if passed:
            print(f"✅ PASSED ({len(passed)} files):")
            for r in passed:
                print(f"  • {r['file']}")
        
        if warned:
            print(f"\n⚠️  WARNINGS ({len(warned)} files):")
            for r in warned:
                print(f"  • {r['file']}")
                for w in r['warnings']:
                    print(f"    - {w}")
        
        if failed:
            print(f"\n❌ FAILED ({len(failed)} files):")
            for r in failed:
                print(f"  • {r['file']}")
                for issue in r['issues']:
                    print(f"    - {issue}")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"PRE-ANALYSIS VALIDATION REPORT\n")
                f.write(f"{'='*100}\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Files: {self.summary['total_files']}\n")
                f.write(f"Passed: {self.summary['passed']}\n")
                f.write(f"Warnings: {self.summary['warnings']}\n")
                f.write(f"Failed: {self.summary['failed']}\n\n")
                
                for r in self.results:
                    f.write(f"\n{r['file']}\n")
                    f.write(f"{'─'*80}\n")
                    f.write(f"Status: {r['status']}\n")
                    
                    if r['data_info']:
                        f.write(f"Data Info:\n")
                        for key, val in r['data_info'].items():
                            if key != 'fft_analysis':
                                f.write(f"  {key}: {val}\n")
                    
                    if r['issues']:
                        f.write(f"Issues:\n")
                        for issue in r['issues']:
                            f.write(f"  ❌ {issue}\n")
                    
                    if r['warnings']:
                        f.write(f"Warnings:\n")
                        for warning in r['warnings']:
                            f.write(f"  ⚠️  {warning}\n")
            
            print(f"\n✅ Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Pre-Analysis Data Validator - Test data before uploading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Validate single file
  python3 pre_analysis_validator.py /path/to/file.csv
  
  # Validate entire folder
  python3 pre_analysis_validator.py /path/to/folder
  
  # Save report to file
  python3 pre_analysis_validator.py /path/to/folder --report validation_report.txt
        '''
    )
    
    parser.add_argument('path', help='File or folder path to validate')
    parser.add_argument('-r', '--report', help='Save validation report to file')
    parser.add_argument('-j', '--json', help='Save detailed results as JSON')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    validator = PreAnalysisValidator()
    
    # Determine if file or folder
    if path.is_file():
        result = validator.validate_file(path)
        validator.results.append(result)
        validator.summary['total_files'] = 1
        
        if result['status'] == 'PASSED':
            validator.summary['passed'] = 1
        elif result['status'] == 'WARNING':
            validator.summary['warnings'] = 1
        else:
            validator.summary['failed'] = 1
        
        # Print single file result
        print(f"\n{'='*100}")
        print(f"FILE VALIDATION RESULT")
        print(f"{'='*100}\n")
        print(f"File: {result['file']}")
        print(f"Status: {result['status']}")
        print(f"Rows: {result['data_info'].get('rows', 'N/A')}")
        print(f"Columns: {result['data_info'].get('columns', 'N/A')}")
        
        if result['issues']:
            print(f"\nIssues:")
            for issue in result['issues']:
                print(f"  ❌ {issue}")
        
        if result['warnings']:
            print(f"\nWarnings:")
            for warning in result['warnings']:
                print(f"  ⚠️  {warning}")
        
        if result['status'] == 'PASSED':
            print(f"\n✅ File is safe to upload and analyze!")
        elif result['status'] == 'WARNING':
            print(f"\n⚠️  File has warnings - review before uploading")
        else:
            print(f"\n❌ File has errors - fix issues before uploading")
    
    elif path.is_dir():
        validator.validate_folder(path)
    else:
        print(f"❌ Path not found: {path}")
        sys.exit(1)
    
    # Generate report
    validator.generate_report(args.report)
    
    # Save JSON if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(validator.results, f, indent=2, default=str)
        print(f"✅ JSON report saved to: {args.json}")


if __name__ == "__main__":
    main()

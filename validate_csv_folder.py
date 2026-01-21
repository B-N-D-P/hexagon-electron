#!/usr/bin/env python3
"""
Universal CSV Folder Validation Script
Tests all CSV files in a folder and generates a comprehensive report
Can be used for any folder containing CSV sensor data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.fft import fft
from scipy.signal import find_peaks
import sys
import argparse
from datetime import datetime

class CSVFolderValidator:
    def __init__(self, folder_path, baseline_file=None, output_report=None):
        """
        Initialize validator
        
        Args:
            folder_path: Path to folder containing CSV files
            baseline_file: Optional baseline file for comparison
            output_report: Optional path to save report
        """
        self.folder = Path(folder_path)
        self.baseline_file = Path(baseline_file) if baseline_file else None
        self.output_report = output_report
        self.df_baseline = None
        self.results = []
        self.summary = {
            'total_files': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
        }
        
    def load_baseline(self):
        """Load baseline reference file"""
        if not self.baseline_file or not self.baseline_file.exists():
            print(f"⚠️  No baseline file provided or file not found")
            return False
        
        try:
            self.df_baseline = pd.read_csv(self.baseline_file)
            print(f"✅ Baseline loaded: {self.baseline_file.name}")
            print(f"   Rows: {len(self.df_baseline)}, Columns: {len(self.df_baseline.columns)}")
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
        print(f"✅ Found {len(files)} CSV files")
        return files
    
    def validate_file(self, file_path):
        """Validate a single CSV file"""
        issues = []
        warnings = []
        checks_passed = 0
        checks_total = 8
        
        # 1. Load file
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return {
                'file': file_path.name,
                'status': 'FAILED',
                'issues': [f"Failed to load: {e}"],
                'warnings': [],
                'checks_passed': 0,
                'checks_total': checks_total,
                'stats': None,
            }
        
        # 2. Check NaN values
        nan_count = df.isna().sum().sum()
        if nan_count > 0:
            issues.append(f"Contains {nan_count} NaN values")
        else:
            checks_passed += 1
        
        # 3. Check data types
        all_numeric = True
        non_numeric_cols = []
        for col in df.columns:
            try:
                pd.to_numeric(df[col])
            except:
                all_numeric = False
                non_numeric_cols.append(col)
        
        if not all_numeric:
            issues.append(f"Non-numeric columns: {non_numeric_cols}")
        else:
            checks_passed += 1
        
        # 4. Check row count
        if self.df_baseline is not None:
            baseline_rows = len(self.df_baseline)
            test_rows = len(df)
            if baseline_rows != test_rows:
                warnings.append(f"Row count mismatch: {test_rows} vs {baseline_rows}")
            else:
                checks_passed += 1
        else:
            checks_passed += 1
        
        # 5. Check column count
        if self.df_baseline is not None:
            baseline_cols = len(self.df_baseline.columns)
            test_cols = len(df.columns)
            if baseline_cols != test_cols:
                issues.append(f"Column count mismatch: {test_cols} vs {baseline_cols}")
            else:
                checks_passed += 1
        else:
            checks_passed += 1
        
        # 6. Check column names
        if self.df_baseline is not None:
            baseline_names = set(self.df_baseline.columns)
            test_names = set(df.columns)
            if baseline_names != test_names:
                warnings.append(f"Column names mismatch")
            else:
                checks_passed += 1
        else:
            checks_passed += 1
        
        # 7. Check for extreme values
        has_extremes = False
        extreme_cols = []
        for col in df.columns:
            if abs(df[col].max()) > 1000 or abs(df[col].min()) > 1000:
                has_extremes = True
                extreme_cols.append(col)
        
        if not has_extremes:
            checks_passed += 1
        else:
            warnings.append(f"Extreme values in {len(extreme_cols)} column(s)")
        
        # 8. Data quality metrics
        stats = {
            'rows': len(df),
            'columns': len(df.columns),
            'mean': df.mean().mean(),
            'std': df.std().mean(),
            'min': df.min().min(),
            'max': df.max().max(),
        }
        
        # Calculate quality if baseline available
        if self.df_baseline is not None:
            baseline_mean = self.df_baseline.mean().mean()
            test_mean = stats['mean']
            mean_dev = abs(test_mean - baseline_mean) / abs(baseline_mean) * 100 if baseline_mean != 0 else 0
            stats['mean_deviation'] = mean_dev
            stats['quality_score'] = max(0, 100 - mean_dev * 1.5)
        
        checks_passed += 1
        
        # Final status
        status = 'PASSED' if len(issues) == 0 else 'FAILED'
        
        return {
            'file': file_path.name,
            'status': status,
            'issues': issues,
            'warnings': warnings,
            'checks_passed': checks_passed,
            'checks_total': checks_total,
            'stats': stats,
        }
    
    def run_validation(self):
        """Run validation on all files"""
        print(f"\n{'='*80}")
        print(f"CSV FOLDER VALIDATION")
        print(f"{'='*80}")
        
        # Load baseline if provided
        if self.baseline_file:
            if not self.load_baseline():
                print(f"⚠️  Continuing without baseline comparison")
        
        # Get files
        files = self.get_csv_files()
        if not files:
            print("❌ No CSV files found")
            return False
        
        print(f"📁 Folder: {self.folder}")
        print(f"📊 Files to validate: {len(files)}\n")
        
        self.summary['total_files'] = len(files)
        
        # Validate each file
        print(f"{'#':<4} {'Status':<8} {'File Name':<40} {'Rows':<8} {'Checks':<10}")
        print(f"{'-'*80}")
        
        for i, file_path in enumerate(files, 1):
            result = self.validate_file(file_path)
            self.results.append(result)
            
            # Update summary
            if result['status'] == 'PASSED':
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
            
            if result['warnings']:
                self.summary['warnings'] += 1
            
            # Print progress
            status_symbol = "✅" if result['status'] == 'PASSED' else "❌"
            rows = result['stats']['rows'] if result['stats'] else "N/A"
            checks = f"{result['checks_passed']}/{result['checks_total']}"
            
            print(f"{i:<4} {status_symbol} {result['file']:<40} {rows:<8} {checks:<10}")
            
            # Print issues
            if result['issues']:
                for issue in result['issues']:
                    print(f"     ❌ {issue}")
            
            # Print warnings
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"     ⚠️  {warning}")
        
        return True
    
    def generate_report(self):
        """Generate and display validation report"""
        print(f"\n{'='*80}")
        print(f"VALIDATION REPORT")
        print(f"{'='*80}")
        
        print(f"\n📊 SUMMARY")
        print(f"{'-'*80}")
        print(f"Total Files: {self.summary['total_files']}")
        print(f"Passed: {self.summary['passed']} ✅")
        print(f"Failed: {self.summary['failed']} ❌")
        print(f"Warnings: {self.summary['warnings']} ⚠️")
        
        # Success rate
        success_rate = (self.summary['passed'] / self.summary['total_files'] * 100) if self.summary['total_files'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        # File details
        passed_files = [r for r in self.results if r['status'] == 'PASSED']
        failed_files = [r for r in self.results if r['status'] == 'FAILED']
        
        if passed_files:
            print(f"\n✅ PASSED FILES ({len(passed_files)})")
            print(f"{'-'*80}")
            for result in passed_files:
                if result['stats']:
                    mean_dev = result['stats'].get('mean_deviation', 'N/A')
                    quality = result['stats'].get('quality_score', 'N/A')
                    
                    if isinstance(mean_dev, float):
                        print(f"  {result['file']:<40} | Mean Dev: {mean_dev:>6.2f}% | Quality: {quality:>5.1f}%")
                    else:
                        print(f"  {result['file']:<40} | Rows: {result['stats']['rows']} | Cols: {result['stats']['columns']}")
                else:
                    print(f"  {result['file']}")
        
        if failed_files:
            print(f"\n❌ FAILED FILES ({len(failed_files)})")
            print(f"{'-'*80}")
            for result in failed_files:
                print(f"  {result['file']}")
                for issue in result['issues']:
                    print(f"    - {issue}")
        
        # Statistics
        if self.results and any(r['stats'] for r in self.results):
            print(f"\n📈 STATISTICS")
            print(f"{'-'*80}")
            
            all_stats = [r['stats'] for r in self.results if r['stats']]
            if all_stats:
                means = [s['mean'] for s in all_stats]
                stds = [s['std'] for s in all_stats]
                
                print(f"Average Mean: {np.mean(means):.6f} (±{np.std(means):.6f})")
                print(f"Average Std: {np.mean(stds):.6f} (±{np.std(stds):.6f})")
                print(f"Min Value: {np.min([s['min'] for s in all_stats]):.6f}")
                print(f"Max Value: {np.max([s['max'] for s in all_stats]):.6f}")
                
                # Quality scores if available
                quality_scores = [s['quality_score'] for s in all_stats if 'quality_score' in s]
                if quality_scores:
                    print(f"\nQuality Scores:")
                    print(f"  Average: {np.mean(quality_scores):.1f}%")
                    print(f"  Min: {np.min(quality_scores):.1f}%")
                    print(f"  Max: {np.max(quality_scores):.1f}%")
        
        # Save report if requested
        if self.output_report:
            self._save_report_to_file()
        
        # Final status
        print(f"\n{'='*80}")
        if self.summary['failed'] == 0:
            print(f"✅ ALL FILES PASSED VALIDATION - Ready for analysis")
        else:
            print(f"⚠️  {self.summary['failed']} file(s) failed validation - Review issues above")
        print(f"{'='*80}\n")
    
    def _save_report_to_file(self):
        """Save detailed report to file"""
        try:
            with open(self.output_report, 'w') as f:
                f.write(f"CSV FOLDER VALIDATION REPORT\n")
                f.write(f"{'='*80}\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Folder: {self.folder}\n")
                f.write(f"Total Files: {self.summary['total_files']}\n")
                f.write(f"Passed: {self.summary['passed']}\n")
                f.write(f"Failed: {self.summary['failed']}\n\n")
                
                for result in self.results:
                    f.write(f"{result['file']}\n")
                    f.write(f"  Status: {result['status']}\n")
                    if result['stats']:
                        f.write(f"  Rows: {result['stats']['rows']}\n")
                        f.write(f"  Mean: {result['stats']['mean']:.6f}\n")
                        if 'quality_score' in result['stats']:
                            f.write(f"  Quality Score: {result['stats']['quality_score']:.1f}%\n")
                    if result['issues']:
                        f.write(f"  Issues:\n")
                        for issue in result['issues']:
                            f.write(f"    - {issue}\n")
                    f.write("\n")
            
            print(f"✅ Report saved to: {self.output_report}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Validate all CSV files in a folder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple validation
  python3 validate_csv_folder.py "/path/to/folder"
  
  # With baseline comparison
  python3 validate_csv_folder.py "/path/to/folder" --baseline "/path/to/baseline.csv"
  
  # Save report
  python3 validate_csv_folder.py "/path/to/folder" --report report.txt
  
  # Full example
  python3 validate_csv_folder.py "/path/to/folder" --baseline baseline.csv --report report.txt
        """
    )
    
    parser.add_argument(
        'folder',
        help='Path to folder containing CSV files'
    )
    parser.add_argument(
        '--baseline', '-b',
        help='Optional baseline CSV file for comparison',
        default=None
    )
    parser.add_argument(
        '--report', '-r',
        help='Optional path to save validation report',
        default=None
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = CSVFolderValidator(
        folder_path=args.folder,
        baseline_file=args.baseline,
        output_report=args.report
    )
    
    # Run validation
    if validator.run_validation():
        validator.generate_report()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

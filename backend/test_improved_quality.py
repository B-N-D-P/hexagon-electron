#!/usr/bin/env python3
"""
Test script for improved repair quality assessment.

Demonstrates the difference between old and new formulas with:
1. Synthetic test cases (restoration vs retrofitting)
2. Real repair datasets (good/bad/verybad repair folders)
"""

import sys
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from improved_repair_quality import (
    calculate_frequency_quality_restoration,
    calculate_frequency_quality_retrofitting,
    detect_repair_type,
    calculate_improved_repair_quality
)


def test_synthetic_cases():
    """Test with synthetic examples to validate formulas"""
    print("\n" + "="*80)
    print("SYNTHETIC TEST CASES - Comparing Old vs New Formulas")
    print("="*80)
    
    test_cases = [
        {
            "name": "Perfect Restoration",
            "fO": np.array([100.0, 200.0, 300.0]),
            "fD": np.array([80.0, 160.0, 240.0]),
            "fR": np.array([100.0, 200.0, 300.0]),
            "expected_type": "restoration"
        },
        {
            "name": "Partial Restoration (50%)",
            "fO": np.array([100.0, 200.0, 300.0]),
            "fD": np.array([80.0, 160.0, 240.0]),
            "fR": np.array([90.0, 180.0, 270.0]),
            "expected_type": "restoration"
        },
        {
            "name": "Moderate Retrofitting (+10%)",
            "fO": np.array([100.0, 200.0, 300.0]),
            "fD": np.array([80.0, 160.0, 240.0]),
            "fR": np.array([110.0, 220.0, 330.0]),
            "expected_type": "retrofitting"
        },
        {
            "name": "Strong Retrofitting (+20%)",
            "fO": np.array([100.0, 200.0, 300.0]),
            "fD": np.array([80.0, 160.0, 240.0]),
            "fR": np.array([120.0, 240.0, 360.0]),
            "expected_type": "retrofitting"
        },
        {
            "name": "Aggressive Retrofitting (+30%)",
            "fO": np.array([100.0, 200.0, 300.0]),
            "fD": np.array([80.0, 160.0, 240.0]),
            "fR": np.array([130.0, 260.0, 390.0]),
            "expected_type": "retrofitting"
        },
        {
            "name": "Mixed Strategy",
            "fO": np.array([100.0, 200.0, 300.0]),
            "fD": np.array([80.0, 160.0, 240.0]),
            "fR": np.array([100.0, 220.0, 300.0]),  # restore, retro, restore
            "expected_type": "mixed"
        },
    ]
    
    for case in test_cases:
        print(f"\n{'─'*80}")
        print(f"Test Case: {case['name']}")
        print(f"{'─'*80}")
        
        fO, fD, fR = case['fO'], case['fD'], case['fR']
        
        # Show frequencies
        print(f"\nFrequencies:")
        print(f"  Original: {fO}")
        print(f"  Damaged:  {fD}")
        print(f"  Repaired: {fR}")
        
        # Detect repair type
        repair_type, strength_factor = detect_repair_type(fO, fD, fR)
        print(f"\nDetected Type: {repair_type} (expected: {case['expected_type']})")
        print(f"Strengthening Factor: {strength_factor:.3f}")
        
        # OLD FORMULA (always capped at 1.0)
        denom = fO - fD
        denom = np.where(np.abs(denom) < 1e-6, 1e-6, denom)
        Q_old = np.clip((fR - fD) / denom, 0.0, 1.0)
        print(f"\n🔴 OLD Formula (restoration-only, capped at 1.0):")
        print(f"   Per-mode: {Q_old}")
        print(f"   Average:  {np.mean(Q_old):.3f}")
        
        # NEW FORMULA (adaptive based on type)
        if repair_type == 'restoration':
            Q_new = calculate_frequency_quality_restoration(fO, fD, fR)
        elif repair_type == 'retrofitting':
            Q_new = calculate_frequency_quality_retrofitting(fO, fD, fR)
        else:
            from improved_repair_quality import calculate_frequency_quality_mixed
            Q_new = calculate_frequency_quality_mixed(fO, fD, fR)
        
        print(f"\n🟢 NEW Formula (type-aware, rewards strengthening):")
        print(f"   Per-mode: {Q_new}")
        print(f"   Average:  {np.mean(Q_new):.3f}")
        
        # Show improvement
        improvement = np.mean(Q_new) - np.mean(Q_old)
        if improvement > 0.01:
            print(f"\n✅ Improvement: +{improvement:.3f} (NEW formula better captures quality)")
        elif improvement < -0.01:
            print(f"\n⚠️  Difference: {improvement:.3f} (NEW formula more conservative)")
        else:
            print(f"\n➡️  Similar: {improvement:.3f} (both formulas agree)")


def test_real_datasets():
    """Test with actual repair datasets"""
    print("\n\n" + "="*80)
    print("REAL DATASET ANALYSIS")
    print("="*80)
    
    from services.data_adapters import load_timeseries_for_modal
    from repair_analyzer import extract_modal_parameters
    
    repair_folders = [
        ("Good Repair", Path("datas/repaired/good_repair")),
        ("Bad Repair", Path("datas/repaired/bad_repair")),
        ("Very Bad Repair", Path("datas/repaired/verybad_repair")),
    ]
    
    # Use baseline as "original"
    baseline_files = list(Path("datas/baseline").glob("*.csv"))
    if not baseline_files:
        print("\n⚠️  No baseline files found. Skipping real dataset tests.")
        return
    
    baseline_file = baseline_files[0]
    print(f"\nUsing baseline: {baseline_file.name}")
    
    # Load baseline (original state)
    try:
        baseline_data = load_timeseries_for_modal(str(baseline_file))
        modal_original = extract_modal_parameters(baseline_data, fs=100.0, max_modes=5)
        print(f"Original frequencies: {modal_original.frequencies}")
    except Exception as e:
        print(f"\n⚠️  Error loading baseline: {e}")
        return
    
    # Test each repair folder
    for folder_name, folder_path in repair_folders:
        print(f"\n{'─'*80}")
        print(f"{folder_name}: {folder_path}")
        print(f"{'─'*80}")
        
        if not folder_path.exists():
            print(f"⚠️  Folder not found")
            continue
        
        repair_files = list(folder_path.glob("*.csv"))
        if not repair_files:
            print(f"⚠️  No CSV files found")
            continue
        
        for repair_file in repair_files[:2]:  # Test first 2 files
            print(f"\n  📄 {repair_file.name}")
            
            try:
                # Load repaired data
                repaired_data = load_timeseries_for_modal(str(repair_file))
                modal_repaired = extract_modal_parameters(repaired_data, fs=100.0, max_modes=5)
                
                print(f"     Repaired frequencies: {modal_repaired.frequencies}")
                
                # For this test, use baseline as both original and damaged
                # (In real use, you'd have separate damaged state)
                fO = np.array(modal_original.frequencies)
                fD = fO * 0.8  # Simulate 20% damage
                fR = np.array(modal_repaired.frequencies)
                
                # Detect type
                repair_type, strength = detect_repair_type(fO, fD, fR)
                
                # OLD vs NEW
                denom = fO - fD
                denom = np.where(np.abs(denom) < 1e-6, 1e-6, denom)
                Q_old = np.mean(np.clip((fR - fD) / denom, 0.0, 1.0))
                
                if repair_type == 'restoration':
                    Q_new = np.mean(calculate_frequency_quality_restoration(fO, fD, fR))
                else:
                    Q_new = np.mean(calculate_frequency_quality_retrofitting(fO, fD, fR))
                
                print(f"     Type: {repair_type}, Strengthening: {strength:.2f}x")
                print(f"     OLD Score: {Q_old:.3f}")
                print(f"     NEW Score: {Q_new:.3f} ({'+' if Q_new > Q_old else ''}{Q_new - Q_old:.3f})")
                
            except Exception as e:
                print(f"     ⚠️  Error: {e}")


def main():
    """Run all tests"""
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + "IMPROVED REPAIR QUALITY ASSESSMENT - TEST SUITE".center(78) + "║")
    print("╚" + "═"*78 + "╝")
    
    # Test 1: Synthetic cases
    test_synthetic_cases()
    
    # Test 2: Real datasets
    test_real_datasets()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nKey Improvements:")
    print("  ✓ Retrofitting repairs no longer penalized")
    print("  ✓ Can distinguish between restoration (1.0) and strengthening (>1.0)")
    print("  ✓ Automatic detection of repair strategy")
    print("  ✓ Appropriate scoring for each repair type")
    print()


if __name__ == "__main__":
    main()

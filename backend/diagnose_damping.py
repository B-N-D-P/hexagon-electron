#!/usr/bin/env python3
"""
Diagnostic tool to check why damping recovery is always 1.0
"""

import sys
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.data_adapters import load_timeseries_for_modal
from repair_analyzer import extract_modal_parameters

def diagnose_damping(original_file, damaged_file, repaired_file):
    """
    Diagnose damping values and recovery calculation
    """
    print("="*80)
    print("DAMPING RECOVERY DIAGNOSTIC")
    print("="*80)
    print()
    
    # Load and extract modal parameters
    print("Loading files...")
    original_data = load_timeseries_for_modal(original_file)
    damaged_data = load_timeseries_for_modal(damaged_file)
    repaired_data = load_timeseries_for_modal(repaired_file)
    
    print("Extracting modal parameters...")
    original = extract_modal_parameters(original_data, fs=100.0, max_modes=5)
    damaged = extract_modal_parameters(damaged_data, fs=100.0, max_modes=5)
    repaired = extract_modal_parameters(repaired_data, fs=100.0, max_modes=5)
    
    print()
    print("="*80)
    print("DAMPING VALUES")
    print("="*80)
    print()
    
    print(f"Original damping:  {original.damping}")
    print(f"Damaged damping:   {damaged.damping}")
    print(f"Repaired damping:  {repaired.damping}")
    print()
    
    # Check for NaN values
    orig_has_nan = any(np.isnan(d) if np.isfinite(d) is False else False for d in original.damping)
    dam_has_nan = any(np.isnan(d) if np.isfinite(d) is False else False for d in damaged.damping)
    rep_has_nan = any(np.isnan(d) if np.isfinite(d) is False else False for d in repaired.damping)
    
    print("NaN Detection:")
    print(f"  Original has NaN: {orig_has_nan}")
    print(f"  Damaged has NaN:  {dam_has_nan}")
    print(f"  Repaired has NaN: {rep_has_nan}")
    print()
    
    # Calculate differences
    zO = np.array(original.damping, dtype=float)
    zD = np.array(damaged.damping, dtype=float)
    zR = np.array(repaired.damping, dtype=float)
    
    denom_z = np.abs(zD - zO)
    
    print("="*80)
    print("DIFFERENCE ANALYSIS")
    print("="*80)
    print()
    print(f"|Damaged - Original|: {denom_z}")
    print(f"|Repaired - Original|: {np.abs(zR - zO)}")
    print()
    
    # Check thresholds
    DAMPING_CHANGE_THRESHOLD_REL = 0.10
    DAMPING_CHANGE_THRESHOLD_ABS = 0.005
    
    significant_change = (denom_z > DAMPING_CHANGE_THRESHOLD_REL * np.abs(zO)) | (denom_z > DAMPING_CHANGE_THRESHOLD_ABS)
    
    print("Significant Change Detection:")
    print(f"  Threshold (10% of original): {DAMPING_CHANGE_THRESHOLD_REL * np.abs(zO)}")
    print(f"  Threshold (absolute):        {DAMPING_CHANGE_THRESHOLD_ABS}")
    print(f"  Modes with significant change: {significant_change}")
    print()
    
    # Calculate recovery scores
    Q_damp_i = np.zeros(len(zO))
    
    if np.any(significant_change):
        denom_z_safe = np.where(denom_z < 1e-6, 1e-6, denom_z)
        Q_damp_i[significant_change] = np.clip(
            1.0 - np.abs(zR[significant_change] - zO[significant_change]) / denom_z_safe[significant_change],
            0.0, 1.0
        )
        print("Recovery formula used for modes with significant change:")
        print(f"  Q = 1.0 - |Repaired - Original| / |Damaged - Original|")
        print(f"  Scores: {Q_damp_i[significant_change]}")
        print()
    
    if np.any(~significant_change):
        error = np.abs(zR[~significant_change] - zO[~significant_change])
        Q_damp_i[~significant_change] = np.clip(1.0 - error / 0.02, 0.0, 1.0)
        print("Similarity formula used for modes without significant change:")
        print(f"  Q = 1.0 - |Repaired - Original| / 0.02")
        print(f"  Errors: {error}")
        print(f"  Scores: {Q_damp_i[~significant_change]}")
        print()
    
    Q_damping = float(np.mean(Q_damp_i))
    
    print("="*80)
    print("FINAL RESULT")
    print("="*80)
    print()
    print(f"Per-mode damping recovery scores: {Q_damp_i}")
    print(f"Average damping recovery: {Q_damping:.4f}")
    print()
    
    # Diagnosis
    print("="*80)
    print("DIAGNOSIS")
    print("="*80)
    print()
    
    if Q_damping >= 0.99:
        print("⚠️  DAMPING RECOVERY IS NEAR 1.0")
        print()
        print("Possible causes:")
        print()
        
        if np.allclose(zO, zD, atol=0.001):
            print("  ❌ Damaged damping same as Original")
            print("     → Damage didn't affect damping significantly")
            print("     → This is NORMAL if damage was stiffness-related only")
            print()
        
        if np.allclose(zR, zO, atol=0.001):
            print("  ✅ Repaired damping perfectly matches Original")
            print("     → This is GOOD! Perfect damping recovery")
            print()
        
        if not np.any(significant_change):
            print("  ⚠️  No significant damping change detected")
            print("     → All changes below threshold")
            print("     → Damping estimation may be imprecise")
            print("     → This is COMMON with small structural changes")
            print()
        
        print("Recommendation:")
        print("  • Check if damage actually affected damping")
        print("  • Damping is harder to measure than frequency")
        print("  • Score of 1.0 may be correct if damping didn't change")
    else:
        print("✅ Damping recovery is working correctly")
        print(f"   Score of {Q_damping:.2f} reflects actual damping changes")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python diagnose_damping.py <original.csv> <damaged.csv> <repaired.csv>")
        sys.exit(1)
    
    diagnose_damping(sys.argv[1], sys.argv[2], sys.argv[3])

#!/usr/bin/env python3
"""
Improved Repair Quality Assessment System

Addresses the fundamental flaw in the original system where retrofitting/strengthening
repairs were penalized or capped at 1.0, making it impossible to distinguish between:
- Perfect restoration (returns to original state)
- Strengthening/retrofitting (intentionally exceeds original capacity)

This improved system:
1. Auto-detects repair type (restoration vs. retrofitting)
2. Uses appropriate formulas for each scenario
3. Provides meaningful quality scores for both repair strategies
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np


@dataclass
class ImprovedQualityBreakdown:
    """Enhanced quality breakdown with repair type awareness"""
    frequency_recovery: float
    mode_shape_match: float
    damping_recovery: float
    repair_type: str  # 'restoration', 'retrofitting', or 'mixed'
    strengthening_factor: float  # How much beyond original (1.0 = restoration, >1.0 = strengthened)
    

@dataclass
class ImprovedQualityAssessment:
    """Enhanced quality assessment with repair type classification"""
    overall_score: float
    breakdown: ImprovedQualityBreakdown
    per_mode_analysis: List[Dict[str, float]]
    interpretation: str
    interpretation_code: str
    confidence_level: str
    repair_strategy: str  # User-friendly description
    

def detect_repair_type(fO: np.ndarray, fD: np.ndarray, fR: np.ndarray, 
                      threshold_pct: float = 3.0) -> Tuple[str, float]:
    """
    Automatically detect repair type based on frequency changes.
    
    Args:
        fO: Original frequencies
        fD: Damaged frequencies
        fR: Repaired frequencies
        threshold_pct: Percentage threshold to distinguish restoration from retrofitting
        
    Returns:
        (repair_type, strengthening_factor):
            - repair_type: 'restoration', 'retrofitting', or 'mixed'
            - strengthening_factor: Average ratio fR/fO (1.0 = restored, >1.0 = strengthened)
    """
    # Calculate how much repaired exceeds original
    exceed_pct = ((fR - fO) / fO) * 100
    
    # Calculate strengthening factor (geometric mean to handle multiple modes)
    strengthening_factor = float(np.exp(np.mean(np.log(fR / fO))))
    
    # Classify based on threshold
    n_modes = len(exceed_pct)
    n_strengthened = np.sum(exceed_pct > threshold_pct)
    n_restored = np.sum(np.abs(exceed_pct) <= threshold_pct)
    
    if n_strengthened >= 0.7 * n_modes:
        return 'retrofitting', strengthening_factor
    elif n_restored >= 0.7 * n_modes:
        return 'restoration', strengthening_factor
    else:
        return 'mixed', strengthening_factor


def calculate_frequency_quality_restoration(fO: np.ndarray, fD: np.ndarray, 
                                           fR: np.ndarray) -> np.ndarray:
    """
    Calculate frequency recovery for RESTORATION repairs.
    Goal: Return to original state.
    
    Formula: Q = (fR - fD) / (fO - fD)
    - Q = 0.0: No improvement (stayed at damaged level)
    - Q = 1.0: Perfect restoration (returned to original)
    - Q > 1.0: Overshot (slightly beyond original)
    """
    denom = fO - fD
    # Avoid division by zero
    denom = np.where(np.abs(denom) < 1e-6, np.sign(denom) * 1e-6 + 1e-6, denom)
    
    Q = (fR - fD) / denom
    
    # For restoration: cap at 1.0 and floor at 0.0
    return np.clip(Q, 0.0, 1.0)


def calculate_frequency_quality_retrofitting(fO: np.ndarray, fD: np.ndarray, 
                                            fR: np.ndarray) -> np.ndarray:
    """
    Calculate frequency recovery for RETROFITTING/STRENGTHENING repairs.
    Goal: Improve beyond original capacity.
    
    Two-part scoring:
    1. Restoration component: Did it at least restore to original? (0-50% of score)
    2. Strengthening component: How much beyond original? (50-100% of score)
    
    Formula:
        If fR < fO: Partial restoration only
            Q = 0.5 * (fR - fD) / (fO - fD)  [max 0.5]
        
        If fR >= fO: Full restoration + strengthening bonus
            Q = 0.5 + 0.5 * min(1.0, (fR - fO) / (0.2 * fO))
            
    This gives:
    - fR = fD (no improvement): Q = 0.0
    - fR = fO (restored): Q = 0.5 (halfway - restored but not strengthened)
    - fR = 1.1*fO (10% stronger): Q = 0.75
    - fR = 1.2*fO (20% stronger): Q = 1.0 (excellent retrofitting)
    - fR > 1.2*fO: Still Q = 1.0 (caps to avoid unrealistic scores)
    """
    denom = fO - fD
    denom = np.where(np.abs(denom) < 1e-6, np.sign(denom) * 1e-6 + 1e-6, denom)
    
    # Initialize quality scores
    Q = np.zeros_like(fR)
    
    # Case 1: Partial restoration (fR < fO)
    mask_partial = fR < fO
    if np.any(mask_partial):
        Q[mask_partial] = 0.5 * np.clip((fR[mask_partial] - fD[mask_partial]) / denom[mask_partial], 0.0, 1.0)
    
    # Case 2: Full restoration + strengthening (fR >= fO)
    mask_full = fR >= fO
    if np.any(mask_full):
        # Base score for restoration: 0.5
        restoration_score = 0.5
        
        # Strengthening bonus: scale from 0 to 0.5 based on improvement
        # 20% improvement = max score
        strengthening_pct = (fR[mask_full] - fO[mask_full]) / fO[mask_full]
        strengthening_score = 0.5 * np.clip(strengthening_pct / 0.20, 0.0, 1.0)
        
        Q[mask_full] = restoration_score + strengthening_score
    
    return np.clip(Q, 0.0, 1.0)


def calculate_frequency_quality_mixed(fO: np.ndarray, fD: np.ndarray, 
                                     fR: np.ndarray) -> np.ndarray:
    """
    Calculate frequency recovery for MIXED repairs.
    Some modes restored, some retrofitted.
    
    Use per-mode adaptive scoring:
    - If mode exceeded original by >3%, use retrofitting formula
    - Otherwise, use restoration formula
    """
    Q = np.zeros_like(fR)
    
    # Determine per-mode strategy
    exceed_pct = ((fR - fO) / fO) * 100
    
    # Modes that are clearly strengthened
    mask_retro = exceed_pct > 3.0
    mask_resto = ~mask_retro
    
    if np.any(mask_retro):
        Q[mask_retro] = calculate_frequency_quality_retrofitting(
            fO[mask_retro], fD[mask_retro], fR[mask_retro]
        )
    
    if np.any(mask_resto):
        Q[mask_resto] = calculate_frequency_quality_restoration(
            fO[mask_resto], fD[mask_resto], fR[mask_resto]
        )
    
    return Q


def calculate_improved_repair_quality(
    fO: List[float],  # Original frequencies
    fD: List[float],  # Damaged frequencies
    fR: List[float],  # Repaired frequencies
    mO: List[List[float]],  # Original mode shapes
    mR: List[List[float]],  # Repaired mode shapes
    zO: List[float],  # Original damping
    zD: List[float],  # Damaged damping
    zR: List[float],  # Repaired damping
    user_specified_type: Optional[str] = None  # Optional: 'restoration' or 'retrofitting'
) -> ImprovedQualityAssessment:
    """
    Calculate improved repair quality with automatic repair type detection.
    
    Args:
        fO, fD, fR: Frequencies for original, damaged, repaired
        mO, mR: Mode shapes for original and repaired
        zO, zD, zR: Damping ratios for original, damaged, repaired
        user_specified_type: Optional manual override for repair type
        
    Returns:
        ImprovedQualityAssessment with appropriate scoring
    """
    # Convert to numpy arrays
    fO_arr = np.array(fO, dtype=float)
    fD_arr = np.array(fD, dtype=float)
    fR_arr = np.array(fR, dtype=float)
    
    # Detect repair type
    if user_specified_type:
        repair_type = user_specified_type
        strengthening_factor = float(np.exp(np.mean(np.log(fR_arr / fO_arr))))
    else:
        repair_type, strengthening_factor = detect_repair_type(fO_arr, fD_arr, fR_arr)
    
    # Calculate frequency quality based on type
    if repair_type == 'restoration':
        Q_freq_i = calculate_frequency_quality_restoration(fO_arr, fD_arr, fR_arr)
    elif repair_type == 'retrofitting':
        Q_freq_i = calculate_frequency_quality_retrofitting(fO_arr, fD_arr, fR_arr)
    else:  # mixed
        Q_freq_i = calculate_frequency_quality_mixed(fO_arr, fD_arr, fR_arr)
    
    Q_frequency = float(np.mean(Q_freq_i))
    
    # Mode shape matching (unchanged - works for both types)
    from repair_analyzer import _mac
    Q_shape_i = []
    for i in range(len(fO)):
        if i < len(mO) and i < len(mR):
            phiO = np.array(mO[i])
            phiR = np.array(mR[i])
            if len(phiO) > 0 and len(phiR) > 0 and len(phiO) == len(phiR):
                Q_shape_i.append(_mac(phiO, phiR))
            else:
                Q_shape_i.append(0.0)
        else:
            Q_shape_i.append(0.0)
    Q_shape = float(np.mean(Q_shape_i)) if Q_shape_i else 0.0
    
    # Damping recovery (unchanged - works for both types)
    zO_arr = np.array(zO, dtype=float)
    zD_arr = np.array(zD, dtype=float)
    zR_arr = np.array(zR, dtype=float)
    
    denom_z = np.abs(zD_arr - zO_arr)
    DAMPING_CHANGE_THRESHOLD_REL = 0.10
    DAMPING_CHANGE_THRESHOLD_ABS = 0.005
    
    significant_change = (denom_z > DAMPING_CHANGE_THRESHOLD_REL * np.abs(zO_arr)) | (denom_z > DAMPING_CHANGE_THRESHOLD_ABS)
    
    Q_damp_i = np.zeros(len(fO))
    
    if np.any(significant_change):
        denom_z_safe = np.where(denom_z < 1e-6, 1e-6, denom_z)
        Q_damp_i[significant_change] = np.clip(
            1.0 - np.abs(zR_arr[significant_change] - zO_arr[significant_change]) / denom_z_safe[significant_change],
            0.0, 1.0
        )
    
    if np.any(~significant_change):
        error = np.abs(zR_arr[~significant_change] - zO_arr[~significant_change])
        Q_damp_i[~significant_change] = np.clip(1.0 - error / 0.02, 0.0, 1.0)
    
    Q_damping = float(np.mean(Q_damp_i))
    
    # Overall score (weighted average)
    overall = 0.5 * Q_frequency + 0.3 * Q_shape + 0.2 * Q_damping
    
    # Interpretation based on score AND repair type
    if repair_type == 'retrofitting':
        if overall >= 0.90:
            interp = ("Excellent Retrofitting - Significant Strengthening Achieved", "EXCELLENT_RETRO")
            strategy = "Advanced strengthening with excellent structural improvement"
        elif overall >= 0.75:
            interp = ("Very Good Retrofitting - Substantial Strengthening", "VERY_GOOD_RETRO")
            strategy = "Effective strengthening beyond original capacity"
        elif overall >= 0.60:
            interp = ("Good Retrofitting - Moderate Strengthening", "GOOD_RETRO")
            strategy = "Acceptable strengthening with partial improvement"
        elif overall >= 0.50:
            interp = ("Fair Retrofitting - Minimal Strengthening", "FAIR_RETRO")
            strategy = "Limited strengthening, consider additional reinforcement"
        else:
            interp = ("Poor Retrofitting - Insufficient Improvement", "POOR_RETRO")
            strategy = "Retrofitting did not achieve strengthening goals"
    else:  # restoration or mixed
        if overall >= 0.95:
            interp = ("Excellent Restoration - Nearly Perfect Recovery", "EXCELLENT_RESTO")
            strategy = "Outstanding restoration to original condition"
        elif overall >= 0.85:
            interp = ("Very Good Restoration - Highly Effective", "VERY_GOOD_RESTO")
            strategy = "Effective restoration of original structural properties"
        elif overall >= 0.70:
            interp = ("Good Restoration - Acceptable Recovery", "GOOD_RESTO")
            strategy = "Acceptable restoration with most properties recovered"
        elif overall >= 0.50:
            interp = ("Fair Restoration - Partial Recovery", "FAIR_RESTO")
            strategy = "Partial restoration, some properties still degraded"
        else:
            interp = ("Poor Restoration - Minimal Recovery", "POOR_RESTO")
            strategy = "Minimal restoration, significant deficiencies remain"
    
    # Per-mode analysis
    per_mode = []
    for i in range(len(fO)):
        per_mode.append({
            "mode": i + 1,
            "frequency_recovery": float(Q_freq_i[i]),
            "mac_value": float(Q_shape_i[i] if i < len(Q_shape_i) else 0.0),
            "damping_recovery": float(Q_damp_i[i]),
            "strengthening_pct": float(((fR_arr[i] - fO_arr[i]) / fO_arr[i]) * 100)
        })
    
    return ImprovedQualityAssessment(
        overall_score=float(overall),
        breakdown=ImprovedQualityBreakdown(
            frequency_recovery=float(Q_frequency),
            mode_shape_match=float(Q_shape),
            damping_recovery=float(Q_damping),
            repair_type=repair_type,
            strengthening_factor=strengthening_factor
        ),
        per_mode_analysis=per_mode,
        interpretation=interp[0],
        interpretation_code=interp[1],
        confidence_level="high" if len(fO) >= 3 else "medium" if len(fO) == 2 else "low",
        repair_strategy=strategy
    )


# Convenience wrapper for backward compatibility
def calculate_repair_quality_smart(original, damaged, repaired, repair_type: Optional[str] = None):
    """
    Drop-in replacement for original calculate_repair_quality() with smart detection.
    
    Args:
        original: ModalParameters from original state
        damaged: ModalParameters from damaged state
        repaired: ModalParameters from repaired state
        repair_type: Optional 'restoration' or 'retrofitting' override
    """
    return calculate_improved_repair_quality(
        fO=original.frequencies,
        fD=damaged.frequencies,
        fR=repaired.frequencies,
        mO=original.mode_shapes,
        mR=repaired.mode_shapes,
        zO=original.damping,
        zD=damaged.damping,
        zR=repaired.damping,
        user_specified_type=repair_type
    )

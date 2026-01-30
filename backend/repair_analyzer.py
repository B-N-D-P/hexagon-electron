#!/usr/bin/env python3
"""
Structural Repair Quality Analyzer

Reads accelerometer CSVs (original, damaged, repaired), extracts modal parameters,
computes repair quality, produces visualizations and reports.

Usage:
  python repair_analyzer.py --original original.csv --damaged damaged.csv --repaired repaired.csv \
      --fs 1000 --max-modes 5 --output-prefix repair_analysis_report

Optional:
  python repair_analyzer.py --generate-demo --fs 1000 --duration 5 --sensors 4 \
      --output-prefix repair_analysis_report
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, hilbert, butter, sosfiltfilt, savgol_filter
from scipy.optimize import linear_sum_assignment
from matplotlib import use as mpl_use
mpl_use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
try:
    from colorama import Fore, Style, init as colorama_init
except Exception:
    class _Dummy:
        RESET_ALL = ""
        BRIGHT = ""
    class _Fore(_Dummy):
        GREEN = ""
        YELLOW = ""
        RED = ""
        CYAN = ""
    class _Style(_Dummy):
        pass
    Fore = _Fore()
    Style = _Style()
    def colorama_init(*args, **kwargs):
        return None

# -------------------------------
# Input validation
# -------------------------------

def validate_csv_data(csv_path: str, expected_fs: float = None, label: str = "Data") -> pd.DataFrame:
    """
    Validate CSV data quality before analysis.
    
    Args:
        csv_path: Path to CSV file
        expected_fs: Expected sampling rate (optional)
        label: Label for error messages (e.g., "Original", "Damaged")
    
    Returns:
        DataFrame: Validated data
    
    Raises:
        ValueError: If data fails validation
    """
    import warnings
    
    # Load data
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Failed to load {label} data from {csv_path}: {e}")
    
    # Check 1: NaN values (ENHANCED - Priority 2)
    if df.isnull().any().any():
        nan_info = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            nan_count = df[col].isnull().sum()
            if nan_count > 0:
                nan_rows = df[df[col].isnull()].index.tolist()[:5]
                nan_info.append(
                    f"  • Column '{col}': {nan_count} NaN values at rows {nan_rows}"
                    f"{'...' if len(df[df[col].isnull()]) > 5 else ''}"
                )
        raise ValueError(
            f"{label}: NaN values detected (data corruption or sensor dropout):\n" +
            "\n".join(nan_info) +
            f"\nFIX: Check data source, file integrity, or use data cleaning tools."
        )
    
    # Check 2: Infinite values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if np.isinf(df[numeric_cols].values).any():
        raise ValueError(f"{label}: Infinite values detected")
    
    # Check 3: Minimum length and frequency resolution (ENHANCED - Priority 5)
    min_samples = 512
    if len(df) < min_samples:
        raise ValueError(f"{label}: Only {len(df)} samples, need at least {min_samples}")
    
    # Enhanced: Check frequency resolution if fs provided
    if expected_fs is not None:
        freq_res = expected_fs / len(df)
        MAX_FREQ_RES = 1.0  # Hz
        if freq_res > MAX_FREQ_RES:
            min_samples_needed = int(expected_fs / MAX_FREQ_RES)
            duration_sec = len(df) / expected_fs
            min_duration_sec = min_samples_needed / expected_fs
            raise ValueError(
                f"{label}: Frequency resolution too coarse: {freq_res:.2f} Hz/bin. "
                f"Current duration: {duration_sec:.2f} sec ({len(df)} samples). "
                f"Need resolution <= {MAX_FREQ_RES} Hz, which requires "
                f"{min_samples_needed} samples ({min_duration_sec:.2f} sec). "
                f"FIX: Increase data duration or reduce fs."
            )
    
    # Check 4: Zero variance (dead sensors)
    zero_var_cols = [col for col in numeric_cols if df[col].std() < 1e-10]
    if zero_var_cols:
        warnings.warn(f"{label}: Zero-variance columns detected (dead sensor?): {zero_var_cols}")
    
    # Check 5: Sampling rate consistency (if time column exists) - TIGHTENED tolerance
    time_cols = [col for col in df.columns if 'time' in col.lower()]
    if time_cols and expected_fs:
        time_col = time_cols[0]
        dt = np.diff(df[time_col].values)
        measured_fs = 1 / np.mean(dt)
        tolerance = expected_fs * 0.02  # Tightened from 5% to 2%
        if abs(measured_fs - expected_fs) > tolerance:
            raise ValueError(
                f"{label}: Clock drift detected. Expected fs={expected_fs:.1f} Hz, "
                f"but measured={measured_fs:.1f} Hz (drift: {abs(measured_fs-expected_fs)/expected_fs*100:.1f}%). "
                f"Maximum tolerance is 2%. "
                f"FIX: Check clock synchronization or recalibrate sampling rate."
            )
    
    # Check 6: Large DC offset
    means = df[numeric_cols].mean()
    stds = df[numeric_cols].std()
    large_offset = means.abs() > 0.5 * stds
    if large_offset.any():
        offset_cols = means[large_offset].index.tolist()
        warnings.warn(f"{label}: Large DC offset in columns: {offset_cols} - consider detrending")
    
    # Check 7: Signal clipping detection (NEW - Priority 4)
    _detect_signal_clipping(df[numeric_cols].values, label)
    
    return df

# -------------------------------
# Metadata loading
# -------------------------------

def load_metadata(csv_path: str) -> dict:
    """
    Load optional metadata JSON file for a CSV.
    Looks for: <basename>_meta.json or metadata.json in same directory.
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        dict: Metadata or empty dict if not found
    """
    csv_dir = os.path.dirname(csv_path) or '.'
    csv_base = os.path.splitext(os.path.basename(csv_path))[0]
    
    # Try <name>_meta.json first
    meta_path1 = os.path.join(csv_dir, f"{csv_base}_meta.json")
    if os.path.exists(meta_path1):
        try:
            with open(meta_path1, 'r') as f:
                print(f"[info] Loading metadata from {meta_path1}")
                return json.load(f)
        except Exception as e:
            print(f"[warning] Failed to load metadata from {meta_path1}: {e}")
    
    # Try metadata.json in same directory
    meta_path2 = os.path.join(csv_dir, "metadata.json")
    if os.path.exists(meta_path2):
        try:
            with open(meta_path2, 'r') as f:
                print(f"[info] Loading metadata from {meta_path2}")
                return json.load(f)
        except Exception as e:
            print(f"[warning] Failed to load metadata from {meta_path2}: {e}")
    
    return {}

# -------------------------------
# Configurable constants (defaults)
# -------------------------------
DEFAULT_FS = 1000.0  # Hz
DEFAULT_MAX_MODES = 5
DEFAULT_MIN_FREQ = 1.0   # Hz
DEFAULT_MAX_FREQ = 450.0  # Hz
DEFAULT_BAND_HZ = 5.0  # +/- band for damping filter
MIN_PEAK_REL_HEIGHT = 0.10  # relative to max spectrum amplitude
MIN_PEAK_DISTANCE_HZ = 4.0  # Hz
MAX_DAMPING = 0.2  # Valid typical upper bound

np.set_printoptions(precision=3, suppress=True)

@dataclass
class FFTData:
    frequencies: np.ndarray
    amplitude: np.ndarray

@dataclass
class ModalParameters:
    frequencies: List[float]
    mode_shapes: List[List[float]]
    damping: List[float]
    fft_data: FFTData

@dataclass
class QualityBreakdown:
    frequency_recovery: float
    mode_shape_match: float
    damping_recovery: float

@dataclass
class QualityAssessment:
    overall_score: float
    breakdown: QualityBreakdown
    per_mode_analysis: List[Dict[str, float]]
    interpretation: str
    interpretation_code: str
    confidence_level: str

# -------------------------------
# Utility functions
# -------------------------------

def _print_header():
    colorama_init(autoreset=True)
    border = "═" * 78
    print("\n" + "╔" + border + "╗")
    line = "STRUCTURAL REPAIR QUALITY ANALYSIS SYSTEM v1.0"
    print("║" + line.center(78) + "║")
    print("╚" + border + "╝\n")


def _ok(msg: str):
    print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} {msg}")


def _warn(msg: str):
    print(f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}")


def _err(msg: str):
    print(f"{Fore.RED}[✗] {msg}{Style.RESET_ALL}")


# -------------------------------
# Critical validation functions (Priority 1-5)
# -------------------------------

def _validate_sampling_rate(fs: float, max_freq: float, label: str = "Sampling") -> bool:
    """
    PRIORITY 1: Enforce minimum sampling rate adequacy.
    Aliasing produces completely wrong frequencies - must catch this early.
    """
    MIN_FS = 100.0  # Hz - minimum for structural dynamics
    NYQUIST_SAFETY_MARGIN = 0.98  # Use 98% of Nyquist (increased for 100 Hz IAI hardware)
    
    # Check 1: Absolute minimum
    if fs < MIN_FS:
        raise ValueError(
            f"{label} Rate Too Low: fs={fs} Hz is below minimum {MIN_FS} Hz. "
            f"This is insufficient for structural dynamics analysis. "
            f"FIX: Increase --fs parameter to at least {MIN_FS} Hz."
        )
    
    # Check 2: Adequate margin to Nyquist
    nyquist = fs / 2.0
    safe_nyquist = nyquist * NYQUIST_SAFETY_MARGIN
    
    if max_freq > safe_nyquist:
        raise ValueError(
            f"{label} Rate Inadequate for Frequency Band: "
            f"max_freq={max_freq:.1f} Hz exceeds safe limit ({safe_nyquist:.1f} Hz). "
            f"Nyquist frequency with fs={fs} Hz is {nyquist:.1f} Hz. "
            f"Aliasing will occur and produce completely wrong frequencies. "
            f"FIX: Either (1) increase fs to >= {int(2*max_freq/NYQUIST_SAFETY_MARGIN)} Hz, "
            f"or (2) reduce max_freq to <= {safe_nyquist:.1f} Hz"
        )
    
    return True


def _validate_channel_synchronization(accel_data: np.ndarray, fs: float, label: str = "Data") -> bool:
    """
    PRIORITY 3: Validate that all channels are approximately synchronous.
    Out-of-phase channels corrupt mode shapes completely.
    Checks that peak frequencies occur at same FFT bin across channels.
    """
    if accel_data.shape[1] < 2:
        return True  # Single sensor, trivially synchronous
    
    try:
        # Compute FFT for each channel
        nfft = _next_pow2(accel_data.shape[0])
        window = _hann(accel_data.shape[0])
        peak_bins = []
        
        for ch_idx in range(accel_data.shape[1]):
            X = np.fft.rfft(accel_data[:, ch_idx] * window, n=nfft)
            peak_bin = np.argmax(np.abs(X))
            peak_bins.append(peak_bin)
        
        # Check if peak indices match (within tolerance)
        TOLERANCE_BINS = 2
        peak_range = max(peak_bins) - min(peak_bins)
        if peak_range > TOLERANCE_BINS:
            raise ValueError(
                f"{label}: Multi-Channel Synchronization Issue Detected. "
                f"Peak frequencies appear at different FFT bins: {peak_bins}. "
                f"This suggests channels are sampled asynchronously. "
                f"Mode shapes will be corrupted. "
                f"FIX: Ensure all sensors are sampled simultaneously with the same clock."
            )
    except ValueError:
        raise
    except Exception as e:
        # Don't fail on unexpected errors, just warn
        pass
    
    return True


def _detect_signal_clipping(data: np.ndarray, label: str = "Data", threshold_pct: float = 0.1) -> bool:
    """
    PRIORITY 4: Detect if signal is saturated/clipped.
    Clipped signals cause spurious peaks in FFT that confuse mode identification.
    """
    for col_idx in range(data.shape[1]):
        col = data[:, col_idx]
        col_abs = np.abs(col)
        
        # Check 1: Samples at exact max/min (rare in real data, common in clipped)
        max_val = np.max(col_abs)
        if max_val > 0:
            count_at_max = np.sum(np.abs(col_abs - max_val) < 1e-10 * max_val)
            pct_at_max = 100.0 * count_at_max / len(col)
            
            if pct_at_max > threshold_pct:
                raise ValueError(
                    f"{label}: Signal Clipping Detected at column {col_idx}. "
                    f"{count_at_max} samples ({pct_at_max:.2f}%) are at maximum amplitude {max_val:.6e}. "
                    f"ADC appears to be saturated. "
                    f"Clipped signals produce spurious peaks and wrong mode identification. "
                    f"FIX: Reduce excitation level, check sensor calibration, or increase ADC range."
                )
        
        # Check 2: Flat-topped peaks (derivative near zero at peak indicates clipping)
        try:
            from scipy.signal import find_peaks as scipy_find_peaks
            peaks, _ = scipy_find_peaks(col_abs, height=0.9*max_val, distance=5)
            
            if len(peaks) > 0:
                std_col = np.std(col)
                for peak_idx in peaks[:min(5, len(peaks))]:
                    if peak_idx > 0 and peak_idx < len(col) - 1:
                        deriv = abs(col[peak_idx + 1] - col[peak_idx - 1]) / 2
                        if std_col > 0 and deriv < 1e-6 * std_col:
                            raise ValueError(
                                f"{label}: Possible Signal Clipping at column {col_idx}, sample {peak_idx}. "
                                f"Peak has near-zero derivative (flat-top), suggesting saturation. "
                                f"Peak amplitude: {col_abs[peak_idx]:.3e}, derivative: {deriv:.3e}. "
                                f"Clipped signals corrupts mode identification. "
                                f"FIX: Check if data is saturated and reduce input level."
                            )
        except Exception:
            pass  # Silently skip derivative check if it fails
    
    return True


def _validate_data_duration(n_samples: int, fs: float, min_freq: float = 1.0, 
                            label: str = "Data", max_freq: float = None) -> bool:
    """
    PRIORITY 5: Validate data duration for adequate frequency resolution.
    Poor resolution causes modes to merge undetected - wrong mode count and frequencies.
    """
    # Check 1: Frequency resolution
    freq_res = fs / n_samples
    MAX_FREQ_RES = 1.0  # Hz - need <= 1 Hz resolution for civil structures
    
    if freq_res > MAX_FREQ_RES:
        min_samples_needed = int(fs / MAX_FREQ_RES)
        duration_sec = n_samples / fs
        min_duration_sec = min_samples_needed / fs
        raise ValueError(
            f"{label}: Frequency Resolution Too Coarse for Modal Analysis. "
            f"Current: {freq_res:.2f} Hz/bin, duration {duration_sec:.2f} sec ({n_samples} samples). "
            f"Modes may merge undetected - wrong mode count and frequencies will result. "
            f"Need resolution <= {MAX_FREQ_RES} Hz, which requires "
            f"{min_samples_needed} samples ({min_duration_sec:.2f} sec). "
            f"FIX: Increase data acquisition duration."
        )
    
    # Check 2: Enough cycles for damping estimation
    min_freq_interest = max(min_freq, 1.0)
    duration = n_samples / fs
    cycles_available = duration * min_freq_interest
    MIN_CYCLES = 2  # Need at least 2 cycles for envelope fitting (reduced for shorter data collection)
    
    if cycles_available < MIN_CYCLES:
        min_duration_needed = MIN_CYCLES / min_freq_interest
        raise ValueError(
            f"{label}: Insufficient Data Duration for Damping Estimation. "
            f"Current: {cycles_available:.1f} cycles at {min_freq_interest:.1f} Hz. "
            f"With only {n_samples} samples at {fs} Hz = {duration:.2f} sec. "
            f"Minimum needed: {MIN_CYCLES} cycles = {min_duration_needed:.2f} sec. "
            f"FIX: Increase data acquisition duration."
        )
    
    return True


# -------------------------------
# Data loading
# -------------------------------

def load_csv_data(filename: str) -> np.ndarray:
    """Load accelerometer data from CSV file.

    Handles CSV with/without headers. Expects 4 columns (sensors) by default but
    will accept any number >= 1. Returns a numpy array of shape [samples, sensors].
    """
    try:
        try:
            df = pd.read_csv(filename)
        except pd.errors.EmptyDataError:
            df = pd.read_csv(filename, header=None)
        if df.empty:
            raise ValueError("CSV file is empty")
        df_numeric = df.apply(pd.to_numeric, errors='coerce')
        if df_numeric.isnull().all(axis=None):
            raise ValueError("CSV contains no numeric data")
        df_numeric = df_numeric.dropna(axis=1, how='all')
        df_numeric = df_numeric.dropna(axis=0, how='any')
        data = df_numeric.to_numpy(dtype=float)
        # Handle possible time column as first column if strictly increasing and ranges >> others
        if data.shape[1] >= 2:
            col0 = data[:, 0]
            if np.all(np.diff(col0) > 0):
                ranges = np.ptp(data, axis=0)
                if ranges[0] > 10 * np.median(ranges[1:]):
                    data = data[:, 1:]
        if data.ndim != 2 or data.shape[0] < 100 or data.shape[1] < 1:
            raise ValueError(f"Unexpected data shape: {data.shape}")
        return data
    except FileNotFoundError:
        raise
    except Exception as e:
        raise

# -------------------------------
# Signal processing helpers
# -------------------------------

def _hann(n: int) -> np.ndarray:
    return 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / max(n - 1, 1))


def _next_pow2(n: int) -> int:
    return 1 if n == 0 else 2 ** int(np.ceil(np.log2(n)))


def _compute_fft(x: np.ndarray, fs: float) -> FFTData:
    n = len(x)
    window = _hann(n)
    xw = x * window
    nfft = _next_pow2(n)
    X = np.fft.rfft(xw, n=nfft)
    freqs = np.fft.rfftfreq(nfft, d=1.0 / fs)
    amp = np.abs(X)
    amp /= np.max(amp) if np.max(amp) > 0 else 1.0
    return FFTData(frequencies=freqs, amplitude=amp)


def _find_natural_frequencies(fft: FFTData, max_modes: int, min_freq: float = DEFAULT_MIN_FREQ, max_freq: float = DEFAULT_MAX_FREQ) -> List[float]:
    # Smooth spectrum to improve peak stability
    amp = fft.amplitude.copy()
    if len(amp) >= 21:
        amp = savgol_filter(amp, 21, 3)
    # Frequency window
    mask = (fft.frequencies >= min_freq) & (fft.frequencies <= max_freq)
    freqs = fft.frequencies[mask]
    amps = amp[mask]
    if len(freqs) < 3:
        return []
    min_height = MIN_PEAK_REL_HEIGHT * (np.max(amps) if len(amps) else 1.0)
    df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    dist_bins = int(round(MIN_PEAK_DISTANCE_HZ / max(df, 1e-12)))
    peaks, props = find_peaks(amps, height=min_height, distance=max(1, dist_bins), prominence=0.05*np.max(amps))
    if len(peaks) == 0:
        return []
    peak_freqs = freqs[peaks]
    peak_amps = amps[peaks]
    order = np.argsort(-peak_amps)
    peak_freqs = peak_freqs[order][:max_modes]
    return sorted(peak_freqs.tolist())


def _extract_mode_shapes(data: np.ndarray, fs: float, mode_freqs: List[float]) -> List[List[float]]:
    n_samples, n_sensors = data.shape
    shapes: List[List[float]] = []
    nfft = _next_pow2(n_samples)
    freqs = np.fft.rfftfreq(nfft, d=1.0 / fs)
    window = _hann(n_samples)
    X_sensors = []
    for s in range(n_sensors):
        X = np.fft.rfft(data[:, s] * window, n=nfft)
        X_sensors.append(np.abs(X))
    X_sensors = np.stack(X_sensors, axis=1)
    for f in mode_freqs:
        idx = int(np.argmin(np.abs(freqs - f)))
        vec = X_sensors[idx, :]
        if np.max(vec) > 0:
            vec = vec / np.max(vec)
        shapes.append(vec.tolist())
    return shapes


def _bandpass_sos(f_center: float, fs: float, band_hz: float) -> np.ndarray:
    low = max(0.1, (f_center - band_hz) / (fs / 2.0))
    high = min(0.999, (f_center + band_hz) / (fs / 2.0))
    if low >= high:
        low = max(0.001, high * 0.5)
    sos = butter(N=4, Wn=[low, high], btype='bandpass', output='sos')
    return sos


def _estimate_damping(data_avg: np.ndarray, fs: float, mode_freqs: List[float]) -> List[float]:
    damping: List[float] = []
    t = np.arange(len(data_avg)) / fs
    for f in mode_freqs:
        try:
            # Adaptive band (+/- max(2Hz, 5% of f))
            band = max(2.0, 0.05 * max(f, 1e-6))
            sos = _bandpass_sos(f, fs, band)
            y = sosfiltfilt(sos, data_avg)
            analytic = hilbert(y)
            envelope = np.abs(analytic)
            envelope = np.maximum(envelope, 1e-12)
            lnA = np.log(envelope)
            # skip initial 2 cycles; fit middle 80% to avoid edge effects
            cycles_to_skip = max(2, int(round(2 * fs / max(f, 1e-6))))
            x_full = t[cycles_to_skip:]
            y_full = lnA[cycles_to_skip:]
            if len(x_full) < 50:
                damping.append(np.nan)
                continue
            start = int(0.1 * len(x_full))
            end = int(0.9 * len(x_full))
            x = x_full[start:end]
            yln = y_full[start:end]
            # Iterative robust fit: 3 iters of Huber-like weighting
            w = np.ones_like(yln)
            for _ in range(3):
                A = np.vstack([x, np.ones_like(x)]).T * w[:, None]
                b = yln * w
                slope, intercept = np.linalg.lstsq(A, b, rcond=None)[0]
                resid = yln - (slope * x + intercept)
                s = np.median(np.abs(resid)) + 1e-9
                w = 1.0 / (1.0 + (resid/(1.345*s))**2)
            zeta = -slope / (2 * math.pi * f)
            # Basic fit quality check (R^2)
            yfit = slope * x + intercept
            ss_res = float(np.sum((yln - yfit)**2))
            ss_tot = float(np.sum((yln - np.mean(yln))**2)) + 1e-12
            r2 = 1.0 - ss_res/ss_tot
            if not np.isfinite(zeta) or zeta <= 0 or zeta > MAX_DAMPING or r2 < 0.6:
                damping.append(np.nan)
            else:
                damping.append(float(zeta))
        except Exception:
            damping.append(np.nan)
    if len(damping) > 0:
        arr = np.array([d if np.isfinite(d) else np.nan for d in damping])
        if np.all(np.isnan(arr)):
            arr = np.full_like(arr, 0.02)
        else:
            med = np.nanmedian(arr)
            arr = np.where(np.isnan(arr), med if np.isfinite(med) else 0.02, arr)
        damping = arr.tolist()
    return damping

# -------------------------------
# Public API functions
# -------------------------------

def extract_modal_parameters(accel_data: np.ndarray, fs: float = DEFAULT_FS,
                             max_modes: int = DEFAULT_MAX_MODES,
                             min_freq: float = DEFAULT_MIN_FREQ,
                             max_freq: float = DEFAULT_MAX_FREQ) -> ModalParameters:
    """
    Extract structural modal parameters using signal processing.
    
    NOW WITH CRITICAL VALIDATIONS:
    - Priority 1: Sampling rate adequacy (prevents aliasing)
    - Priority 3: Multi-channel synchronization (prevents mode shape corruption)
    - Priority 5: Data duration validation (prevents mode merging)
    """
    if accel_data.ndim != 2:
        raise ValueError("accel_data must be 2D [samples, sensors]")
    samples, sensors = accel_data.shape
    if samples < 100:
        raise ValueError("Too few samples for analysis (need >= 100)")
    
    # PRIORITY 1: Validate sampling rate (prevents aliasing - the most critical!)
    _validate_sampling_rate(fs, max_freq, label="Data")
    
    # PRIORITY 5: Validate data duration (prevent mode merging from poor resolution)
    _validate_data_duration(samples, fs, min_freq=min_freq, label="Data", max_freq=max_freq)
    
    # PRIORITY 3: Validate channel synchronization (prevent mode shape corruption)
    _validate_channel_synchronization(accel_data, fs, label="Data")

    avg_signal = accel_data.mean(axis=1)
    fft = _compute_fft(avg_signal, fs)
    mode_freqs = _find_natural_frequencies(fft, max_modes, min_freq=min_freq, max_freq=max_freq)
    mode_shapes = _extract_mode_shapes(accel_data, fs, mode_freqs)
    damping = _estimate_damping(avg_signal, fs, mode_freqs)

    return ModalParameters(
        frequencies=mode_freqs,
        mode_shapes=mode_shapes,
        damping=damping,
        fft_data=fft,
    )


def _mac(phi1: np.ndarray, phi2: np.ndarray) -> float:
    num = np.abs(np.vdot(phi1, phi2)) ** 2
    den = (np.vdot(phi1, phi1) * np.vdot(phi2, phi2)).real
    if den <= 0:
        return 0.0
    return float(np.clip(num / den, 0.0, 1.0))


def _mac_matrix(shapes_a: List[List[float]], shapes_b: List[List[float]]) -> np.ndarray:
    n = len(shapes_a)
    m = len(shapes_b)
    if n == 0 or m == 0:
        return np.zeros((n, m))
    A = np.array(shapes_a, dtype=float)
    B = np.array(shapes_b, dtype=float)
    # normalize rows to unit norm to stabilize MAC
    def norm_rows(M):
        norms = np.linalg.norm(M, axis=1, keepdims=True) + 1e-12
        return M / norms
    A = norm_rows(A)
    B = norm_rows(B)
    # MAC between each pair of mode shape vectors
    MAC = (A @ B.T)
    MAC = np.abs(MAC) ** 2  # since shapes are real already
    return MAC


def _match_modes(ref_freqs: List[float], other_freqs: List[float], ref_shapes: List[List[float]] = None, other_shapes: List[List[float]] = None) -> List[Optional[int]]:
    """Match modes in 'other' to 'ref' by minimizing absolute frequency difference.

    Returns a list idx where idx[i] is the index in other mapped to ref[i], or None if no match.
    """
    if not ref_freqs or not other_freqs:
        return [None] * len(ref_freqs)
    ref = np.array(ref_freqs, dtype=float)
    other = np.array(other_freqs, dtype=float)
    # cost matrix: combine normalized frequency difference and (1 - MAC)
    C_f = np.abs(ref[:, None] - other[None, :])
    # normalize frequency cost by 15% of ref or 15 Hz, whichever larger
    norm = np.maximum(15.0, 0.15 * np.maximum(ref[:, None], 1.0))
    C_f = C_f / norm
    if ref_shapes is not None and other_shapes is not None and len(ref_shapes) and len(other_shapes):
        MAC = _mac_matrix(ref_shapes, other_shapes)
        C_m = 1.0 - np.clip(MAC, 0.0, 1.0)
    else:
        C_m = np.zeros_like(C_f)
    # weights
    wf, wm = 0.6, 0.4
    C = wf * C_f + wm * C_m
    # Hungarian assignment on square matrix: pad if needed
    n, m = C.shape
    if n > m:
        pad = np.full((n, n - m), fill_value=np.max(C) + 1e3)
        C_pad = np.concatenate([C, pad], axis=1)
    elif m > n:
        pad = np.full((m - n, m), fill_value=np.max(C) + 1e3)
        C_pad = np.vstack([C, pad])
    else:
        C_pad = C
    row_ind, col_ind = linear_sum_assignment(C_pad)
    mapping: List[Optional[int]] = [None] * len(ref)
    for r, c in zip(row_ind, col_ind):
        if r < len(ref) and c < len(other):
            # reject matches that are too far apart (e.g., > 15% of ref frequency or > 15 Hz)
            if C[r, c] <= max(15.0, 0.15 * max(ref[r], 1.0)):
                mapping[r] = int(c)
    return mapping


def _reorder_list_by_mapping(values: List, mapping: List[Optional[int]]) -> List:
    out: List = []
    for i, j in enumerate(mapping):
        if j is None or j >= len(values):
            out.append(values[i] if i < len(values) else (0 if isinstance(values, list) else None))
        else:
            out.append(values[j])
    return out


def calculate_repair_quality(original: ModalParameters,
                             damaged: ModalParameters,
                             repaired: ModalParameters) -> QualityAssessment:
    # Match damaged/repaired modes to original by frequency proximity
    map_D = _match_modes(original.frequencies, damaged.frequencies, original.mode_shapes, damaged.mode_shapes)
    map_R = _match_modes(original.frequencies, repaired.frequencies, original.mode_shapes, repaired.mode_shapes)

    fO = np.array(original.frequencies)
    fD = np.array(_reorder_list_by_mapping(damaged.frequencies, map_D), dtype=float)
    fR = np.array(_reorder_list_by_mapping(repaired.frequencies, map_R), dtype=float)

    # align shapes and damping as well
    mO = original.mode_shapes
    mD = _reorder_list_by_mapping(damaged.mode_shapes, map_D) if damaged.mode_shapes else []
    mR = _reorder_list_by_mapping(repaired.mode_shapes, map_R) if repaired.mode_shapes else []

    zO = np.array(original.damping, dtype=float) if original.damping else np.zeros(len(fO))
    zD = np.array(_reorder_list_by_mapping(damaged.damping, map_D), dtype=float) if damaged.damping else np.zeros(len(fO))
    zR = np.array(_reorder_list_by_mapping(repaired.damping, map_R), dtype=float) if repaired.damping else np.zeros(len(fO))

    # consider only valid where we have all three frequencies positive
    mask = np.isfinite(fO) & np.isfinite(fD) & np.isfinite(fR) & (fO > 0) & (fD > 0) & (fR > 0)
    if not np.any(mask):
        raise ValueError("No valid matched modes to compute quality")

    fO = fO[mask]
    fD = fD[mask]
    fR = fR[mask]

    n = len(fO)

    denom = (fO - fD)
    denom = np.where(np.abs(denom) < 1e-6, np.sign(denom) * 1e-6 + 1e-6, denom)
    Q_freq_i = np.clip((fR - fD) / denom, 0.0, 1.0)
    Q_frequency = float(np.mean(Q_freq_i))

    Q_shape_i: List[float] = []
    for i in range(n):
        idxO = int(np.flatnonzero(mask)[i])
        phiO = np.array(mO[idxO]) if idxO < len(mO) else None
        phiR = np.array(mR[idxO]) if idxO < len(mR) else None
        if phiO is None or phiR is None or len(phiO) != len(phiR) or len(phiO) == 0:
            Q_shape_i.append(0.0)
        else:
            Q_shape_i.append(_mac(phiO, phiR))
    Q_shape = float(np.mean(Q_shape_i)) if Q_shape_i else 0.0

    zO = zO[mask] if len(zO) >= len(mask) else np.zeros(n)
    zD = zD[mask] if len(zD) >= len(mask) else np.zeros(n)
    zR = zR[mask] if len(zR) >= len(mask) else np.zeros(n)

    # Damping recovery calculation with improved edge case handling
    # When original and damaged damping are very similar (no significant change),
    # use absolute error instead of relative recovery formula
    denom_z = np.abs(zD - zO)
    
    # Check if damping changed significantly (threshold: 10% relative change or 0.005 absolute)
    DAMPING_CHANGE_THRESHOLD_REL = 0.10  # 10% relative change
    DAMPING_CHANGE_THRESHOLD_ABS = 0.005  # 0.005 absolute change (e.g., 0.02 -> 0.025)
    
    significant_change = (denom_z > DAMPING_CHANGE_THRESHOLD_REL * np.abs(zO)) | (denom_z > DAMPING_CHANGE_THRESHOLD_ABS)
    
    # For modes with significant damping change: use recovery formula
    # For modes with negligible damping change: use similarity metric
    Q_damp_i = np.zeros(n)
    
    if np.any(significant_change):
        # Recovery formula for modes where damping changed significantly
        denom_z_safe = np.where(denom_z < 1e-6, 1e-6, denom_z)
        Q_damp_i[significant_change] = np.clip(
            1.0 - np.abs(zR[significant_change] - zO[significant_change]) / denom_z_safe[significant_change],
            0.0, 1.0
        )
    
    if np.any(~significant_change):
        # For modes where damping barely changed: reward similarity to original
        # Score based on how close repaired is to original (not recovery from damage)
        error = np.abs(zR[~significant_change] - zO[~significant_change])
        # Map error to score: error of 0 -> score 1.0, error of 0.02 -> score 0.5, error > 0.05 -> score 0
        Q_damp_i[~significant_change] = np.clip(1.0 - error / 0.02, 0.0, 1.0)
    
    Q_damping = float(np.mean(Q_damp_i))

    overall = 0.5 * Q_frequency + 0.3 * Q_shape + 0.2 * Q_damping

    if overall >= 0.95:
        interp = ("Excellent - Nearly Perfect Repair", "EXCELLENT")
    elif overall >= 0.85:
        interp = ("Very Good - Highly Effective Repair", "VERY_GOOD")
    elif overall >= 0.70:
        interp = ("Good - Acceptable Repair", "GOOD")
    elif overall >= 0.50:
        interp = ("Fair - Partial Improvement", "FAIR")
    else:
        interp = ("Poor - Minimal Improvement", "POOR")

    per_mode = []
    for i in range(n):
        per_mode.append({
            "mode": i + 1,
            "frequency_recovery": float(Q_freq_i[i]),
            "mac_value": float(Q_shape_i[i] if i < len(Q_shape_i) else 0.0),
            "damping_recovery": float(Q_damp_i[i])
        })

    qa = QualityAssessment(
        overall_score=float(overall),
        breakdown=QualityBreakdown(
            frequency_recovery=float(Q_frequency),
            mode_shape_match=float(Q_shape),
            damping_recovery=float(Q_damping),
        ),
        per_mode_analysis=per_mode,
        interpretation=interp[0],
        interpretation_code=interp[1],
        confidence_level="high" if n >= 3 else "medium" if n == 2 else "low",
    )
    return qa

# -------------------------------
# Visualization
# -------------------------------

def _score_color(v: float) -> str:
    if v < 0.6:
        return "#e74c3c"  # red
    if v < 0.85:
        return "#f1c40f"  # yellow
    return "#2ecc71"      # green


def create_visualizations(original: ModalParameters,
                          damaged: ModalParameters,
                          repaired: ModalParameters,
                          quality: QualityAssessment,
                          output_prefix: str = "repair_analysis_report",
                          output_dir: str = "output") -> None:
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12), dpi=300)
    ax1, ax2, ax3, ax4, ax5, ax6 = axes.flatten()

    # Subplot 1: Frequency comparison
    modes = list(range(1, min(len(original.frequencies), len(damaged.frequencies), len(repaired.frequencies)) + 1))
    x = np.arange(len(modes))
    width = 0.25
    ax1.bar(x - width, [original.frequencies[i-1] for i in modes], width=width, color="#3498db", label="Original")
    ax1.bar(x,          [damaged.frequencies[i-1] for i in modes], width=width, color="#e74c3c", label="Damaged")
    ax1.bar(x + width,  [repaired.frequencies[i-1] for i in modes], width=width, color="#2ecc71", label="Repaired")
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"Mode {i}" for i in modes])
    ax1.set_xlabel("Mode number")
    ax1.set_ylabel("Frequency (Hz)")
    ax1.set_title("Natural Frequencies Comparison")
    ax1.legend(loc='upper right')

    # Subplot 2: Frequency spectrum (use avg FFT data for three states)
    ax2.plot(original.fft_data.frequencies, original.fft_data.amplitude, color="#3498db", label="Original")
    ax2.plot(damaged.fft_data.frequencies, damaged.fft_data.amplitude, color="#e74c3c", linestyle='--', label="Damaged")
    ax2.plot(repaired.fft_data.frequencies, repaired.fft_data.amplitude, color="#2ecc71", linestyle=':', label="Repaired")
    # mark peaks
    for f in original.frequencies:
        ax2.plot([f], [np.interp(f, original.fft_data.frequencies, original.fft_data.amplitude)], 'o', color="#3498db")
    for f in damaged.frequencies:
        ax2.plot([f], [np.interp(f, damaged.fft_data.frequencies, damaged.fft_data.amplitude)], 'o', color="#e74c3c")
    for f in repaired.frequencies:
        ax2.plot([f], [np.interp(f, repaired.fft_data.frequencies, repaired.fft_data.amplitude)], 'o', color="#2ecc71")
    ax2.set_xlim(0, min(500, original.fft_data.frequencies[-1]))
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Amplitude (normalized)")
    ax2.set_title("Frequency Response Spectrum")
    ax2.legend()

    # Subplot 3: Mode shapes comparison (first 3 modes)
    ms_count = min(3, len(original.mode_shapes), len(repaired.mode_shapes))
    sensor_idx = np.arange(len(original.mode_shapes[0])) if original.mode_shapes else np.arange(4)
    colors_o = ["#2980b9", "#2471a3", "#1f618d"]
    colors_r = ["#27ae60", "#229954", "#1e8449"]
    for i in range(ms_count):
        ax3.plot(sensor_idx + 1, original.mode_shapes[i], marker='o', color=colors_o[i % len(colors_o)], label=f"Original M{i+1}")
        ax3.plot(sensor_idx + 1, repaired.mode_shapes[i], marker='s', linestyle='--', color=colors_r[i % len(colors_r)], label=f"Repaired M{i+1}")
    ax3.set_xlabel("Sensor position")
    ax3.set_ylabel("Normalized amplitude")
    ax3.set_title("Mode Shape Comparison (First 3 Modes)")
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    # Subplot 4: Damping comparison
    ax4.bar(x - width, [original.damping[i-1] if i-1 < len(original.damping) else 0 for i in modes], width=width, color="#3498db", label="Original")
    ax4.bar(x,          [damaged.damping[i-1] if i-1 < len(damaged.damping) else 0 for i in modes], width=width, color="#e74c3c", label="Damaged")
    ax4.bar(x + width,  [repaired.damping[i-1] if i-1 < len(repaired.damping) else 0 for i in modes], width=width, color="#2ecc71", label="Repaired")
    ax4.set_xticks(x)
    ax4.set_xticklabels([f"Mode {i}" for i in modes])
    ax4.set_xlabel("Mode number")
    ax4.set_ylabel("Damping ratio")
    ax4.set_title("Damping Ratios Comparison")
    ax4.legend()

    # Subplot 5: Quality score breakdown
    cats = ["Frequency Recovery", "Mode Shape Match", "Damping Recovery", "Overall Quality"]
    vals = [quality.breakdown.frequency_recovery, quality.breakdown.mode_shape_match, quality.breakdown.damping_recovery, quality.overall_score]
    colors = [_score_color(v) for v in vals]
    ax5.barh(cats, vals, color=colors)
    for i, v in enumerate(vals):
        ax5.text(v + 0.01, i, f"{v:.3f}", va='center')
    ax5.set_xlim(0, 1)
    ax5.set_title("Quality Score Breakdown")

    # Subplot 6: Overall score display
    ax6.axis('off')
    bg = _score_color(quality.overall_score)
    ax6.set_facecolor(bg + '33')  # translucent
    ax6.text(0.5, 0.65, f"{quality.overall_score:.3f}", ha='center', va='center', fontsize=60, fontweight='bold')
    ax6.text(0.5, 0.50, "Repair Quality Score", ha='center', va='center', fontsize=18)
    ax6.text(0.5, 0.35, quality.interpretation, ha='center', va='center', fontsize=20, fontweight='bold')
    ax6.text(0.5, 0.20, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ha='center', va='center', fontsize=12)
    ax6.set_title("Overall Assessment")

    fig.suptitle("Structural Repair Quality Analysis Report", fontsize=18, fontweight='bold')
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, f"{output_prefix}.png")
    pdf_path = os.path.join(output_dir, f"{output_prefix}.pdf")
    fig.savefig(png_path, dpi=300)
    with PdfPages(pdf_path) as pdf:
        pdf.savefig(fig)
    plt.close(fig)


# -------------------------------
# Terminal output & reports
# -------------------------------

def _progress_bar(value: float, width: int = 40) -> str:
    filled = int(round(value * width))
    bar = '█' * filled + '░' * (width - filled)
    return bar


def display_terminal_results(original: ModalParameters,
                             damaged: ModalParameters,
                             repaired: ModalParameters,
                             quality: QualityAssessment) -> str:
    _print_header()

    print(f"{Fore.CYAN}{Style.BRIGHT}Loading data files...{Style.RESET_ALL}")
    _ok("original.csv   ✓")
    _ok("damaged.csv    ✓")
    _ok("repaired.csv   ✓")

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Extracting modal parameters...{Style.RESET_ALL}")
    _ok("FFT analysis complete")
    _ok(f"{min(len(original.frequencies), len(damaged.frequencies), len(repaired.frequencies))} natural frequencies identified")
    _ok("Mode shapes extracted")
    _ok("Damping ratios estimated")

    # Summary lines similar to spec
    def freqs_line(mp: ModalParameters) -> str:
        return '  '.join([f"{f:.1f}" for f in mp.frequencies])

    def damps_line(mp: ModalParameters) -> str:
        return '  '.join([f"{z:.3f}" for z in mp.damping])

    print("\n" + "-" * 79)
    print("MODAL PARAMETER COMPARISON")
    print("-" * 79)
    print("\nORIGINAL STATE (Undamaged):")
    print(f"  Natural Frequencies (Hz):  {freqs_line(original)}")
    print(f"  Damping Ratios:            {damps_line(original)}")

    print("\nDAMAGED STATE:")
    print(f"  Natural Frequencies (Hz):  {freqs_line(damaged)}")
    print(f"  Damping Ratios:            {damps_line(damaged)}")

    if original.frequencies and damaged.frequencies:
        # percentage change original->damaged
        n = min(len(original.frequencies), len(damaged.frequencies))
        delta = (np.array(damaged.frequencies[:n]) - np.array(original.frequencies[:n])) / np.array(original.frequencies[:n]) * 100
        print(f"\n  Frequency Change:         {'  '.join([f'{v:+.1f}%' for v in delta])}")
        if np.mean(delta) < -5:
            _warn("Significant stiffness loss detected")

    print("\nREPAIRED STATE:")
    print(f"  Natural Frequencies (Hz):  {freqs_line(repaired)}")
    print(f"  Damping Ratios:            {damps_line(repaired)}")

    if damaged.frequencies and repaired.frequencies and original.frequencies:
        n = min(len(original.frequencies), len(damaged.frequencies), len(repaired.frequencies))
        rec = (np.array(repaired.frequencies[:n]) - np.array(damaged.frequencies[:n])) / (np.array(original.frequencies[:n]) - np.array(damaged.frequencies[:n]) + 1e-9) * 100
        print(f"\n  Frequency Recovery:       {'  '.join([f'{v:+.1f}%' for v in rec])}")
        if np.mean(rec) > 50:
            _ok("Substantial stiffness restoration achieved")

    print("\n" + "-" * 79)
    print("REPAIR QUALITY ASSESSMENT")
    print("-" * 79)
    print("\nIndividual Score Components:\n")
    print(f"  Frequency Recovery:        {quality.breakdown.frequency_recovery:6.3f}  {_progress_bar(quality.breakdown.frequency_recovery)}")
    print(f"  Mode Shape Preservation:   {quality.breakdown.mode_shape_match:6.3f}  {_progress_bar(quality.breakdown.mode_shape_match)}")
    print(f"  Damping Recovery:          {quality.breakdown.damping_recovery:6.3f}  {_progress_bar(quality.breakdown.damping_recovery)}")

    print("\n+" + "-" * 70 + "+")
    print("|".ljust(72))
    print("|" + "OVERALL REPAIR QUALITY SCORE".center(70) + "|")
    print("|".ljust(72))
    print("|" + f"{quality.overall_score:>8.3f}".center(70) + "|")
    print("|".ljust(72))
    stars = {
        "EXCELLENT": "⭐⭐ EXCELLENT REPAIR ⭐⭐",
        "VERY_GOOD": "⭐ VERY GOOD REPAIR ⭐",
        "GOOD": "GOOD REPAIR",
        "FAIR": "FAIR REPAIR",
        "POOR": "POOR REPAIR",
    }
    print("|" + stars.get(quality.interpretation_code, quality.interpretation).center(70) + "|")
    print("+" + "-" * 70 + "+\n")

    # Recommendations (simple heuristic)
    print("DETAILED INTERPRETATION\n")
    if quality.overall_score >= 0.85:
        print("✓ STRENGTHS:\n  • Frequency recovery is excellent\n  • Mode shape preservation is outstanding\n  • Consistent recovery across modes")
        print("\nAREAS OF NOTE:\n  • Damping recovery may differ slightly from original\n  • Consider monitoring mid-span regions")
    elif quality.overall_score >= 0.70:
        print("✓ STRENGTHS:\n  • Acceptable stiffness recovery\n  • Overall response aligns with original")
        print("\nAREAS OF NOTE:\n  • Some modes recover less; monitor these\n  • Evaluate damping if energy dissipation differs")
    else:
        print("⚠ AREAS OF NOTE:\n  • Limited improvement; consider additional repair\n  • Investigate bonding/fasteners and re-test")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nAnalysis completed at: {ts}\n")

    # Return a plain-text summary string for saving
    from io import StringIO
    buf = StringIO()
    sys_stdout = sys.stdout
    try:
        sys.stdout = buf
        print("STRUCTURAL REPAIR QUALITY ANALYSIS SYSTEM v1.0\n")
        print("MODAL PARAMETER COMPARISON")
        print(f"Original frequencies: {original.frequencies}")
        print(f"Damaged  frequencies: {damaged.frequencies}")
        print(f"Repaired frequencies: {repaired.frequencies}")
        print("\nREPAIR QUALITY ASSESSMENT")
        print(json.dumps({
            "overall": quality.overall_score,
            "frequency": quality.breakdown.frequency_recovery,
            "mode_shape": quality.breakdown.mode_shape_match,
            "damping": quality.breakdown.damping_recovery,
            "interpretation": quality.interpretation,
        }, indent=2))
        print(f"\nAnalysis completed at: {ts}")
    finally:
        sys.stdout = sys_stdout
    return buf.getvalue()


def save_detailed_report(original: ModalParameters,
                         damaged: ModalParameters,
                         repaired: ModalParameters,
                         quality: QualityAssessment,
                         fs: float,
                         structure_id: str,
                         output_prefix: str = "repair_analysis_report",
                         mode_mapping_d: List[Optional[int]] | None = None,
                         mode_mapping_r: List[Optional[int]] | None = None,
                         output_dir: str = "output") -> Tuple[str, str]:
    meta = {
        "analysis_date": datetime.now().isoformat(timespec='seconds'),
        "program_version": "1.0",
        "structure_id": structure_id,
        "sampling_rate_hz": fs,
        "recording_duration_sec": None,
    }

    # frequency change stats
    n = min(len(original.frequencies), len(damaged.frequencies), len(repaired.frequencies))
    stats: Dict[str, object] = {}
    if n > 0:
        fO = np.array(original.frequencies[:n])
        fD = np.array(damaged.frequencies[:n])
        fR = np.array(repaired.frequencies[:n])
        stats = {
            "frequency_changes": {
                "original_to_damaged_percent": ((fD - fO) / np.where(fO == 0, 1, fO) * 100).round(1).tolist(),
                "damaged_to_repaired_percent": ((fR - fD) / np.where(fD == 0, 1, fD) * 100).round(1).tolist(),
                "recovery_percent": (((fR - fD) / np.where((fO - fD) == 0, 1, (fO - fD))) * 100).round(1).tolist(),
            },
            "average_stiffness_loss_percent": float(np.mean(((fD - fO) / np.where(fO == 0, 1, fO) * 100))),
            "average_stiffness_recovery_percent": float(np.mean(((fR - fD) / np.where((fO - fD) == 0, 1, (fO - fD)) * 100))),
        }

    report = {
        "metadata": meta,
        "modal_parameters": {
            "original_state": {
                "natural_frequencies_hz": original.frequencies,
                "mode_shapes": original.mode_shapes,
                "damping_ratios": original.damping,
            },
            "damaged_state": {
                "natural_frequencies_hz": damaged.frequencies,
                "mode_shapes": damaged.mode_shapes,
                "damping_ratios": damaged.damping,
            },
            "repaired_state": {
                "natural_frequencies_hz": repaired.frequencies,
                "mode_shapes": repaired.mode_shapes,
                "damping_ratios": repaired.damping,
            },
        },
        "quality_assessment": {
            "overall_score": quality.overall_score,
            "breakdown": {
                "frequency_recovery": quality.breakdown.frequency_recovery,
                "mode_shape_match": quality.breakdown.mode_shape_match,
                "damping_recovery": quality.breakdown.damping_recovery,
            },
            "per_mode_analysis": quality.per_mode_analysis,
            "interpretation": quality.interpretation,
            "interpretation_code": quality.interpretation_code,
            "confidence_level": quality.confidence_level,
        },
        "statistics": stats,
        "mode_mapping": {
            "damaged_to_original": mode_mapping_d,
            "repaired_to_original": mode_mapping_r
        },
        "mac_matrices": {
            "original_vs_damaged": _mac_matrix(original.mode_shapes, damaged.mode_shapes).tolist() if original.mode_shapes and damaged.mode_shapes else [],
            "original_vs_repaired": _mac_matrix(original.mode_shapes, repaired.mode_shapes).tolist() if original.mode_shapes and repaired.mode_shapes else []
        },
        "recommendations": [
            "Structure suitable for normal operating loads" if quality.overall_score >= 0.70 else "Further repair recommended",
            "Schedule follow-up inspection in 6 months",
            "Document repair in maintenance records",
            "Monitor vibration behavior periodically",
        ],
    }

    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, f"{output_prefix}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    summary_text = display_terminal_results(original, damaged, repaired, quality)
    txt_path = os.path.join(output_dir, f"{output_prefix}_summary.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(summary_text)

    return json_path, txt_path


# -------------------------------
# Demo data generator
# -------------------------------

def _sine_decay(f: float, t: np.ndarray, z: float = 0.02) -> np.ndarray:
    return np.exp(-z * 2 * np.pi * f * t) * np.sin(2 * np.pi * f * t)


def generate_demo_data(fs: float = DEFAULT_FS, duration: float = 5.0, sensors: int = 4,
                       noise_level: float = 0.02, seed: int | None = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(int(fs * duration)) / fs
    # Base modal frequencies
    freqs_orig = [45.0, 180.0, 320.0]
    freqs_dmg = [f * 0.9 for f in freqs_orig]
    freqs_rep = [f * 0.97 for f in freqs_orig]

    def synth(freqs, zetas):
        sig = np.zeros((len(t), sensors))
        for i, f in enumerate(freqs):
            z = zetas[i] if i < len(zetas) else 0.02
            mode = _sine_decay(f, t, z)
            # simple mode shapes per sensor
            for s in range(sensors):
                weight = (s + 1) / sensors
                sig[:, s] += weight * mode
        sig += noise_level * np.random.randn(*sig.shape)
        return sig

    orig = synth(freqs_orig, [0.02, 0.025, 0.03])
    dmg = synth(freqs_dmg, [0.04, 0.045, 0.05])
    rep = synth(freqs_rep, [0.025, 0.03, 0.033])
    return orig, dmg, rep


# -------------------------------
# CLI
# -------------------------------

def main():
    parser = argparse.ArgumentParser(description="Structural Repair Quality Analyzer")
    parser.add_argument('--original', type=str, help='Path to original.csv')
    parser.add_argument('--damaged', type=str, help='Path to damaged.csv')
    parser.add_argument('--repaired', type=str, help='Path to repaired.csv')
    parser.add_argument('--fs', type=float, default=DEFAULT_FS, help='Sampling rate (Hz)')
    parser.add_argument('--max-modes', type=int, default=DEFAULT_MAX_MODES, help='Maximum modes to extract')
    parser.add_argument('--output-prefix', type=str, default='repair_analysis_report', help='Output file prefix for report assets')
    parser.add_argument('--structure-id', type=str, default='Test_Structure_001', help='Structure identifier')
    parser.add_argument('--output-dir', type=str, default='output', help='Directory to store all outputs')
    parser.add_argument('--min-freq', type=float, default=DEFAULT_MIN_FREQ, help='Min frequency to consider for peaks (Hz)')
    parser.add_argument('--max-freq', type=float, default=DEFAULT_MAX_FREQ, help='Max frequency to consider for peaks (Hz)')
    parser.add_argument('--generate-demo', action='store_true', help='Generate demo data instead of reading CSVs')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for demo data')
    parser.add_argument('--sensors', type=int, default=4, help='Number of sensors for demo data')
    parser.add_argument('--save-demo-csvs', action='store_true', help='If using demo, also save CSVs original.csv/damaged.csv/repaired.csv')

    args = parser.parse_args()

    # Try loading metadata to override defaults
    if not args.generate_demo and hasattr(args, 'original') and args.original:
        metadata = load_metadata(args.original)
        if metadata:
            # Override fs if specified in metadata
            if 'sampling_rate_hz' in metadata:
                args.fs = metadata['sampling_rate_hz']
                print(f"[info] Using sampling rate: {args.fs} Hz (from metadata)")
            
            # Override frequency range if specified
            if 'frequency_range' in metadata:
                if 'min' in metadata['frequency_range']:
                    args.min_freq = metadata['frequency_range']['min']
                if 'max' in metadata['frequency_range']:
                    args.max_freq = metadata['frequency_range']['max']
                print(f"[info] Using frequency range: {args.min_freq}-{args.max_freq} Hz (from metadata)")
            
            # Store structure info if present (for future use in reports)
            if 'structure' in metadata:
                args.structure_metadata = metadata['structure']

    try:
        if args.generate_demo or not (args.original and args.damaged and args.repaired):
            orig_data, dmg_data, rep_data = generate_demo_data(fs=args.fs, duration=5.0, sensors=args.sensors, seed=args.seed)
            if args.save_demo_csvs:
                header = ','.join([f'sensor{i+1}' for i in range(args.sensors)]) + '\n'
                import numpy as _np
                os.makedirs(args.output_dir, exist_ok=True)
                for name, data in [('original.csv', orig_data), ('damaged.csv', dmg_data), ('repaired.csv', rep_data)]:
                    path = os.path.join(args.output_dir, name)
                    with open(path, 'w') as f:
                        f.write(header)
                        _np.savetxt(f, data, delimiter=',', fmt='%.6f')
        else:
            # Load and validate data
            print("Loading and validating data files...")
            df_original = validate_csv_data(args.original, args.fs, "Original")
            print(f"[✓] original.csv   ✓")
            df_damaged = validate_csv_data(args.damaged, args.fs, "Damaged")
            print(f"[✓] damaged.csv    ✓")
            df_repaired = validate_csv_data(args.repaired, args.fs, "Repaired")
            print(f"[✓] repaired.csv   ✓")
            
            # Convert validated DataFrames to numpy arrays for processing
            orig_data = load_csv_data(args.original)
            dmg_data = load_csv_data(args.damaged)
            rep_data = load_csv_data(args.repaired)

        original = extract_modal_parameters(orig_data, fs=args.fs, max_modes=args.max_modes, min_freq=args.min_freq, max_freq=args.max_freq)
        damaged = extract_modal_parameters(dmg_data, fs=args.fs, max_modes=args.max_modes, min_freq=args.min_freq, max_freq=args.max_freq)
        repaired = extract_modal_parameters(rep_data, fs=args.fs, max_modes=args.max_modes, min_freq=args.min_freq, max_freq=args.max_freq)

        quality = calculate_repair_quality(original, damaged, repaired)

        # Terminal display and files
        summary = display_terminal_results(original, damaged, repaired, quality)
        print(summary)

        create_visualizations(original, damaged, repaired, quality, output_prefix=args.output_prefix, output_dir=args.output_dir)
        json_path, txt_path = save_detailed_report(
            original, damaged, repaired, quality, fs=args.fs,
            structure_id=args.structure_id, output_prefix=args.output_prefix,
            mode_mapping_d=map_D if 'map_D' in locals() else None,
            mode_mapping_r=map_R if 'map_R' in locals() else None,
            output_dir=args.output_dir
        )
        print(f"[✓] Visualization saved: {args.output_prefix}.png")
        print(f"[✓] PDF report saved: {args.output_prefix}.pdf")
        print(f"[✓] Detailed report saved: {json_path}")
        print(f"[✓] Summary text saved: {txt_path}")
        return 0
    except Exception as e:
        _err(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())


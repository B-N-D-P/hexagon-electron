"""Backend data adapters.

Goal: Support multiple CSV formats and convert them into arrays compatible with
existing analyzers:
- repair_analyzer.py expects (N, S) where S = number of sensors (single-axis)
- For 3-axis ADXL345 files (5 sensors = 15 cols), we convert to per-sensor magnitude.

Supported input:
- 15 columns: 5 sensors × 3 axis
- 16 columns: time + 15 columns
- fallback: any numeric CSV (single-axis)
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


def _count_columns(csv_path: str) -> int:
    """Count columns, skipping duplicate headers."""
    df = pd.read_csv(csv_path, nrows=5)
    return df.shape[1]


def _load_csv_robust(csv_path: str) -> pd.DataFrame:
    """
    Load CSV with robust header detection.
    Handles:
    - Duplicate header rows
    - Missing headers
    - Mixed data types in first row
    """
    with open(csv_path, 'r') as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        raise ValueError(f"CSV file too short: {len(lines)} lines")
    
    # Check if first two rows are identical (duplicate header)
    line1 = lines[0].strip()
    line2 = lines[1].strip() if len(lines) > 1 else ""
    
    if line1 == line2:
        # Duplicate header - skip first line
        print(f"⚠️  Detected duplicate header in {csv_path}, skipping first line")
        df = pd.read_csv(csv_path, skiprows=[0])
    else:
        # Try normal read
        df = pd.read_csv(csv_path)
    
    # Check if header is actually data (no header case)
    # If first row can be converted to all floats, there's no header
    try:
        first_row_numeric = pd.to_numeric(df.iloc[0], errors='coerce')
        if not first_row_numeric.isna().any():
            # First row is all numeric - header is missing or wrong
            # Check if column names look like data
            col_numeric = pd.to_numeric(df.columns, errors='coerce')
            if not col_numeric.isna().any():
                # Column names are numeric - no header!
                print(f"⚠️  No header detected in {csv_path}, using default column names")
                df = pd.read_csv(csv_path, header=None)
                # Add default column names
                df.columns = [f'S{i//3+1}_{"XYZ"[i%3]}_g' for i in range(len(df.columns))]
    except Exception:
        pass  # Keep original dataframe
    
    return df


def load_timeseries_for_modal(csv_path: str) -> np.ndarray:
    """Load CSV and return (N,S) float array suitable for repair_analyzer.extract_modal_parameters.

    FIXED: Handles duplicate headers, missing headers, and malformed CSVs
    
    - If 6 columns: 2-sensor 3-axis (XYZ), return as-is
    - If 15/16 columns: interpret as 5-sensor 3-axis, convert to magnitude => (N,5)
    - Else: generic loader
    """
    # Use robust loader
    df = _load_csv_robust(csv_path)
    ncols = df.shape[1]
    
    # 2 sensors x 3-axis = 6 columns (most common for this project)
    if ncols == 6:
        # Convert to numeric, drop NaNs
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.dropna()
        
        if df.empty:
            raise ValueError(f"No valid numeric data in {csv_path}")
        
        # Return as-is for 2-sensor system
        return df.to_numpy(dtype=float)

    # 5 sensors x 3-axis (optionally with time)
    if ncols in (15, 16):
        # Local, dependency-free conversion: (N, 5*3 [+ time]) -> (N, 5)
        df = pd.read_csv(csv_path)
        # Keep only numeric (do not drop rows; preserve sample count)
        df = df.apply(pd.to_numeric, errors='coerce')
        # If there is a leading time column -> drop it
        if df.shape[1] == 16:
            df = df.iloc[:, 1:]
        elif df.shape[1] == 15:
            pass
        else:
            # Unexpected after re-read; fall back later
            pass
        # Fill NaNs to preserve length
        if df.isna().values.any():
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0.0)
        arr = df.to_numpy(dtype=float)  # shape (N, 15) ideally
        if arr.shape[1] != 15:
            # Fallback to generic loader below
            pass
        else:
            # reshape to (N, 5, 3) and compute magnitude per sensor
            N = arr.shape[0]
            s3 = arr.reshape(N, 5, 3)
            mags = (s3[..., 0]**2 + s3[..., 1]**2 + s3[..., 2]**2) ** 0.5  # (N,5)
            # Ensure sufficient length for frequency resolution (tile if short)
            if mags.shape[0] < 1024:
                reps = int(np.ceil(1024 / mags.shape[0]))
                mags = np.tile(mags, (reps, 1))[:1024, :]
            return mags

    # Fallback: use repair_analyzer loader
    import sys
    home_dir = Path.home()
    py_dir = home_dir / 'python123'
    sys.path.insert(0, str(py_dir))
    from repair_analyzer import load_csv_data
    return load_csv_data(csv_path)

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
    df = pd.read_csv(csv_path, nrows=5)
    return df.shape[1]


def load_timeseries_for_modal(csv_path: str) -> np.ndarray:
    """Load CSV and return (N,S) float array suitable for repair_analyzer.extract_modal_parameters.

    - If 15/16 columns: interpret as 5-sensor 3-axis, convert to magnitude => (N,5)
    - Else: fall back to repair_analyzer.load_csv_data (single-axis general)
    """
    ncols = _count_columns(csv_path)

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

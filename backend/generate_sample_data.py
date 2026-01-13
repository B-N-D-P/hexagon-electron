#!/usr/bin/env python3
"""
Generate sample accelerometer data for testing the Structural Repair Analysis System

This script creates realistic synthetic data simulating:
1. Original (undamaged) structure
2. Damaged structure (with stiffness loss)
3. Repaired structure (partial recovery)

Output: CSV files suitable for upload to the web application
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Parameters
FS = 1000.0  # Sampling rate (Hz)
DURATION = 10.0  # Duration (seconds)
NUM_SENSORS = 5
NUM_SAMPLES = int(FS * DURATION)

# Modal frequencies (Hz)
MODES_ORIGINAL = [45.0, 180.0, 320.0]
MODES_DAMAGED = [40.0, 160.0, 290.0]  # ~10-12% frequency loss
MODES_REPAIRED = [43.0, 175.0, 310.0]  # Partial recovery

# Damping ratios
DAMPING_ORIGINAL = [0.02, 0.025, 0.03]
DAMPING_DAMAGED = [0.04, 0.045, 0.05]  # Increased damping from damage
DAMPING_REPAIRED = [0.025, 0.030, 0.033]  # Improved but not perfect


def sine_decay(f: float, t: np.ndarray, z: float = 0.02, amplitude: float = 1.0) -> np.ndarray:
    """
    Generate damped sinusoid signal.
    
    x(t) = A * exp(-z*2π*f*t) * sin(2π*f*t)
    
    Args:
        f: Frequency (Hz)
        t: Time array
        z: Damping ratio
        amplitude: Signal amplitude
    
    Returns:
        Time series data
    """
    return amplitude * np.exp(-z * 2 * np.pi * f * t) * np.sin(2 * np.pi * f * t)


def generate_accelerometer_data(frequencies: list, damping_ratios: list, 
                               fs: float = 1000.0, duration: float = 10.0,
                               num_sensors: int = 4, noise_level: float = 0.02,
                               seed: int = None) -> np.ndarray:
    """
    Generate synthetic accelerometer data.
    
    Args:
        frequencies: List of modal frequencies (Hz)
        damping_ratios: List of damping ratios for each mode
        fs: Sampling frequency (Hz)
        duration: Duration of signal (seconds)
        num_sensors: Number of sensors
        noise_level: Gaussian noise standard deviation
        seed: Random seed for reproducibility
    
    Returns:
        Array of shape (num_samples, num_sensors) with acceleration data
    """
    if seed is not None:
        np.random.seed(seed)
    
    num_samples = int(fs * duration)
    t = np.arange(num_samples) / fs
    
    # Initialize data array
    data = np.zeros((num_samples, num_sensors))
    
    # Add each mode to all sensors
    for mode_idx, (f, z) in enumerate(zip(frequencies, damping_ratios)):
        mode_signal = sine_decay(f, t, z, amplitude=1.0)
        
        # Each sensor has a different mode shape
        for sensor_idx in range(num_sensors):
            # Mode shape: weight varies by sensor position
            sensor_weight = (sensor_idx + 1) / num_sensors
            
            # Add some phase variation between sensors (realistic)
            phase_shift = (sensor_idx * 0.2) % (2 * np.pi)
            phase_shifted_mode = sensor_weight * mode_signal * np.cos(phase_shift)
            
            data[:, sensor_idx] += phase_shifted_mode
    
    # Add realistic Gaussian noise
    data += noise_level * np.random.randn(num_samples, num_sensors)
    
    # Normalize to realistic accelerometer range (-10g to +10g, in m/s²)
    data = data * 5.0  # Scale to ~5 m/s² peak
    
    return data


def create_csv_file(data: np.ndarray, filename: str, sensor_names: list = None):
    """
    Save accelerometer data to CSV file.
    
    Args:
        data: Array of shape (num_samples, num_sensors)
        filename: Output filename
        sensor_names: List of sensor names (optional)
    """
    if sensor_names is None:
        sensor_names = [f'sensor{i+1}' for i in range(data.shape[1])]
    
    df = pd.DataFrame(data, columns=sensor_names)
    df.to_csv(filename, index=False)
    print(f"✓ Created: {filename}")
    print(f"  - Samples: {data.shape[0]}")
    print(f"  - Sensors: {data.shape[1]}")
    print(f"  - Duration: {data.shape[0] / FS:.1f}s")


def main():
    """Generate all sample data files."""
    print("\n" + "="*70)
    print("SAMPLE DATA GENERATION FOR STRUCTURAL REPAIR ANALYSIS SYSTEM")
    print("="*70 + "\n")
    
    # Create sample_data directory
    sample_dir = Path(__file__).parent / "sample_data"
    sample_dir.mkdir(exist_ok=True)
    
    print("Generating synthetic accelerometer data...\n")
    
    # 1. Original (Baseline) Structure
    print("[1/3] Original (Undamaged) Structure")
    print(f"      Modes: {MODES_ORIGINAL}")
    print(f"      Damping: {DAMPING_ORIGINAL}")
    original_data = generate_accelerometer_data(
        MODES_ORIGINAL, DAMPING_ORIGINAL,
        fs=FS, duration=DURATION, num_sensors=NUM_SENSORS,
        noise_level=0.02, seed=42
    )
    create_csv_file(original_data, sample_dir / "original.csv")
    print()
    
    # 2. Damaged Structure
    print("[2/3] Damaged Structure")
    print(f"      Modes: {MODES_DAMAGED}")
    print(f"      Damping: {DAMPING_DAMAGED}")
    print(f"      Frequency loss: {((np.mean(MODES_ORIGINAL) - np.mean(MODES_DAMAGED)) / np.mean(MODES_ORIGINAL) * 100):.1f}%")
    damaged_data = generate_accelerometer_data(
        MODES_DAMAGED, DAMPING_DAMAGED,
        fs=FS, duration=DURATION, num_sensors=NUM_SENSORS,
        noise_level=0.03, seed=123  # Slightly more noise for damaged structure
    )
    create_csv_file(damaged_data, sample_dir / "damaged.csv")
    print()
    
    # 3. Repaired Structure
    print("[3/3] Repaired Structure")
    print(f"      Modes: {MODES_REPAIRED}")
    print(f"      Damping: {DAMPING_REPAIRED}")
    print(f"      Frequency recovery: {((MODES_REPAIRED[0] - MODES_DAMAGED[0]) / (MODES_ORIGINAL[0] - MODES_DAMAGED[0]) * 100):.1f}%")
    repaired_data = generate_accelerometer_data(
        MODES_REPAIRED, DAMPING_REPAIRED,
        fs=FS, duration=DURATION, num_sensors=NUM_SENSORS,
        noise_level=0.02, seed=456
    )
    create_csv_file(repaired_data, sample_dir / "repaired.csv")
    print()
    
    # 4. Summary Statistics
    print("="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    print(f"\nOriginal Structure:")
    print(f"  - Mean frequency: {np.mean(MODES_ORIGINAL):.1f} Hz")
    print(f"  - Mean damping: {np.mean(DAMPING_ORIGINAL):.4f}")
    print(f"  - RMS acceleration: {np.sqrt(np.mean(original_data**2)):.3f} m/s²")
    
    print(f"\nDamaged Structure:")
    print(f"  - Mean frequency: {np.mean(MODES_DAMAGED):.1f} Hz ({(np.mean(MODES_DAMAGED)/np.mean(MODES_ORIGINAL)-1)*100:+.1f}%)")
    print(f"  - Mean damping: {np.mean(DAMPING_DAMAGED):.4f}")
    print(f"  - RMS acceleration: {np.sqrt(np.mean(damaged_data**2)):.3f} m/s²")
    
    print(f"\nRepaired Structure:")
    print(f"  - Mean frequency: {np.mean(MODES_REPAIRED):.1f} Hz ({(np.mean(MODES_REPAIRED)/np.mean(MODES_ORIGINAL)-1)*100:+.1f}%)")
    print(f"  - Mean damping: {np.mean(DAMPING_REPAIRED):.4f}")
    print(f"  - RMS acceleration: {np.sqrt(np.mean(repaired_data**2)):.3f} m/s²")
    
    print("\n" + "="*70)
    print("✓ Sample data generation complete!")
    print(f"✓ Files saved to: {sample_dir}")
    print("="*70 + "\n")
    
    print("Usage:")
    print("  1. Open http://localhost:3000 in your browser")
    print("  2. Select 'Repair Quality Analysis'")
    print(f"  3. Upload the three CSV files from {sample_dir}")
    print("  4. Click 'Run Analysis'")
    print("  5. View results in dashboard!\n")


if __name__ == "__main__":
    main()

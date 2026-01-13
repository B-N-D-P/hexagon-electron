#!/usr/bin/env python3
"""
Integration test for real-time streaming monitoring.

Tests Mode B (no baseline) and Mode A (with baseline) scenarios.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "services"))

from live_buffer import LiveAnalysisEngine
from baseline_manager import BaselineManager


def test_mode_b_basic():
    """Test Mode B: Basic streaming without baseline."""
    print("\n" + "="*80)
    print("TEST: Mode B - Basic Streaming (No Baseline)")
    print("="*80)
    
    # Initialize engine
    engine = LiveAnalysisEngine(fs=1000.0, num_sensors=5, buffer_duration_sec=60)
    
    print("\n✓ Engine initialized")
    print(f"  - Buffer duration: 60s")
    print(f"  - Sensors: 5")
    print(f"  - Sampling rate: 1000 Hz")
    
    # Simulate ingest of frames
    print("\n▶ Simulating frame ingestion (10 seconds)...")
    
    start_time = datetime.utcnow()
    for i in range(10000):  # 10 seconds at 1000 Hz
        ts = datetime.utcnow()
        
        # Generate synthetic frame (magnitude mode)
        frame = [
            0.1 + 0.05 * np.sin(2 * np.pi * 12.5 * i / 1000),  # S1
            0.12 + 0.05 * np.sin(2 * np.pi * 12.5 * i / 1000 + 0.5),  # S2
            0.11 + 0.05 * np.sin(2 * np.pi * 12.5 * i / 1000 + 1.0),  # S3
            0.09 + 0.05 * np.sin(2 * np.pi * 12.5 * i / 1000 + 1.5),  # S4
            0.13 + 0.05 * np.sin(2 * np.pi * 12.5 * i / 1000 + 2.0),  # S5
        ]
        
        frame_data = {
            'ts': ts.isoformat() + 'Z',
            'fs': 1000.0,
            'sensors': 5,
            'mode': 'magnitude',
            'frame': frame
        }
        
        engine.ingest_frame(frame_data)
        
        if (i + 1) % 2000 == 0:
            print(f"  → {(i+1)/1000:.0f}s of data ingested")
    
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    print(f"\n✓ Ingestion complete ({elapsed:.2f}s wall time)")
    
    # Compute metrics
    print("\n▶ Computing metrics...")
    metrics = engine.compute_metrics()
    
    print(f"\n✓ Metrics computed:")
    print(f"  QC:")
    print(f"    - Jitter: {metrics['qc']['jitter_ms']:.3f} ms")
    print(f"    - SNR: {metrics['qc']['snr_db']:.1f} dB")
    print(f"    - Clipping: {sum(metrics['qc']['clipping'])}/5 sensors")
    
    print(f"  Analysis:")
    print(f"    - PSD computed: {len(metrics['metrics'].get('psd', {}).get('freqs', []))} frequency bins")
    print(f"    - Peaks detected: {len(metrics['metrics'].get('peaks', []))}")
    print(f"    - RMS values: {[f'{r:.3f}g' for r in metrics['metrics'].get('rms', [])]}")
    
    # Test baseline capture
    print("\n▶ Testing baseline capture (Mode B)...")
    baseline = engine.capture_baseline_from_buffer()
    print(f"\n✓ Baseline captured:")
    print(f"    - Peaks: {baseline.get('peaks', [])}")
    print(f"    - RMS baseline: {baseline.get('rms_baseline', {})}")
    
    return True


def test_mode_a_comparative():
    """Test Mode A: Comparative analysis with baseline."""
    print("\n" + "="*80)
    print("TEST: Mode A - Comparative Analysis (With Baseline)")
    print("="*80)
    
    # Create baseline manager
    outputs_dir = Path(__file__).parent.parent / "backend" / "outputs"
    baseline_mgr = BaselineManager(outputs_dir)
    
    print(f"\n✓ Baseline manager initialized")
    print(f"  - Outputs dir: {outputs_dir}")
    print(f"  - Available baselines: {len(baseline_mgr.baselines)}")
    
    # Initialize engine without baseline
    engine1 = LiveAnalysisEngine(fs=1000.0, num_sensors=5)
    
    print("\n▶ Simulating healthy baseline collection (5 seconds)...")
    for i in range(5000):
        ts = datetime.utcnow()
        frame = [
            0.1 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000),
            0.12 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000 + 0.5),
            0.11 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000 + 1.0),
            0.09 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000 + 1.5),
            0.13 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000 + 2.0),
        ]
        frame_data = {
            'ts': ts.isoformat() + 'Z',
            'fs': 1000.0,
            'sensors': 5,
            'mode': 'magnitude',
            'frame': frame
        }
        engine1.ingest_frame(frame_data)
    
    # Capture baseline
    baseline_profile = engine1.capture_baseline_from_buffer()
    baseline_obj = baseline_mgr.create_baseline_from_live(
        baseline_profile, 
        name="TestBaseline_Healthy"
    )
    baseline_mgr.set_current_baseline(baseline_obj.profile_id)
    print(f"✓ Baseline created: {baseline_obj.name}")
    
    # Initialize engine with baseline
    engine2 = LiveAnalysisEngine(
        fs=1000.0, 
        num_sensors=5,
        baseline_profile=baseline_mgr.get_current_baseline_dict()
    )
    
    print("\n▶ Simulating damaged state (5 seconds)...")
    for i in range(5000):
        ts = datetime.utcnow()
        # Simulate damage: frequency shift and amplitude change on sensor 3
        frame = [
            0.1 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000),
            0.12 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000 + 0.5),
            # Sensor 3: frequency shift (13 Hz instead of 12.5) and amplitude increase
            0.20 + 0.04 * np.sin(2 * np.pi * 13.0 * i / 1000 + 1.0),
            0.09 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000 + 1.5),
            0.13 + 0.02 * np.sin(2 * np.pi * 12.5 * i / 1000 + 2.0),
        ]
        frame_data = {
            'ts': ts.isoformat() + 'Z',
            'fs': 1000.0,
            'sensors': 5,
            'mode': 'magnitude',
            'frame': frame
        }
        engine2.ingest_frame(frame_data)
    
    print(f"✓ Damaged state simulated")
    
    # Compute comparative metrics
    print("\n▶ Computing comparative metrics...")
    metrics = engine2.compute_metrics()
    
    print(f"\n✓ Comparative analysis results:")
    if metrics.get('comparative'):
        comp = metrics['comparative']
        print(f"  Quality score: {comp.get('quality', 0)*100:.1f}%")
        print(f"  Frequency shifts: {[f'{df:.2f}%' for df in comp.get('delta_f', [])]}")
        print(f"  Energy anomalies:")
        for sensor_id, score in comp.get('heatmap', {}).items():
            print(f"    - {sensor_id}: {score*100:.1f}%")
    else:
        print(f"  ✗ No comparative data (baseline may not be set)")
    
    # List baselines
    baselines = baseline_mgr.list_baselines()
    print(f"\n✓ Available baselines ({len(baselines)}):")
    for b in baselines:
        print(f"  - {b['name']}: {b['num_peaks']} peaks (created {b['created_at']})")
    
    return True


def test_buffer_operations():
    """Test buffer operations and data integrity."""
    print("\n" + "="*80)
    print("TEST: Buffer Operations & Data Integrity")
    print("="*80)
    
    from live_buffer import LiveSensorBuffer
    
    # Create buffer
    buf = LiveSensorBuffer(fs=1000.0, duration_sec=10)
    print(f"\n✓ Buffer created (10s @ 1000 Hz)")
    
    # Add samples
    samples = np.sin(2 * np.pi * 10 * np.arange(5000) / 1000)
    buf.add_samples(list(samples))
    print(f"✓ Added {len(samples)} samples")
    
    # Get data
    data, ts = buf.get_data()
    print(f"✓ Retrieved {len(data)} samples")
    
    # Get recent
    recent, recent_ts = buf.get_recent(2.0)
    print(f"✓ Retrieved recent 2s: {len(recent)} samples")
    
    assert len(recent) == 2000, f"Expected 2000 samples, got {len(recent)}"
    assert abs(np.mean(recent)) < 0.5, "Mean should be close to 0"
    
    print(f"✓ All buffer tests passed")
    return True


def test_psd_analyzer():
    """Test PSD computation."""
    print("\n" + "="*80)
    print("TEST: PSD Analysis")
    print("="*80)
    
    from live_buffer import RollingPSDAnalyzer
    
    analyzer = RollingPSDAnalyzer(fs=1000.0, window_sec=8)
    
    # Generate signal with known frequencies
    t = np.arange(8000) / 1000.0
    signal = (
        1.0 * np.sin(2 * np.pi * 12.5 * t) +
        0.7 * np.sin(2 * np.pi * 24.3 * t) +
        0.5 * np.sin(2 * np.pi * 48.1 * t) +
        0.1 * np.random.randn(8000)
    )
    
    freqs, psd = analyzer.compute_psd(signal)
    
    print(f"\n✓ PSD computed")
    print(f"  - Frequency bins: {len(freqs)}")
    print(f"  - Frequency range: {freqs[0]:.1f} - {freqs[-1]:.1f} Hz")
    print(f"  - Peak PSD: {np.max(psd):.3f} g²/Hz")
    
    # Detect peaks
    peaks = analyzer.peak_tracker.detect_peaks(freqs, psd) if hasattr(analyzer, 'peak_tracker') else []
    print(f"✓ Peaks detected: {len(peaks)}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("REAL-TIME STREAMING INTEGRATION TESTS")
    print("="*80)
    
    tests = [
        ("Buffer Operations", test_buffer_operations),
        ("PSD Analysis", test_psd_analyzer),
        ("Mode B: Basic Streaming", test_mode_b_basic),
        ("Mode A: Comparative", test_mode_a_comparative),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {name}: PASSED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name}: FAILED")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("="*80 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

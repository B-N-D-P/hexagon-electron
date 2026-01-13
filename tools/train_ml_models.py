#!/usr/bin/env python3
"""
Train ML anomaly detection models on baseline data.

Supports:
- Training on CSV baseline files
- Hybrid Isolation Forest + Autoencoder
- Model versioning and persistence
- Automatic model loading into live system

Usage:
    python3 train_ml_models.py --baseline-dir data/baseline
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "ml_models"))

from feature_extractor import BatchFeatureExtractor
from anomaly_detector import HybridAnomalyDetector
from model_manager import ModelTrainer


def load_csv_data(baseline_dir: Path, num_sensors: int = 5) -> np.ndarray:
    """
    Load and combine all CSV files from baseline directory.
    
    Args:
        baseline_dir: Directory with CSV files
        num_sensors: Number of sensors
        
    Returns:
        Combined sensor data array
    """
    print(f"\n📂 Loading CSV files from {baseline_dir}...")
    
    csv_files = sorted(baseline_dir.glob("data_*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {baseline_dir}")
    
    print(f"   Found {len(csv_files)} CSV files")
    
    all_data = []
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            # Extract sensor columns (S1_x, S1_y, S1_z, S2_x, ...)
            sensor_cols = [col for col in df.columns 
                          if col.startswith('S') and col[1].isdigit()]
            
            if len(sensor_cols) == 0:
                print(f"   ⚠ No sensor columns in {csv_file.name}, skipping")
                continue
            
            data = df[sensor_cols].values
            all_data.append(data)
            print(f"   ✓ Loaded {csv_file.name}: {data.shape[0]} samples")
        
        except Exception as e:
            print(f"   ✗ Error loading {csv_file.name}: {e}")
            continue
    
    if not all_data:
        raise ValueError("Could not load any CSV files")
    
    # Combine all data
    combined = np.vstack(all_data)
    print(f"\n✓ Total data loaded: {combined.shape[0]} samples, {combined.shape[1]} columns")
    
    return combined


def extract_features(data: np.ndarray, fs: float = 1000.0, 
                    num_sensors: int = 5) -> np.ndarray:
    """Extract features from raw sensor data."""
    print(f"\n🔧 Extracting features from {data.shape[0]} samples...")
    
    extractor = BatchFeatureExtractor(
        fs=fs,
        num_sensors=num_sensors,
        window_size_sec=8.0  # 8-second windows
    )
    
    features = extractor.extract_batch_features(data)
    
    print(f"✓ Features extracted: {features.shape[0]} windows, {features.shape[1]} features")
    
    # Show feature statistics
    print(f"\n📊 Feature statistics:")
    print(f"   Min: {np.min(features):.6f}")
    print(f"   Max: {np.max(features):.6f}")
    print(f"   Mean: {np.mean(features):.6f}")
    print(f"   Std: {np.std(features):.6f}")
    
    return features


def train_models(features: np.ndarray, baseline_name: str = "structure",
                contamination: float = 0.1) -> str:
    """
    Train hybrid anomaly detection models.
    
    Args:
        features: Extracted features
        baseline_name: Name for this baseline
        contamination: Expected anomaly rate
        
    Returns:
        Model version string
    """
    print(f"\n{'='*80}")
    print(f"🤖 TRAINING HYBRID ANOMALY DETECTION MODEL")
    print(f"{'='*80}")
    
    print(f"\n📋 Configuration:")
    print(f"   Training samples: {features.shape[0]}")
    print(f"   Features per sample: {features.shape[1]}")
    print(f"   Contamination rate: {contamination*100:.1f}%")
    print(f"   Baseline name: {baseline_name}")
    
    # Initialize trainer
    models_dir = Path(__file__).parent.parent / "backend" / "ml_models" / "trained"
    trainer = ModelTrainer(models_dir)
    
    # Train model
    version = trainer.manager.train_model(
        features,
        baseline_name=baseline_name,
        contamination=contamination
    )
    
    if not version:
        raise RuntimeError("Model training failed")
    
    return version


def verify_model(version: str) -> None:
    """Verify trained model by testing on sample data."""
    print(f"\n✅ VERIFYING MODEL")
    print(f"{'='*80}")
    
    models_dir = Path(__file__).parent.parent / "backend" / "ml_models" / "trained"
    trainer = ModelTrainer(models_dir)
    
    # Load model
    if not trainer.manager.load_model(version):
        raise RuntimeError(f"Could not load model {version}")
    
    print(f"\n✓ Model loaded: {version}")
    
    # Test on random features
    num_features = trainer.manager.model_info.num_features
    
    # Generate test samples
    print(f"\nGenerating test samples...")
    
    # Normal samples (from a Gaussian)
    normal_features = np.random.normal(0, 1, (10, num_features)).astype(np.float32)
    
    # Anomalous samples (outliers)
    anomaly_features = np.random.uniform(-5, 5, (10, num_features)).astype(np.float32)
    
    print(f"\nTesting on normal samples:")
    for i in range(3):
        result = trainer.manager.predict(normal_features[i])
        print(f"  Sample {i+1}: anomaly_score={result['anomaly_score']:.3f}, "
              f"is_anomaly={result['is_anomaly']}")
    
    print(f"\nTesting on anomalous samples:")
    for i in range(3):
        result = trainer.manager.predict(anomaly_features[i])
        print(f"  Sample {i+1}: anomaly_score={result['anomaly_score']:.3f}, "
              f"is_anomaly={result['is_anomaly']}")
    
    print(f"\n✓ Model verification complete!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Train ML anomaly detection models on baseline data'
    )
    
    # Input
    parser.add_argument(
        '--baseline-dir',
        type=str,
        required=True,
        help='Directory with baseline CSV files'
    )
    
    # Options
    parser.add_argument(
        '--contamination',
        type=float,
        default=0.1,
        help='Expected anomaly rate for training (default: 0.1 = 10%)'
    )
    
    parser.add_argument(
        '--structure-name',
        type=str,
        default='Iron Structure',
        help='Name of structure being monitored'
    )
    
    parser.add_argument(
        '--fs',
        type=float,
        default=1000.0,
        help='Sampling frequency (Hz)'
    )
    
    parser.add_argument(
        '--num-sensors',
        type=int,
        default=5,
        help='Number of sensors'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify trained model'
    )
    
    args = parser.parse_args()
    
    try:
        print("\n" + "="*80)
        print("🤖 ML MODEL TRAINING PIPELINE")
        print("="*80)
        
        # Step 1: Load data
        baseline_dir = Path(args.baseline_dir)
        if not baseline_dir.exists():
            raise ValueError(f"Baseline directory not found: {baseline_dir}")
        
        data = load_csv_data(baseline_dir, args.num_sensors)
        
        # Step 2: Extract features
        features = extract_features(data, args.fs, args.num_sensors)
        
        # Step 3: Train models
        version = train_models(
            features,
            baseline_name=args.structure_name,
            contamination=args.contamination
        )
        
        # Step 4: Verify
        if args.verify:
            verify_model(version)
        
        # Success
        print(f"\n{'='*80}")
        print(f"✅ MODEL TRAINING COMPLETE!")
        print(f"{'='*80}")
        print(f"\n📦 Trained model:")
        print(f"   Version: {version}")
        print(f"   Location: backend/ml_models/trained/{version}")
        print(f"\n🚀 The model is now ready for deployment!")
        print(f"   - It will be automatically loaded when LiveMonitoring starts")
        print(f"   - Real-time anomaly scores will appear in the dashboard")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

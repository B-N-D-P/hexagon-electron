"""
Model lifecycle management: training, versioning, loading, caching.

Handles:
- Model persistence (save/load from disk)
- Version management
- Metadata tracking
- Live model switching
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import numpy as np
from dataclasses import dataclass, asdict
import shutil

from .feature_extractor import FeatureExtractor, BatchFeatureExtractor
from .anomaly_detector import HybridAnomalyDetector


@dataclass
class ModelInfo:
    """Metadata for a trained model."""
    version: str
    name: str
    created_at: str
    baseline_name: str
    num_training_samples: int
    num_features: int
    if_trained: bool
    ae_trained: bool
    contamination: float
    description: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ModelManager:
    """Manage anomaly detection models."""
    
    def __init__(self, models_dir: Path = None):
        """
        Initialize model manager.
        
        Args:
            models_dir: Directory to store models (default: backend/ml_models/trained/)
        """
        if models_dir is None:
            models_dir = Path(__file__).parent / "trained"
        
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_model: Optional[HybridAnomalyDetector] = None
        self.current_version: Optional[str] = None
        self.feature_extractor: Optional[FeatureExtractor] = None
        self.model_info: Optional[ModelInfo] = None
        
        # Load latest model if available
        self._load_latest_model()
    
    def _load_latest_model(self) -> bool:
        """Load the most recent model."""
        try:
            versions = self._list_versions()
            if not versions:
                return False
            
            latest_version = versions[-1]
            self.load_model(latest_version)
            return True
        except Exception as e:
            print(f"Could not load latest model: {e}")
            return False
    
    def _list_versions(self) -> List[str]:
        """List all available model versions."""
        versions = []
        for version_dir in sorted(self.models_dir.glob("v*")):
            if version_dir.is_dir():
                versions.append(version_dir.name)
        return versions
    
    def train_model(self, features: np.ndarray, baseline_name: str = "baseline",
                   contamination: float = 0.1) -> str:
        """
        Train a new model on features.
        
        Args:
            features: Training data (num_samples, num_features)
            baseline_name: Name for this baseline
            contamination: Anomaly contamination rate
            
        Returns:
            Version string for new model
        """
        print(f"\n{'='*80}")
        print(f"🔧 Training new anomaly detection model")
        print(f"{'='*80}")
        
        # Generate version
        version = datetime.now().strftime("v%Y%m%d_%H%M%S")
        version_dir = self.models_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize feature extractor
        num_features = features.shape[1]
        self.feature_extractor = FeatureExtractor()
        
        # Create and train detector
        detector = HybridAnomalyDetector(num_features, contamination)
        detector.train(features, name=baseline_name)
        
        # Save models
        detector.save(version_dir)
        
        # Create model info
        info = ModelInfo(
            version=version,
            name=f"Model_{version}",
            created_at=datetime.now().isoformat(),
            baseline_name=baseline_name,
            num_training_samples=features.shape[0],
            num_features=num_features,
            if_trained=True,
            ae_trained=True,
            contamination=contamination
        )
        
        # Save metadata
        info_file = version_dir / "info.json"
        with open(info_file, 'w') as f:
            json.dump(info.to_dict(), f, indent=2)
        
        # Set as current
        self.current_model = detector
        self.current_version = version
        self.model_info = info
        
        print(f"\n✓ Model trained successfully!")
        print(f"  Version: {version}")
        print(f"  Samples: {features.shape[0]}")
        print(f"  Features: {num_features}")
        print(f"  Location: {version_dir}")
        print(f"{'='*80}\n")
        
        return version
    
    def load_model(self, version: str) -> bool:
        """
        Load a model by version.
        
        Args:
            version: Version string (e.g., "v20260112_090000")
            
        Returns:
            True if successful
        """
        try:
            version_dir = self.models_dir / version
            if not version_dir.exists():
                print(f"✗ Model version not found: {version}")
                return False
            
            # Load detector
            detector = HybridAnomalyDetector(input_dim=None)
            detector.load(version_dir)
            
            # Load metadata
            info_file = version_dir / "info.json"
            if info_file.exists():
                with open(info_file, 'r') as f:
                    info_dict = json.load(f)
                    self.model_info = ModelInfo(**info_dict)
            
            self.current_model = detector
            self.current_version = version
            
            print(f"✓ Loaded model: {version}")
            return True
        except Exception as e:
            print(f"✗ Error loading model {version}: {e}")
            return False
    
    def predict(self, features: np.ndarray) -> Dict:
        """
        Predict using current model.
        
        Args:
            features: Feature vector
            
        Returns:
            Prediction result dictionary
        """
        if not self.current_model:
            return {'error': 'No model loaded'}
        
        return self.current_model.predict(features)
    
    def get_model_info(self, version: Optional[str] = None) -> Optional[Dict]:
        """Get information about a model version."""
        if version is None:
            version = self.current_version
        
        if version is None:
            return None
        
        version_dir = self.models_dir / version
        info_file = version_dir / "info.json"
        
        if info_file.exists():
            with open(info_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def list_models(self) -> List[Dict]:
        """List all trained models with metadata."""
        models = []
        for version in self._list_versions():
            info = self.get_model_info(version)
            if info:
                info['is_current'] = (version == self.current_version)
                models.append(info)
        return models
    
    def delete_model(self, version: str) -> bool:
        """Delete a model version."""
        try:
            version_dir = self.models_dir / version
            if version_dir.exists():
                shutil.rmtree(version_dir)
                print(f"✓ Deleted model: {version}")
                
                # If we deleted current model, load latest
                if version == self.current_version:
                    self._load_latest_model()
                
                return True
        except Exception as e:
            print(f"✗ Error deleting model: {e}")
        
        return False
    
    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self.current_model is not None
    
    def get_current_version(self) -> Optional[str]:
        """Get current model version."""
        return self.current_version


class ModelTrainer:
    """High-level training interface."""
    
    def __init__(self, models_dir: Path = None):
        """Initialize trainer."""
        self.manager = ModelManager(models_dir)
        self.batch_extractor: Optional[BatchFeatureExtractor] = None
    
    def train_from_csv(self, csv_file: Path, baseline_name: str = "structure",
                      contamination: float = 0.1) -> Optional[str]:
        """
        Train model from CSV file.
        
        Args:
            csv_file: Path to CSV with sensor data
            baseline_name: Name for baseline
            contamination: Anomaly rate
            
        Returns:
            Model version or None
        """
        try:
            import pandas as pd
            
            print(f"Loading data from {csv_file}...")
            df = pd.read_csv(csv_file)
            
            # Extract sensor columns (format: S1_x, S1_y, S1_z, S2_x, ...)
            sensor_cols = [col for col in df.columns 
                          if col.startswith('S') and col[1].isdigit()]
            
            data = df[sensor_cols].values
            print(f"Loaded {data.shape[0]} samples, {data.shape[1]} features")
            
            # Initialize batch extractor
            self.batch_extractor = BatchFeatureExtractor(
                fs=1000.0,
                num_sensors=5,
                window_size_sec=8.0
            )
            
            # Extract features
            print("Extracting features...")
            features = self.batch_extractor.extract_batch_features(data)
            print(f"Extracted {features.shape[0]} feature vectors, {features.shape[1]} features each")
            
            # Train model
            version = self.manager.train_model(
                features,
                baseline_name=baseline_name,
                contamination=contamination
            )
            
            return version
        
        except Exception as e:
            print(f"✗ Error training from CSV: {e}")
            return None
    
    def train_from_arrays(self, data_arrays: List[np.ndarray],
                         baseline_name: str = "structure",
                         contamination: float = 0.1) -> Optional[str]:
        """
        Train model from sensor data arrays.
        
        Args:
            data_arrays: List of sensor data arrays
            baseline_name: Name for baseline
            contamination: Anomaly rate
            
        Returns:
            Model version or None
        """
        try:
            # Combine arrays
            combined = np.hstack(data_arrays)
            print(f"Combined data shape: {combined.shape}")
            
            # Initialize batch extractor
            self.batch_extractor = BatchFeatureExtractor(
                fs=1000.0,
                num_sensors=len(data_arrays),
                window_size_sec=8.0
            )
            
            # Extract features
            print("Extracting features...")
            features = self.batch_extractor.extract_batch_features(combined)
            print(f"Extracted {features.shape[0]} feature vectors")
            
            # Train model
            version = self.manager.train_model(
                features,
                baseline_name=baseline_name,
                contamination=contamination
            )
            
            return version
        
        except Exception as e:
            print(f"✗ Error training from arrays: {e}")
            return None

"""
Hybrid anomaly detection using Isolation Forest + Autoencoder.

Two complementary approaches:
1. Isolation Forest: Fast, statistical outlier detection
2. Autoencoder: Deep learning, learns feature distributions
3. Ensemble: Combines both for robustness
"""

import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime
import json

# Try to import joblib for model persistence
try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    print("⚠ joblib not available - model persistence will be limited")

# Sklearn for Isolation Forest
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# TensorFlow for Autoencoder (with fallback to sklearn if not available)
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠ TensorFlow not available, Autoencoder will be disabled")


class IsolationForestAnomalyDetector:
    """Fast statistical anomaly detection using Isolation Forest."""
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize Isolation Forest.
        
        Args:
            contamination: Expected proportion of anomalies (0.0-1.0)
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train(self, features: np.ndarray) -> None:
        """
        Train Isolation Forest on baseline data.
        
        Args:
            features: Training features (num_samples, num_features)
        """
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.model.fit(features_scaled)
        self.is_trained = True
    
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """
        Predict anomaly score for new features.
        
        Args:
            features: Feature vector (num_features,) or batch (num_samples, num_features)
            
        Returns:
            (anomaly_score, confidence) where:
            - anomaly_score: [0, 1] (1 = strong anomaly)
            - confidence: [0, 1] (model confidence)
        """
        if not self.is_trained:
            return 0.5, 0.0
        
        # Handle single sample
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Normalize
        features_scaled = self.scaler.transform(features)
        
        # Get anomaly scores (-1 for anomalies, 1 for normal)
        predictions = self.model.predict(features_scaled)
        scores = self.model.score_samples(features_scaled)
        
        # Convert to [0, 1] scale
        # Isolation Forest scores are typically in [-0.5, 0.5]
        anomaly_scores = 1.0 / (1.0 + np.exp(-scores))  # Sigmoid
        
        avg_score = np.mean(anomaly_scores)
        confidence = 0.8  # Isolation Forest confidence
        
        return float(avg_score), float(confidence)
    
    def save(self, filepath: Path) -> None:
        """Save model to disk."""
        if not JOBLIB_AVAILABLE:
            print("⚠ joblib not available - model not saved")
            return
        
        data = {
            'model': self.model,
            'scaler': self.scaler,
            'contamination': self.contamination,
            'is_trained': self.is_trained
        }
        joblib.dump(data, filepath)
    
    def load(self, filepath: Path) -> None:
        """Load model from disk."""
        if not JOBLIB_AVAILABLE:
            print("⚠ joblib not available - model not loaded")
            return
        
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.contamination = data['contamination']
        self.is_trained = data['is_trained']


class AutoencoderAnomalyDetector:
    """Deep learning anomaly detection using Autoencoder."""
    
    def __init__(self, input_dim: int, hidden_dim: int = 32):
        """
        Initialize Autoencoder.
        
        Args:
            input_dim: Number of input features
            hidden_dim: Size of bottleneck layer
        """
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.scaler = StandardScaler()
        self.model = None
        self.is_trained = False
        
        if TENSORFLOW_AVAILABLE:
            self._build_model()
    
    def _build_model(self) -> None:
        """Build autoencoder architecture."""
        if not TENSORFLOW_AVAILABLE:
            return
        
        # Encoder
        encoder_input = keras.Input(shape=(self.input_dim,))
        encoded = layers.Dense(128, activation='relu')(encoder_input)
        encoded = layers.Dropout(0.2)(encoded)
        encoded = layers.Dense(64, activation='relu')(encoded)
        encoded = layers.Dropout(0.2)(encoded)
        encoded = layers.Dense(self.hidden_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = layers.Dense(64, activation='relu')(encoded)
        decoded = layers.Dropout(0.2)(decoded)
        decoded = layers.Dense(128, activation='relu')(decoded)
        decoded = layers.Dropout(0.2)(decoded)
        decoded = layers.Dense(self.input_dim, activation='linear')(decoded)
        
        # Full autoencoder
        self.model = keras.Model(encoder_input, decoded)
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse'
        )
    
    def train(self, features: np.ndarray, epochs: int = 50, 
              validation_split: float = 0.2) -> None:
        """
        Train autoencoder on baseline data.
        
        Args:
            features: Training features
            epochs: Number of training epochs
            validation_split: Fraction for validation
        """
        if not TENSORFLOW_AVAILABLE:
            print("⚠ TensorFlow not available, skipping autoencoder training")
            return
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train with early stopping
        early_stop = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
        
        self.model.fit(
            features_scaled, features_scaled,
            epochs=epochs,
            batch_size=32,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=0
        )
        
        self.is_trained = True
    
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """
        Predict anomaly score for new features.
        
        Args:
            features: Feature vector (num_features,) or batch
            
        Returns:
            (anomaly_score, confidence)
        """
        if not TENSORFLOW_AVAILABLE or not self.is_trained:
            return 0.5, 0.0
        
        # Handle single sample
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Normalize
        features_scaled = self.scaler.transform(features)
        
        # Reconstruct
        reconstructed = self.model.predict(features_scaled, verbose=0)
        
        # Compute reconstruction error
        mse = np.mean((features_scaled - reconstructed) ** 2, axis=1)
        
        # Convert MSE to [0, 1] anomaly score
        # Use exponential mapping: higher MSE → higher anomaly score
        anomaly_scores = 1.0 - np.exp(-mse)
        
        avg_score = np.mean(anomaly_scores)
        confidence = 0.85
        
        return float(avg_score), float(confidence)
    
    def save(self, filepath: Path) -> None:
        """Save model to disk."""
        if not TENSORFLOW_AVAILABLE or not JOBLIB_AVAILABLE:
            print("⚠ TensorFlow or joblib not available - autoencoder not saved")
            return
        
        model_dir = Path(filepath).parent
        model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model.save(str(filepath) + '.h5')
        joblib.dump(self.scaler, str(filepath) + '_scaler.pkl')
    
    def load(self, filepath: Path) -> None:
        """Load model from disk."""
        if not TENSORFLOW_AVAILABLE or not JOBLIB_AVAILABLE:
            print("⚠ TensorFlow or joblib not available - autoencoder not loaded")
            return
        
        try:
            self.model = keras.models.load_model(str(filepath) + '.h5')
            self.scaler = joblib.load(str(filepath) + '_scaler.pkl')
            self.is_trained = True
        except Exception as e:
            print(f"Error loading autoencoder: {e}")


class HybridAnomalyDetector:
    """Ensemble of Isolation Forest + Autoencoder for robust anomaly detection."""
    
    def __init__(self, input_dim: int, contamination: float = 0.1):
        """
        Initialize hybrid detector.
        
        Args:
            input_dim: Number of input features
            contamination: Expected anomaly proportion
        """
        self.input_dim = input_dim
        self.contamination = contamination
        
        # Two detectors
        self.if_detector = IsolationForestAnomalyDetector(contamination)
        self.ae_detector = AutoencoderAnomalyDetector(input_dim) if TENSORFLOW_AVAILABLE else None
        
        self.is_trained = False
        self.metadata = {}
    
    def train(self, features: np.ndarray, name: str = "baseline") -> None:
        """
        Train both detectors on baseline data.
        
        Args:
            features: Training features (num_samples, num_features)
            name: Name for this baseline
        """
        print(f"Training hybrid detector on {features.shape[0]} samples...")
        
        # Train Isolation Forest
        self.if_detector.train(features)
        
        # Train Autoencoder if available
        if self.ae_detector:
            self.ae_detector.train(features)
        
        self.is_trained = True
        self.metadata = {
            'trained_at': datetime.now().isoformat(),
            'name': name,
            'num_samples': features.shape[0],
            'num_features': features.shape[1],
            'contamination': self.contamination,
            'tensorflow_available': TENSORFLOW_AVAILABLE
        }
    
    def predict(self, features: np.ndarray) -> Dict:
        """
        Predict anomaly scores using both detectors.
        
        Args:
            features: Feature vector or batch
            
        Returns:
            Dictionary with scores from both detectors and ensemble
        """
        if not self.is_trained:
            return {
                'anomaly_score': 0.5,
                'confidence': 0.0,
                'is_anomaly': False
            }
        
        # Isolation Forest prediction
        if_score, if_conf = self.if_detector.predict(features)
        
        # Autoencoder prediction (if available)
        if self.ae_detector and TENSORFLOW_AVAILABLE:
            ae_score, ae_conf = self.ae_detector.predict(features)
            has_ae = True
        else:
            ae_score, ae_conf = 0.5, 0.0
            has_ae = False
        
        # Ensemble score (weighted average)
        if has_ae:
            ensemble_score = 0.5 * if_score + 0.5 * ae_score
            ensemble_conf = (if_conf + ae_conf) / 2
        else:
            ensemble_score = if_score
            ensemble_conf = if_conf
        
        # Threshold for anomaly (moderate sensitivity: 0.6)
        anomaly_threshold = 0.6
        is_anomaly = ensemble_score > anomaly_threshold
        
        return {
            'anomaly_score': float(ensemble_score),
            'confidence': float(ensemble_conf),
            'is_anomaly': bool(is_anomaly),
            'if_score': float(if_score),
            'if_confidence': float(if_conf),
            'ae_score': float(ae_score) if has_ae else None,
            'ae_confidence': float(ae_conf) if has_ae else None,
            'threshold': anomaly_threshold,
            'has_autoencoder': has_ae
        }
    
    def save(self, model_dir: Path) -> None:
        """Save both models to directory."""
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Isolation Forest
        self.if_detector.save(model_dir / 'if_model.pkl')
        
        # Save Autoencoder if available
        if self.ae_detector:
            self.ae_detector.save(model_dir / 'ae_model')
        
        # Save metadata
        with open(model_dir / 'metadata.json', 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def load(self, model_dir: Path) -> None:
        """Load both models from directory."""
        model_dir = Path(model_dir)
        
        # Load Isolation Forest
        self.if_detector.load(model_dir / 'if_model.pkl')
        
        # Load Autoencoder if available
        if TENSORFLOW_AVAILABLE and (model_dir / 'ae_model.h5').exists():
            self.ae_detector.load(model_dir / 'ae_model')
        
        # Load metadata
        if (model_dir / 'metadata.json').exists():
            with open(model_dir / 'metadata.json', 'r') as f:
                self.metadata = json.load(f)
        
        self.is_trained = True

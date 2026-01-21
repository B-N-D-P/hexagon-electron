"""
Damage Classification Service
Uses trained ML model to classify structural damage types from sensor data
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DamageClassifier:
    """
    Damage Classification Service using trained Random Forest model
    
    Detects 5 damage categories:
    - healthy: Undamaged structure
    - deformation: Bent/deformed beams
    - bolt_damage: Loose or missing bolts
    - missing_beam: Structural beam missing
    - brace_damage: Bracing removed
    
    Model Performance: 98.28% accuracy on test data
    """
    
    def __init__(self, model_dir: str = "ml_models/damage_classifier"):
        """
        Initialize the damage classifier
        
        Args:
            model_dir: Directory containing the trained model files
        """
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.is_loaded = False
        
        # Load model on initialization
        self.load_model()
    
    def load_model(self) -> bool:
        """
        Load the trained model, scaler, and feature names
        
        Returns:
            True if successful, False otherwise
        """
        try:
            model_path = self.model_dir / 'damage_classifier.pkl'
            scaler_path = self.model_dir / 'feature_scaler.pkl'
            features_path = self.model_dir / 'feature_names.pkl'
            
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return False
            
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.feature_names = joblib.load(features_path)
            
            self.is_loaded = True
            logger.info(f"✅ Damage classifier loaded successfully")
            logger.info(f"   Classes: {self.model.classes_}")
            logger.info(f"   Features: {len(self.feature_names)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load damage classifier: {e}")
            self.is_loaded = False
            return False
    
    def extract_features_from_dataframe(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Extract statistical and frequency features from sensor data DataFrame
        
        Args:
            df: DataFrame with columns [S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g]
        
        Returns:
            Dictionary of extracted features
        """
        # Ensure numeric data
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        
        features = {}
        
        # Extract features for each sensor axis
        for col in df.columns:
            data = df[col].values
            
            # Time domain features
            features[f'{col}_mean'] = np.mean(data)
            features[f'{col}_std'] = np.std(data)
            features[f'{col}_min'] = np.min(data)
            features[f'{col}_max'] = np.max(data)
            features[f'{col}_range'] = np.max(data) - np.min(data)
            features[f'{col}_rms'] = np.sqrt(np.mean(data**2))
            features[f'{col}_skew'] = pd.Series(data).skew()
            features[f'{col}_kurtosis'] = pd.Series(data).kurtosis()
            
            # Frequency domain features (FFT)
            fft = np.fft.fft(data)
            fft_mag = np.abs(fft)[:len(data)//2]
            features[f'{col}_fft_mean'] = np.mean(fft_mag)
            features[f'{col}_fft_max'] = np.max(fft_mag)
            features[f'{col}_fft_std'] = np.std(fft_mag)
        
        # Cross-sensor features
        if all(col in df.columns for col in ['S1_X_g', 'S1_Y_g', 'S1_Z_g', 'S2_X_g', 'S2_Y_g', 'S2_Z_g']):
            features['S1_magnitude'] = np.mean(np.sqrt(
                df['S1_X_g']**2 + df['S1_Y_g']**2 + df['S1_Z_g']**2
            ))
            features['S2_magnitude'] = np.mean(np.sqrt(
                df['S2_X_g']**2 + df['S2_Y_g']**2 + df['S2_Z_g']**2
            ))
            features['sensors_correlation'] = df['S1_Z_g'].corr(df['S2_Z_g'])
        
        return features
    
    def extract_features_from_csv(self, csv_path: str) -> Dict[str, float]:
        """
        Extract features from a CSV file
        
        Args:
            csv_path: Path to CSV file with sensor data
        
        Returns:
            Dictionary of extracted features
        """
        df = pd.read_csv(csv_path)
        
        # Skip header row if duplicated
        if df.iloc[0].astype(str).str.contains('S1_X_g').any():
            df = df.iloc[1:].reset_index(drop=True)
        
        return self.extract_features_from_dataframe(df)
    
    def extract_features_from_array(self, data: np.ndarray, 
                                   column_names: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Extract features from a numpy array
        
        Args:
            data: Sensor data array (n_samples, n_channels)
            column_names: Optional column names. If None, assumes standard order:
                         [S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g]
        
        Returns:
            Dictionary of extracted features
        """
        if column_names is None:
            column_names = ['S1_X_g', 'S1_Y_g', 'S1_Z_g', 'S2_X_g', 'S2_Y_g', 'S2_Z_g']
        
        df = pd.DataFrame(data, columns=column_names)
        return self.extract_features_from_dataframe(df)
    
    def predict(self, features: Dict[str, float]) -> Dict[str, any]:
        """
        Predict damage type from extracted features
        
        Args:
            features: Dictionary of extracted features
        
        Returns:
            Dictionary containing:
                - prediction: Predicted damage type
                - confidence: Confidence percentage (0-100)
                - probabilities: Dict of all class probabilities
                - top_3_predictions: List of top 3 predictions with probabilities
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Convert to DataFrame with correct column order
        features_df = pd.DataFrame([features])[self.feature_names]
        
        # Scale features
        features_scaled = self.scaler.transform(features_df)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Get class names
        classes = self.model.classes_
        
        # Create probability dictionary
        prob_dict = {cls: float(prob * 100) for cls, prob in zip(classes, probabilities)}
        
        # Get top 3 predictions
        sorted_probs = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
        top_3 = [
            {"damage_type": cls, "probability": prob}
            for cls, prob in sorted_probs[:3]
        ]
        
        return {
            'prediction': prediction,
            'confidence': float(max(probabilities) * 100),
            'probabilities': prob_dict,
            'top_3_predictions': top_3,
            'model_info': {
                'accuracy': 98.28,
                'algorithm': 'Random Forest',
                'features_used': len(self.feature_names)
            }
        }
    
    def predict_from_csv(self, csv_path: str) -> Dict[str, any]:
        """
        Predict damage type directly from CSV file
        
        Args:
            csv_path: Path to CSV file with sensor data
        
        Returns:
            Prediction results dictionary
        """
        features = self.extract_features_from_csv(csv_path)
        return self.predict(features)
    
    def predict_from_array(self, data: np.ndarray,
                          column_names: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Predict damage type directly from numpy array
        
        Args:
            data: Sensor data array (n_samples, n_channels)
            column_names: Optional column names
        
        Returns:
            Prediction results dictionary
        """
        features = self.extract_features_from_array(data, column_names)
        return self.predict(features)
    
    def get_damage_description(self, damage_type: str) -> Dict[str, str]:
        """
        Get human-readable description for damage type
        
        Args:
            damage_type: The damage classification
        
        Returns:
            Dictionary with description and recommendations
        """
        descriptions = {
            'healthy': {
                'title': 'Healthy Structure',
                'description': 'No structural damage detected. The structure is in good condition.',
                'severity': 'None',
                'color': 'green',
                'icon': '✅',
                'recommendation': 'Continue regular maintenance and monitoring.'
            },
            'deformation': {
                'title': 'Structural Deformation',
                'description': 'Bent or deformed structural beams detected. This indicates permanent deformation.',
                'severity': 'High',
                'color': 'red',
                'icon': '⚠️',
                'recommendation': 'Immediate inspection required. Consider beam replacement or reinforcement.'
            },
            'bolt_damage': {
                'title': 'Bolt Connection Damage',
                'description': 'Loose or missing bolts detected in structural connections.',
                'severity': 'Medium',
                'color': 'orange',
                'icon': '🔩',
                'recommendation': 'Tighten or replace loose/missing bolts. Inspect all connections.'
            },
            'missing_beam': {
                'title': 'Missing Structural Member',
                'description': 'One or more structural beams are missing or completely damaged.',
                'severity': 'Critical',
                'color': 'darkred',
                'icon': '❌',
                'recommendation': 'Critical repair needed. Replace missing structural members immediately.'
            },
            'brace_damage': {
                'title': 'Bracing System Damage',
                'description': 'Lateral bracing system is damaged or removed, reducing structural stability.',
                'severity': 'High',
                'color': 'red',
                'icon': '⚡',
                'recommendation': 'Restore or replace bracing system to maintain lateral stability.'
            }
        }
        
        return descriptions.get(damage_type, {
            'title': 'Unknown Damage Type',
            'description': f'Damage type "{damage_type}" not recognized.',
            'severity': 'Unknown',
            'color': 'gray',
            'icon': '❓',
            'recommendation': 'Further investigation required.'
        })


# Create global instance
_damage_classifier_instance = None

def get_damage_classifier() -> DamageClassifier:
    """Get or create the global damage classifier instance"""
    global _damage_classifier_instance
    if _damage_classifier_instance is None:
        _damage_classifier_instance = DamageClassifier()
    return _damage_classifier_instance

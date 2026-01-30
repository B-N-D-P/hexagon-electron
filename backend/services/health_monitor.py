"""
Structural Health Monitoring Service
Uses trained PyTorch CNN model to classify structural damage from accelerometer data
100% accuracy on 4 damage types
"""

import torch
import torch.nn as nn
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class TimeSeriesCNN(nn.Module):
    """1D CNN for time-series classification"""
    def __init__(self, input_channels, num_classes, seq_length):
        super(TimeSeriesCNN, self).__init__()
        
        self.conv1 = nn.Conv1d(input_channels, 64, kernel_size=7, padding=3)
        self.bn1 = nn.BatchNorm1d(64)
        self.pool1 = nn.MaxPool1d(2)
        
        self.conv2 = nn.Conv1d(64, 128, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(128)
        self.pool2 = nn.MaxPool1d(2)
        
        self.conv3 = nn.Conv1d(128, 256, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm1d(256)
        self.pool3 = nn.MaxPool1d(2)
        
        self.conv4 = nn.Conv1d(256, 512, kernel_size=3, padding=1)
        self.bn4 = nn.BatchNorm1d(512)
        
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        self.fc1 = nn.Linear(512, 256)
        self.dropout1 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, 128)
        self.dropout2 = nn.Dropout(0.4)
        self.fc3 = nn.Linear(128, num_classes)
        
        self.relu = nn.ReLU()
    
    def forward(self, x):
        x = x.permute(0, 2, 1)
        
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        
        x = self.relu(self.bn4(self.conv4(x)))
        x = self.global_pool(x)
        
        x = x.view(x.size(0), -1)
        
        x = self.relu(self.fc1(x))
        x = self.dropout1(x)
        x = self.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.fc3(x)
        
        return x


class HealthMonitor:
    """
    Structural Health Monitoring Service using PyTorch CNN
    
    Detects 4 structural conditions:
    - Baseline (Healthy): Normal structure
    - First Floor Damaged: Damage on first floor
    - Second Floor Damaged: Damage on second floor  
    - Top Floor Bolt Loosened: Bolt loosening on top floor
    
    Model: 1D CNN with 702,788 parameters
    Performance: 100% test accuracy
    """
    
    def __init__(self, model_dir: Optional[Path] = None):
        """Initialize the health monitor"""
        self.model = None
        self.scaler = None
        self.model_info = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.is_loaded = False
        
        if model_dir is None:
            # Default to backend/ml_models/health_monitoring
            backend_dir = Path(__file__).resolve().parent.parent
            model_dir = backend_dir / "ml_models" / "health_monitoring"
        
        self.model_dir = Path(model_dir)
        self._load_model()
    
    def _load_model(self):
        """Load the trained model and artifacts"""
        try:
            model_path = self.model_dir / "best_model_improved.pth"
            scaler_path = self.model_dir / "scaler_improved.pkl"
            info_path = self.model_dir / "model_info_improved.json"
            
            if not all([model_path.exists(), scaler_path.exists(), info_path.exists()]):
                logger.error(f"Model files not found in {self.model_dir}")
                return
            
            # Load model info
            with open(info_path, 'r') as f:
                self.model_info = json.load(f)
            
            # Load scaler
            self.scaler = joblib.load(scaler_path)
            
            # Initialize and load model
            self.model = TimeSeriesCNN(
                input_channels=self.model_info['n_features'],
                num_classes=self.model_info['num_classes'],
                seq_length=self.model_info['window_size']
            )
            
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            logger.info(f"✓ Health monitoring model loaded (Device: {self.device})")
            logger.info(f"  Classes: {', '.join(self.model_info['class_names'])}")
            logger.info(f"  Accuracy: {self.model_info['test_accuracy']*100:.1f}%")
            
        except Exception as e:
            logger.error(f"Failed to load health monitoring model: {e}")
            self.is_loaded = False
    
    def _create_windows(self, data: np.ndarray, window_size: int, stride: int) -> Optional[np.ndarray]:
        """Create overlapping windows from time-series data"""
        windows = []
        n_samples = data.shape[0]
        
        for start in range(0, n_samples - window_size + 1, stride):
            end = start + window_size
            window = data[start:end, :]
            windows.append(window)
        
        return np.array(windows) if windows else None
    
    def predict(self, csv_data: pd.DataFrame) -> Dict:
        """
        Predict structural health from sensor data
        
        Args:
            csv_data: DataFrame with columns [S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g]
        
        Returns:
            dict with prediction, confidence, probabilities, etc.
        """
        if not self.is_loaded:
            raise RuntimeError("Health monitoring model not loaded")
        
        try:
            # Extract features
            feature_cols = ['S1_X_g', 'S1_Y_g', 'S1_Z_g', 'S2_X_g', 'S2_Y_g', 'S2_Z_g']
            data = csv_data[feature_cols].values
            
            n_timesteps = data.shape[0]
            window_size = self.model_info['window_size']
            stride = self.model_info['stride']
            
            # Check if enough data
            if n_timesteps < window_size:
                return {
                    'success': False,
                    'error': f'Insufficient data. Need at least {window_size} timesteps, got {n_timesteps}'
                }
            
            # Create windows
            windows = self._create_windows(data, window_size, stride)
            
            if windows is None or len(windows) == 0:
                return {
                    'success': False,
                    'error': 'Failed to create windows from data'
                }
            
            # Normalize
            n_windows = windows.shape[0]
            n_timesteps = windows.shape[1]
            n_features = windows.shape[2]
            
            windows_reshaped = windows.reshape(-1, n_features)
            windows_scaled = self.scaler.transform(windows_reshaped).reshape(windows.shape)
            
            # Predict
            X_tensor = torch.FloatTensor(windows_scaled).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(X_tensor)
                probabilities = torch.softmax(outputs, dim=1).cpu().numpy()
                predictions = torch.argmax(outputs, dim=1).cpu().numpy()
            
            # Analyze results
            class_names = self.model_info['class_names']
            unique, counts = np.unique(predictions, return_counts=True)
            
            # Overall prediction (majority vote)
            majority_idx = unique[np.argmax(counts)]
            majority_pct = (counts[np.argmax(counts)] / len(predictions)) * 100
            overall_conf = np.mean(probabilities[predictions == majority_idx, majority_idx]) * 100
            
            # Get probabilities for all classes
            all_probs = {}
            for i, class_name in enumerate(class_names):
                class_windows = predictions == i
                if class_windows.sum() > 0:
                    avg_prob = np.mean(probabilities[class_windows, i]) * 100
                    all_probs[class_name] = {
                        'probability': float(avg_prob),
                        'windows': int(class_windows.sum()),
                        'percentage': float((class_windows.sum() / len(predictions)) * 100)
                    }
                else:
                    all_probs[class_name] = {
                        'probability': 0.0,
                        'windows': 0,
                        'percentage': 0.0
                    }
            
            # Top 3 predictions
            majority_class_probs = probabilities[predictions == majority_idx, majority_idx]
            top_3_indices = np.argsort(np.mean(probabilities, axis=0))[-3:][::-1]
            top_3 = [
                {
                    'class': class_names[idx],
                    'probability': float(np.mean(probabilities[:, idx]) * 100)
                }
                for idx in top_3_indices
            ]
            
            return {
                'success': True,
                'prediction': class_names[majority_idx],
                'confidence': float(overall_conf),
                'majority_percentage': float(majority_pct),
                'probabilities': all_probs,
                'top_3_predictions': top_3,
                'num_windows': int(n_windows),
                'num_timesteps': int(n_timesteps),
                'is_healthy': bool(majority_idx == 0),
                'model_info': {
                    'accuracy': f"{self.model_info['test_accuracy']*100:.1f}%",
                    'framework': 'PyTorch',
                    'parameters': self.model_info['total_parameters']
                }
            }
            
        except KeyError as e:
            return {
                'success': False,
                'error': f'Missing required column: {e}. Expected: S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g'
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'success': False,
                'error': f'Prediction failed: {str(e)}'
            }
    
    def get_damage_description(self, damage_type: str) -> Dict:
        """Get detailed description of damage type"""
        descriptions = {
            'Baseline (Healthy)': {
                'title': 'Structure is Healthy',
                'description': 'No structural damage detected. All vibration patterns are normal.',
                'severity': 'None',
                'color': 'green',
                'icon': '✅',
                'recommendation': 'Continue regular monitoring and maintenance schedule.'
            },
            'First Floor Damaged': {
                'title': 'First Floor Structural Damage',
                'description': 'Damage detected on the first floor. Abnormal vibration patterns indicate structural compromise at ground level.',
                'severity': 'High',
                'color': 'red',
                'icon': '🏗️',
                'recommendation': 'Immediate inspection required. Restrict access and assess structural integrity.'
            },
            'Second Floor Damaged': {
                'title': 'Second Floor Structural Damage',
                'description': 'Damage detected on the second floor. Vibration analysis shows structural issues at mid-level.',
                'severity': 'High',
                'color': 'red',
                'icon': '🏢',
                'recommendation': 'Urgent structural assessment needed. Evaluate load-bearing capacity.'
            },
            'Top Floor Bolt Loosened': {
                'title': 'Top Floor Bolt Loosening',
                'description': 'Bolts are loose or missing on the top floor. This affects structural connections and stability.',
                'severity': 'Medium',
                'color': 'orange',
                'icon': '🔩',
                'recommendation': 'Inspect and retighten all bolts. Replace damaged or missing fasteners.'
            }
        }
        
        return descriptions.get(damage_type, {
            'title': 'Unknown Condition',
            'description': f'Condition "{damage_type}" not recognized.',
            'severity': 'Unknown',
            'color': 'gray',
            'icon': '❓',
            'recommendation': 'Further investigation required.'
        })


# Global instance
_health_monitor_instance = None

def get_health_monitor() -> HealthMonitor:
    """Get or create the global health monitor instance"""
    global _health_monitor_instance
    if _health_monitor_instance is None:
        _health_monitor_instance = HealthMonitor()
    return _health_monitor_instance

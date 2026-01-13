"""
Feature extraction for anomaly detection.

Extracts both time-domain and frequency-domain features from sensor streams:
- Statistical: RMS, Kurtosis, Skewness, Peak-to-Peak
- Spectral: Power at bands, Spectral centroid, Spectral entropy
- Wavelet: Energy in frequency bands
- Temporal: Peak intervals, Energy decay
"""

import numpy as np
from scipy import signal, stats
from typing import Dict, List, Tuple, Optional

# Try to import pywt for wavelet features, with graceful fallback
try:
    import pywt
    PYWT_AVAILABLE = True
except ImportError:
    PYWT_AVAILABLE = False
    print("⚠ PyWavelets (pywt) not available - wavelet features will be zeros")


class FeatureExtractor:
    """Extract features from sensor data for ML models."""
    
    def __init__(self, fs: float = 1000.0, num_sensors: int = 5):
        """
        Initialize feature extractor.
        
        Args:
            fs: Sampling frequency (Hz)
            num_sensors: Number of sensors
        """
        self.fs = fs
        self.num_sensors = num_sensors
        
        # Feature name definitions
        self.time_domain_features = [
            'rms', 'peak_to_peak', 'kurtosis', 'skewness', 
            'crest_factor', 'shape_factor', 'impulse_factor'
        ]
        
        self.freq_domain_features = [
            'spectral_centroid', 'spectral_entropy', 'spectral_energy',
            'band_0_5hz', 'band_5_50hz', 'band_50_200hz', 'band_200_450hz',
            'peak_freq', 'peak_power'
        ]
        
        self.wavelet_features = [
            'wavelet_energy_d1', 'wavelet_energy_d2', 'wavelet_energy_d3',
            'wavelet_energy_a3'
        ]
        
        self.feature_names = (
            [f"{feat}_s{i+1}" for i in range(num_sensors) 
             for feat in self.time_domain_features] +
            [f"{feat}_s{i+1}" for i in range(num_sensors) 
             for feat in self.freq_domain_features] +
            [f"{feat}_s{i+1}" for i in range(num_sensors) 
             for feat in self.wavelet_features] +
            ['rms_mean', 'rms_std', 'freq_mean', 'freq_std']  # Aggregated features
        )
    
    def extract_features(self, sensor_data: Dict[int, np.ndarray]) -> np.ndarray:
        """
        Extract all features from sensor data.
        
        Args:
            sensor_data: Dictionary {sensor_id: time_series_array}
            
        Returns:
            Feature vector (1D numpy array)
        """
        features = []
        
        # Per-sensor features
        for sensor_id in range(self.num_sensors):
            if sensor_id not in sensor_data:
                # Log warning if sensor data is missing
                print(f"Warning: Sensor {sensor_id} data not available in feature extraction")
                continue
            
            data = sensor_data[sensor_id]
            
            # Time-domain features
            time_feats = self._extract_time_domain(data)
            features.extend(time_feats)
            
            # Frequency-domain features
            freq_feats = self._extract_freq_domain(data)
            features.extend(freq_feats)
            
            # Wavelet features
            wav_feats = self._extract_wavelet(data)
            features.extend(wav_feats)
        
        # Aggregated features (cross-sensor statistics)
        agg_feats = self._extract_aggregated(sensor_data)
        features.extend(agg_feats)
        
        return np.array(features, dtype=np.float32)
    
    def _extract_time_domain(self, data: np.ndarray) -> List[float]:
        """Extract time-domain features."""
        features = []
        
        # RMS
        rms = np.sqrt(np.mean(data ** 2))
        features.append(rms)
        
        # Peak-to-peak
        ptp = np.ptp(data)
        features.append(ptp)
        
        # Kurtosis (measure of impulsive events)
        kurtosis = stats.kurtosis(data)
        features.append(kurtosis)
        
        # Skewness
        skewness = stats.skew(data)
        features.append(skewness)
        
        # Crest factor (peak / RMS)
        crest = np.max(np.abs(data)) / (rms + 1e-10)
        features.append(crest)
        
        # Shape factor (RMS / mean absolute value)
        mav = np.mean(np.abs(data))
        shape = rms / (mav + 1e-10)
        features.append(shape)
        
        # Impulse factor (peak / mean absolute value)
        impulse = np.max(np.abs(data)) / (mav + 1e-10)
        features.append(impulse)
        
        return features
    
    def _extract_freq_domain(self, data: np.ndarray) -> List[float]:
        """Extract frequency-domain features."""
        features = []
        
        try:
            # Compute FFT
            freqs, psd = signal.welch(data, fs=self.fs, nperseg=min(1024, len(data)))
            
            # Spectral centroid (center of mass in frequency)
            total_power = np.sum(psd)
            if total_power > 0:
                centroid = np.sum(freqs * psd) / total_power
            else:
                centroid = 0.0
            features.append(centroid)
            
            # Spectral entropy
            psd_norm = psd / (total_power + 1e-10)
            entropy = -np.sum(psd_norm * np.log(psd_norm + 1e-10))
            features.append(entropy)
            
            # Total spectral energy
            spectral_energy = total_power
            features.append(spectral_energy)
            
            # Energy in frequency bands
            band_0_5 = np.sum(psd[(freqs >= 0) & (freqs < 5)])
            features.append(band_0_5)
            
            band_5_50 = np.sum(psd[(freqs >= 5) & (freqs < 50)])
            features.append(band_5_50)
            
            band_50_200 = np.sum(psd[(freqs >= 50) & (freqs < 200)])
            features.append(band_50_200)
            
            band_200_450 = np.sum(psd[(freqs >= 200) & (freqs < 450)])
            features.append(band_200_450)
            
            # Peak frequency and power
            peak_idx = np.argmax(psd)
            peak_freq = freqs[peak_idx] if len(freqs) > 0 else 0.0
            peak_power = psd[peak_idx] if len(psd) > 0 else 0.0
            features.append(peak_freq)
            features.append(peak_power)
            
        except Exception as e:
            print(f"Error in frequency domain extraction: {e}")
            features.extend([0.0] * 9)  # 9 frequency features
        
        return features
    
    def _extract_wavelet(self, data: np.ndarray) -> List[float]:
        """Extract wavelet-based features."""
        features = []
        
        try:
            if not PYWT_AVAILABLE:
                # Return zeros if pywt is not available
                return [0.0, 0.0, 0.0, 0.0]
            
            # Use Daubechies wavelet (db4) for 3-level decomposition
            wavelet = 'db4'
            level = 3
            
            # Multi-level wavelet decomposition
            coeffs = pywt.wavedec(data, wavelet, level=level)
            
            # coeffs = [cA3, cD3, cD2, cD1]
            # Extract energy from each level
            for i, coeff in enumerate(coeffs):
                energy = np.sum(coeff ** 2)
                features.append(energy)
            
            # Ensure we have exactly 4 features (A3, D3, D2, D1)
            while len(features) < 4:
                features.append(0.0)
            
        except Exception as e:
            print(f"Error in wavelet extraction: {e}")
            features.extend([0.0] * 4)  # 4 wavelet features
        
        return features[:4]  # Take only first 4
    
    def _extract_aggregated(self, sensor_data: Dict[int, np.ndarray]) -> List[float]:
        """Extract aggregated cross-sensor features."""
        features = []
        
        # Collect RMS from all sensors
        rms_values = []
        peak_freqs = []
        
        for sensor_id in range(self.num_sensors):
            if sensor_id not in sensor_data:
                continue
            
            data = sensor_data[sensor_id]
            rms = np.sqrt(np.mean(data ** 2))
            rms_values.append(rms)
            
            # Get peak frequency
            try:
                freqs, psd = signal.welch(data, fs=self.fs, nperseg=min(1024, len(data)))
                peak_idx = np.argmax(psd)
                peak_freqs.append(freqs[peak_idx])
            except:
                peak_freqs.append(0.0)
        
        # RMS statistics
        if rms_values:
            features.append(np.mean(rms_values))  # Mean RMS
            features.append(np.std(rms_values))   # Std RMS
        else:
            features.extend([0.0, 0.0])
        
        # Frequency statistics
        if peak_freqs:
            features.append(np.mean(peak_freqs))  # Mean peak freq
            features.append(np.std(peak_freqs))   # Std peak freq
        else:
            features.extend([0.0, 0.0])
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names."""
        return self.feature_names
    
    def get_num_features(self) -> int:
        """Get total number of features."""
        return len(self.feature_names)


class BatchFeatureExtractor:
    """Extract features from batches of data for training."""
    
    def __init__(self, fs: float = 1000.0, num_sensors: int = 5,
                 window_size_sec: float = 8.0):
        """
        Initialize batch extractor.
        
        Args:
            fs: Sampling frequency
            num_sensors: Number of sensors
            window_size_sec: Duration of each feature window
        """
        self.extractor = FeatureExtractor(fs, num_sensors)
        self.fs = fs
        self.num_sensors = num_sensors
        self.window_size = int(fs * window_size_sec)
    
    def extract_batch_features(self, data: np.ndarray) -> np.ndarray:
        """
        Extract features from batched data.
        
        Args:
            data: Shape (num_samples, num_sensors)
            
        Returns:
            Features array (num_windows, num_features)
        """
        num_samples = data.shape[0]
        num_windows = num_samples // self.window_size
        
        features_list = []
        
        for window_idx in range(num_windows):
            start_idx = window_idx * self.window_size
            end_idx = start_idx + self.window_size
            
            window_data = data[start_idx:end_idx, :]
            
            # Convert to sensor dictionary format
            sensor_dict = {}
            for sensor_id in range(self.num_sensors):
                sensor_dict[sensor_id] = window_data[:, sensor_id]
            
            # Extract features
            features = self.extractor.extract_features(sensor_dict)
            features_list.append(features)
        
        return np.array(features_list, dtype=np.float32)

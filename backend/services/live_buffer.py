"""
Live buffer and real-time analysis for streaming ADXL345 data.

Manages:
- In-memory circular buffers per sensor
- Rolling Welch PSD computation
- Peak tracking and matching
- Damping estimation
- Comparative analysis against baseline
- ML-based anomaly detection
"""

from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.signal import welch, find_peaks, decimate
from scipy.stats import linregress
import threading
import json
from pathlib import Path
import sys


class LiveSensorBuffer:
    """Circular buffer for live sensor data with timestamp tracking."""
    
    def __init__(self, fs: float, duration_sec: float = 120):
        """
        Initialize buffer.
        
        Args:
            fs: Sampling frequency (Hz)
            duration_sec: Buffer duration to keep (seconds)
        """
        self.fs = fs
        self.duration_sec = duration_sec
        self.max_samples = int(fs * duration_sec)
        
        # Buffers: [samples] and [timestamps]
        self.samples = deque(maxlen=self.max_samples)
        self.timestamps = deque(maxlen=self.max_samples)
        
        # Metadata
        self.last_update = None
        self.sample_count = 0
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    def add_sample(self, value: float, timestamp: Optional[datetime] = None) -> None:
        """Add a single sample."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        with self._lock:
            self.samples.append(value)
            self.timestamps.append(timestamp)
            self.last_update = timestamp
            self.sample_count += 1
    
    def add_samples(self, values: List[float], timestamps: Optional[List[datetime]] = None) -> None:
        """Add multiple samples at once."""
        if timestamps is None:
            now = datetime.utcnow()
            timestamps = [now] * len(values)
        
        with self._lock:
            for val, ts in zip(values, timestamps):
                self.samples.append(val)
                self.timestamps.append(ts)
            self.last_update = datetime.utcnow()
            self.sample_count += len(values)
    
    def get_data(self) -> Tuple[np.ndarray, List[datetime]]:
        """Get current buffer data."""
        with self._lock:
            return np.array(list(self.samples)), list(self.timestamps)
    
    def get_recent(self, duration_sec: float) -> Tuple[np.ndarray, List[datetime]]:
        """Get most recent N seconds of data."""
        with self._lock:
            if len(self.samples) == 0:
                return np.array([]), []
            
            samples_to_get = min(int(self.fs * duration_sec), len(self.samples))
            recent_samples = list(self.samples)[-samples_to_get:]
            recent_ts = list(self.timestamps)[-samples_to_get:]
            
            return np.array(recent_samples), recent_ts
    
    def clear(self) -> None:
        """Clear all data."""
        with self._lock:
            self.samples.clear()
            self.timestamps.clear()
            self.sample_count = 0


class RollingPSDAnalyzer:
    """Compute rolling Welch PSD on sliding windows."""
    
    def __init__(self, fs: float, window_sec: float = 8, update_rate_hz: float = 1):
        """
        Initialize PSD analyzer.
        
        Args:
            fs: Sampling frequency (Hz)
            window_sec: Window size for Welch (seconds)
            update_rate_hz: How often to update PSD (Hz)
        """
        self.fs = fs
        self.window_sec = window_sec
        self.window_samples = int(fs * window_sec)
        self.update_interval_samples = int(fs / update_rate_hz)
        
        # Last computed PSD
        self.last_freqs = None
        self.last_psd = None
        self.last_update_sample = 0
    
    def compute_psd(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Welch PSD for given data.
        
        Args:
            data: Input signal
            
        Returns:
            (frequencies, power spectral density)
        """
        if len(data) < self.window_samples:
            # Not enough data; return zeros
            return np.array([]), np.array([])
        
        try:
            freqs, psd = welch(
                data,
                fs=self.fs,
                nperseg=self.window_samples,
                noverlap=self.window_samples // 2,
                scaling='density'
            )
            return freqs, psd
        except Exception as e:
            print(f"PSD computation error: {e}")
            return np.array([]), np.array([])


class PeakTracker:
    """Track and match peaks across overlapping windows."""
    
    def __init__(self, fs: float, min_freq: float = 1.0, max_freq: float = 450.0):
        """
        Initialize peak tracker.
        
        Args:
            fs: Sampling frequency
            min_freq: Minimum frequency to track (Hz)
            max_freq: Maximum frequency to track (Hz)
        """
        self.fs = fs
        self.min_freq = min_freq
        self.max_freq = max_freq
        
        # Track peaks: {freq: count, stability}
        self.peak_history = {}
        self.peak_tolerance = 2.0  # Hz tolerance for matching
        
        # Last detected peaks
        self.last_peaks = []
    
    def detect_peaks(self, freqs: np.ndarray, psd: np.ndarray, 
                    num_peaks: int = 5, prominence_percentile: float = 75) -> List[float]:
        """
        Detect prominent peaks in PSD.
        
        Args:
            freqs: Frequency array
            psd: Power spectral density
            num_peaks: Number of peaks to return
            prominence_percentile: Prominence threshold percentile
            
        Returns:
            List of peak frequencies (Hz)
        """
        if len(freqs) == 0 or len(psd) == 0:
            return []
        
        try:
            # Filter to frequency range
            mask = (freqs >= self.min_freq) & (freqs <= self.max_freq)
            freqs_filt = freqs[mask]
            psd_filt = psd[mask]
            
            if len(psd_filt) < 10:
                return []
            
            # Compute prominence threshold
            prominence_threshold = np.percentile(psd_filt, prominence_percentile)
            
            # Find peaks
            # Ensure distance is at least 1 to avoid scipy validation error
            distance = max(1, int(self.fs / (self.max_freq - self.min_freq) * 0.05))
            peaks, properties = find_peaks(
                psd_filt,
                prominence=prominence_threshold / 10,
                distance=distance
            )
            
            if len(peaks) == 0:
                return []
            
            # Get peak frequencies
            peak_freqs = freqs_filt[peaks]
            peak_powers = psd_filt[peaks]
            
            # Sort by power (descending) and take top N
            sorted_idx = np.argsort(peak_powers)[::-1]
            top_peaks = sorted(peak_freqs[sorted_idx][:num_peaks])
            
            self.last_peaks = list(top_peaks)
            return list(top_peaks)
            
        except Exception as e:
            print(f"Peak detection error: {e}")
            return []
    
    def match_peak(self, freq: float) -> Optional[float]:
        """Match a frequency to existing tracked peak (within tolerance)."""
        for tracked_freq in self.peak_history.keys():
            if abs(freq - tracked_freq) < self.peak_tolerance:
                return tracked_freq
        return None


class DampingEstimator:
    """Estimate damping ratio from signal or spectral characteristics."""
    
    def __init__(self, fs: float):
        self.fs = fs
    
    def estimate_from_impulse(self, data: np.ndarray, peak_freq: float) -> Optional[float]:
        """
        Estimate damping from impulse response decay.
        
        Args:
            data: Time-domain signal
            peak_freq: Expected modal frequency (Hz)
            
        Returns:
            Damping ratio (0-1) or None if estimation fails
        """
        try:
            # Demodulate around peak frequency
            from scipy.signal import hilbert
            
            # Simple band-pass around peak
            N = len(data)
            if N < 100:
                return None
            
            # Compute envelope
            analytic = hilbert(data)
            envelope = np.abs(analytic)
            
            # Log-decrement: fit exponential to envelope
            log_envelope = np.log(envelope + 1e-10)
            
            # Linear regression on log(envelope)
            x = np.arange(N)
            slope, intercept, r_value, p_value, std_err = linregress(x, log_envelope)
            
            # Damping ratio from log decrement
            # ζ ≈ -slope / sqrt(4*π² + slope²)
            if slope < 0:
                damping = -slope / np.sqrt(4 * np.pi**2 + slope**2)
                return max(0, min(0.5, damping))  # Clamp to [0, 0.5]
            
            return None
        except Exception as e:
            print(f"Damping estimation error: {e}")
            return None
    
    def estimate_from_bandwidth(self, freqs: np.ndarray, psd: np.ndarray, 
                               peak_freq: float, peak_idx: int) -> Optional[float]:
        """
        Estimate damping from 3dB bandwidth of a spectral peak.
        
        Args:
            freqs: Frequency array
            psd: Power spectral density
            peak_freq: Peak frequency (Hz)
            peak_idx: Index of peak in frequency array
            
        Returns:
            Damping ratio or None
        """
        try:
            peak_power = psd[peak_idx]
            power_3db = peak_power / (10 ** 0.15)  # -3dB
            
            # Find -3dB bandwidth
            # Search left and right of peak
            left_idx = peak_idx
            while left_idx > 0 and psd[left_idx] > power_3db:
                left_idx -= 1
            
            right_idx = peak_idx
            while right_idx < len(psd) - 1 and psd[right_idx] > power_3db:
                right_idx += 1
            
            if left_idx < peak_idx < right_idx:
                bw = freqs[right_idx] - freqs[left_idx]
                # ζ = bw / (2 * f_peak)
                damping = bw / (2 * peak_freq)
                return max(0, min(0.5, damping))
            
            return None
        except Exception as e:
            print(f"Bandwidth estimation error: {e}")
            return None


class ComparativeEngine:
    """Compare live metrics against baseline."""
    
    def __init__(self, baseline_profile: Optional[Dict] = None):
        """
        Initialize comparative engine.
        
        Args:
            baseline_profile: Cached baseline with freqs, psd, damping, etc.
        """
        self.baseline_profile = baseline_profile
        self.freq_tolerance = 2.0  # Hz
    
    def compute_delta_f(self, live_peaks: List[float]) -> List[float]:
        """
        Compute frequency shifts (%) vs baseline.
        
        Args:
            live_peaks: Current detected peak frequencies
            
        Returns:
            List of Δf% for each peak (paired with baseline peaks)
        """
        if not self.baseline_profile or 'peaks' not in self.baseline_profile:
            return []
        
        baseline_peaks = self.baseline_profile.get('peaks', [])
        delta_f = []
        
        for i, baseline_freq in enumerate(baseline_peaks[:len(live_peaks)]):
            if i < len(live_peaks):
                live_freq = live_peaks[i]
                shift_pct = 100 * (live_freq - baseline_freq) / baseline_freq
                delta_f.append(shift_pct)
        
        return delta_f
    
    def compute_energy_anomalies(self, sensor_rms_values: Dict[int, float]) -> Dict[int, float]:
        """
        Compute energy anomaly scores per sensor (0-1).
        
        Args:
            sensor_rms_values: {sensor_id: rms_value}
            
        Returns:
            {sensor_id: anomaly_score} where higher = more anomalous
        """
        if not self.baseline_profile or 'rms_baseline' not in self.baseline_profile:
            return {i: 0.0 for i in sensor_rms_values.keys()}
        
        baseline_rms = self.baseline_profile.get('rms_baseline', {})
        anomalies = {}
        
        for sensor_id, rms in sensor_rms_values.items():
            baseline_val = baseline_rms.get(sensor_id, rms)
            if baseline_val > 0:
                ratio = rms / baseline_val
                # Sigmoid-like anomaly score
                anomaly = 1.0 / (1.0 + np.exp(-5 * (ratio - 1.5)))
                anomalies[sensor_id] = max(0, min(1.0, anomaly))
            else:
                anomalies[sensor_id] = 0.0
        
        return anomalies
    
    def compute_quality_score(self, delta_f: List[float], 
                            damping_delta: List[float]) -> float:
        """
        Compute overall quality score (0-1).
        
        Args:
            delta_f: Frequency shifts (%)
            damping_delta: Damping ratio changes
            
        Returns:
            Quality score (1.0 = perfect match to baseline)
        """
        if not delta_f:
            return 0.5
        
        # Penalize frequency shifts
        freq_error = np.mean(np.abs(delta_f))
        freq_score = np.exp(-freq_error / 50.0)  # Decay with 50% shift
        
        # Penalize damping changes (if available)
        damping_score = 1.0
        if damping_delta:
            damping_error = np.mean(np.abs(damping_delta))
            damping_score = np.exp(-damping_error)
        
        # Combined score
        quality = 0.7 * freq_score + 0.3 * damping_score
        return max(0, min(1.0, quality))


class LiveAnalysisEngine:
    """Main real-time analysis orchestrator."""
    
    def __init__(self, fs: float = 1000.0, num_sensors: int = 5, 
                 buffer_duration_sec: float = 120,
                 psd_window_sec: float = 8,
                 baseline_profile: Optional[Dict] = None):
        """
        Initialize live analysis engine.
        
        Args:
            fs: Sampling frequency (Hz)
            num_sensors: Number of sensors
            buffer_duration_sec: Buffer duration (seconds)
            psd_window_sec: PSD window size (seconds)
            baseline_profile: Optional baseline for comparative analysis
        """
        self.fs = fs
        self.num_sensors = num_sensors
        
        # Per-sensor buffers (for raw xyz or magnitude)
        self.sensor_buffers = {i: LiveSensorBuffer(fs, buffer_duration_sec) 
                               for i in range(num_sensors)}
        
        # Per-sensor magnitude buffers (if raw xyz is received)
        self.magnitude_buffers = {i: LiveSensorBuffer(fs, buffer_duration_sec) 
                                  for i in range(num_sensors)}
        
        # Analyzers
        self.psd_analyzer = RollingPSDAnalyzer(fs, psd_window_sec)
        self.peak_tracker = PeakTracker(fs)
        self.damping_estimator = DampingEstimator(fs)
        self.comparative_engine = ComparativeEngine(baseline_profile)
        
        # QC metrics
        self.last_timestamps = {}
        self.jitter_history = deque(maxlen=1000)
        self.clipping_count = {i: 0 for i in range(num_sensors)}
        self.max_adc_value = 16384  # Typical ADC max for ADXL345
        
        # ML-based anomaly detection
        self.ml_detector = None
        self.feature_extractor = None
        self._initialize_ml_detector()
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    def _initialize_ml_detector(self) -> None:
        """Initialize ML detector if models are available."""
        try:
            from ml_models.model_manager import ModelManager
            from ml_models.feature_extractor import FeatureExtractor
            
            model_manager = ModelManager()
            if model_manager.is_model_loaded():
                self.ml_detector = model_manager.current_model
                self.feature_extractor = FeatureExtractor(self.fs, self.num_sensors)
                print("✓ ML anomaly detector loaded")
            else:
                print("ℹ No ML model available (will train after baseline collection)")
        except Exception as e:
            print(f"ℹ ML models not available: {e}")
    
    def ingest_frame(self, frame_data: Dict) -> None:
        """
        Ingest a frame from the host.
        
        Args:
            frame_data: {
                'ts': datetime or ISO string (OPTIONAL - auto-generated if missing),
                'fs': sampling frequency,
                'sensors': number of sensors (should be 2 for XYZ data),
                'mode': 'raw_xyz' or 'magnitude',
                'frame': 2D array of samples [[s1x, s1y, s1z], [s2x, s2y, s2z]] for raw_xyz
            }
            
        Supports 2-sensor XYZ format (6 columns) without timestamp.
        """
        with self._lock:
            try:
                mode = frame_data.get('mode', 'magnitude')
                frame = np.array(frame_data.get('frame', []))
                ts = frame_data.get('ts')
                
                # Auto-generate timestamp if not provided
                if ts is None:
                    ts = datetime.utcnow()
                elif isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                
                if mode == 'raw_xyz':
                    # Frame is [sensor, [x, y, z]]
                    for sensor_id, xyz in enumerate(frame):
                        if sensor_id < self.num_sensors:
                            # Store raw components
                            self.sensor_buffers[sensor_id].add_samples(list(xyz), [ts] * 3)
                            
                            # Compute magnitude
                            magnitude = np.linalg.norm(xyz)
                            self.magnitude_buffers[sensor_id].add_sample(magnitude, ts)
                            
                            # Check for clipping
                            if np.any(np.abs(xyz) > self.max_adc_value * 0.95):
                                self.clipping_count[sensor_id] += 1
                
                elif mode == 'magnitude':
                    # Frame is [sensor] -> magnitude values
                    for sensor_id, magnitude in enumerate(frame):
                        if sensor_id < self.num_sensors:
                            self.magnitude_buffers[sensor_id].add_sample(float(magnitude), ts)
                
                # Update jitter metric
                if len(self.last_timestamps) > 0:
                    prev_ts = self.last_timestamps.get(0)
                    if prev_ts:
                        dt_ms = (ts - prev_ts).total_seconds() * 1000
                        self.jitter_history.append(dt_ms)
                
                self.last_timestamps[0] = ts
                
            except Exception as e:
                print(f"Ingest error: {e}")
    
    def compute_metrics(self) -> Dict:
        """
        Compute current QC and analysis metrics.
        
        Returns:
            Dictionary with QC, metrics, and comparative data
        """
        with self._lock:
            result = {
                'ts': datetime.utcnow().isoformat() + 'Z',
                'qc': self._compute_qc(),
                'metrics': self._compute_metrics(),
                'comparative': self._compute_comparative(),
                'ml_anomaly': self._compute_ml_anomaly()
            }
            return result
    
    def _compute_qc(self) -> Dict:
        """Compute QC metrics."""
        # Jitter
        jitter_ms = 0.0
        if len(self.jitter_history) > 10:
            jitter_ms = float(np.std(list(self.jitter_history)))
        
        # Clipping status
        clipping = [self.clipping_count.get(i, 0) > 0 for i in range(self.num_sensors)]
        
        # SNR proxy (ratio of signal to noise floor)
        snr_db = 35.0  # Placeholder
        
        return {
            'jitter_ms': jitter_ms,
            'clipping': clipping,
            'snr_db': snr_db
        }
    
    def _compute_metrics(self) -> Dict:
        """Compute analysis metrics (PSD, peaks, RMS)."""
        metrics = {
            'psd': {},
            'peaks': [],
            'rms': []
        }
        
        try:
            freqs = np.array([])  # Initialize freqs to avoid undefined variable error
            
            for sensor_id in range(self.num_sensors):
                # Get magnitude data
                data, _ = self.magnitude_buffers[sensor_id].get_recent(8.0)
                
                if len(data) > 100:
                    # Compute PSD
                    freqs, psd = self.psd_analyzer.compute_psd(data)
                    
                    if len(freqs) > 0:
                        metrics['psd'][f's{sensor_id+1}'] = psd.tolist()
                    
                    # Compute RMS
                    rms = np.sqrt(np.mean(data ** 2))
                    metrics['rms'].append(rms)
                else:
                    metrics['rms'].append(0.0)
            
            # Set frequency array (same for all sensors)
            if len(freqs) > 0:
                metrics['psd']['freqs'] = freqs.tolist()
            
            # Detect peaks from first sensor (or average)
            peak_data, _ = self.magnitude_buffers[0].get_recent(8.0)
            if len(peak_data) > 100:
                freqs, psd = self.psd_analyzer.compute_psd(peak_data)
                peaks = self.peak_tracker.detect_peaks(freqs, psd)
                metrics['peaks'] = [float(p) for p in peaks]
            
        except Exception as e:
            print(f"Metrics computation error: {e}")
        
        return metrics
    
    def _compute_comparative(self) -> Dict:
        """Compute comparative metrics (if baseline available)."""
        if not self.comparative_engine.baseline_profile:
            return {}
        
        try:
            metrics = self._compute_metrics()
            peaks = metrics.get('peaks', [])
            
            delta_f = self.comparative_engine.compute_delta_f(peaks)
            
            # Compute RMS baseline
            sensor_rms = {i: metrics['rms'][i] for i in range(len(metrics['rms']))}
            anomalies = self.comparative_engine.compute_energy_anomalies(sensor_rms)
            
            # Quality score
            damping_delta = [0.01] * len(peaks)  # Placeholder
            quality = self.comparative_engine.compute_quality_score(delta_f, damping_delta)
            
            return {
                'delta_f': [float(d) for d in delta_f],
                'damping_delta': [float(d) for d in damping_delta],
                'quality': float(quality),
                'heatmap': {f's{i+1}': float(anomalies.get(i, 0.0)) 
                           for i in range(self.num_sensors)}
            }
        except Exception as e:
            print(f"Comparative computation error: {e}")
            return {}
    
    def set_baseline_profile(self, profile: Dict) -> None:
        """Set baseline profile for comparative analysis."""
        with self._lock:
            self.comparative_engine.baseline_profile = profile
    
    def get_baseline_profile(self) -> Optional[Dict]:
        """Get current baseline profile."""
        with self._lock:
            return self.comparative_engine.baseline_profile
    
    def capture_baseline_from_buffer(self) -> Dict:
        """Capture current buffer state as baseline profile."""
        with self._lock:
            profile = {
                'ts': datetime.utcnow().isoformat() + 'Z',
                'fs': self.fs,
                'num_sensors': self.num_sensors,
                'peaks': [],
                'rms_baseline': {},
                'psd_profile': {}
            }
            
            try:
                # Capture peaks and RMS
                metrics = self._compute_metrics()
                profile['peaks'] = metrics.get('peaks', [])
                profile['rms_baseline'] = {i: metrics['rms'][i] 
                                          for i in range(len(metrics['rms']))}
                profile['psd_profile'] = metrics.get('psd', {})
            except Exception as e:
                print(f"Baseline capture error: {e}")
            
            return profile
    
    def _compute_ml_anomaly(self) -> Dict:
        """Compute ML-based anomaly detection scores."""
        if not self.ml_detector or not self.feature_extractor:
            return {}
        
        try:
            # Collect recent data from all sensors
            sensor_data = {}
            for sensor_id in range(self.num_sensors):
                data, _ = self.magnitude_buffers[sensor_id].get_recent(8.0)
                if len(data) > 0:
                    sensor_data[sensor_id] = data
            
            if len(sensor_data) < self.num_sensors:
                return {}
            
            # Extract features
            features = self.feature_extractor.extract_features(sensor_data)
            
            # Get anomaly prediction
            prediction = self.ml_detector.predict(features)
            
            return prediction
        
        except Exception as e:
            print(f"ML anomaly computation error: {e}")
            return {}

"""
Advanced vibration parameter calculator for dual-sensor ADXL345 system.
Computes 50+ parameters across time-domain, frequency-domain, statistical, 
advanced, and correlation metrics.
"""

import numpy as np
from scipy import signal, stats
from scipy.fft import fft, fftfreq
from typing import Dict, Tuple, List
import warnings

warnings.filterwarnings('ignore')


class ParameterCalculator:
    """Calculates comprehensive vibration monitoring parameters."""
    
    def __init__(self, sampling_rate: float = 50.0):
        """
        Initialize calculator with sampling parameters.
        
        Args:
            sampling_rate: Samples per second (default 50Hz)
        """
        self.sampling_rate = sampling_rate
        self.nyquist = sampling_rate / 2
        
    def calculate_all_parameters(self, 
                                data_s1: np.ndarray,
                                data_s2: np.ndarray) -> Dict:
        """
        Calculate all parameters for dual sensor system.
        
        Args:
            data_s1: Nx3 array (X, Y, Z for sensor 1)
            data_s2: Nx3 array (X, Y, Z for sensor 2)
            
        Returns:
            Dictionary with all calculated parameters
        """
        result = {
            'timestamp': None,
            'sensor_1': {},
            'sensor_2': {},
            'correlation': {}
        }
        
        # Process each sensor
        result['sensor_1'] = self._process_sensor(data_s1, 'Sensor 1')
        result['sensor_2'] = self._process_sensor(data_s2, 'Sensor 2')
        
        # Calculate correlation metrics between sensors
        result['correlation'] = self._calculate_correlation_metrics(data_s1, data_s2)
        
        return result
    
    def _process_sensor(self, data: np.ndarray, sensor_name: str) -> Dict:
        """Process single sensor (3-axis data)."""
        result = {}
        
        # Ensure data is proper shape
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        
        # Calculate magnitude (resultant acceleration)
        magnitude = np.sqrt(np.sum(data**2, axis=1))
        
        # Time-domain parameters
        result['time_domain'] = self._calculate_time_domain(magnitude)
        
        # Frequency-domain parameters
        result['frequency_domain'] = self._calculate_frequency_domain(magnitude)
        
        # Statistical parameters
        result['statistical'] = self._calculate_statistical(magnitude)
        
        # Advanced parameters
        result['advanced'] = self._calculate_advanced(magnitude)
        
        # Per-axis data (for waveform visualization)
        result['axes'] = {
            'x': data[:, 0].tolist() if data.shape[1] > 0 else [],
            'y': data[:, 1].tolist() if data.shape[1] > 1 else [],
            'z': data[:, 2].tolist() if data.shape[1] > 2 else [],
        }
        
        # Per-axis parameters
        result['axis_parameters'] = {
            'x': self._calculate_time_domain(data[:, 0]) if data.shape[1] > 0 else {},
            'y': self._calculate_time_domain(data[:, 1]) if data.shape[1] > 1 else {},
            'z': self._calculate_time_domain(data[:, 2]) if data.shape[1] > 2 else {},
        }
        
        return result
    
    def _calculate_time_domain(self, signal_data: np.ndarray) -> Dict:
        """Calculate 14 time-domain parameters."""
        if len(signal_data) == 0:
            return {}
        
        sig = signal_data.astype(np.float64)
        
        # Basic statistics
        mean = np.mean(sig)
        std_dev = np.std(sig)
        rms = np.sqrt(np.mean(sig**2))
        peak = np.max(np.abs(sig))
        peak_to_peak = np.max(sig) - np.min(sig)
        
        # Handle edge case: all zeros or very small values
        if rms < 1e-10:
            return {
                'mean': float(mean),
                'std_dev': float(std_dev),
                'rms': float(rms),
                'peak': float(peak),
                'peak_to_peak': float(peak_to_peak),
                'crest_factor': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0,
                'mean_absolute': float(np.mean(np.abs(sig))),
                'median': float(np.median(sig)),
                'variance': float(np.var(sig)),
                'rms_factor': 0.0,
                'form_factor': 0.0,
                'impulse_factor': 0.0,
            }
        
        # Crest factor (peak / RMS)
        crest_factor = peak / rms if rms > 1e-10 else 0
        
        # Skewness and Kurtosis (returns NaN for constant data, handle gracefully)
        with np.errstate(all='ignore'):
            skewness = stats.skew(sig)
            kurtosis = stats.kurtosis(sig)
        
        # Replace NaN with 0 for constant/near-constant data
        skewness = 0.0 if np.isnan(skewness) or np.isinf(skewness) else float(skewness)
        kurtosis = 0.0 if np.isnan(kurtosis) or np.isinf(kurtosis) else float(kurtosis)
        
        # Mean absolute
        mean_abs = np.mean(np.abs(sig))
        
        # Median
        median = np.median(sig)
        
        # Variance
        variance = np.var(sig)
        
        # RMS Factor (RMS of signal / RMS of mean)
        rms_factor = rms / (np.abs(mean) + 1e-10)
        
        # Form Factor (RMS / mean absolute)
        form_factor = rms / (mean_abs + 1e-10)
        
        # Impulse Factor (peak / mean absolute)
        impulse_factor = peak / (mean_abs + 1e-10)
        
        return {
            'mean': float(mean),
            'std_dev': float(std_dev),
            'rms': float(rms),
            'peak': float(peak),
            'peak_to_peak': float(peak_to_peak),
            'crest_factor': float(crest_factor),
            'skewness': float(skewness),
            'kurtosis': float(kurtosis),
            'mean_absolute': float(mean_abs),
            'median': float(median),
            'variance': float(variance),
            'rms_factor': float(rms_factor),
            'form_factor': float(form_factor),
            'impulse_factor': float(impulse_factor),
        }
    
    def _calculate_frequency_domain(self, signal_data: np.ndarray) -> Dict:
        """Calculate 9 frequency-domain parameters using FFT."""
        if len(signal_data) < 4:
            return {}
        
        sig = signal_data.astype(np.float64)
        
        # Compute FFT
        fft_vals = fft(sig)
        fft_mag = np.abs(fft_vals[:len(sig)//2])
        freqs = fftfreq(len(sig), 1/self.sampling_rate)[:len(sig)//2]
        
        # Normalize
        fft_mag = fft_mag / (len(sig) / 2)
        
        # Dominant frequency
        dominant_idx = np.argmax(fft_mag)
        dominant_freq = freqs[dominant_idx]
        
        # Frequency bandwidth (width of spectrum at half max)
        max_mag = np.max(fft_mag)
        half_max_idx = np.where(fft_mag >= max_mag * 0.5)[0]
        if len(half_max_idx) > 1:
            freq_bandwidth = freqs[half_max_idx[-1]] - freqs[half_max_idx[0]]
        else:
            freq_bandwidth = 0
        
        # Spectral centroid
        spectral_centroid = np.sum(freqs * fft_mag) / (np.sum(fft_mag) + 1e-10)
        
        # Spectral rolloff (frequency below which 95% of energy)
        energy_cumsum = np.cumsum(fft_mag)
        total_energy = energy_cumsum[-1]
        rolloff_idx = np.argmax(energy_cumsum >= total_energy * 0.95)
        spectral_rolloff = freqs[rolloff_idx] if rolloff_idx > 0 else 0
        
        # Spectral flux (change in spectrum magnitude)
        if len(sig) > 1:
            spectral_flux = np.sqrt(np.sum(np.diff(fft_mag)**2))
        else:
            spectral_flux = 0
        
        # Spectral skewness and kurtosis (handle NaN for low-energy signals)
        fft_normalized = fft_mag / (np.sum(fft_mag) + 1e-10)
        with np.errstate(all='ignore'):
            spectral_skewness = stats.skew(fft_mag)
            spectral_kurtosis = stats.kurtosis(fft_mag)
        
        spectral_skewness = 0.0 if np.isnan(spectral_skewness) or np.isinf(spectral_skewness) else float(spectral_skewness)
        spectral_kurtosis = 0.0 if np.isnan(spectral_kurtosis) or np.isinf(spectral_kurtosis) else float(spectral_kurtosis)
        
        # Spectral spread
        spectral_spread = np.sqrt(np.sum(((freqs - spectral_centroid)**2) * fft_mag) / 
                                  (np.sum(fft_mag) + 1e-10))
        
        # Spectral slope (linear regression of log spectrum)
        if len(freqs) > 1 and dominant_freq > 0:
            log_freqs = np.log10(freqs[1:] + 1e-10)
            log_mags = np.log10(fft_mag[1:] + 1e-10)
            coeffs = np.polyfit(log_freqs, log_mags, 1)
            spectral_slope = coeffs[0]
        else:
            spectral_slope = 0
        
        return {
            'dominant_frequency': float(dominant_freq),
            'frequency_bandwidth': float(freq_bandwidth),
            'spectral_centroid': float(spectral_centroid),
            'spectral_rolloff': float(spectral_rolloff),
            'spectral_flux': float(spectral_flux),
            'spectral_skewness': float(spectral_skewness),
            'spectral_kurtosis': float(spectral_kurtosis),
            'spectral_spread': float(spectral_spread),
            'spectral_slope': float(spectral_slope),
        }
    
    def _calculate_statistical(self, signal_data: np.ndarray) -> Dict:
        """Calculate 9 statistical parameters."""
        if len(signal_data) == 0:
            return {}
        
        sig = signal_data.astype(np.float64)
        
        # Zero-crossing rate
        zero_crossings = np.sum(np.abs(np.diff(np.sign(sig)))) / 2
        zcr = zero_crossings / len(sig)
        
        # Mean-crossing rate
        mean_val = np.mean(sig)
        mean_crossings = np.sum(np.abs(np.diff(np.sign(sig - mean_val)))) / 2
        mcr = mean_crossings / len(sig)
        
        # Entropy (Shannon entropy of normalized histogram)
        hist, _ = np.histogram(sig, bins=20, density=True)
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        
        # Energy
        energy = np.sum(sig**2)
        
        # Power
        power = energy / len(sig)
        
        # RMS Power
        rms_power = np.sqrt(power)
        
        # Peak Power
        peak_power = np.max(np.abs(sig))
        
        # Dynamic range
        signal_range = np.max(sig) - np.min(sig)
        snr_estimate = 20 * np.log10(np.max(np.abs(sig)) / (np.std(sig) + 1e-10))
        
        return {
            'zero_crossing_rate': float(zcr),
            'mean_crossing_rate': float(mcr),
            'entropy': float(entropy),
            'energy': float(energy),
            'power': float(power),
            'rms_power': float(rms_power),
            'peak_power': float(peak_power),
            'dynamic_range': float(signal_range),
            'snr_estimate': float(snr_estimate),
        }
    
    def _calculate_advanced(self, signal_data: np.ndarray) -> Dict:
        """Calculate 7 advanced parameters."""
        if len(signal_data) < 4:
            return {}
        
        sig = signal_data.astype(np.float64)
        result = {}
        
        # Autocorrelation maximum and lag
        autocorr = np.correlate(sig - np.mean(sig), sig - np.mean(sig), mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr_max = np.max(autocorr[1:]) / autocorr[0] if autocorr[0] != 0 else 0
        autocorr_lag = np.argmax(autocorr[1:]) + 1
        
        result['autocorr_max'] = float(autocorr_max)
        result['autocorr_lag'] = int(autocorr_lag)
        
        # Hurst Exponent (simplified)
        try:
            hurst = self._calculate_hurst_exponent(sig)
            result['hurst_exponent'] = float(hurst)
        except:
            result['hurst_exponent'] = 0.5
        
        # Lyapunov Exponent (simplified - using delay reconstruction)
        try:
            lyapunov = self._calculate_lyapunov_exponent(sig)
            result['lyapunov_exponent'] = float(lyapunov)
        except:
            result['lyapunov_exponent'] = 0.0
        
        # Correlation dimension (simplified)
        try:
            corr_dim = self._calculate_correlation_dimension(sig)
            result['correlation_dimension'] = float(corr_dim)
        except:
            result['correlation_dimension'] = 1.0
        
        # Sample Entropy
        try:
            sample_entropy = self._calculate_sample_entropy(sig, m=2, r=0.2*np.std(sig))
            result['sample_entropy'] = float(sample_entropy)
        except:
            result['sample_entropy'] = 0.0
        
        # Approximate Entropy
        try:
            approx_entropy = self._calculate_approximate_entropy(sig, m=2, r=0.2*np.std(sig))
            result['approximate_entropy'] = float(approx_entropy)
        except:
            result['approximate_entropy'] = 0.0
        
        return result
    
    def _calculate_hurst_exponent(self, signal_data: np.ndarray) -> float:
        """Calculate Hurst exponent (simplified R/S analysis)."""
        sig = signal_data - np.mean(signal_data)
        n = len(sig)
        
        if n < 10:
            return 0.5
        
        # Rescaled range analysis
        lags = range(10, min(n//2, 100), 5)
        taus = []
        
        for lag in lags:
            # Split into chunks and calculate R/S
            chunks = n // lag
            rs_values = []
            
            for i in range(chunks):
                chunk = sig[i*lag:(i+1)*lag]
                if len(chunk) > 0:
                    mean_chunk = np.mean(chunk)
                    Y = np.cumsum(chunk - mean_chunk)
                    R = np.max(Y) - np.min(Y)
                    S = np.std(chunk, ddof=1)
                    
                    if S > 0:
                        rs_values.append(R / S)
            
            if rs_values:
                taus.append(np.mean(rs_values))
        
        if len(taus) > 1:
            # Linear regression in log-log
            log_lags = np.log(list(lags))
            log_taus = np.log(taus)
            coeffs = np.polyfit(log_lags, log_taus, 1)
            return coeffs[0]
        
        return 0.5
    
    def _calculate_lyapunov_exponent(self, signal_data: np.ndarray, dim: int = 3, delay: int = 1) -> float:
        """Calculate Lyapunov exponent (simplified)."""
        sig = signal_data - np.mean(signal_data)
        n = len(sig)
        
        if n < dim * delay + 100:
            return 0.0
        
        # Reconstruct phase space
        m = n - (dim - 1) * delay
        trajectory = np.zeros((m, dim))
        
        for i in range(dim):
            trajectory[:, i] = sig[i*delay:i*delay + m]
        
        # Find nearest neighbors and calculate divergence
        lyap_sum = 0
        count = 0
        
        for i in range(m - delay):
            # Find nearest neighbor
            distances = np.linalg.norm(trajectory[i:i+1, :] - trajectory, axis=1)
            distances[i] = np.inf
            nearest_idx = np.argmin(distances)
            
            # Calculate divergence rate
            if i + delay < m and nearest_idx + delay < m:
                initial_dist = distances[nearest_idx]
                final_dist = np.linalg.norm(trajectory[i + delay] - trajectory[nearest_idx + delay])
                
                if initial_dist > 0 and final_dist > 0:
                    lyap_sum += np.log(final_dist / initial_dist)
                    count += 1
        
        if count > 0:
            return lyap_sum / (count * delay)
        
        return 0.0
    
    def _calculate_correlation_dimension(self, signal_data: np.ndarray, dim: int = 3, delay: int = 1) -> float:
        """Calculate correlation dimension (simplified)."""
        sig = signal_data - np.mean(signal_data)
        n = len(sig)
        
        if n < dim * delay + 50:
            return 1.0
        
        # Reconstruct phase space
        m = n - (dim - 1) * delay
        trajectory = np.zeros((m, dim))
        
        for i in range(dim):
            trajectory[:, i] = sig[i*delay:i*delay + m]
        
        # Calculate correlation dimension
        r_values = np.logspace(-2, 1, 20)
        c_values = []
        
        for r in r_values:
            count = 0
            for i in range(m):
                distances = np.linalg.norm(trajectory[i:i+1, :] - trajectory, axis=1)
                count += np.sum(distances < r)
            
            if count > 0:
                c_values.append(count / (m * m))
        
        if len(c_values) > 1:
            log_r = np.log(r_values)
            log_c = np.log(np.array(c_values))
            valid_idx = ~np.isinf(log_c) & ~np.isnan(log_c)
            
            if np.sum(valid_idx) > 1:
                coeffs = np.polyfit(log_r[valid_idx], log_c[valid_idx], 1)
                return coeffs[0]
        
        return 1.0
    
    def _calculate_sample_entropy(self, signal_data: np.ndarray, m: int = 2, r: float = 0.2) -> float:
        """Calculate sample entropy."""
        sig = signal_data - np.mean(signal_data)
        n = len(sig)
        
        if n < m + 1:
            return 0.0
        
        def _maxdist(x_i, x_j):
            return max(abs(ua - va) for ua, va in zip(x_i, x_j))
        
        # Count matches for m and m+1
        phi_m = 0
        phi_m1 = 0
        
        for i in range(n - m):
            template = sig[i:i + m]
            for j in range(i + 1, n - m):
                if _maxdist(template, sig[j:j + m]) < r:
                    phi_m += 1
        
        for i in range(n - m - 1):
            template = sig[i:i + m + 1]
            for j in range(i + 1, n - m - 1):
                if _maxdist(template, sig[j:j + m + 1]) < r:
                    phi_m1 += 1
        
        if phi_m > 0 and phi_m1 > 0:
            return -np.log(phi_m1 / phi_m)
        
        return 0.0
    
    def _calculate_approximate_entropy(self, signal_data: np.ndarray, m: int = 2, r: float = 0.2) -> float:
        """Calculate approximate entropy."""
        sig = signal_data - np.mean(signal_data)
        n = len(sig)
        
        if n < m + 1:
            return 0.0
        
        def _count_patterns(data, pattern_len, tolerance):
            count = 0
            for i in range(len(data) - pattern_len + 1):
                pattern = data[i:i + pattern_len]
                for j in range(i + 1, len(data) - pattern_len + 1):
                    if max(abs(p - d) for p, d in zip(pattern, data[j:j + pattern_len])) < tolerance:
                        count += 1
            return count
        
        # Calculate entropy for m and m+1
        c_m = _count_patterns(sig, m, r) / (n - m + 1)
        c_m1 = _count_patterns(sig, m + 1, r) / (n - m)
        
        if c_m > 0 and c_m1 > 0:
            return np.log(c_m / c_m1)
        
        return 0.0
    
    def _calculate_correlation_metrics(self, data_s1: np.ndarray, data_s2: np.ndarray) -> Dict:
        """Calculate correlation metrics between two sensors."""
        result = {}
        
        if len(data_s1) == 0 or len(data_s2) == 0:
            return result
        
        # Ensure same length
        min_len = min(len(data_s1), len(data_s2))
        s1 = data_s1[:min_len]
        s2 = data_s2[:min_len]
        
        # Calculate magnitude for each
        mag1 = np.sqrt(np.sum(s1**2, axis=1)) if s1.ndim > 1 else s1
        mag2 = np.sqrt(np.sum(s2**2, axis=1)) if s2.ndim > 1 else s2
        
        # Cross-correlation
        xcorr = np.correlate(mag1 - np.mean(mag1), mag2 - np.mean(mag2), mode='full')
        xcorr_normalized = xcorr / (np.std(mag1) * np.std(mag2) * len(mag1) + 1e-10)
        
        # Max cross-correlation and lag
        max_xcorr_idx = np.argmax(np.abs(xcorr_normalized))
        max_xcorr = xcorr_normalized[max_xcorr_idx]
        xcorr_lag = max_xcorr_idx - len(xcorr)//2
        
        # Direct correlation
        direct_correlation = np.corrcoef(mag1, mag2)[0, 1]
        
        result['cross_correlation'] = float(direct_correlation)
        result['max_cross_correlation'] = float(max_xcorr)
        result['cross_correlation_lag'] = int(xcorr_lag)
        
        # Coherence (simplified)
        try:
            f, coh = signal.coherence(mag1, mag2, fs=self.sampling_rate)
            result['coherence_mean'] = float(np.mean(coh))
            result['coherence_max'] = float(np.max(coh))
            result['coherence_freq'] = float(f[np.argmax(coh)])
        except:
            result['coherence_mean'] = 0.0
            result['coherence_max'] = 0.0
            result['coherence_freq'] = 0.0
        
        # Phase delay (simplified)
        fft1 = fft(mag1)
        fft2 = fft(mag2)
        phase_diff = np.angle(fft1) - np.angle(fft2)
        result['phase_delay_mean'] = float(np.mean(phase_diff))
        result['phase_delay_max'] = float(np.max(np.abs(phase_diff)))
        
        # MSC (Magnitude Squared Coherence)
        result['msc'] = float(np.max([0, direct_correlation])**2)
        
        # Transfer function gain
        try:
            gain = np.std(mag2) / (np.std(mag1) + 1e-10)
            result['transfer_function_gain'] = float(gain)
        except:
            result['transfer_function_gain'] = 0.0
        
        return result


if __name__ == "__main__":
    # Test with sample data
    calc = ParameterCalculator(sampling_rate=50.0)
    
    # Generate test signal (30 seconds @ 50Hz = 1500 samples)
    n_samples = 1500
    t = np.linspace(0, 30, n_samples)
    
    # Sensor 1: combination of frequencies
    s1_x = 0.5 * np.sin(2 * np.pi * 5 * t) + 0.2 * np.sin(2 * np.pi * 15 * t)
    s1_y = 0.4 * np.sin(2 * np.pi * 7 * t) + 0.3 * np.sin(2 * np.pi * 10 * t)
    s1_z = 0.6 * np.sin(2 * np.pi * 8 * t) + 0.1 * np.sin(2 * np.pi * 20 * t)
    data_s1 = np.column_stack([s1_x, s1_y, s1_z])
    
    # Sensor 2: slightly different signal
    s2_x = 0.45 * np.sin(2 * np.pi * 5 * t + 0.3) + 0.25 * np.sin(2 * np.pi * 15 * t)
    s2_y = 0.35 * np.sin(2 * np.pi * 7 * t + 0.2) + 0.35 * np.sin(2 * np.pi * 10 * t)
    s2_z = 0.55 * np.sin(2 * np.pi * 8 * t + 0.1) + 0.15 * np.sin(2 * np.pi * 20 * t)
    data_s2 = np.column_stack([s2_x, s2_y, s2_z])
    
    # Calculate parameters
    params = calc.calculate_all_parameters(data_s1, data_s2)
    
    print("Sample Parameter Calculation Results:")
    print(f"Sensor 1 RMS: {params['sensor_1']['time_domain']['rms']:.4f} g")
    print(f"Sensor 2 RMS: {params['sensor_2']['time_domain']['rms']:.4f} g")
    print(f"Correlation: {params['correlation']['cross_correlation']}")

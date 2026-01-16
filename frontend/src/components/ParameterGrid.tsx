import React, { useMemo } from 'react';
import ParameterCard from './ParameterCard';

interface ParameterGridProps {
  parameters: any;
}

const ParameterGrid: React.FC<ParameterGridProps> = ({ parameters }) => {
  const categorizedParams = useMemo(() => {
    if (!parameters || !parameters.sensor_1) return {};

    const s1 = parameters.sensor_1;

    return {
      'Time Domain': [
        { name: 'Mean', value: s1.time_domain?.mean || 0, unit: 'g' },
        { name: 'Std Dev', value: s1.time_domain?.std_dev || 0, unit: 'g' },
        { name: 'RMS', value: s1.time_domain?.rms || 0, unit: 'g' },
        { name: 'Peak', value: s1.time_domain?.peak || 0, unit: 'g' },
        { name: 'Peak-to-Peak', value: s1.time_domain?.peak_to_peak || 0, unit: 'g' },
        { name: 'Crest Factor', value: s1.time_domain?.crest_factor || 0, unit: '' },
        { name: 'Skewness', value: s1.time_domain?.skewness || 0, unit: '' },
        { name: 'Kurtosis', value: s1.time_domain?.kurtosis || 0, unit: '' },
        { name: 'Mean Absolute', value: s1.time_domain?.mean_absolute || 0, unit: 'g' },
        { name: 'Median', value: s1.time_domain?.median || 0, unit: 'g' },
        { name: 'Variance', value: s1.time_domain?.variance || 0, unit: 'g²' },
        { name: 'RMS Factor', value: s1.time_domain?.rms_factor || 0, unit: '' },
        { name: 'Form Factor', value: s1.time_domain?.form_factor || 0, unit: '' },
        { name: 'Impulse Factor', value: s1.time_domain?.impulse_factor || 0, unit: '' },
      ],
      'Frequency Domain': [
        { name: 'Dominant Freq', value: s1.frequency_domain?.dominant_frequency || 0, unit: 'Hz' },
        { name: 'Freq Bandwidth', value: s1.frequency_domain?.frequency_bandwidth || 0, unit: 'Hz' },
        { name: 'Spectral Centroid', value: s1.frequency_domain?.spectral_centroid || 0, unit: 'Hz' },
        { name: 'Spectral Rolloff', value: s1.frequency_domain?.spectral_rolloff || 0, unit: 'Hz' },
        { name: 'Spectral Flux', value: s1.frequency_domain?.spectral_flux || 0, unit: '' },
        { name: 'Spectral Skewness', value: s1.frequency_domain?.spectral_skewness || 0, unit: '' },
        { name: 'Spectral Kurtosis', value: s1.frequency_domain?.spectral_kurtosis || 0, unit: '' },
        { name: 'Spectral Spread', value: s1.frequency_domain?.spectral_spread || 0, unit: 'Hz' },
        { name: 'Spectral Slope', value: s1.frequency_domain?.spectral_slope || 0, unit: '' },
      ],
      'Statistical': [
        { name: 'Zero-Cross Rate', value: s1.statistical?.zero_crossing_rate || 0, unit: '' },
        { name: 'Mean-Cross Rate', value: s1.statistical?.mean_crossing_rate || 0, unit: '' },
        { name: 'Entropy', value: s1.statistical?.entropy || 0, unit: 'bits' },
        { name: 'Energy', value: s1.statistical?.energy || 0, unit: 'J' },
        { name: 'Power', value: s1.statistical?.power || 0, unit: 'W' },
        { name: 'RMS Power', value: s1.statistical?.rms_power || 0, unit: 'W' },
        { name: 'Peak Power', value: s1.statistical?.peak_power || 0, unit: 'W' },
        { name: 'Dynamic Range', value: s1.statistical?.dynamic_range || 0, unit: 'g' },
        { name: 'SNR Estimate', value: s1.statistical?.snr_estimate || 0, unit: 'dB' },
      ],
      'Advanced': [
        { name: 'Autocorr Max', value: s1.advanced?.autocorr_max || 0, unit: '' },
        { name: 'Autocorr Lag', value: s1.advanced?.autocorr_lag || 0, unit: 'samples' },
        { name: 'Hurst Exponent', value: s1.advanced?.hurst_exponent || 0, unit: '' },
        { name: 'Lyapunov Exp', value: s1.advanced?.lyapunov_exponent || 0, unit: '' },
        { name: 'Corr Dimension', value: s1.advanced?.correlation_dimension || 0, unit: '' },
        { name: 'Sample Entropy', value: s1.advanced?.sample_entropy || 0, unit: '' },
        { name: 'Approx Entropy', value: s1.advanced?.approximate_entropy || 0, unit: '' },
      ],
      'Correlation': [
        { name: 'Cross-Corr', value: parameters.correlation?.cross_correlation || 0, unit: '' },
        { name: 'Max Cross-Corr', value: parameters.correlation?.max_cross_correlation || 0, unit: '' },
        { name: 'Corr Lag', value: parameters.correlation?.cross_correlation_lag || 0, unit: 'samples' },
        { name: 'Coherence Mean', value: parameters.correlation?.coherence_mean || 0, unit: '' },
        { name: 'Coherence Max', value: parameters.correlation?.coherence_max || 0, unit: '' },
        { name: 'Phase Delay Mean', value: parameters.correlation?.phase_delay_mean || 0, unit: 'rad' },
        { name: 'Phase Delay Max', value: parameters.correlation?.phase_delay_max || 0, unit: 'rad' },
        { name: 'MSC', value: parameters.correlation?.msc || 0, unit: '' },
        { name: 'Transfer Gain', value: parameters.correlation?.transfer_function_gain || 0, unit: '' },
      ],
    };
  }, [parameters]);

  return (
    <div className="parameter-grid-container">
      {Object.entries(categorizedParams).map(([category, params]) => (
        <div key={category} className="category-section">
          <h3 className="category-title">{category}</h3>
          <div className="parameter-grid">
            {(params as any[]).map((param, idx) => (
              <ParameterCard key={idx} {...param} category={category} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ParameterGrid;

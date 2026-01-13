import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  ReferenceLine
} from 'recharts';

export default function LivePSD({ metrics }) {
  const psdData = useMemo(() => {
    if (!metrics || !metrics.metrics || !metrics.metrics.psd) {
      return [];
    }

    const psd = metrics.metrics.psd;
    const freqs = psd.freqs || [];
    
    if (freqs.length === 0) {
      return [];
    }

    // Create data array with all sensor PSDs
    return freqs.map((freq, idx) => ({
      freq: freq.toFixed(1),
      s1: psd.s1 ? psd.s1[idx] : 0,
      s2: psd.s2 ? psd.s2[idx] : 0,
      s3: psd.s3 ? psd.s3[idx] : 0,
      s4: psd.s4 ? psd.s4[idx] : 0,
      s5: psd.s5 ? psd.s5[idx] : 0,
    }));
  }, [metrics]);

  const peaks = metrics?.metrics?.peaks || [];
  const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];

  // Downsample data for performance (show every Nth point)
  const downsampledData = psdData.filter((_, idx) => idx % 5 === 0);

  return (
    <div className="live-psd-container">
      <div className="psd-chart">
        <h3>Power Spectral Density (All Sensors)</h3>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart
            data={downsampledData.length > 0 ? downsampledData : [{ freq: 0 }]}
            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
            <XAxis 
              dataKey="freq" 
              label={{ value: 'Frequency (Hz)', position: 'insideBottomRight', offset: -5 }}
              stroke="#888"
            />
            <YAxis 
              label={{ value: 'PSD (g²/Hz)', angle: -90, position: 'insideLeft' }}
              scale="log"
              domain={[1e-6, 1e2]}
              stroke="#888"
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #4b5563' }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Legend />
            
            {/* Reference lines for detected peaks */}
            {peaks.map((peak, idx) => (
              <ReferenceLine 
                key={idx}
                x={peak.toFixed(1)} 
                stroke="#fbbf24" 
                strokeDasharray="5 5"
                label={{ value: `f${idx + 1}=${peak.toFixed(1)}Hz`, fill: '#fbbf24', offset: 10 }}
              />
            ))}

            <Line type="monotone" dataKey="s1" stroke={colors[0]} dot={false} strokeWidth={1.5} isAnimationActive={false} name="S1" />
            <Line type="monotone" dataKey="s2" stroke={colors[1]} dot={false} strokeWidth={1.5} isAnimationActive={false} name="S2" />
            <Line type="monotone" dataKey="s3" stroke={colors[2]} dot={false} strokeWidth={1.5} isAnimationActive={false} name="S3" />
            <Line type="monotone" dataKey="s4" stroke={colors[3]} dot={false} strokeWidth={1.5} isAnimationActive={false} name="S4" />
            <Line type="monotone" dataKey="s5" stroke={colors[4]} dot={false} strokeWidth={1.5} isAnimationActive={false} name="S5" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="peaks-info">
        <h3>Detected Peaks</h3>
        {peaks.length > 0 ? (
          <div className="peaks-list">
            {peaks.map((peak, idx) => (
              <div key={idx} className="peak-item">
                <span className="peak-label">f{idx + 1}</span>
                <span className="peak-value">{peak.toFixed(2)} Hz</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-peaks">No peaks detected yet</p>
        )}
      </div>
    </div>
  );
}

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export default function LiveChart({ data, metrics }) {
  // Format data for recharts - keep last 10 seconds
  const displayData = data.slice(-10).map((point, idx) => ({
    time: idx,
    S1: point.rms ? point.rms[0] : 0,
    S2: point.rms ? point.rms[1] : 0,
    S3: point.rms ? point.rms[2] : 0,
    S4: point.rms ? point.rms[3] : 0,
    S5: point.rms ? point.rms[4] : 0,
  }));

  const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];

  return (
    <div className="live-chart-container">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={displayData.length > 0 ? displayData : [{ time: 0, S1: 0, S2: 0, S3: 0, S4: 0, S5: 0 }]}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis 
            dataKey="time" 
            label={{ value: 'Time (s)', position: 'insideBottomRight', offset: -5 }}
            stroke="#888"
          />
          <YAxis 
            label={{ value: 'RMS (g)', angle: -90, position: 'insideLeft' }}
            stroke="#888"
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #4b5563' }}
            labelStyle={{ color: '#e5e7eb' }}
          />
          <Legend />
          <Line type="monotone" dataKey="S1" stroke={colors[0]} dot={false} strokeWidth={2} isAnimationActive={false} />
          <Line type="monotone" dataKey="S2" stroke={colors[1]} dot={false} strokeWidth={2} isAnimationActive={false} />
          <Line type="monotone" dataKey="S3" stroke={colors[2]} dot={false} strokeWidth={2} isAnimationActive={false} />
          <Line type="monotone" dataKey="S4" stroke={colors[3]} dot={false} strokeWidth={2} isAnimationActive={false} />
          <Line type="monotone" dataKey="S5" stroke={colors[4]} dot={false} strokeWidth={2} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>

      <div className="chart-stats">
        {metrics && metrics.metrics && metrics.metrics.rms && (
          <div className="stats-grid">
            {metrics.metrics.rms.map((rms, idx) => (
              <div key={idx} className="stat-item">
                <span className="sensor-label">S{idx + 1}</span>
                <span className="rms-value">{rms.toFixed(3)} g</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

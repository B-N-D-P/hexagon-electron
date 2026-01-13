import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function ComparativeDashboard({ comparative, baseline }) {
  const heatmapData = useMemo(() => {
    if (!comparative || !comparative.heatmap) {
      return {};
    }
    return comparative.heatmap;
  }, [comparative]);

  const deltaF = comparative?.delta_f || [];
  const dampingDelta = comparative?.damping_delta || [];
  const quality = comparative?.quality || 0;

  // Map sensor positions for heatmap visualization
  const sensorPositions = [
    { id: 0, name: 'S1', x: 50, y: 20, label: 'Front Left' },
    { id: 1, name: 'S2', x: 50, y: 80, label: 'Front Right' },
    { id: 2, name: 'S3', x: 20, y: 50, label: 'Mid Left' },
    { id: 3, name: 'S4', x: 80, y: 50, label: 'Mid Right' },
    { id: 4, name: 'S5', x: 50, y: 50, label: 'Center' },
  ];

  const getAnomalyColor = (score) => {
    if (score < 0.2) return '#10b981'; // green
    if (score < 0.4) return '#84cc16'; // lime
    if (score < 0.6) return '#f59e0b'; // amber
    if (score < 0.8) return '#f97316'; // orange
    return '#dc2626'; // red
  };

  return (
    <div className="comparative-dashboard">
      {/* Quality Score */}
      <div className="quality-section">
        <h3>Overall Quality Score</h3>
        <div className="quality-meter">
          <div className="quality-bar">
            <div 
              className="quality-fill"
              style={{
                width: `${quality * 100}%`,
                backgroundColor: quality > 0.8 ? '#10b981' : quality > 0.6 ? '#f59e0b' : '#ef4444'
              }}
            ></div>
          </div>
          <div className="quality-value">{(quality * 100).toFixed(1)}%</div>
          <div className="quality-label">
            {quality > 0.8 ? '✓ Excellent match to baseline' : 
             quality > 0.6 ? '⚠ Notable deviations' : 
             '✗ Significant changes detected'}
          </div>
        </div>
      </div>

      {/* Frequency Comparison Table */}
      <div className="comparison-table">
        <h3>Frequency Shifts vs Baseline</h3>
        <table>
          <thead>
            <tr>
              <th>Peak</th>
              <th>Baseline (Hz)</th>
              <th>Current (Hz)</th>
              <th>Shift (%)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {deltaF.map((shift, idx) => {
              const isWarning = Math.abs(shift) > 2;
              const isAlert = Math.abs(shift) > 5;
              
              return (
                <tr key={idx} className={isAlert ? 'alert-row' : isWarning ? 'warn-row' : ''}>
                  <td>f{idx + 1}</td>
                  <td>--</td>
                  <td>--</td>
                  <td>
                    <span className="shift-value">
                      {shift > 0 ? '+' : ''}{shift.toFixed(2)}%
                    </span>
                    {shift > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  </td>
                  <td>
                    {isAlert && <span className="badge-alert">ALERT</span>}
                    {isWarning && !isAlert && <span className="badge-warn">WARN</span>}
                    {!isWarning && <span className="badge-ok">OK</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Damping Comparison */}
      <div className="damping-section">
        <h3>Damping Ratio Changes</h3>
        <div className="damping-grid">
          {dampingDelta.map((delta, idx) => (
            <div key={idx} className="damping-item">
              <span className="label">Mode {idx + 1}</span>
              <span className={`value ${Math.abs(delta) > 0.01 ? 'changed' : ''}`}>
                {delta > 0 ? '+' : ''}{(delta * 100).toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Energy Anomaly Heatmap */}
      <div className="heatmap-section">
        <h3>Energy Anomaly Map</h3>
        <div className="heatmap-container">
          <svg viewBox="0 0 200 150" className="heatmap-svg">
            {/* Structure outline */}
            <rect x="20" y="20" width="160" height="110" fill="none" stroke="#666" strokeWidth="2" />
            
            {/* Sensor positions */}
            {sensorPositions.map(sensor => {
              const anomaly = heatmapData[`s${sensor.id + 1}`] || 0;
              const color = getAnomalyColor(anomaly);
              
              return (
                <g key={sensor.id}>
                  {/* Sensor circle */}
                  <circle
                    cx={sensor.x}
                    cy={sensor.y}
                    r="12"
                    fill={color}
                    opacity="0.8"
                  />
                  {/* Sensor label */}
                  <text
                    x={sensor.x}
                    y={sensor.y}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="white"
                    fontSize="12"
                    fontWeight="bold"
                  >
                    {sensor.name}
                  </text>
                  {/* Sensor annotation */}
                  <text
                    x={sensor.x}
                    y={sensor.y + 25}
                    textAnchor="middle"
                    fill="#ccc"
                    fontSize="10"
                  >
                    {(anomaly * 100).toFixed(0)}%
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Heatmap Legend */}
        <div className="heatmap-legend">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#10b981' }}></div>
            <span>Normal (0-20%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#f59e0b' }}></div>
            <span>Anomaly (40-60%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#dc2626' }}></div>
            <span>Critical (80-100%)</span>
          </div>
        </div>
      </div>

      {/* Sensor Details */}
      <div className="sensor-details">
        <h3>Sensor Energy Status</h3>
        <div className="details-grid">
          {sensorPositions.map(sensor => {
            const anomaly = heatmapData[`s${sensor.id + 1}`] || 0;
            const status = anomaly < 0.3 ? 'normal' : anomaly < 0.7 ? 'caution' : 'alert';
            
            return (
              <div key={sensor.id} className={`detail-card detail-${status}`}>
                <div className="detail-header">
                  <span className="sensor-name">{sensor.name}</span>
                  <span className={`status-dot status-${status}`}></span>
                </div>
                <div className="detail-info">
                  <p className="detail-label">{sensor.label}</p>
                  <p className="anomaly-score">
                    Anomaly: <strong>{(anomaly * 100).toFixed(1)}%</strong>
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

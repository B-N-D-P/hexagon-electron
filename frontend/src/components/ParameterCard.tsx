import React, { useMemo } from 'react';

interface ParameterCardProps {
  name: string;
  value: number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  category?: string;
}

const ParameterCard: React.FC<ParameterCardProps> = ({
  name,
  value,
  unit,
  trend = 'stable',
}) => {
  const statusColor = useMemo(() => {
    // Simple thresholding based on parameter type
    if (name.includes('RMS') || name.includes('Peak')) {
      if (value > 8) return '#ff4757'; // Red - danger
      if (value > 5) return '#ffaa00'; // Orange - warning
      return '#2ed573'; // Green - ok
    }
    return '#00d9ff'; // Default cyan
  }, [name, value]);

  const trendIcon = {
    up: '📈',
    down: '📉',
    stable: '→',
  }[trend];

  return (
    <div
      className="parameter-card"
      style={{
        borderLeft: `4px solid ${statusColor}`,
      }}
    >
      <div className="param-header">
        <h3>{name}</h3>
        <span className="trend-icon">{trendIcon}</span>
      </div>
      <div className="param-value">
        <span className="value-text" style={{ color: statusColor }}>
          {typeof value === 'number' ? value.toFixed(3) : value}
        </span>
        <span className="unit-text">{unit}</span>
      </div>
      <div className="param-indicator" style={{ backgroundColor: statusColor }}></div>
    </div>
  );
};

export default ParameterCard;

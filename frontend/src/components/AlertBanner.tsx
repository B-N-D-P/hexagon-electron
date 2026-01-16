import React from 'react';

interface Alert {
  id: string;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
  timestamp: string;
}

interface AlertBannerProps {
  alert: Alert;
}

const AlertBanner: React.FC<AlertBannerProps> = ({ alert }) => {
  const severityConfig = {
    success: {
      bg: 'bg-green-900',
      text: 'text-green-200',
      icon: '✓',
      border: 'border-green-500',
    },
    error: {
      bg: 'bg-red-900',
      text: 'text-red-200',
      icon: '✕',
      border: 'border-red-500',
    },
    warning: {
      bg: 'bg-yellow-900',
      text: 'text-yellow-200',
      icon: '⚠',
      border: 'border-yellow-500',
    },
    info: {
      bg: 'bg-blue-900',
      text: 'text-blue-200',
      icon: 'ℹ',
      border: 'border-blue-500',
    },
  };

  const config = severityConfig[alert.severity];

  return (
    <div
      className={`alert-banner ${config.bg} ${config.text} ${config.border} border-l-4 p-3 rounded mb-2 animate-fadeIn`}
      style={{
        animation: 'slideIn 0.3s ease-out',
      }}
    >
      <div className="flex items-center">
        <span className="mr-2 text-lg">{config.icon}</span>
        <span className="flex-1">{alert.message}</span>
        <span className="text-xs opacity-70">
          {new Date(alert.timestamp).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};

export default AlertBanner;

import React from 'react';
import { AlertTriangle, AlertCircle, X } from 'lucide-react';

export default function AlertBanner({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  return (
    <div className="alert-banner-container">
      {alerts.map((alert) => (
        <div
          key={`${alert.id}-${alert.timestamp}`}
          className={`alert-banner alert-${alert.severity}`}
        >
          <div className="alert-content">
            {alert.severity === 'warn' && <AlertCircle size={20} />}
            {alert.severity === 'alert' && <AlertTriangle size={20} />}
            <span className="alert-message">{alert.message}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

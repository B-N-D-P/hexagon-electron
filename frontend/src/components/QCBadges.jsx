import React from 'react';
import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

export default function QCBadges({ qc }) {
  if (!qc) {
    return <div className="placeholder">No QC data available</div>;
  }

  const getJitterStatus = () => {
    const jitter = qc.jitter_ms || 0;
    if (jitter < 1) return { status: 'good', label: 'Excellent' };
    if (jitter < 3) return { status: 'ok', label: 'Good' };
    if (jitter < 5) return { status: 'warn', label: 'Warning' };
    return { status: 'alert', label: 'Critical' };
  };

  const jitterStatus = getJitterStatus();
  const clippingCount = (qc.clipping || []).filter(c => c).length;
  const snrDb = qc.snr_db || 0;

  return (
    <div className="qc-badges">
      {/* Jitter Badge */}
      <div className={`badge badge-${jitterStatus.status}`}>
        <div className="badge-header">
          <span className="badge-label">Timing Jitter</span>
          {jitterStatus.status === 'good' && <CheckCircle size={18} />}
          {jitterStatus.status === 'ok' && <CheckCircle size={18} />}
          {jitterStatus.status === 'warn' && <AlertCircle size={18} />}
          {jitterStatus.status === 'alert' && <AlertTriangle size={18} />}
        </div>
        <div className="badge-value">{(qc.jitter_ms || 0).toFixed(2)} ms</div>
        <div className="badge-status">{jitterStatus.label}</div>
      </div>

      {/* Clipping Badge */}
      <div className={`badge badge-${clippingCount > 0 ? 'alert' : 'good'}`}>
        <div className="badge-header">
          <span className="badge-label">Clipping Detection</span>
          {clippingCount === 0 ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
        </div>
        <div className="badge-value">{clippingCount}/5 sensors</div>
        <div className="badge-status">
          {clippingCount === 0 ? 'No clipping' : `Clipping on ${clippingCount} sensors`}
        </div>
        {clippingCount > 0 && (
          <div className="clipping-details">
            {(qc.clipping || []).map((isClipped, idx) => (
              isClipped && (
                <span key={idx} className="clipped-sensor">S{idx + 1}</span>
              )
            ))}
          </div>
        )}
      </div>

      {/* SNR Badge */}
      <div className={`badge badge-${snrDb > 30 ? 'good' : snrDb > 20 ? 'ok' : 'warn'}`}>
        <div className="badge-header">
          <span className="badge-label">Signal-to-Noise Ratio</span>
          {snrDb > 30 && <CheckCircle size={18} />}
          {snrDb <= 30 && snrDb > 20 && <AlertCircle size={18} />}
          {snrDb <= 20 && <AlertTriangle size={18} />}
        </div>
        <div className="badge-value">{snrDb.toFixed(1)} dB</div>
        <div className="badge-status">
          {snrDb > 30 ? 'Excellent' : snrDb > 20 ? 'Good' : 'Poor'}
        </div>
      </div>

      {/* Per-Sensor RMS Indicators */}
      <div className="badge badge-info">
        <div className="badge-header">
          <span className="badge-label">Sensor Status</span>
          <CheckCircle size={18} />
        </div>
        <div className="sensor-indicators">
          {[0, 1, 2, 3, 4].map(idx => (
            <div key={idx} className="sensor-indicator">
              <span className="sensor-num">S{idx + 1}</span>
              <span className={`sensor-dot ${!qc.clipping?.[idx] ? 'active' : 'clipped'}`}></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

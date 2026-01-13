import React from 'react';
import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

/**
 * ML Anomaly Meter Component
 * 
 * Displays real-time anomaly score, confidence, and per-detector scores
 * with visual indicators and status information.
 */
export default function MLAnomalyMeter({ mlData }) {
  if (!mlData) {
    return (
      <div className="ml-meter-container">
        <div className="ml-meter-placeholder">
          <AlertCircle size={24} />
          <p>ML models not loaded</p>
          <span className="help-text">Train baseline first (Day 3-5)</span>
        </div>
      </div>
    );
  }

  const {
    anomaly_score = 0.5,
    confidence = 0.0,
    is_anomaly = false,
    if_score = 0.0,
    ae_score = 0.0,
    threshold = 0.60,
    has_autoencoder = false
  } = mlData;

  // Determine status and colors
  const getStatus = () => {
    if (!confidence || confidence < 0.5) {
      return { status: 'uncertain', label: 'Uncertain', color: '#6b7280' };
    }
    if (anomaly_score > threshold) {
      return { status: 'alert', label: 'Alert', color: '#ef4444' };
    }
    if (anomaly_score > threshold * 0.7) {
      return { status: 'warn', label: 'Warning', color: '#f59e0b' };
    }
    return { status: 'normal', label: 'Normal', color: '#10b981' };
  };

  const statusInfo = getStatus();

  // Calculate percentages
  const anomalyPercent = Math.round(anomaly_score * 100);
  const confidencePercent = Math.round(confidence * 100);
  const ifPercent = Math.round(if_score * 100);
  const aePercent = Math.round(ae_score * 100);

  // Determine if detectors agree (confidence indicator)
  const detectorDifference = Math.abs(if_score - ae_score);
  const detectorsAgree = detectorDifference < 0.2;

  return (
    <div className="ml-meter-container">
      {/* Main Anomaly Score */}
      <div className="ml-meter-main">
        <div className="ml-meter-header">
          <h3>🤖 ML Anomaly Detection</h3>
          <div className={`ml-status-badge ml-status-${statusInfo.status}`}>
            {statusInfo.status === 'normal' && <CheckCircle size={16} />}
            {statusInfo.status === 'warn' && <AlertCircle size={16} />}
            {statusInfo.status === 'alert' && <AlertTriangle size={16} />}
            {statusInfo.status === 'uncertain' && <AlertCircle size={16} />}
            {statusInfo.label}
          </div>
        </div>

        {/* Anomaly Score Gauge */}
        <div className="ml-gauge-container">
          <div className="ml-gauge-wrapper">
            <svg viewBox="0 0 200 200" className="ml-gauge-svg">
              {/* Background circle */}
              <circle cx="100" cy="100" r="90" fill="none" stroke="#374151" strokeWidth="20" />
              
              {/* Alert zone (> threshold)*/}
              <circle
                cx="100"
                cy="100"
                r="90"
                fill="none"
                stroke="#ef4444"
                strokeWidth="20"
                strokeDasharray={`${(threshold / 1) * 565} 565`}
                strokeDashoffset="0"
                opacity="0.2"
              />
              
              {/* Progress arc (current score)*/}
              <circle
                cx="100"
                cy="100"
                r="90"
                fill="none"
                stroke={statusInfo.color}
                strokeWidth="20"
                strokeDasharray={`${(anomaly_score / 1) * 565} 565`}
                strokeDashoffset="0"
                strokeLinecap="round"
                className="ml-gauge-progress"
              />

              {/* Center text */}
              <text
                x="100"
                y="95"
                textAnchor="middle"
                className="ml-gauge-value"
              >
                {anomalyPercent}%
              </text>
              <text
                x="100"
                y="115"
                textAnchor="middle"
                className="ml-gauge-label"
              >
                Score
              </text>
            </svg>
          </div>

          {/* Risk Level Text */}
          <div className="ml-risk-level">
            <span className={`ml-risk-text ml-risk-${statusInfo.status}`}>
              {anomalyPercent < 30 ? 'LOW RISK' :
               anomalyPercent < 60 ? 'MEDIUM RISK' : 'HIGH RISK'}
            </span>
            <span className="ml-threshold-info">
              Threshold: {Math.round(threshold * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* Confidence Indicator */}
      <div className="ml-confidence-section">
        <div className="ml-confidence-header">
          <span className="ml-label">Confidence</span>
          <span className={`ml-confidence-value ${confidence > 0.8 ? 'high' : confidence > 0.6 ? 'medium' : 'low'}`}>
            {confidencePercent}%
          </span>
        </div>
        <div className="ml-confidence-bar">
          <div className="ml-confidence-fill" style={{ width: `${confidence * 100}%` }}></div>
        </div>
        <p className="ml-confidence-help">
          {confidence > 0.8 ? '✓ Detectors agree strongly' :
           confidence > 0.6 ? '⚠ Moderate agreement' :
           '❓ Detectors disagree - review scores'}
        </p>
      </div>

      {/* Per-Detector Scores */}
      <div className="ml-detector-scores">
        <div className="ml-score-card">
          <div className="ml-detector-name">
            <span className="ml-detector-icon">⚡</span>
            Isolation Forest
          </div>
          <div className="ml-detector-score">
            <span className="ml-score-value">{ifPercent}%</span>
            <div className="ml-score-bar">
              <div className="ml-score-fill" style={{ width: `${if_score * 100}%`, backgroundColor: '#3b82f6' }}></div>
            </div>
          </div>
          <p className="ml-detector-note">Fast statistical detection</p>
        </div>

        {has_autoencoder && (
          <div className="ml-score-card">
            <div className="ml-detector-name">
              <span className="ml-detector-icon">🧠</span>
              Autoencoder
            </div>
            <div className="ml-detector-score">
              <span className="ml-score-value">{aePercent}%</span>
              <div className="ml-score-bar">
                <div className="ml-score-fill" style={{ width: `${ae_score * 100}%`, backgroundColor: '#8b5cf6' }}></div>
              </div>
            </div>
            <p className="ml-detector-note">Deep learning reconstruction</p>
          </div>
        )}

        {!has_autoencoder && (
          <div className="ml-score-card ml-disabled">
            <div className="ml-detector-name">
              <span className="ml-detector-icon">🧠</span>
              Autoencoder
            </div>
            <p className="ml-detector-disabled">TensorFlow not available</p>
          </div>
        )}
      </div>

      {/* Detector Agreement Indicator */}
      <div className={`ml-agreement-indicator ${detectorsAgree ? 'agree' : 'disagree'}`}>
        <div className="ml-agreement-icon">
          {detectorsAgree ? '✓' : '⚠'}
        </div>
        <div className="ml-agreement-text">
          <span className="ml-agreement-label">
            {detectorsAgree ? 'Detectors Agree' : 'Detectors Disagree'}
          </span>
          <span className="ml-agreement-detail">
            Difference: {(detectorDifference * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Alert Status */}
      {is_anomaly && (
        <div className="ml-alert-banner ml-alert-active">
          <AlertTriangle size={20} />
          <span>Anomaly Detected - Review structure immediately</span>
        </div>
      )}

      {/* Info Section */}
      <div className="ml-info-section">
        <details>
          <summary>How it works</summary>
          <div className="ml-info-content">
            <p>
              <strong>Anomaly Score</strong>: Ensemble of Isolation Forest (fast statistical) 
              and Autoencoder (deep learning). Range [0-1], higher = more anomalous.
            </p>
            <p>
              <strong>Confidence</strong>: How certain the system is. High confidence when both 
              detectors agree. Low confidence when they disagree.
            </p>
            <p>
              <strong>Threshold</strong>: Score above {(threshold * 100).toFixed(0)}% triggers alert. 
              Configure in training phase.
            </p>
            <p>
              <strong>Isolation Forest</strong>: Fast statistical outlier detection. 
              Responds instantly to new patterns.
            </p>
            <p>
              <strong>Autoencoder</strong>: Deep learning model. Learns what "normal" looks like. 
              High reconstruction error = anomaly.
            </p>
          </div>
        </details>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import '../styles/ControlPanel.css';

interface ControlPanelProps {
  isRecording: boolean;
  serverStatus: any;
  onStartRecording: () => void;
  onStopRecording: () => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  isRecording,
  serverStatus,
  onStartRecording,
  onStopRecording,
}) => {
  const [recordingTime, setRecordingTime] = useState(0);

  React.useEffect(() => {
    if (!isRecording) {
      setRecordingTime(0);
      return;
    }

    const interval = setInterval(() => {
      setRecordingTime((prev) => {
        if (prev >= 30) {
          onStopRecording();
          return 0;
        }
        return prev + 0.1;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isRecording, onStopRecording]);

  const formatTime = (seconds: number) => {
    return `${seconds.toFixed(1)}s / 30.0s`;
  };

  const progress = (recordingTime / 30) * 100;

  return (
    <div className="control-panel">
      <div className="control-section">
        <div className="button-group">
          {!isRecording ? (
            <button
              className="btn btn-start"
              onClick={onStartRecording}
              disabled={!serverStatus?.serial?.connection_status === 'connected'}
            >
              ▶ START RECORDING
            </button>
          ) : (
            <button className="btn btn-stop" onClick={onStopRecording}>
              ⏹ STOP RECORDING
            </button>
          )}

          <button className="btn btn-export">
            📥 EXPORT DATA
          </button>

          <button className="btn btn-settings">
            ⚙️ SETTINGS
          </button>
        </div>
      </div>

      <div className="status-section">
        {isRecording && (
          <div className="recording-info">
            <div className="recording-indicator">
              <span className="pulsing-dot"></span>
              RECORDING
            </div>
            <div className="recording-timer">
              <span className="time">{formatTime(recordingTime)}</span>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
            </div>
          </div>
        )}

        <div className="status-info">
          <span className="status-item">
            🔌 {serverStatus?.serial?.port || 'No port'}
          </span>
          <span className="status-item">
            📡 {serverStatus?.serial?.samples_per_second || 0}Hz
          </span>
          <span className="status-item">
            🔋 {serverStatus?.serial?.connection_status === 'connected' ? '✓' : '✗'} Connected
          </span>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;

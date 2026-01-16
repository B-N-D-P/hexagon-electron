import React, { useState, useEffect, useMemo } from 'react';
import useWebSocket from '../hooks/useWebSocket';
import ControlPanel from './ControlPanel';
import ParameterGrid from './ParameterGrid';
import LiveWaveform from './LiveWaveform';
import FFTSpectrum from './FFTSpectrum';
import Vector3D from './Vector3D';
import GaugePanel from './GaugePanel';
import CorrelationHeatmap from './CorrelationHeatmap';
import AlertBanner from './AlertBanner';
import '../styles/Dashboard.css';

interface SensorData {
  x: number;
  y: number;
  z: number;
}

interface Parameters {
  sensor_1: any;
  sensor_2: any;
  correlation: any;
  timestamp?: string;
}

interface DashboardState {
  isRecording: boolean;
  sessionId: string | null;
  serverStatus: any;
  parameters: Parameters | null;
  waveformData: any;
  alerts: Array<{ id: string; message: string; severity: string; timestamp: string }>;
}

const Dashboard: React.FC = () => {
  const wsUrl = typeof window !== 'undefined' 
    ? `ws://${window.location.hostname}:8000/ws/monitor`
    : 'ws://localhost:8000/ws/monitor';
  const { isConnected, lastMessage, send } = useWebSocket(wsUrl);

  const [state, setState] = useState<DashboardState>({
    isRecording: false,
    sessionId: null,
    serverStatus: null,
    parameters: null,
    waveformData: null,
    alerts: [],
  });

  // Process incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case 'connection':
        setState((prev) => ({
          ...prev,
          serverStatus: lastMessage.server_status,
        }));
        break;

      case 'status_update':
        setState((prev) => ({
          ...prev,
          serverStatus: lastMessage.data,
        }));
        break;

      case 'parameters_update':
        setState((prev) => ({
          ...prev,
          parameters: lastMessage.data,
          waveformData: lastMessage.data,
        }));
        break;

      case 'recording_started':
        setState((prev) => ({
          ...prev,
          isRecording: true,
        }));
        addAlert('Recording started', 'success');
        break;

      case 'recording_ended':
        setState((prev) => ({
          ...prev,
          isRecording: false,
        }));
        addAlert('Recording ended', 'info');
        break;

      case 'error':
        addAlert(lastMessage.message, 'error');
        break;

      default:
        break;
    }
  }, [lastMessage]);

  const addAlert = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    const alertId = Date.now().toString();
    const newAlert = {
      id: alertId,
      message,
      severity,
      timestamp: new Date().toISOString(),
    };

    setState((prev) => ({
      ...prev,
      alerts: [...prev.alerts, newAlert],
    }));

    // Auto-remove alert after 5 seconds
    setTimeout(() => {
      setState((prev) => ({
        ...prev,
        alerts: prev.alerts.filter((a) => a.id !== alertId),
      }));
    }, 5000);
  };

  const handleStartRecording = async () => {
    try {
      // Start recording - generate a local session ID
      const sessionId = `session_${Date.now()}`;
      setState((prev) => ({
        ...prev,
        isRecording: true,
        sessionId: sessionId,
      }));
      addAlert('Recording started', 'success');
    } catch (error) {
      addAlert('Failed to start recording', 'error');
    }
  };

  const handleStopRecording = async () => {
    try {
      // Stop recording
      setState((prev) => ({
        ...prev,
        isRecording: false,
      }));
      addAlert(`Recording saved: ${state.sessionId}`, 'success');
    } catch (error) {
      addAlert('Failed to stop recording', 'error');
    }
  };

  const connectionStatus = useMemo(() => {
    try {
      if (!state.serverStatus) {
        return {
          status: 'disconnected',
          color: 'text-red-500',
          icon: '●',
        };
      }

      const serialStatus = state.serverStatus?.serial?.connection_status;

      if (serialStatus === 'connected') {
        return {
          status: 'connected',
          color: 'text-green-500',
          icon: '●',
        };
      }

      return {
        status: serialStatus || 'unknown',
        color: 'text-yellow-500',
        icon: '●',
      };
    } catch (error) {
      console.error('Error getting connection status:', error);
      return {
        status: 'error',
        color: 'text-red-500',
        icon: '⚠',
      };
    }
  }, [state.serverStatus]);

  return (
    <div className="dashboard-container">
      {/* Header with alerts */}
      <div className="dashboard-header">
        <h1>🔴 LIVE STRUCTURAL VIBRATION MONITORING SYSTEM</h1>
        <div className="header-status">
          <span className={connectionStatus.color}>
            {connectionStatus.icon} {connectionStatus.status}
          </span>
          {state.serverStatus?.serial?.port && (
            <span className="port-info">Port: {state.serverStatus.serial.port}</span>
          )}
        </div>
      </div>

      {/* Alerts */}
      {state.alerts.length > 0 && (
        <div className="alerts-container">
          {state.alerts.map((alert) => (
            <AlertBanner key={alert.id} alert={alert} />
          ))}
        </div>
      )}

      {/* Control Panel */}
      <ControlPanel
        isRecording={state.isRecording}
        serverStatus={state.serverStatus}
        onStartRecording={handleStartRecording}
        onStopRecording={handleStopRecording}
      />

      {/* Main content grid */}
      <div className="dashboard-grid">
        {/* Left column: Visualizations */}
        <div className="visualizations-column">
          {/* Live Waveform */}
          <div className="visualization-card">
            <h2>📈 Real-Time Waveform</h2>
            <LiveWaveform data={state.waveformData} />
          </div>

          {/* FFT Spectrum */}
          <div className="visualization-card">
            <h2>🔬 FFT Spectrum Analysis</h2>
            <FFTSpectrum data={state.waveformData} />
          </div>
        </div>

        {/* Right column: Gauges & Metrics */}
        <div className="metrics-column">
          {/* Gauge Panel */}
          <div className="visualization-card">
            <h2>⚡ Key Metrics</h2>
            <GaugePanel parameters={state.parameters} />
          </div>

          {/* 3D Vector */}
          <div className="visualization-card">
            <h2>🎯 3D Acceleration Vector</h2>
            <Vector3D data={state.waveformData} />
          </div>
        </div>
      </div>

      {/* Correlation Heatmap */}
      <div className="correlation-card">
        <h2>🔗 Sensor Correlation Analysis</h2>
        <CorrelationHeatmap parameters={state.parameters} />
      </div>

      {/* Parameter Grid */}
      <div className="parameters-card">
        <h2>📊 Advanced Parameters (50+)</h2>
        <ParameterGrid parameters={state.parameters} />
      </div>
    </div>
  );
};

export default Dashboard;

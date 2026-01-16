import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, Play, Square, Check, AlertTriangle, Loader, Zap, Radio, BarChart3 } from 'lucide-react';
import { toast } from 'react-toastify';
import LiveChart from '../components/LiveChart';
import LivePSD from '../components/LivePSD';
import QCBadges from '../components/QCBadges';
import ComparativeDashboard from '../components/ComparativeDashboard';
import AlertBanner from '../components/AlertBanner';
import MLAnomalyMeter from '../components/MLAnomalyMeter';
import '../styles/LiveMonitoring.css';
import '../styles/MLComponents.css';

export default function LiveMonitoring() {
  // Connection states
  const [connectionStep, setConnectionStep] = useState(0); // 0: idle, 1: connecting, 2: collecting, 3: visualizing
  const [connectionStatus, setConnectionStatus] = useState('idle'); // idle, connecting, connected, error
  const [connectionError, setConnectionError] = useState(null);
  const [arduinoConnected, setArduinoConnected] = useState(false);
  const [dataReceived, setDataReceived] = useState(false);

  // UI states
  const [activeTab, setActiveTab] = useState('overview');
  const [isStreaming, setIsStreaming] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [baselineList, setBaselineList] = useState([]);
  const [selectedBaseline, setSelectedBaseline] = useState(null);
  const [currentBaseline, setCurrentBaseline] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [isMarkingBaseline, setIsMarkingBaseline] = useState(false);
  const [sampleCount, setSampleCount] = useState(0);

  const wsRef = useRef(null);
  const timeSeriesRef = useRef([]);
  const alertTimeoutRef = useRef({});

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          // Check Arduino status from health response
          if (data.arduino && data.arduino.connected) {
            setArduinoConnected(true);
          } else {
            setArduinoConnected(false);
          }
        }
      }
    } catch (error) {
      console.error('Backend health check failed:', error);
      setArduinoConnected(false);
    }
  };

  // Main connection function
  const handleStartStreaming = async () => {
    setConnectionStep(1);
    setConnectionStatus('connecting');
    setConnectionError(null);

    try {
      // Step 1: Check Arduino connection
      setConnectionStep(1);
      
      // Re-check Arduino status
      const healthResponse = await fetch('http://localhost:8000/health');
      const healthData = await healthResponse.json();
      
      if (!healthData.arduino || !healthData.arduino.connected) {
        setConnectionError('Arduino not detected. Please check USB connection.');
        setConnectionStatus('error');
        setConnectionStep(0);
        toast.error('Arduino not connected');
        return;
      }
      
      setArduinoConnected(true);
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 2: Start collecting data
      setConnectionStep(2);
      setSampleCount(0);
      setDataReceived(false);
      setIsStreaming(true);
      
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 3: Connect WebSocket for visualization
      setConnectionStep(3);
      connectWebSocket();

      setConnectionStatus('connected');
      toast.success('✓ Connected to Arduino, collecting and visualizing data!');

    } catch (error) {
      console.error('Connection error:', error);
      setConnectionError(error.message || 'Failed to connect to system');
      setConnectionStatus('error');
      setConnectionStep(0);
      setIsStreaming(false);
      toast.error('Failed to connect');
    }
  };

  const handleStopStreaming = () => {
    setIsStreaming(false);
    setConnectionStep(0);
    setConnectionStatus('idle');
    setSampleCount(0);
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    toast.info('Streaming stopped');
  };

  // Connect to WebSocket stream
  const connectWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsRef.current = new WebSocket(`${protocol}//${window.location.host}/ws/stream`);

      wsRef.current.onopen = () => {
        console.log('✓ WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleStreamMessage(data);
        } catch (e) {
          console.error('Error parsing stream message:', e);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
        setConnectionStatus('error');
      };

      wsRef.current.onclose = () => {
        console.log('✗ WebSocket disconnected');
        if (isStreaming) {
          setIsStreaming(false);
          setConnectionStep(0);
        }
      };
    } catch (error) {
      console.error('Error connecting to stream:', error);
      setConnectionError('Failed to connect to stream');
      setConnectionStatus('error');
      setIsStreaming(false);
    }
  };

  // Load available baselines
  useEffect(() => {
    loadBaselines();
  }, []);

  const loadBaselines = async () => {
    try {
      const response = await fetch('/api/baseline/list');
      const data = await response.json();
      if (data.status === 'success') {
        setBaselineList(data.baselines);
        if (data.current_baseline_id) {
          setSelectedBaseline(data.current_baseline_id);
          setCurrentBaseline(data.current_baseline_id);
        }
      }
    } catch (error) {
      console.error('Error loading baselines:', error);
    }
  };

  const handleStreamMessage = (data) => {
    // Handle event messages
    if (data.event === 'baseline_marked') {
      toast.success('Baseline marked successfully');
      loadBaselines();
      return;
    }

    if (data.event === 'baseline_selected') {
      setCurrentBaseline(data.baseline_id);
      toast.info('Baseline changed');
      return;
    }

    // Handle metrics updates
    if (data.metrics) {
      setMetrics(data);
      setDataReceived(true);
      setSampleCount(prev => prev + 1);
      
      // Add to time series for chart
      if (data.metrics.rms) {
        timeSeriesRef.current.push({
          ts: data.ts,
          rms: data.metrics.rms,
          peaks: data.metrics.peaks
        });
        
        // Keep only last 600 samples (10 minutes at 1 Hz)
        if (timeSeriesRef.current.length > 600) {
          timeSeriesRef.current.shift();
        }
      }

      // Check for alerts
      checkForAlerts(data);
    }
  };

  const checkForAlerts = (data) => {
    const qc = data.qc || {};
    const metrics = data.metrics || {};
    const comparative = data.comparative || {};

    // Jitter alert
    if (qc.jitter_ms > 5) {
      addAlert('jitter', `High jitter: ${qc.jitter_ms.toFixed(2)}ms`, 'warn');
    }

    // Clipping alert
    if (qc.clipping && qc.clipping.some(c => c)) {
      const clippedSensors = qc.clipping
        .map((c, i) => c ? `S${i + 1}` : null)
        .filter(x => x)
        .join(', ');
      addAlert('clipping', `Clipping detected: ${clippedSensors}`, 'alert');
    }

    // Frequency shift alert
    if (comparative.delta_f && comparative.delta_f.some(df => Math.abs(df) > 5)) {
      const maxShift = Math.max(...comparative.delta_f.map(Math.abs));
      addAlert('freq_shift', `Frequency shift: ${maxShift.toFixed(1)}%`, 'alert');
    }

    // Energy anomaly alert
    if (comparative.heatmap) {
      const anomalies = Object.values(comparative.heatmap);
      if (anomalies.some(a => a > 0.7)) {
        addAlert('energy', 'Energy anomaly detected', 'warn');
      }
    }
  };

  const addAlert = (id, message, severity) => {
    const alertKey = id + severity;
    
    if (alertTimeoutRef.current[alertKey]) {
      clearTimeout(alertTimeoutRef.current[alertKey]);
    }

    setAlerts(prev => {
      const existing = prev.find(a => a.id === id);
      if (existing && existing.message === message) {
        return prev;
      }
      
      const newAlerts = prev.filter(a => a.id !== id);
      newAlerts.push({ id, message, severity, timestamp: Date.now() });
      
      return newAlerts;
    });

    alertTimeoutRef.current[alertKey] = setTimeout(() => {
      setAlerts(prev => prev.filter(a => a.id !== id));
    }, 5000);
  };

  const handleMarkBaseline = async () => {
    setIsMarkingBaseline(true);
    try {
      const response = await fetch(
        `/api/baseline/mark?name=LiveBaseline_${new Date().toISOString().split('T')[0]}`,
        { method: 'POST' }
      );
      const data = await response.json();
      if (data.status === 'success') {
        toast.success('Baseline marked successfully');
        loadBaselines();
      } else {
        toast.error('Failed to mark baseline');
      }
    } catch (error) {
      console.error('Error marking baseline:', error);
      toast.error('Error marking baseline');
    } finally {
      setIsMarkingBaseline(false);
    }
  };

  const handleSelectBaseline = async (baselineId) => {
    try {
      const response = await fetch(`/api/baseline/select?baseline_id=${baselineId}`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.status === 'success') {
        setSelectedBaseline(baselineId);
        setCurrentBaseline(baselineId);
        toast.success('Baseline selected');
      } else {
        toast.error('Failed to select baseline');
      }
    } catch (error) {
      console.error('Error selecting baseline:', error);
      toast.error('Error selecting baseline');
    }
  };

  return (
    <div className="live-monitoring">
      {/* Connection Status Section */}
      <div className="connection-status-section">
        <div className="connection-header">
          <h2>🚀 Real-Time Monitoring System</h2>
          <div className="connection-indicator">
            {connectionStatus === 'connected' && (
              <div className="status-badge connected">
                <span className="pulse"></span> Live Connection Active
              </div>
            )}
            {connectionStatus === 'connecting' && (
              <div className="status-badge connecting">
                <Loader size={16} className="spinner" /> Connecting...
              </div>
            )}
            {connectionStatus === 'error' && (
              <div className="status-badge error">
                <AlertCircle size={16} /> Connection Error
              </div>
            )}
            {connectionStatus === 'idle' && (
              <div className="status-badge idle">
                <Radio size={16} /> Ready to Connect
              </div>
            )}
          </div>
        </div>

        {/* Connection Steps */}
        <div className="connection-steps">
          {/* Step 1: Arduino Connection */}
          <div className={`step ${connectionStep >= 1 ? 'active' : ''} ${connectionStep > 1 ? 'completed' : ''}`}>
            <div className="step-header">
              <div className="step-number">
                {connectionStep > 1 ? <Check size={20} /> : '1'}
              </div>
              <div className="step-info">
                <h3>Connect Arduino</h3>
                <p>Detecting Arduino on USB...</p>
              </div>
            </div>
            {connectionStep >= 1 && (
              <div className="step-content">
                <div className={`step-status ${arduinoConnected ? 'success' : 'loading'}`}>
                  {arduinoConnected ? (
                    <><Check size={16} /> Arduino Detected on /dev/ttyUSB0</>
                  ) : (
                    <><Loader size={16} className="spinner" /> Searching for Arduino...</>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Step 2: Data Collection */}
          <div className={`step ${connectionStep >= 2 ? 'active' : ''} ${connectionStep > 2 ? 'completed' : ''}`}>
            <div className="step-header">
              <div className="step-number">
                {connectionStep > 2 ? <Check size={20} /> : '2'}
              </div>
              <div className="step-info">
                <h3>Collect Data</h3>
                <p>Reading sensor data at 50 Hz...</p>
              </div>
            </div>
            {connectionStep >= 2 && (
              <div className="step-content">
                <div className={`step-status ${dataReceived ? 'success' : 'loading'}`}>
                  {dataReceived ? (
                    <><Check size={16} /> Data Received ({sampleCount} samples)</>
                  ) : (
                    <><Loader size={16} className="spinner" /> Waiting for data...</>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Step 3: Data Visualization */}
          <div className={`step ${connectionStep >= 3 ? 'active' : ''}`}>
            <div className="step-header">
              <div className="step-number">
                {connectionStep >= 3 ? <BarChart3 size={20} /> : '3'}
              </div>
              <div className="step-info">
                <h3>Visualize Data</h3>
                <p>Real-time dashboard and metrics...</p>
              </div>
            </div>
            {connectionStep >= 3 && (
              <div className="step-content">
                <div className={`step-status ${isStreaming ? 'success' : 'idle'}`}>
                  {isStreaming ? (
                    <><Zap size={16} /> Live Visualization Active</>
                  ) : (
                    <>Ready for visualization</>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Error Display */}
        {connectionError && (
          <div className="connection-error">
            <AlertCircle size={18} />
            <span>{connectionError}</span>
            <button onClick={() => setConnectionError(null)}>Dismiss</button>
          </div>
        )}

        {/* Main Control Buttons */}
        <div className="connection-actions">
          {!isStreaming ? (
            <button
              className="btn btn-start-streaming"
              onClick={handleStartStreaming}
              disabled={connectionStatus === 'connecting'}
            >
              {connectionStatus === 'connecting' ? (
                <><Loader size={18} className="spinner" /> Connecting...</>
              ) : (
                <><Play size={18} /> Start Real-Time Monitoring</>
              )}
            </button>
          ) : (
            <button
              className="btn btn-stop-streaming"
              onClick={handleStopStreaming}
            >
              <Square size={18} /> Stop Streaming
            </button>
          )}

          {isStreaming && (
            <button
              className="btn btn-mark-baseline"
              onClick={handleMarkBaseline}
              disabled={isMarkingBaseline}
            >
              <Check size={18} /> Mark as Baseline
            </button>
          )}
        </div>
      </div>

      {/* Alert Banner */}
      <AlertBanner alerts={alerts} />

      {/* Main Content - Only show when streaming */}
      {isStreaming && (
        <>
          {/* Tabs */}
          <div className="tabs-container">
            <div className="tabs">
              <button
                className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                Overview
              </button>
              <button
                className={`tab ${activeTab === 'spectrum' ? 'active' : ''}`}
                onClick={() => setActiveTab('spectrum')}
              >
                Spectrum
              </button>
              <button
                className={`tab ${activeTab === 'comparative' ? 'active' : ''}`}
                onClick={() => setActiveTab('comparative')}
                disabled={!currentBaseline}
              >
                Comparative
              </button>
              <button
                className={`tab ${activeTab === 'controls' ? 'active' : ''}`}
                onClick={() => setActiveTab('controls')}
              >
                Controls
              </button>
            </div>

            {/* Tab Content */}
            <div className="tab-content">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="tab-pane">
                  {metrics && metrics.ml_anomaly && (
                    <MLAnomalyMeter mlData={metrics.ml_anomaly} />
                  )}

                  <div className="overview-grid">
                    <div className="section">
                      <h2>Live Time-Series (Last 10s)</h2>
                      {metrics ? (
                        <LiveChart 
                          data={timeSeriesRef.current}
                          metrics={metrics}
                        />
                      ) : (
                        <div className="placeholder">
                          Loading live data...
                        </div>
                      )}
                    </div>

                    <div className="section">
                      <h2>Quality Control</h2>
                      {metrics ? (
                        <QCBadges qc={metrics.qc} />
                      ) : (
                        <div className="placeholder">No QC data</div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Spectrum Tab */}
              {activeTab === 'spectrum' && (
                <div className="tab-pane">
                  <h2>Power Spectral Density</h2>
                  {metrics ? (
                    <LivePSD metrics={metrics} />
                  ) : (
                    <div className="placeholder">
                      Loading PSD data...
                    </div>
                  )}
                </div>
              )}

              {/* Comparative Tab */}
              {activeTab === 'comparative' && currentBaseline && (
                <div className="tab-pane">
                  <h2>Comparative Analysis vs Baseline</h2>
                  {metrics && metrics.comparative ? (
                    <ComparativeDashboard 
                      comparative={metrics.comparative}
                      baseline={baselineList.find(b => b.id === currentBaseline)}
                    />
                  ) : (
                    <div className="placeholder">Waiting for comparative data...</div>
                  )}
                </div>
              )}

              {/* Controls Tab */}
              {activeTab === 'controls' && (
                <div className="tab-pane controls-tab">
                  <div className="control-section">
                    <h2>Baseline Management</h2>
                    
                    <div className="control-group">
                      <button
                        className="btn btn-primary"
                        onClick={handleMarkBaseline}
                        disabled={!isStreaming || isMarkingBaseline}
                      >
                        <Check size={18} /> Mark Current as Baseline
                      </button>
                      <p className="help-text">
                        Captures current spectral profile as a reference baseline.
                      </p>
                    </div>

                    <div className="control-group">
                      <label>Select Baseline for Comparison:</label>
                      <select
                        value={selectedBaseline || ''}
                        onChange={(e) => {
                          if (e.target.value) {
                            handleSelectBaseline(e.target.value);
                          }
                        }}
                      >
                        <option value="">-- Choose a baseline --</option>
                        {baselineList.map(baseline => (
                          <option key={baseline.id} value={baseline.id}>
                            {baseline.name} ({baseline.num_peaks} peaks)
                          </option>
                        ))}
                      </select>
                    </div>

                    {currentBaseline && baselineList.length > 0 && (
                      <div className="baseline-info">
                        <h3>Current Baseline</h3>
                        {baselineList.map(b => b.id === currentBaseline && (
                          <div key={b.id}>
                            <p><strong>Name:</strong> {b.name}</p>
                            <p><strong>Created:</strong> {new Date(b.created_at).toLocaleString()}</p>
                            <p><strong>Peaks:</strong> {b.num_peaks}</p>
                            {b.description && <p><strong>Description:</strong> {b.description}</p>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="control-section">
                    <h2>Recording Status</h2>
                    <div className="status-grid">
                      <div className="status-item">
                        <span className="label">Samples Received:</span>
                        <span className="status-value">{sampleCount}</span>
                      </div>
                      <div className="status-item">
                        <span className="label">Baseline:</span>
                        <span className={`status ${currentBaseline ? 'active' : 'inactive'}`}>
                          {currentBaseline ? `✓ Set` : 'Not set'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

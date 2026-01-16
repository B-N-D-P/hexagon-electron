import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, Play, Square, Check, AlertTriangle } from 'lucide-react';
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
  const [activeTab, setActiveTab] = useState('overview');
  const [isStreaming, setIsStreaming] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [baselineList, setBaselineList] = useState([]);
  const [selectedBaseline, setSelectedBaseline] = useState(null);
  const [currentBaseline, setCurrentBaseline] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [isMarkingBaseline, setIsMarkingBaseline] = useState(false);
  
  const wsRef = useRef(null);
  const timeSeriesRef = useRef([]);
  const alertTimeoutRef = useRef({});

  // Connect to WebSocket stream
  useEffect(() => {
    if (!isStreaming) return;

    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsRef.current = new WebSocket(`${protocol}//${window.location.host}/ws/stream`);

        wsRef.current.onopen = () => {
          console.log('✓ Connected to stream');
          toast.success('Connected to live stream');
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
          toast.error('Stream connection error');
        };

        wsRef.current.onclose = () => {
          console.log('✗ Stream disconnected');
          setIsStreaming(false);
        };
      } catch (error) {
        console.error('Error connecting to stream:', error);
        toast.error('Failed to connect to stream');
        setIsStreaming(false);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isStreaming]);

  // Load available baselines on mount
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
    // Debounce alerts to avoid spam
    const alertKey = id + severity;
    
    if (alertTimeoutRef.current[alertKey]) {
      clearTimeout(alertTimeoutRef.current[alertKey]);
    }

    setAlerts(prev => {
      const existing = prev.find(a => a.id === id);
      if (existing && existing.message === message) {
        return prev; // Don't add duplicate
      }
      
      const newAlerts = prev.filter(a => a.id !== id);
      newAlerts.push({ id, message, severity, timestamp: Date.now() });
      
      return newAlerts;
    });

    // Auto-dismiss after 5 seconds
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
      <div className="live-header">
        <h1>📡 Real-Time Monitoring</h1>
        
        <div className="live-controls">
          <button
            className={`btn btn-large ${isStreaming ? 'btn-danger' : 'btn-primary'}`}
            onClick={() => setIsStreaming(!isStreaming)}
          >
            {isStreaming ? (
              <>
                <Square size={18} /> Stop Streaming
              </>
            ) : (
              <>
                <Play size={18} /> Start Streaming
              </>
            )}
          </button>

          {isStreaming && (
            <button
              className="btn btn-secondary"
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
              {/* ML Anomaly Detection Section */}
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
                      {isStreaming ? 'Waiting for data...' : 'Start streaming to see data'}
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
                  {isStreaming ? 'Waiting for PSD data...' : 'Start streaming to see PSD'}
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
                <h2>Incident Capture</h2>
                <div className="control-group">
                  <button 
                    className="btn btn-secondary"
                    disabled={!isStreaming}
                  >
                    📸 Capture Incident Window (10s pre/post)
                  </button>
                  <p className="help-text">
                    Captures 10 seconds before and after this moment with auto-generated summary.
                  </p>
                </div>
              </div>

              <div className="control-section">
                <h2>Recording Status</h2>
                <div className="status-grid">
                  <div className="status-item">
                    <span className="label">Streaming:</span>
                    <span className={`status ${isStreaming ? 'active' : 'inactive'}`}>
                      {isStreaming ? '🟢 Active' : '🔴 Inactive'}
                    </span>
                  </div>
                  <div className="status-item">
                    <span className="label">Baseline:</span>
                    <span className={`status ${currentBaseline ? 'active' : 'inactive'}`}>
                      {currentBaseline ? `✓ Set (${baselineList.find(b => b.id === currentBaseline)?.name})` : 'Not set'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

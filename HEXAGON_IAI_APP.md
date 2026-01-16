# HEXAGON IAI APP — Structural Repair Quality Analysis Platform and Real‑Time Vibration Monitoring System

## Abstract
This document is a complete, academically structured, mathematically rigorous technical report for a software system that performs (i) offline structural repair quality assessment from vibration time-series datasets and (ii) real-time vibration monitoring with baseline comparison and machine-learning (ML) assisted anomaly detection. The backend is implemented in Python using FastAPI and provides REST and WebSocket interfaces for upload, asynchronous analysis, report generation (PDF/HTML), live streaming metrics, and baseline management. The frontend is implemented in React (Vite) and provides dashboards for offline analysis review, live monitoring, and an additional serial-connected monitoring interface.

A critical traceability limitation exists: offline modal extraction and repair-quality scoring are invoked through an external dependency (`python123.repair_analyzer`) that is **not present in this repository**. This report therefore documents those portions strictly from the repository-visible interfaces and downstream usage, and marks missing implementations as limitations.

## Keywords
Structural health monitoring (SHM); vibration analysis; FastAPI; WebSocket streaming; Welch PSD; FFT; feature extraction; damping; baseline comparison; anomaly detection; Isolation Forest; Autoencoder; correlation; coherence; nonlinear time-series analysis.

---

## 1. Introduction
Structural repair verification and structural health monitoring (SHM) rely on the principle that damage and repair alter a structure’s dynamic response. In a linearized structural dynamics viewpoint, damage typically reduces effective stiffness and increases damping, shifting modal frequencies and changing mode shapes. Repair should restore these properties toward a baseline.

This project operationalizes those ideas via two complementary workflows:

1. **Offline repair-quality analysis**: users upload vibration datasets (baseline/original, damaged, repaired), trigger an asynchronous analysis pipeline, and obtain computed metrics and reports.
2. **Real-time monitoring**: live sensor frames are ingested via WebSocket, buffered, transformed into rolling spectral/statistical metrics, compared against a selectable baseline, and published to a dashboard.
3. **Serial-connected monitoring dashboard**: a separate subsystem ingests two 3-axis accelerometers over serial, computes 50+ parameters per update, and broadcasts them to a dedicated dashboard.

The report is self-contained: every computation implemented in the repository is presented with explicit symbol definitions, equations in LaTeX, numerical stability considerations, and computational complexity. Where the code references missing external modules, the report explicitly states what cannot be verified.

---

## 2. System Overview

### 2.1 System function from first principles
Let \(x_{s,a}[n]\) denote the discrete-time acceleration signal from sensor \(s\) and axis \(a\in\{x,y,z\}\), sampled at frequency \(f_s\) (Hz). The system computes a set of functions

\[
\mathbf{y} = \mathcal{A}(\{x_{s,a}[n]\}; \Theta),
\]

where \(\mathbf{y}\) includes features, spectra, comparative metrics, and report artifacts, and \(\Theta\) includes parameters such as window length, overlap, peak thresholds, and ML thresholds.

Repository-verified outputs include:
- rolling PSD \(\hat P_s(f)\) (Welch estimator)
- peak frequencies \(\{f_i\}\)
- RMS and simple QC metrics
- baseline-derived deltas and quality score
- ML anomaly score (hybrid detector)
- offline charts and PDF/HTML report generation based on provided analysis results

Offline modal identification and repair quality scoring are initiated but implemented outside this repository.

### 2.2 Repository layout (analyzed scope)
**Backend (`backend/`)**:
- `app.py`: primary FastAPI app (REST + `/ws/ingest` + `/ws/stream` + baseline endpoints).
- `services/live_buffer.py`: live buffering, Welch PSD, peaks, QC, baseline comparison, ML anomaly.
- `services/baseline_manager.py`: baseline persistence and selection.
- `services/data_adapters.py`: CSV format adapters → arrays.
- `services/damage_localizer.py`: physics + optional ML damage localization.
- `parameter_calculator.py`: 50+ parameters for serial monitoring.
- `realtime_monitor.py`, `serial_handler.py`: serial ingest + `/ws/monitor`.
- `ml_models/anomaly_detector.py`, `ml_models/feature_extractor.py`, `ml_models/model_manager.py`: ML feature extraction and model lifecycle.
- `enhanced_pdf_generator.py`, `enhanced_report_generator.py`: report generation.

**Frontend (`frontend/`)**:
- `src/pages/Upload.jsx`: upload + analysis trigger.
- `src/pages/Dashboard.jsx`: offline results visualization + downloads.
- `src/pages/LiveMonitoring.jsx`: live monitoring dashboard for `/ws/stream`.
- `src/components/Dashboard.tsx`: serial-monitor dashboard for `/ws/monitor`.
- `src/hooks/useWebSocket.ts`: resilient WS client.
- `src/services/api.js`: REST client.

---

## 3. Architectural Design

### 3.1 Backend Architecture

#### 3.1.1 Primary FastAPI application (`backend/app.py`)
**Responsibility**: orchestrate offline analysis and live monitoring.

**Key interfaces**:
- REST: `/api/v1/upload`, `/api/v1/analyze`, `/api/v1/results/{analysis_id}`, report downloads.
- WebSockets: `/ws/ingest` (authenticated ingest), `/ws/stream` (broadcast metrics).
- Baselines: `/api/baseline/mark`, `/api/baseline/list`, `/api/baseline/select`.

**State and storage model**:
- Uploads persisted to `backend/uploads/`.
- Outputs persisted to `backend/outputs/`.
- Analysis metadata/results stored in in-memory dicts (`uploaded_files`, `analysis_results`).

**Concurrency model**:
- Offline analyses run via FastAPI `BackgroundTasks`.
- Live metrics are published by an asyncio task (`metrics_publisher`) at `METRICS_UPDATE_RATE_HZ = 1`.
- Connected `/ws/stream` clients are tracked in a thread-safe set guarded by `stream_lock`.

#### 3.1.2 Live analysis engine (`backend/services/live_buffer.py`)
`LiveAnalysisEngine` is the real-time computation core. It owns:
- per-sensor circular buffers (`LiveSensorBuffer`)
- PSD analyzer (`RollingPSDAnalyzer`)
- peak tracker (`PeakTracker`)
- comparative engine (`ComparativeEngine`)
- optional ML inference (`ml_detector` + `feature_extractor`)

The engine processes ingest frames (mode `raw_xyz` or `magnitude`) and produces per-second metric messages.

#### 3.1.3 Baseline manager (`backend/services/baseline_manager.py`)
Manages baselines as `BaselineProfile` dataclasses:
- `peaks`: baseline peak frequencies
- `rms_baseline`: per-sensor RMS
- `psd_profile`: stored PSD arrays

Baselines created from live buffer snapshots are persisted as:
- `backend/outputs/baseline_<profile_id>_<YYYYMMDD_HHMMSS>.json`

#### 3.1.4 Serial monitor subsystem (`backend/realtime_monitor.py`)
A separate server path reads a serial device and broadcasts computed parameters over `/ws/monitor`. It uses:
- `SerialHandler` for device IO
- `ParameterCalculator` for feature computation

**Important distinction**: this subsystem’s outputs differ from `/ws/stream` and are consumed by a different frontend dashboard.

### 3.2 Frontend Architecture

#### 3.2.1 Offline analysis UI
- `Upload.jsx`: uploads CSV to `/api/v1/upload` and triggers `/api/v1/analyze`.
- `Dashboard.jsx`: polls `/api/v1/results/{analysis_id}` and visualizes:
  - `modal_data` (frequencies/damping/mode_shapes)
  - `enhanced_graphs` (time-domain overlays, PSD/FFT, energy, MAC, etc.)
  - download links for JSON/PDF/comprehensive PDF/HTML

#### 3.2.2 Live monitoring UI (`frontend/src/pages/LiveMonitoring.jsx`)
- Connects to `/ws/stream`.
- Maintains a rolling history of RMS values (up to 600 points).
- Implements client-side alert rules based on QC and comparative outputs.

#### 3.2.3 Serial monitor UI (`frontend/src/components/Dashboard.tsx`)
- Connects to `/ws/monitor`.
- Renders waveform/FFT/gauges/parameter grid/correlation heatmap.

### 3.3 API Interfaces

#### 3.3.1 REST API (offline analysis)
- `GET /health`
- `POST /api/v1/upload`
- `POST /api/v1/analyze`
- `GET /api/v1/results/{analysis_id}`
- `GET /api/v1/results/{analysis_id}/download/json`
- `GET /api/v1/results/{analysis_id}/download/pdf`
- `GET /api/v1/results/{analysis_id}/download/comprehensive-pdf`
- `GET /api/v1/results/{analysis_id}/download/enhanced-html`

#### 3.3.2 WebSockets (live monitoring)
- `WS /ws/ingest?token=...` expects frames in one of these forms:
  - `mode='raw_xyz'`, `frame=[[s1x,s1y,s1z],[s2x,s2y,s2z]]`
  - `mode='magnitude'`, `frame=[m1,m2,...]`
- `WS /ws/stream` publishes (approx. 1 Hz):
  - `qc` (jitter, clipping, placeholder SNR)
  - `metrics` (psd, peaks, rms)
  - `comparative` (delta_f, damping_delta placeholder, quality, heatmap)
  - `ml_anomaly` (if model loaded)

#### 3.3.3 Baseline management
- `POST /api/baseline/mark?name=...` captures current buffer.
- `GET /api/baseline/list` lists baselines.
- `POST /api/baseline/select?baseline_id=...` selects baseline.

#### 3.3.4 Missing endpoint
Frontend `SensorSetup.jsx` calls `POST /api/v1/save-sensor-positions`. This endpoint does **not** exist in `backend/app.py`; therefore sensor-position persistence is not implemented.

### 3.4 Data Flow Pipeline

#### 3.4.1 Offline analysis pipeline (text diagram)
```
User
  → Upload CSV(s)
  → POST /api/v1/upload
Backend
  → Save to backend/uploads/
  → Store metadata in uploaded_files
User
  → POST /api/v1/analyze
Backend background task run_analysis
  → data_adapters.load_timeseries_for_modal
  → python123.repair_analyzer.extract_modal_parameters   (external)
  → python123.repair_analyzer.calculate_repair_quality   (external)
  → services.enhanced_graphs.generate_all_graph_data     (in repo)
  → enhanced_pdf_generator.create_comprehensive_pdf_report (in repo)
  → enhanced_report_generator.create_enhanced_report       (in repo)
  → Store result in analysis_results
User
  → GET /api/v1/results/{analysis_id}
  → Download artifacts
```

#### 3.4.2 Live monitoring pipeline (text diagram)
```
Ingest host → WS /ws/ingest?token=...
  → LiveAnalysisEngine.ingest_frame
  → Buffers updated

Publisher task (1 Hz)
  → LiveAnalysisEngine.compute_metrics
  → broadcast to WS /ws/stream

Frontend LiveMonitoring.jsx
  → update charts
  → apply alert rules
  → baseline mark/select via REST
```

#### 3.4.3 Serial monitor pipeline (text diagram)
```
Serial device → SerialHandler
  → RealtimeMonitorServer buffer
  → ParameterCalculator.calculate_all_parameters
  → WS /ws/monitor (parameters_update)
  → Frontend Dashboard.tsx visualizations
```

---

## 4. Mathematical Framework

### 4.1 Problem Definition
Let \(x_{s,a}[n]\) denote acceleration for sensor \(s\in\{1,\dots,S\}\) and axis \(a\in\{x,y,z\}\), sampled uniformly at frequency \(f_s\) (Hz). The system computes a set of health and quality indicators by applying transforms and statistics over finite windows \(n=0,\dots,N-1\).

Two distinct problem settings occur:

1. **Live monitoring (implemented in-repo)**: continuous streaming, online feature extraction, baseline comparison, optional ML anomaly scoring.
2. **Offline repair quality analysis (partially external)**: compute modal parameters and compare original/damaged/repaired datasets. The repository invokes this via `python123.repair_analyzer`, but the implementation is absent.

Therefore, this section fully formalizes all computations that are **implemented in this repository**, and separately documents the external portions as interface-level behavior.

### 4.2 Mathematical Models

#### 4.2.1 Magnitude reduction of 3-axis acceleration
Given \(\mathbf{x}_s[n] = (x_{s,x}[n],x_{s,y}[n],x_{s,z}[n])^T\), define

\[
 m_s[n] = \|\mathbf{x}_s[n]\|_2
        = \sqrt{x_{s,x}[n]^2 + x_{s,y}[n]^2 + x_{s,z}[n]^2}.
\]

**Code mapping**:
- `backend/services/live_buffer.py::LiveAnalysisEngine.ingest_frame` (when `mode='raw_xyz'`).
- `backend/parameter_calculator.py::ParameterCalculator._process_sensor`.
- `backend/services/data_adapters.py::load_timeseries_for_modal` for 5-sensor 3-axis files.

**Assumptions**:
- Axes are orthogonal and comparable in units.
- Directional information is not required for the target health indicators.

#### 4.2.2 Discrete Fourier Transform (DFT)
For a real-valued sequence \(x[n]\) of length \(N\),

\[
X[k] = \sum_{n=0}^{N-1} x[n] e^{-j 2\pi kn/N},\quad k=0,\dots,N-1.
\]

A single-sided magnitude spectrum uses \(|X[k]|\) for \(k=0,\dots,\lfloor N/2\rfloor\).

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_frequency_domain` uses `scipy.fft.fft` and `scipy.fft.fftfreq`.

**Normalization used (traceable)**:
\[
\tilde X[k] = \frac{|X[k]|}{N/2}.
\]
This is an amplitude-scaling heuristic. It does not apply windowing and will exhibit leakage.

#### 4.2.3 Welch PSD estimator
Welch PSD is computed by dividing a signal into overlapping segments of length \(L\), applying a window \(w[n]\), and averaging periodograms. In continuous-frequency notation:

\[
\hat P(f) = \frac{1}{R}\sum_{r=1}^{R} \frac{1}{U f_s}
\left|\sum_{n=0}^{L-1} w[n] x_r[n] e^{-j2\pi fn/f_s}\right|^2,
\]
where \(U = \frac{1}{L}\sum_{n=0}^{L-1} w[n]^2\).

**Code mapping**:
- `backend/services/live_buffer.py::RollingPSDAnalyzer.compute_psd` uses `scipy.signal.welch` with `nperseg=L`, `noverlap=L/2`, `scaling='density'`.

**Edge-case behavior**:
- If \(N < L\), it returns empty arrays.

#### 4.2.4 RMS, peak, peak-to-peak
Define

\[
\mu = \frac{1}{N}\sum_{n=0}^{N-1} x[n],\qquad
\mathrm{RMS} = \sqrt{\frac{1}{N}\sum_{n=0}^{N-1} x[n]^2},
\]
\[
\mathrm{Peak} = \max_n |x[n]|,\qquad
\mathrm{P2P} = \max_n x[n] - \min_n x[n].
\]

**Code mapping**:
- Live RMS: `backend/services/live_buffer.py::_compute_metrics`.
- Full time-domain: `backend/parameter_calculator.py::_calculate_time_domain`.

#### 4.2.5 Shape/crest/impulse factors (ratios)
The serial-monitor parameter set computes:

- Crest factor: \(\mathrm{CF} = \mathrm{Peak}/(\mathrm{RMS}+\varepsilon)\)
- Mean absolute value: \(\mathrm{MAV}=\frac{1}{N}\sum_n |x[n]|\)
- RMS factor: \(\mathrm{RMS}/(|\mu|+\varepsilon)\)
- Form factor: \(\mathrm{RMS}/(\mathrm{MAV}+\varepsilon)\)
- Impulse factor: \(\mathrm{Peak}/(\mathrm{MAV}+\varepsilon)\)

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_time_domain`.

#### 4.2.6 Skewness and kurtosis
Let \(\sigma\) be standard deviation. Then

\[
\gamma_1 = \frac{\mathbb{E}[(x-\mu)^3]}{\sigma^3},\qquad
\gamma_2 = \frac{\mathbb{E}[(x-\mu)^4]}{\sigma^4} - 3.
\]

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_time_domain` (SciPy). NaN/Inf values are replaced with 0 for near-constant signals.

#### 4.2.7 Zero-crossing and mean-crossing rates
Zero-crossing rate (ZCR): number of sign changes normalized by length.

\[
\mathrm{ZCR} = \frac{1}{N}\sum_{n=1}^{N-1} \mathbb{I}(\mathrm{sign}(x[n]) \ne \mathrm{sign}(x[n-1])).
\]
Mean-crossing rate uses \(x[n]-\mu\) in place of \(x[n]\).

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_statistical`.

#### 4.2.8 Entropy proxy
The implementation uses a histogram density estimate \(h_i\) and computes

\[
H \approx -\sum_i h_i \log_2(h_i+\varepsilon).
\]

**Important limitation**: because `density=True` produces densities rather than probabilities, \(H\) is not a true Shannon entropy unless corrected by bin width. It is a heuristic for distribution complexity.

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_statistical`.

#### 4.2.9 Energy and power
Energy proxy:
\[
E = \sum_{n=0}^{N-1} x[n]^2,
\]
Power proxy:
\[
P = \frac{E}{N}.
\]

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_statistical`.

#### 4.2.10 Frequency-domain descriptors
From FFT magnitudes \(A_k\) at frequencies \(f_k\), the serial-monitor path computes:

- Dominant frequency: \(f_{\max} = f_{\arg\max_k A_k}\)
- Spectral centroid:
\[
 f_c = \frac{\sum_k f_k A_k}{\sum_k A_k + \varepsilon}.
\]
- Spectral spread:
\[
 \sigma_f = \sqrt{\frac{\sum_k (f_k-f_c)^2 A_k}{\sum_k A_k + \varepsilon}}.
\]
- Spectral rolloff: smallest \(f_r\) such that \(\sum_{f_k\le f_r}A_k \ge 0.95\sum_k A_k\)

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_frequency_domain`.

#### 4.2.11 Cross-correlation, lag, Pearson correlation
Given magnitudes \(m_1[n], m_2[n]\), define cross-correlation:

\[
 r_{12}[\ell] = \sum_n (m_1[n]-\bar m_1)(m_2[n-\ell]-\bar m_2).
\]

The implementation normalizes by \(\sigma_1\sigma_2 N\):
\[
\tilde r_{12}[\ell] = \frac{r_{12}[\ell]}{\sigma_1\sigma_2 N + \varepsilon}.
\]
Then
\[
\ell^* = \arg\max_{\ell} |\tilde r_{12}[\ell]|.
\]

Pearson correlation:
\[
\rho = \frac{\mathrm{cov}(m_1,m_2)}{\sigma_1\sigma_2}.
\]

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_correlation_metrics`.

**Traceable naming discrepancy**:
- `cross_correlation` field is assigned \(\rho\), while `max_cross_correlation` stores the extremum of \(\tilde r_{12}[\ell]\).

#### 4.2.12 Coherence
Magnitude-squared coherence:

\[
C_{12}(f) = \frac{|S_{12}(f)|^2}{S_{11}(f)S_{22}(f)} \in [0,1].
\]

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_correlation_metrics` via `signal.coherence`.

#### 4.2.13 Phase-delay proxy
Using FFT phases:
\[
\Delta\phi[k] = \angle X_1[k] - \angle X_2[k].
\]

The code reports mean \(\mathbb{E}[\Delta\phi]\) and max absolute \(\max_k|\Delta\phi[k]|\).

**Code mapping**:
- `backend/parameter_calculator.py::_calculate_correlation_metrics`.

#### 4.2.14 Live peak detection
Given PSD values \(p(f_k)\), peaks are detected via prominence heuristics and then sorted by peak power. This is not a closed-form model; it is a signal-processing heuristic.

**Code mapping**:
- `backend/services/live_buffer.py::PeakTracker.detect_peaks`.

#### 4.2.15 Live QC: jitter and clipping
- Jitter is computed as the standard deviation of inter-arrival times \(\Delta t\) in milliseconds:
\[
\mathrm{jitter}_{ms} = \mathrm{StdDev}(\Delta t_{ms}).
\]
- Clipping is flagged if any \(|x| > 0.95\,\mathrm{max\_adc\_value}\), where `max_adc_value=16384`.

**Code mapping**:
- `backend/services/live_buffer.py::LiveAnalysisEngine._compute_qc` and `ingest_frame`.

**Limitation**:
- The jitter metric measures message timing jitter, not necessarily ADC sampling jitter.
- SNR is hard-coded as `35.0` dB in `_compute_qc`.

#### 4.2.16 Baseline comparative metrics
Frequency shift:
\[
\Delta f_i(\%) = 100\cdot\frac{f_i^{(t)}-f_i^{(0)}}{f_i^{(0)}+\varepsilon}.
\]

Energy anomaly score per sensor (sigmoid of RMS ratio):
\[
\eta_s = \frac{\mathrm{RMS}_s^{(t)}}{\mathrm{RMS}_s^{(0)}+\varepsilon},\qquad
A_s = \frac{1}{1+\exp(-5(\eta_s-1.5))}.
\]

Quality score:
\[
E_f = \frac{1}{K}\sum_{i=1}^{K} |\Delta f_i|,\qquad
Q_f = \exp\left(-\frac{E_f}{50}\right).
\]
The combined quality is
\[
Q = 0.7 Q_f + 0.3 Q_\zeta,
\]
where \(Q_\zeta\) depends on damping deltas.

**Traceable limitation**:
- In the live comparative computation, damping deltas are placeholders (`0.01`), so \(Q_\zeta\) is not physically meaningful.

**Code mapping**:
- `backend/services/live_buffer.py::ComparativeEngine`.

#### 4.2.17 Hybrid ML anomaly detection
The hybrid anomaly detector combines:

1. **Isolation Forest**: trained on baseline feature vectors \(\mathbf{x}\in\mathbb{R}^d\). Scores \(s\) are mapped using a sigmoid:
\[
A_{IF} = \sigma(s) = \frac{1}{1+e^{-s}}.
\]

2. **Autoencoder** (if TensorFlow available): reconstruction error
\[
\mathrm{MSE} = \frac{1}{d}\sum_{j=1}^d (z_j - \hat z_j)^2,
\]
mapped to
\[
A_{AE} = 1-e^{-\mathrm{MSE}}.
\]

3. **Ensemble**:
\[
A = \begin{cases}
0.5A_{IF}+0.5A_{AE}, & \text{if AE available}\\
A_{IF}, & \text{otherwise}.
\end{cases}
\]

Anomaly decision:
\[
\mathrm{is\_anomaly} = (A>0.6).
\]

**Code mapping**:
- `backend/ml_models/anomaly_detector.py`.

### 4.3 Variable Definitions and Units
| Symbol | Meaning | Units / Domain |
|---|---|---|
| \(x_{s,a}[n]\) | acceleration sample | typically \(g\) |
| \(m_s[n]\) | magnitude | \(g\) |
| \(f_s\) | sampling frequency | Hz |
| \(N\) | window length | samples |
| \(X[k]\) | DFT coefficient | signal units |
| \(\hat P(f)\) | PSD estimate | \(g^2/\text{Hz}\) (conceptually) |
| \(f_i\) | detected peak frequencies | Hz |
| \(\Delta f_i\) | frequency shift | % |
| \(\rho\) | Pearson correlation | [-1,1] |
| \(C(f)\) | coherence | [0,1] |
| \(Q\) | quality score | [0,1] |
| \(A\) | anomaly score | [0,1] |

### 4.4 Governing Equations
The implemented computations follow:
- Euclidean norm (magnitude)
- FFT/DFT and Welch PSD for spectral estimation
- Moment statistics and ratio metrics
- Cross-correlation / coherence for inter-sensor coupling
- Sigmoid/exponential mappings for comparative scoring
- Isolation Forest and autoencoder reconstruction error for anomaly inference

### 4.5 Algorithmic Derivations

#### 4.5.1 Spectral rolloff
Define cumulative spectral sum \(S[k]=\sum_{i=0}^{k} A_i\). The 95% rolloff index is
\[
 k_r = \min\{k: S[k] \ge 0.95 S[K]\},\quad f_r=f_{k_r}.
\]
This is implemented using cumulative sums and `argmax`.

#### 4.5.2 Finite-difference curvature in damage localization
For a mode shape vector \(\boldsymbol\phi\in\mathbb{R}^M\), second-order finite difference curvature:
\[
\kappa_i = \phi_{i+1} - 2\phi_i + \phi_{i-1},\quad i=1,\dots,M-2.
\]
The code normalizes by \(\max_i |\kappa_i|+\varepsilon\).

### 4.6 Numerical Methods
- Welch PSD: variance reduction via averaging; reduced frequency resolution relative to a full FFT.
- Peak detection: prominence-based heuristic; sensitive to noise floor.
- Nonlinear metrics: simplified and may be biased for short/noisy signals.

### 4.7 Computational Complexity
Let \(N\) be samples per window.

- FFT: \(O(N\log N)\).
- Welch PSD: \(O(N\log N)\) per segment; in practice similar scale.
- `np.correlate` full-mode cross-correlation: worst-case \(O(N^2)\).
- Sample entropy / approximate entropy (naive nested loops): \(O(N^2)\).

**Practical implication**: the serial-monitor subsystem may struggle to maintain a 10 Hz update rate when advanced metrics are enabled on long windows.

### 4.8 Error Propagation and Stability
Key numerical stability protections present in code:
- Additive \(\varepsilon\approx 10^{-10}\) in denominators.
- Replacement of NaN/Inf skewness and kurtosis with 0.
- Guard clauses for short sequences.

Key instability sources:
- entropy computed on densities (not normalized probabilities)
- nonlinear metrics are sensitive and may be unreliable for short/noisy signals
- lack of windowing in FFT-based metrics can cause spectral leakage

---

## 5. Algorithms and Implementation Mapping

### 5.1 Backend Algorithms

#### 5.1.1 `backend/app.py` — offline analysis orchestration + live streaming
**Responsibility**:
- Defines REST and WS endpoints and initializes streaming.

**Input → processing → output**:
- Upload (`/api/v1/upload`): multipart CSV → stored in `uploads/` → metadata returned.
- Analyze (`/api/v1/analyze`): validates request → schedules background `run_analysis` → returns `analysis_id`.
- Results (`/api/v1/results/{analysis_id}`): returns processing progress or completed result object.
- Downloads: returns file responses from `outputs/`.
- Streaming: initializes `LiveAnalysisEngine` and publishes metrics.

**Failure modes**:
- validation errors: bad file extension, empty file, non-numeric data, too few samples.
- analysis failure: missing external `python123.repair_analyzer`.
- comprehensive PDF generation risk: `enhanced_graphs` is passed to `create_comprehensive_pdf_report` before it is assigned in the repair-quality branch (exception is caught and logged).

#### 5.1.2 `backend/services/data_adapters.py` — CSV adapters
**Responsibility**: produce numeric arrays in shapes expected by modal analyzers.

**Notable behavior**:
- For 15/16 columns: reshape to (N,5,3) and compute magnitudes to return (N,5).
- If N<1024, tiles the data to length 1024 (this increases apparent sample count and can bias spectral estimates; it is a pragmatic workaround).
- For other formats, falls back to external loader `repair_analyzer.load_csv_data`.

#### 5.1.3 `backend/services/live_buffer.py` — live metric computation
**Responsibility**: implement the online signal-processing chain.

**Key methods**:
- `ingest_frame`: parses incoming frame, computes magnitudes, appends to buffers, updates jitter and clipping.
- `_compute_metrics`: computes PSD, peaks, RMS.
- `_compute_comparative`: if baseline present, computes Δf, energy anomaly heatmap, quality score.
- `_compute_ml_anomaly`: extracts features and invokes ML detector.

**Failure modes / edge cases**:
- insufficient samples for PSD window → empty PSD arrays.
- invalid frame shapes → ingest errors.

#### 5.1.4 `backend/services/baseline_manager.py` — baseline lifecycle
**Responsibility**: save/load baseline profiles and maintain a “current” baseline.

**Failure modes**:
- JSON parse failures for corrupted files.
- Baseline scan criteria checks for keys (`damaged_modal`/`original_modal`) that may not exist in current offline outputs (`modal_data`), reducing reuse.

#### 5.1.5 `backend/parameter_calculator.py` — 50+ parameter extraction
**Responsibility**: compute extensive time/frequency/statistical/advanced/correlation features on two 3-axis sensors.

**Key computations mapped to equations**:
- Time: RMS, peak, peak-to-peak, crest factor, skewness, kurtosis.
- Frequency: dominant frequency, bandwidth, centroid, rolloff, spread, slope.
- Statistical: ZCR, MCR, entropy proxy, energy, power, SNR estimate.
- Advanced: autocorrelation peak/lag; Hurst, Lyapunov, correlation dimension, sample entropy, approximate entropy.
- Correlation: Pearson correlation, cross-correlation peak and lag, coherence, phase delay.

**Failure modes**:
- for constant signals, skew/kurtosis can be undefined; handled.
- advanced metrics may be unstable or expensive.

#### 5.1.6 `backend/services/damage_localizer.py` — hybrid localization
**Responsibility**:
- physics-based localization via frequency shift + mode-shape curvature/strain-energy proxy
- optional ML-based prediction if a model is provided
- a constrained 2-sensor localization method (line between sensors)

**Edge-case handling**:
- if no modes exist, returns “no damage” result.
- 2-sensor geometry degeneracy (zero distance) handled via default direction.

#### 5.1.7 `backend/ml_models/anomaly_detector.py` — hybrid anomaly detection
**Responsibility**:
- train and score anomalies using Isolation Forest and optional autoencoder.

**Failure modes**:
- TensorFlow not installed: autoencoder disabled.
- joblib not installed: persistence disabled.

### 5.2 Frontend Computation Logic

#### 5.2.1 Offline analysis pages
- `Upload.jsx`: constructs analysis requests and polls status.
- `Dashboard.jsx`: transforms returned arrays into chart series and handles downloads.

#### 5.2.2 Live monitoring page
- `LiveMonitoring.jsx`: websocket parsing, state update, alert logic, baseline selection.

#### 5.2.3 Serial monitor dashboard
- `components/Dashboard.tsx`: interprets typed WS messages (`parameters_update`) and renders specialized components.

### 5.3 Data Validation and Constraints
- Upload endpoint enforces minimum sample count (512) and whitelisted column counts.
- Live ingest requires a token and expects either raw XYZ or magnitude frames.
- Baseline capture requires live buffers to be initialized.

### 5.4 Optimization Techniques
Implemented:
- bounded buffers (memory cap)
- publish rate throttling (1 Hz for `/ws/stream`)

Not implemented but recommended:
- FFT-based cross-correlation (reduce \(O(N^2)\) to \(O(N\log N)\))
- replace naive entropy computations with probability-corrected estimators
- vectorize nonlinear metrics or reduce update frequency

---

## 6. Software Engineering Analysis

### 6.1 Modularity and Design Patterns
- Service decomposition: buffering, baselines, localization, graph generation.
- Engine pattern: `LiveAnalysisEngine` encapsulates stateful streaming analytics.
- Dataclass modeling: `BaselineProfile`.
- Frontend separation into pages/components/hooks.

### 6.2 Scalability
Current constraints:
- In-memory dicts for results and uploads prevent multi-instance scaling.
- WebSocket broadcast is single-process.

To scale:
- store analysis state in Redis/DB
- store uploads/outputs in object storage
- use a WS broker or server supporting fan-out

### 6.3 Security
- `/ws/ingest` uses a shared token.
- `/ws/stream` is unauthenticated.
- file upload lacks explicit size limits and content scanning.

### 6.4 Performance
- `/ws/stream` computations are lightweight at 1 Hz.
- `/ws/monitor` can be heavy if advanced metrics run at 10 Hz.

### 6.5 Maintainability
- Two “real-time” subsystems (`/ws/stream` and `/ws/monitor`) increase cognitive load.
- External dependency for offline core analysis reduces reproducibility.

---

## 7. Experimental Validation / Test Logic

### 7.1 Input Scenarios
1. **Zero signal**: \(x[n]=0\).
2. **Single sine**: \(x[n]=A\sin(2\pi f_0 n/f_s)\).
3. **Two-tone**: \(x[n]=A_1\sin(2\pi f_1 n/f_s)+A_2\sin(2\pi f_2 n/f_s)\).
4. **Baseline vs shifted**: baseline \(f_0\), live \(f_0(1-\delta)\).
5. **Correlated sensors**: \(x_2[n]=x_1[n-\ell]+\eta[n]\).

### 7.2 Expected Outputs
- Zero signal: RMS \(=0\), ratios \(=0\) or guarded, PSD empty.
- Single sine: dominant frequency \(\approx f_0\); Welch PSD shows peak at \(f_0\).
- Shifted sine: \(|\Delta f|\) increases; quality decreases (exponential penalty).
- Correlated sensors: high \(\rho\), high coherence around dominant frequencies, nonzero lag estimate.

### 7.3 Boundary Conditions
- \(N < L\) for PSD window: PSD cannot be computed.
- Constant signals: skew/kurtosis undefined; replaced by 0.
- Very noisy signals: peak detection may fail; outputs empty peaks.

### 7.4 Error Handling
Backend:
- returns HTTP 400 for validation failures
- returns HTTP 404 for missing analysis IDs
- catches and logs exceptions in background analysis; marks analysis failed

Frontend:
- displays toast errors on REST failures
- auto-reconnect logic for serial-monitor websocket

---

## 8. Limitations and Assumptions

1. **Missing offline core analysis code**: `python123.repair_analyzer` is not included; modal extraction and repair scoring cannot be validated here.
2. **Comprehensive PDF generation order bug**: in `run_analysis` repair-quality path, `enhanced_graphs` is used before assignment when creating comprehensive PDF; this may prevent PDF generation.
3. **Baseline scanning mismatch**: `BaselineManager` looks for keys not used by current offline output format; automatic baseline loading may be incomplete.
4. **Entropy correctness**: entropy uses histogram densities; values are heuristic.
5. **Nonlinear metrics**: simplified implementations are sensitive and computationally expensive.
6. **2-sensor localization**: fundamentally underdetermined in 3D; only line-based estimate is possible.
7. **Security**: `/ws/stream` is unauthenticated; uploads have no explicit size limits.
8. **Persistence and scaling**: in-memory state prevents horizontal scaling and restart recovery.

---

## 9. Future Enhancements

1. Vendor-independent inclusion of the offline modal-analysis code (remove external dependency or vendor it as a library).
2. Fix comprehensive PDF generation ordering (compute `enhanced_graphs` before PDF generation).
3. Implement missing `POST /api/v1/save-sensor-positions` and persist sensor layouts.
4. Add proper entropy estimators and unit-consistent PSD normalization.
5. Replace naive \(O(N^2)\) computations with FFT-based or approximate algorithms.
6. Implement persistent storage for `analysis_results` and `uploaded_files`.
7. Add authentication/authorization for dashboards and WebSocket endpoints.
8. Add a reproducible test suite with deterministic synthetic signals.

---

## 10. Conclusion
This repository implements a multi-modal SHM application integrating offline report-centric workflows and live monitoring. The real-time analytics pipeline is fully traceable to implemented signal-processing and ML algorithms: magnitude conversion, Welch PSD, peak tracking, comparative scoring, and hybrid anomaly detection. A separate serial-monitor subsystem computes an extensive parameter set including nonlinear metrics.

The system’s principal technical gap is the missing offline modal-analysis engine (`python123.repair_analyzer`), which prevents full verification of the repair-quality scoring logic within this repository. Addressing this dependency and improving baseline interoperability, performance hotspots, and security would significantly strengthen the system for academic evaluation and engineering deployment.

---

## References
1. A. V. Oppenheim and R. W. Schafer, *Discrete-Time Signal Processing*, 3rd ed.
2. P. D. Welch, “The use of fast Fourier transform for the estimation of power spectra,” *IEEE Trans. Audio Electroacoust.*, 1967.
3. T. Hastie, R. Tibshirani, and J. Friedman, *The Elements of Statistical Learning* (for Isolation Forest context).
4. S. Mallat, *A Wavelet Tour of Signal Processing* (general time-frequency methods).

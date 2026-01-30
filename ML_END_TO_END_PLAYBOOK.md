# ML End-to-End Playbook (Data → Training → Evaluation → Deployment → Monitoring)

This playbook is a comprehensive, practical checklist and Q&A covering everything you need to know to explain, build, train, deploy, and maintain ML systems. It’s tailored to this project’s structure (Python + PyTorch backend, Vite/React frontend, Docker options) and the domain (structural health monitoring / damage classification & analysis).

---

## 1) Core Concepts (What to know before anything else)

- Problem framing
  - What type? Classification, regression, anomaly detection, or ranking. In this repo: damage classification and health monitoring.
  - Target(s) and features: What are you predicting and from what data? Here: vibration/accel time-series → health/damage state.
- Data lifecycle
  - Collection → Validation → Preprocessing → Splits → Feature engineering → Training → Validation → Testing → Monitoring & feedback.
- Experiment discipline
  - Reproducibility, version control (code + data + models), fixed seeds, logged configs/metrics.
- Operational constraints
  - Latency, throughput, memory, model size, hardware/accelerator availability, privacy.
- Responsible AI
  - Bias checks, data consent, PII handling, security, auditability, rollback plans.

---

## 2) Data: Collection, Validation, and Management

- Source and format
  - Sensors (e.g., ADXL345) → CSV files. See datas/ folders.
- Folder structure in this project
  - datas/baseline/: healthy/baseline datasets
  - datas/damaged/: damaged datasets
  - datas/repaired/good_repair/ and datas/repaired/bad_repair/: repaired datasets
- Validation utilities you can run
  - pre_analysis_validator.py and validate_csv_folder.py
  - test_data_validation.py and batch_test_data_validation.py (for bulk checks)
  - HOW_TO_USE_VALIDATION_SCRIPT.md and USE_VALIDATOR_NOW.md for quick usage
- Minimum viable checks
  - File readability (CSV parse), expected columns and sampling rate, no NaNs/inf, duration minimums.
  - Statistical sanity: mean/variance ranges, spikes/clipping detection, timestamps monotonicity.
- Splitting strategy
  - Train/val/test by structure or session to avoid leakage.
  - Keep a fixed seed and store split indices.
- Versioning
  - Keep raw data immutable; write derived data (normalized, features) to a separate folder with a manifest (hash + provenance).

---

## 3) Feature Engineering and Preprocessing

- Typical steps
  - Detrending, normalization/standardization, band-pass filtering (e.g., 0.1–45 Hz), windowing.
  - Frequency-domain features: FFT peaks, spectral power in bands, modal parameters.
  - Time-domain features: RMS, kurtosis, skewness, correlation across sensors.
- Project utilities
  - backend/ml_models/feature_extractor.py and services/enhanced_graphs.py can guide how features are computed/visualized.
- Reproducibility principle
  - Save the preprocessing config along with the model (e.g., JSON alongside .pth) so inference matches training.

---

## 4) Modeling (Architectures, Losses, Metrics)

- Architecture choices for time series
  - CNNs (1D), RNNs/LSTMs/GRUs, Temporal ConvNets, Transformers, classical ML on features (RF, XGBoost)
- In this project
  - PyTorch-based models for health monitoring; see backend/ml_models/health_monitoring/
  - Model artifact: best_model_improved.pth with info in model_info_improved.json
- Loss functions & metrics
  - Classification: CrossEntropyLoss, accuracy, F1, per-class recall
  - Regression: MSE/MAE, R^2
  - Anomaly detection: AUROC, AUPRC, thresholded precision/recall
- Practical metrics to report
  - Confusion matrix, per-class metrics, calibration, latency per sample, memory footprint

---

## 5) Training: Configuration, Running, and Tracking

- Where to look in this repo
  - tools/train_ml_models.py and scripts/train_models.sh
  - backend/ml_models/model_manager.py to understand how models are loaded/selected
  - backend/ml_models/anomaly_detector.py and external_predictor.py for alternative flows
- Typical training pipeline steps
  1) Prepare datasets (cleaned CSVs → windows)
  2) Build DataLoaders (shuffle train, stratify if needed)
  3) Define model + optimizer + scheduler
  4) Train with validation after each epoch
  5) Early stopping/checkpointing best model
  6) Log metrics, config, seed
- Reproducibility
  - Fix random seeds: torch, numpy, python random
  - Save: code commit hash, data manifest/split, hyperparams, model weights
- Running locally
  - python tools/train_ml_models.py --config path/to/config.json (if available)
  - or scripts/train_models.sh for a curated flow
- Resource tips
  - Enable GPU if available (torch.cuda.is_available())
  - Mixed precision for speed (torch.cuda.amp)

---

## 6) Evaluation and Validation

- Offline evaluation
  - Use a held-out test set that mirrors expected deployment conditions
  - Produce confusion matrix, per-class metrics, ROC/PR curves, error analysis
- In this project
  - FORMULA_VALIDATION_REPORT.md, VALIDATION_SCRIPT_USAGE.txt, and various *_SUMMARY.txt files demonstrate reporting
  - backend/outputs/ contains generated PDFs/JSON/HTML summaries for real runs
- Stress tests
  - Noise robustness, sensor dropout, drift over time, domain shift (different structures)
- Acceptance criteria
  - Define minimum accuracy, per-class recall targets, and latency budget before go-live

---

## 7) Serving and APIs (Backend)

- Stack
  - FastAPI/Uvicorn backend (backend/app.py)
  - Frontend built with Vite/React (frontend/)
- Key endpoints (examples)
  - GET /health → service and model availability
  - POST /api/v1/upload → upload CSV files (baseline/damaged/repaired)
  - POST /api/v1/analyze → run analysis pipeline and generate reports
  - POST /api/v1/predict/baseline → run baseline predictors
  - GET /api/v1/results/{analysis_id} → retrieve analysis results
- Model loading
  - backend/ml_models/health_monitoring/best_model_improved.pth (PyTorch)
  - backend/ml_models/health_monitoring/model_info_improved.json describes metadata
- Practical deployment options
  - Run locally: python backend/app.py (or uvicorn app:app --host 0.0.0.0 --port 8000)
  - Docker: docker-compose up -d (uses Dockerfile.backend and Dockerfile.frontend)
- Performance & reliability
  - Use lazy imports for heavy deps (PyTorch) to avoid startup failures
  - Configure workers (gunicorn/uvicorn) per CPU cores; pin model on load

---

## 8) Frontend & UX (Explainability and Demo Readiness)

- Pages of interest
  - frontend/src/pages/: Upload.jsx, Dashboard.jsx, Analysis.jsx, SensorSetup.jsx
- Components
  - ComparativeDashboard, FFTSpectrum, SensorHeatmap2D, MLAnomalyMeter
- Tips for judges/stakeholders
  - Prepare a small, curated dataset to upload live
  - Show end-to-end flow: upload → analyze → view PDF/HTML report in backend/outputs/
  - Use the Dashboard to show spectra, heatmaps, and decisions

---

## 9) Deployment Environments and Configuration

- Environments
  - Local dev: Vite dev server (default port ~5173/5174), FastAPI on 8000
  - Docker: docker-compose binds 3000 → Nginx, 8000 → API
- Config files
  - backend/config.py, .env.example, frontend/.env
  - docker-compose.yml binds volumes for uploads and outputs
- Model packaging
  - Bundle .pth + corresponding model_info_*.json
  - Provide a checksum and a model version string

---

## 10) Monitoring in Production

- What to monitor
  - API health, latency, error rates, model load failures
  - Input drift: feature distributions vs. training baseline
  - Output drift: prediction class balance over time
  - Model confidence and abstentions
- Implementations
  - Add logging around inference timing
  - Save periodic sampling of inputs (hashed) and outputs (aggregated) with privacy
  - Alerts when drift exceeds thresholds

---

## 11) Reliability, Testing, and CI/CD

- Tests to include
  - Unit tests for preprocessing, feature extraction, and model wrappers
  - Integration tests: upload → analyze → result
  - Data validation tests (already provided scripts)
- Pipelines
  - Lint + unit tests on PR
  - Build Docker images and run basic smoke tests
  - Stage rollout with feature flags or canary models

---

## 12) Security & Compliance

- Data handling
  - Validate and sanitize uploads
  - Access controls for sensitive outputs
- Supply chain
  - Pin dependency versions (backend/requirements.txt)
  - Scan Docker images for CVEs
- Runtime safety
  - Resource limits in Docker, rate limiting on APIs
  - Avoid arbitrary code execution patterns

---

## 13) Frequently Asked Questions (Self-Quiz with Answers)

Q1: How do we ensure the same preprocessing at training and inference?
A: Save preprocessing parameters (scalers, filters, frequency ranges) into a JSON next to the model. Load and apply the same pipeline in production.

Q2: How do we prevent data leakage?
A: Split by structure/session/time so samples from the same physical acquisition don’t span train/test. Freeze test set and keep it offline.

Q3: How do we compare two repairs fairly?
A: Keep acquisition conditions consistent (sensor positions, sampling rate). Normalize signals, compute comparable features, and run the same analysis pipeline.

Q4: What metrics matter for judges?
A: Accuracy and per-class recall, confusion matrix, latency per request, robustness to noise/sensor dropout, and a concise explanation of decisions.

Q5: How to speed up inference?
A: Use torchscript or onnx export, quantization, and batch small windows together. Cache model and allocate on GPU once.

Q6: What if PyTorch is missing on the server?
A: Use lazy imports and feature flags to degrade gracefully, or ship a CPU-only wheel in requirements. Provide a clear health endpoint message.

Q7: How do I regenerate the demo reports?
A: Use the UI to upload and analyze, or call POST /api/v1/analyze; outputs appear in backend/outputs/ as PDF/HTML/JSON.

Q8: How do I robustly reproduce a training run?
A: Pin requirements, set seeds, snapshot config and data split manifest, log metrics, and store model weights + metadata.

Q9: How do we add a new model version safely?
A: Side-by-side deploy (v1, v2), shadow traffic to v2, compare metrics, then switch over via config. Keep rollback to v1 ready.

Q10: How do we explain model results?
A: Show input spectra, salient frequencies, and feature importances (if classical). Provide per-class score/confidence and textual rationale.

---

## 14) Command Snippets (Cheatsheet)

- Start backend locally
  - uvicorn app:app --host 0.0.0.0 --port 8000
- Start full stack with Docker
  - docker-compose up -d
- Upload a file (CLI)
  - curl -F "file=@datas/baseline/baseline_01.csv" http://localhost:8000/api/v1/upload
- Run analysis
  - curl -X POST http://localhost:8000/api/v1/analyze -H "Content-Type: application/json" -d '{"analysis_type":"repair_quality", ... }'
- Check health
  - curl http://localhost:8000/health

---

## 15) Demo Narrative (What to say in front of judges)

1) Our goal: rapid structural health assessment using vibration data.
2) The pipeline: Upload → Validate → Extract features → ML inference → Report.
3) Models: PyTorch-based health monitoring classifier (see model_info_improved.json).
4) Reliability: Graceful startup via lazy imports, health checks, and robust validation.
5) Results: PDF/HTML reports in backend/outputs/ that summarize damage localization and repair quality.
6) Deployment: Docker Compose for one-command bring-up; flexible to CPU/GPU.

---

## 16) Next Steps / Checklists

- Pre-demo checklist
  - [ ] Backend healthy (GET /health)
  - [ ] Frontend reachable
  - [ ] Sample CSVs ready
  - [ ] Model file present (.pth) + metadata JSON
  - [ ] Outputs directory writable
- Post-demo checklist
  - [ ] Archive run artifacts
  - [ ] Note feedback and edge cases to test
  - [ ] Decide on next model improvements (data or architecture)

---

## 17) Artifacts in this Repository (Where to point people)

- Code
  - backend/app.py (FastAPI), backend/ml_models/* (model code), frontend/* (Vite/React)
- Models
  - backend/ml_models/health_monitoring/best_model_improved.pth
  - backend/ml_models/health_monitoring/model_info_improved.json
- Reports and examples
  - backend/outputs/* (PDF, HTML, JSON summaries)
- Utilities and docs
  - VALIDATOR_* docs, HOW_TO_USE_VALIDATION_SCRIPT.md, ML_* guides, UI_* guides

---

If you need talking points tailored to a 2–3 minute pitch, jump to sections 15 and 16 and keep the commands from section 14 handy.

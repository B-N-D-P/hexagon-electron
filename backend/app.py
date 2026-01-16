"""
Main FastAPI Application for Structural Repair Quality Analysis
2-Sensor XYZ Data System - Repair Quality Analysis Only
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import sys
from pathlib import Path
import os
from datetime import datetime
from typing import Optional
import json
import uuid
import asyncio
import threading
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    API_TITLE, API_VERSION, API_DESCRIPTION, CORS_ORIGINS,
    UPLOAD_DIR, OUTPUT_DIR, DEFAULT_FS, DEFAULT_MAX_MODES,
    SENSOR_POSITIONS, ML_MODELS_DIR
)
from models.schemas import (
    UploadResponse, AnalysisRequest, AnalysisResult,
    ErrorResponse, HealthCheckResponse
)

# Import analysis services
sys.path.insert(0, str(Path(__file__).parent / "services"))
from live_buffer import LiveAnalysisEngine
from baseline_manager import BaselineManager
from serial_handler import SerialHandler

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# STREAMING CONFIGURATION & GLOBAL STATE
# ============================================================================

# Streaming configuration
LIVE_BUFFER_DURATION_SEC = 120  # Keep 2 minutes of data
PSD_WINDOW_SIZE_SEC = 8
METRICS_UPDATE_RATE_HZ = 1
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
STREAM_INGEST_AUTH_TOKEN = os.getenv("STREAM_INGEST_AUTH_TOKEN", "dev-token")
NUM_SENSORS = 2  # Changed to 2 sensors for XYZ data (6 columns total)
DEFAULT_FS = 100.0  # IAI Hardware: 100 samples per second

# Global streaming state
live_analysis_engine: Optional[LiveAnalysisEngine] = None
baseline_manager: Optional[BaselineManager] = None
serial_handler: Optional[SerialHandler] = None
stream_clients = set()  # WebSocket connections to /ws/stream
stream_lock = threading.Lock()

# Background task for periodic metrics publishing
metrics_publish_task = None

# ---------------------------------------------------------------------------
# JSON sanitization utilities to prevent numpy/pydantic serialization issues
# ---------------------------------------------------------------------------
from datetime import date
import numpy as _np
from pydantic import BaseModel as _PydanticBaseModel
from pathlib import Path as _Path


def _json_safe(obj):
    """Recursively convert common non-JSON types to JSON-serializable ones.
    - numpy scalars -> python scalars
    - numpy arrays -> lists
    - sets/tuples -> lists
    - datetime/date -> ISO strings
    - pydantic models -> dict
    - pathlib.Path -> str
    - dicts/lists -> recurse
    """
    # Fast path for None and basic types
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Datetime/date
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    # pathlib.Path
    if isinstance(obj, _Path):
        return str(obj)

    # pydantic models
    if isinstance(obj, _PydanticBaseModel):
        return _json_safe(obj.model_dump())

    # numpy types
    if isinstance(obj, (_np.generic,)):
        return obj.item()
    if isinstance(obj, _np.ndarray):
        return obj.tolist()

    # containers
    if isinstance(obj, dict):
        return { _json_safe(k): _json_safe(v) for k, v in obj.items() }
    if isinstance(obj, (list, tuple, set)):
        return [ _json_safe(x) for x in obj ]

    # Fallback to string
    try:
        return json.loads(json.dumps(obj))
    except Exception:
        return str(obj)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for analysis results (in production, use database)
analysis_results = {}
uploaded_files = {}

# Serve output artifacts (reports/plots)
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    global serial_handler

    arduino_status = "disconnected"
    arduino_port = None

    if serial_handler:
        try:
            status = serial_handler.get_status()
            arduino_status = status.get('connection_status', 'disconnected')
            arduino_port = status.get('port', None)
        except:
            arduino_status = "disconnected"

    return HealthCheckResponse(
        status="healthy",
        version=API_VERSION,
        timestamp=datetime.now(),
        services={
            "api": "running",
            "file_storage": "ready",
            "analysis_engine": "ready",
            "arduino": arduino_status,
        },
        arduino={
            "status": arduino_status,
            "port": arduino_port,
            "connected": arduino_status == "connected"
        }
    )


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "status": "ready",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "upload": "/api/v1/upload",
            "analyze": "/api/v1/analyze",
            "results": "/api/v1/results/{analysis_id}",
        }
    }


# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload CSV accelerometer data file

    Accepts:
    - Single-axis: 4-5 columns (4-5 sensors)
    - 3-axis: 6 columns (2 sensors × 3 axes) - NO TIMESTAMP
    - 3-axis: 12 columns (4 sensors × 3 axes)
    - 3-axis: 15 columns (5 sensors × 3 axes)
    - Optional leading time column: +1 to any format
    """
    try:
        # Validate file extension
        if not file.filename.endswith('.csv'):
            raise ValueError(f"Invalid file type: {file.filename}. Only CSV files are supported.")

        # Generate unique file ID
        file_id = str(uuid.uuid4())[:8]

        # Save file
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        contents = await file.read()

        if len(contents) == 0:
            raise ValueError("Empty file uploaded")

        with open(file_path, 'wb') as f:
            f.write(contents)

        # Load and validate data
        import pandas as pd
        import numpy as np

        df = pd.read_csv(file_path)

        if df.empty:
            raise ValueError("CSV file is empty")

        df_numeric = df.apply(pd.to_numeric, errors='coerce').dropna()

        if df_numeric.empty:
            raise ValueError("No valid numeric data found in CSV file")

        num_samples = len(df_numeric)
        num_sensors = df_numeric.shape[1]

        # Estimate sampling rate and duration (assuming 1000 Hz default)
        fs = DEFAULT_FS
        duration_sec = num_samples / fs

        # Validate data
        if num_samples < 512:
            raise ValueError(f"Too few samples: {num_samples} (need at least 512)")

        # Supported formats:
        # - single-axis 4-5 columns (4-5 sensors)
        # - 3-axis 6 columns (2 sensors × 3 axes) - NO TIMESTAMP
        # - 3-axis 12 columns (4 sensors × 3 axes)
        # - 3-axis 15 columns (5 sensors × 3 axes)
        # - optional leading time column => +1 to any format
        if num_sensors not in [4, 5, 6, 12, 15, 5, 13, 16, 7]:
            raise ValueError(
                f"Unexpected number of columns: {num_sensors}. "
                f"Expected: 4/5 (single-axis), 6 (2 sensors×3axis), 12 (4 sensors×3axis), "
                f"15 (5 sensors×3axis), or those plus a time column."
            )

        # Store file info
        uploaded_files[file_id] = {
            "filename": file.filename,
            "file_path": str(file_path),
            "num_samples": num_samples,
            "num_sensors": num_sensors,
            "duration_sec": duration_sec,
            "sampling_rate_hz": fs,
            "upload_time": datetime.now(),
        }

        # Calculate actual number of sensors (6 columns = 2 sensors × 3 axes)
        # Support formats: 4-5 (single axis), 6 (2×3), 12 (4×3), 15 (5×3)
        if num_sensors == 6:
            actual_sensors = 2
            sensor_format = "2 sensors × 3 axes (XYZ)"
        elif num_sensors == 12:
            actual_sensors = 4
            sensor_format = "4 sensors × 3 axes (XYZ)"
        elif num_sensors == 15:
            actual_sensors = 5
            sensor_format = "5 sensors × 3 axes (XYZ)"
        elif num_sensors in [4, 5]:
            actual_sensors = num_sensors
            sensor_format = f"{num_sensors} sensors (single-axis)"
        else:
            actual_sensors = num_sensors
            sensor_format = f"{num_sensors} channels"

        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            upload_time=datetime.now(),
            num_samples=num_samples,
            num_sensors=actual_sensors,
            duration_sec=duration_sec,
            sampling_rate_hz=fs,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload error: {str(e)}"
        )




# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/v1/analyze")
async def analyze_structure(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze structural repair quality

    Supports two analysis types:
    1. repair_quality: Compare original → damaged → repaired (3-file analysis)
    2. comparative: Compare damaged → repaired (2-file analysis)
    """
    try:
        analysis_id = str(uuid.uuid4())[:12]

        # Validate analysis type (2-sensor system supports localization but limited)
        valid_types = ["repair_quality", "comparative", "localization"]
        if request.analysis_type not in valid_types:
            raise ValueError(f"Invalid analysis type: {request.analysis_type}. Must be one of {valid_types}")

        # Validate file IDs
        if request.damaged_file_id not in uploaded_files:
            raise ValueError(f"Damaged file not found: {request.damaged_file_id}")

        if request.analysis_type == "repair_quality":
            if not request.original_file_id:
                raise ValueError("repair_quality analysis requires original_file_id")
            if request.original_file_id not in uploaded_files:
                raise ValueError(f"Original file not found: {request.original_file_id}")
            if not request.repaired_file_id:
                raise ValueError("repair_quality analysis requires repaired_file_id")
            if request.repaired_file_id not in uploaded_files:
                raise ValueError(f"Repaired file not found: {request.repaired_file_id}")

        elif request.analysis_type == "comparative":
            if not request.repaired_file_id:
                raise ValueError("comparative analysis requires repaired_file_id")
            if request.repaired_file_id not in uploaded_files:
                raise ValueError(f"Repaired file not found: {request.repaired_file_id}")


        # Validate analysis parameters
        if request.fs <= 0:
            raise ValueError(f"Invalid sampling rate: {request.fs} (must be > 0)")
        if request.max_modes <= 0:
            raise ValueError(f"Invalid max_modes: {request.max_modes} (must be > 0)")
        if request.min_freq < 0 or request.max_freq <= 0:
            raise ValueError(f"Invalid frequency range: min={request.min_freq}, max={request.max_freq}")
        if request.min_freq >= request.max_freq:
            raise ValueError(f"Invalid frequency range: min_freq must be < max_freq")

        # Start analysis in background
        background_tasks.add_task(
            run_analysis,
            analysis_id=analysis_id,
            request=request
        )

        return {
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "Analysis started. Check status periodically.",
            "check_status_url": f"/api/v1/results/{analysis_id}",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis error: {str(e)}"
        )






@app.get("/api/v1/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """
    Get analysis results by analysis ID

    Status values:
    - processing: Still running
    - completed: Ready to view
    - failed: Error occurred
    """
    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis not found: {analysis_id}"
        )

    result = analysis_results[analysis_id]

    # If processing, check if still running
    if result["status"] == "processing":
        return _json_safe({
            "analysis_id": analysis_id,
            "status": "processing",
            "progress": result.get("progress", 0),
            "current_step": result.get("current_step", "Initializing..."),
        })

    # Return full results (sanitized)
    return _json_safe(result)


@app.get("/api/v1/results/{analysis_id}/download/json")
async def download_json_report(analysis_id: str):
    """Download JSON report"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")

    result = analysis_results[analysis_id]
    if result["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")

    json_path = OUTPUT_DIR / f"{analysis_id}_report.json"
    return FileResponse(json_path, filename=f"{analysis_id}_report.json")


@app.get("/api/v1/results/{analysis_id}/download/pdf")
async def download_pdf_report(analysis_id: str):
    """Download PDF report"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")

    result = analysis_results[analysis_id]
    if result["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")

    pdf_path = OUTPUT_DIR / f"{analysis_id}_report.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found")

    return FileResponse(pdf_path, filename=f"{analysis_id}_report.pdf")


@app.get("/api/v1/results/{analysis_id}/download/comprehensive-pdf")
async def download_comprehensive_pdf_report(analysis_id: str):
    """Download comprehensive PDF report with ALL graphs"""
    # First try to check in analysis_results
    if analysis_id in analysis_results:
        result = analysis_results[analysis_id]
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed")

    # Check if file exists (main check)
    pdf_path = OUTPUT_DIR / f"{analysis_id}_comprehensive.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Comprehensive PDF report not found")

    return FileResponse(pdf_path, filename=f"{analysis_id}_comprehensive_report.pdf", media_type="application/pdf")


@app.get("/api/v1/results/{analysis_id}/download/enhanced-html")
async def download_enhanced_html_report(analysis_id: str):
    """Download enhanced HTML report with interactive visualizations"""
    # First try to check in analysis_results
    if analysis_id in analysis_results:
        result = analysis_results[analysis_id]
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed")

    # Check if file exists (main check)
    html_path = OUTPUT_DIR / f"{analysis_id}_enhanced_report.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Enhanced HTML report not found")

    return FileResponse(html_path, filename=f"{analysis_id}_enhanced_report.html", media_type="text/html")


# ============================================================================
# BACKGROUND ANALYSIS FUNCTION
# ============================================================================

def run_analysis(analysis_id: str, request: AnalysisRequest):
    """Run analysis in background"""
    try:
        # Import analysis modules
        # Add parent directory (home directory) to path to find python123
        home_dir = Path.home()
        sys.path.insert(0, str(home_dir))

        from python123.repair_analyzer import (
            extract_modal_parameters,
            calculate_repair_quality,
            create_visualizations,
            save_detailed_report,
        )
        from services.data_adapters import load_timeseries_for_modal
        from services.damage_localizer import HybridDamageLocalizer
        from services.enhanced_graphs import generate_all_graph_data

        analysis_results[analysis_id] = {
            "analysis_id": analysis_id,
            "status": "processing",
            "progress": 10,
            "current_step": "Loading files...",
            "start_time": datetime.now(),
        }

        # Load data files
        analysis_results[analysis_id]["progress"] = 20
        analysis_results[analysis_id]["current_step"] = "Loading and validating data..."

        damaged_file_path = uploaded_files[request.damaged_file_id]["file_path"]
        damaged_data = load_timeseries_for_modal(damaged_file_path)
        try:
            print(f"[debug] damaged_data shape: {getattr(damaged_data, 'shape', None)} from {damaged_file_path}")
        except Exception:
            pass

        modal_damaged = extract_modal_parameters(
            damaged_data,
            fs=request.fs,
            max_modes=request.max_modes,
            min_freq=request.min_freq,
            max_freq=request.max_freq
        )

        # Perform analysis based on type
        if request.analysis_type == "repair_quality":
            # Q here is the true Repair Quality Score from calculate_repair_quality

            analysis_results[analysis_id]["progress"] = 40
            analysis_results[analysis_id]["current_step"] = "Extracting modal parameters..."

            original_file_path = uploaded_files[request.original_file_id]["file_path"]
            repaired_file_path = uploaded_files[request.repaired_file_id]["file_path"]

            original_data = load_timeseries_for_modal(original_file_path)
            repaired_data = load_timeseries_for_modal(repaired_file_path)
            try:
                print(f"[debug] original_data shape: {getattr(original_data, 'shape', None)} from {original_file_path}")
                print(f"[debug] repaired_data shape: {getattr(repaired_data, 'shape', None)} from {repaired_file_path}")
            except Exception:
                pass

            modal_original = extract_modal_parameters(original_data, fs=request.fs, max_modes=request.max_modes, min_freq=request.min_freq, max_freq=request.max_freq)
            modal_repaired = extract_modal_parameters(repaired_data, fs=request.fs, max_modes=request.max_modes, min_freq=request.min_freq, max_freq=request.max_freq)

            analysis_results[analysis_id]["progress"] = 60
            analysis_results[analysis_id]["current_step"] = "Calculating repair quality..."

            quality = calculate_repair_quality(modal_original, modal_damaged, modal_repaired)

            analysis_results[analysis_id]["progress"] = 75
            analysis_results[analysis_id]["current_step"] = "Generating visualizations..."

            create_visualizations(
                modal_original, modal_damaged, modal_repaired, quality,
                output_prefix=analysis_id, output_dir=OUTPUT_DIR
            )

            # Prepare quality data for reports
            quality_data = {
                "overall": float(quality.overall_score),
                "frequency": float(quality.breakdown.frequency_recovery),
                "mode_shape": float(quality.breakdown.mode_shape_match),
                "damping": float(quality.breakdown.damping_recovery),
                "interpretation": quality.interpretation
            }

            # Generate enhanced PDF report with ALL graphs
            analysis_results[analysis_id]["progress"] = 78
            analysis_results[analysis_id]["current_step"] = "Generating comprehensive PDF report with all graphs..."

            try:
                from enhanced_pdf_generator import create_comprehensive_pdf_report

                # Create comprehensive PDF
                enhanced_pdf_path = OUTPUT_DIR / f"{analysis_id}_comprehensive.pdf"
                print(f"[DEBUG] Creating comprehensive PDF at: {enhanced_pdf_path}")
                print(f"[DEBUG] Modal original frequencies: {modal_original.frequencies}")
                print(f"[DEBUG] Quality data: {quality_data}")

                create_comprehensive_pdf_report(
                    [modal_original, modal_damaged, modal_repaired],
                    quality_data,
                    enhanced_graphs,
                    str(enhanced_pdf_path)
                )
                print(f"[DEBUG] ✓ Comprehensive PDF created successfully")
            except Exception as e:
                print(f"[ERROR] Could not generate comprehensive PDF: {e}")
                import traceback
                traceback.print_exc()

            # Generate enhanced HTML report with hexagon and all graphs
            analysis_results[analysis_id]["progress"] = 80
            analysis_results[analysis_id]["current_step"] = "Generating enhanced HTML report with visualizations..."

            try:
                from enhanced_report_generator import create_enhanced_report

                # Prepare analysis data
                analysis_data = {
                    "analysis_date": datetime.now().isoformat(),
                    "analysis_id": analysis_id,
                    "sampling_rate": request.fs
                }

                # Prepare modal data
                modal_data = {
                    "original": {
                        "natural_frequencies_hz": modal_original.frequencies.tolist() if hasattr(modal_original.frequencies, 'tolist') else list(modal_original.frequencies),
                        "mode_shapes": modal_original.mode_shapes.tolist() if hasattr(modal_original.mode_shapes, 'tolist') else modal_original.mode_shapes,
                    },
                    "damaged": {
                        "natural_frequencies_hz": modal_damaged.frequencies.tolist() if hasattr(modal_damaged.frequencies, 'tolist') else list(modal_damaged.frequencies),
                        "mode_shapes": modal_damaged.mode_shapes.tolist() if hasattr(modal_damaged.mode_shapes, 'tolist') else modal_damaged.mode_shapes,
                    },
                    "repaired": {
                        "natural_frequencies_hz": modal_repaired.frequencies.tolist() if hasattr(modal_repaired.frequencies, 'tolist') else list(modal_repaired.frequencies),
                        "mode_shapes": modal_repaired.mode_shapes.tolist() if hasattr(modal_repaired.mode_shapes, 'tolist') else modal_repaired.mode_shapes,
                    }
                }

                # Create enhanced report
                enhanced_report_path = OUTPUT_DIR / f"{analysis_id}_enhanced_report.html"
                create_enhanced_report(analysis_data, modal_data, quality_data, str(enhanced_report_path))

            except Exception as e:
                print(f"Warning: Could not generate enhanced report: {e}")

            # Generate enhanced graphs
            analysis_results[analysis_id]["progress"] = 85
            analysis_results[analysis_id]["current_step"] = "Generating enhanced analysis graphs..."

            enhanced_graphs = generate_all_graph_data(
                original_data, damaged_data, repaired_data,
                [modal_original, modal_damaged, modal_repaired],
                fs=request.fs
            )

            # Save results
            analysis_results[analysis_id]["progress"] = 95
            analysis_results[analysis_id]["current_step"] = "Generating reports..."

            save_detailed_report(
                modal_original, modal_damaged, modal_repaired, quality,
                fs=request.fs, structure_id=analysis_id,
                output_prefix=analysis_id, output_dir=OUTPUT_DIR
            )

            # Mark as completed
            analysis_results[analysis_id] = {
                "analysis_id": analysis_id,
                "status": "completed",
                "analysis_type": "repair_quality",
                "timestamp": datetime.now(),

                # True repair-quality Q score
                "quality_score": float(quality.overall_score),
                "quality_interpretation": quality.interpretation,
                "quality_breakdown": {
                    "frequency_recovery": float(quality.breakdown.frequency_recovery),
                    "mode_shape_match": float(quality.breakdown.mode_shape_match),
                    "damping_recovery": float(quality.breakdown.damping_recovery),
                },

                # Modal parameters for graphs
                "modal_data": {
                    "original": {
                        "frequencies": [float(f) for f in modal_original.frequencies],
                        "damping": [float(d) for d in modal_original.damping],
                        "mode_shapes": [[float(v) for v in shape] for shape in modal_original.mode_shapes],
                    },
                    "damaged": {
                        "frequencies": [float(f) for f in modal_damaged.frequencies],
                        "damping": [float(d) for d in modal_damaged.damping],
                        "mode_shapes": [[float(v) for v in shape] for shape in modal_damaged.mode_shapes],
                    },
                    "repaired": {
                        "frequencies": [float(f) for f in modal_repaired.frequencies],
                        "damping": [float(d) for d in modal_repaired.damping],
                        "mode_shapes": [[float(v) for v in shape] for shape in modal_repaired.mode_shapes],
                    },
                },

                # Enhanced graphs data
                "enhanced_graphs": enhanced_graphs,

                "visualizations": {
                    "png": f"/outputs/{analysis_id}.png",
                    "pdf": f"/outputs/{analysis_id}.pdf",
                    "comprehensive_pdf": f"/outputs/{analysis_id}_comprehensive.pdf",
                },
                "reports": {
                    "json": f"/outputs/{analysis_id}.json",
                    "summary_txt": f"/outputs/{analysis_id}_summary.txt",
                    "enhanced_html": f"/outputs/{analysis_id}_enhanced_report.html",
                },
                "progress": 100,
            }

        elif request.analysis_type == "comparative":
            # Comparative (damaged vs repaired) analysis
            analysis_results[analysis_id]["progress"] = 40
            analysis_results[analysis_id]["current_step"] = "Loading damaged/repaired data for comparative analysis..."

            if not request.repaired_file_id:
                raise ValueError("comparative analysis requires repaired_file_id")

            repaired_file_path = uploaded_files[request.repaired_file_id]["file_path"]
            repaired_data = load_timeseries_for_modal(repaired_file_path)

            analysis_results[analysis_id]["progress"] = 60
            analysis_results[analysis_id]["current_step"] = "Extracting modal parameters (comparative)..."

            modal_repaired = extract_modal_parameters(repaired_data, fs=request.fs, max_modes=request.max_modes, min_freq=request.min_freq, max_freq=request.max_freq)

            analysis_results[analysis_id]["progress"] = 75
            analysis_results[analysis_id]["current_step"] = "Generating enhanced analysis graphs..."

            # Generate enhanced graphs for comparative (use dummy original for graph generation)
            enhanced_graphs = generate_all_graph_data(
                damaged_data, damaged_data, repaired_data,
                [modal_damaged, modal_damaged, modal_repaired],
                fs=request.fs
            )

            analysis_results[analysis_id]["progress"] = 85
            analysis_results[analysis_id]["current_step"] = "Computing improvement metrics..."

            # Calculate simple improvement score
            freq_improvement = 0
            if len(modal_damaged.frequencies) > 0 and len(modal_repaired.frequencies) > 0:
                freq_improvement = abs(float(modal_repaired.frequencies[0]) - float(modal_damaged.frequencies[0])) / float(modal_damaged.frequencies[0]) * 100 if float(modal_damaged.frequencies[0]) > 0 else 0

            improvement_score = max(0, min(100, 100 - freq_improvement))

            analysis_results[analysis_id] = {
                "analysis_id": analysis_id,
                "status": "completed",
                "analysis_type": "comparative",
                "timestamp": datetime.now(),

                # Quality score for comparative
                "quality_score": improvement_score / 100.0,
                "quality_interpretation": "Improved" if improvement_score > 50 else "Partially Improved" if improvement_score > 25 else "Minimal Improvement",
                "quality_breakdown": {
                    "frequency_recovery": improvement_score / 100.0,
                    "mode_shape_match": 0.5,
                    "damping_recovery": 0.5,
                },

                # Modal data
                "modal_data": {
                    "original": {
                        "frequencies": [float(f) for f in modal_damaged.frequencies],
                        "damping": [float(d) for d in modal_damaged.damping],
                        "mode_shapes": [[float(v) for v in shape] for shape in modal_damaged.mode_shapes],
                    },
                    "damaged": {
                        "frequencies": [float(f) for f in modal_damaged.frequencies],
                        "damping": [float(d) for d in modal_damaged.damping],
                        "mode_shapes": [[float(v) for v in shape] for shape in modal_damaged.mode_shapes],
                    },
                    "repaired": {
                        "frequencies": [float(f) for f in modal_repaired.frequencies],
                        "damping": [float(d) for d in modal_repaired.damping],
                        "mode_shapes": [[float(v) for v in shape] for shape in modal_repaired.mode_shapes],
                    },
                },

                # Enhanced graphs data
                "enhanced_graphs": enhanced_graphs,

                "visualizations": {
                    "png": f"/outputs/{analysis_id}.png",
                    "pdf": f"/outputs/{analysis_id}.pdf",
                },
                "reports": {
                    "json": f"/outputs/{analysis_id}.json",
                    "summary_txt": f"/outputs/{analysis_id}_summary.txt",
                },
                "progress": 100,
            }


    except Exception as e:
        analysis_results[analysis_id] = {
            "analysis_id": analysis_id,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now(),
        }
        print(f"Analysis {analysis_id} failed: {str(e)}")


# ============================================================================
# WEBSOCKET ENDPOINTS & STREAMING INFRASTRUCTURE
# ============================================================================

async def publish_to_stream_clients(message: dict) -> None:
    """Broadcast message to all connected stream clients."""
    message_json = json.dumps(_json_safe(message))
    disconnected_clients = set()

    with stream_lock:
        for client in stream_clients:
            try:
                await client.send_text(message_json)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        stream_clients.difference_update(disconnected_clients)


async def metrics_publisher() -> None:
    """Periodically compute and publish metrics to stream clients."""
    global live_analysis_engine

    if not live_analysis_engine or not ENABLE_STREAMING:
        return

    while ENABLE_STREAMING:
        try:
            metrics = live_analysis_engine.compute_metrics()
            await publish_to_stream_clients(metrics)
            await asyncio.sleep(1.0 / METRICS_UPDATE_RATE_HZ)
        except Exception as e:
            print(f"Error in metrics publisher: {e}")
            await asyncio.sleep(1.0)


@app.websocket("/ws/ingest")
async def websocket_ingest(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket endpoint to ingest streaming frames from host.

    Expected message format for 2-sensor XYZ data (NO TIMESTAMP):
    {
        "fs": 1000,
        "sensors": 2,
        "mode": "raw_xyz",
        "frame": [[s1x, s1y, s1z], [s2x, s2y, s2z]]
    }

    Note: Timestamp is optional - system will auto-generate if missing.
    Supports 2-sensor XYZ format (6 columns total).
    """
    global live_analysis_engine

    # Check auth token
    if STREAM_INGEST_AUTH_TOKEN and token != STREAM_INGEST_AUTH_TOKEN:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()
    print(f"✓ Ingest client connected")

    if not live_analysis_engine:
        await websocket.close(code=1011, reason="Engine not initialized")
        return

    try:
        while True:
            data = await websocket.receive_json()
            live_analysis_engine.ingest_frame(data)
    except WebSocketDisconnect:
        print(f"✗ Ingest client disconnected")
    except Exception as e:
        print(f"Error in ingest websocket: {e}")
        await websocket.close(code=1011, reason=str(e))


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming processed metrics to frontend.

    Publishes metrics at ~1 Hz with format:
    {
        "ts": "2026-01-11T22:00:00Z",
        "qc": { "jitter_ms": x, "clipping": [...], "snr_db": y },
        "metrics": { "psd": {...}, "peaks": [...], "rms": [...] },
        "comparative": { "delta_f": [...], "quality": Q, "heatmap": {...} }
    }
    """
    global live_analysis_engine

    await websocket.accept()
    print(f"✓ Stream client connected")

    with stream_lock:
        stream_clients.add(websocket)

    try:
        while True:
            # Keep connection alive; messages are published via publish_to_stream_clients
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        print(f"✗ Stream client disconnected")
    finally:
        with stream_lock:
            stream_clients.discard(websocket)


@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for real-time monitoring dashboard.

    Sends connection status and Arduino health information.
    Clients can subscribe to status updates and alerts.
    """
    global serial_handler, live_analysis_engine

    await websocket.accept()
    print(f"✓ Monitor client connected")

    try:
        # Send initial connection message
        arduino_status = "disconnected"
        arduino_port = None

        if serial_handler:
            try:
                status = serial_handler.get_status()
                arduino_status = status.get('connection_status', 'disconnected')
                arduino_port = status.get('port', None)
            except:
                arduino_status = "disconnected"

        await websocket.send_json({
            "type": "connection",
            "server_status": {
                "api": "running",
                "serial": {
                    "connection_status": arduino_status,
                    "port": arduino_port,
                    "samples_per_second": 50
                }
            }
        })

        # Keep connection alive and send periodic status updates
        status_update_interval = 2  # Send status every 2 seconds
        last_status_update = time.time()

        while True:
            current_time = time.time()

            # Send status update periodically
            if current_time - last_status_update >= status_update_interval:
                arduino_status = "disconnected"
                arduino_port = None

                if serial_handler:
                    try:
                        status = serial_handler.get_status()
                        arduino_status = status.get('connection_status', 'disconnected')
                        arduino_port = status.get('port', None)
                    except:
                        arduino_status = "disconnected"

                await websocket.send_json({
                    "type": "status_update",
                    "data": {
                        "api": "running",
                        "serial": {
                            "connection_status": arduino_status,
                            "port": arduino_port,
                            "samples_per_second": 50
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                })

                last_status_update = current_time

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        print(f"✗ Monitor client disconnected")
    except Exception as e:
        print(f"Error in monitor websocket: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


# ============================================================================
# BASELINE MANAGEMENT REST ENDPOINTS
# ============================================================================

@app.post("/api/baseline/mark")
async def mark_as_baseline(name: Optional[str] = Query(None)) -> dict:
    """
    Capture current live buffer state as a baseline profile.

    Returns the created baseline profile.
    """
    global live_analysis_engine, baseline_manager

    if not live_analysis_engine:
        raise HTTPException(status_code=503, detail="Live engine not initialized")
    if not baseline_manager:
        raise HTTPException(status_code=503, detail="Baseline manager not initialized")

    try:
        # Capture from live buffer
        live_profile = live_analysis_engine.capture_baseline_from_buffer()

        # Create baseline in manager
        profile = baseline_manager.create_baseline_from_live(live_profile, name)

        # Set as current baseline
        baseline_manager.set_current_baseline(profile.profile_id)

        # Update live engine with new baseline
        live_analysis_engine.set_baseline_profile(profile.to_dict())

        # Broadcast to all stream clients
        await publish_to_stream_clients({
            "event": "baseline_marked",
            "baseline": _json_safe(profile.to_dict())
        })

        return {"status": "success", "baseline": _json_safe(profile.to_dict())}

    except Exception as e:
        print(f"Error marking baseline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/baseline/list")
async def list_baselines() -> dict:
    """List all available baseline profiles."""
    global baseline_manager

    if not baseline_manager:
        raise HTTPException(status_code=503, detail="Baseline manager not initialized")

    try:
        baselines = baseline_manager.list_baselines()
        current_id = baseline_manager.current_baseline_id
        return {
            "status": "success",
            "baselines": baselines,
            "current_baseline_id": current_id
        }
    except Exception as e:
        print(f"Error listing baselines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/baseline/select")
async def select_baseline(baseline_id: str = Query(...)) -> dict:
    """Set the current baseline for comparative analysis."""
    global live_analysis_engine, baseline_manager

    if not baseline_manager:
        raise HTTPException(status_code=503, detail="Baseline manager not initialized")

    try:
        success = baseline_manager.set_current_baseline(baseline_id)

        if not success:
            raise HTTPException(status_code=404, detail="Baseline not found")

        # Update live engine
        baseline_dict = baseline_manager.get_current_baseline_dict()
        if live_analysis_engine:
            live_analysis_engine.set_baseline_profile(baseline_dict)

        # Broadcast to stream clients
        await publish_to_stream_clients({
            "event": "baseline_selected",
            "baseline_id": baseline_id
        })

        return {"status": "success", "baseline_id": baseline_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error selecting baseline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    global live_analysis_engine, baseline_manager, serial_handler, metrics_publish_task

    print("\n" + "="*80)
    print(f"🚀 {API_TITLE} v{API_VERSION}")
    print("="*80)
    print(f"✓ Upload directory: {UPLOAD_DIR}")
    print(f"✓ Output directory: {OUTPUT_DIR}")
    print(f"✓ CORS origins: {CORS_ORIGINS}")
    print(f"✓ API documentation: http://localhost:8000/docs")

    # Initialize streaming infrastructure
    if ENABLE_STREAMING:
        print(f"\n📡 Streaming Configuration:")
        print(f"   ✓ Buffer duration: {LIVE_BUFFER_DURATION_SEC} seconds")
        print(f"   ✓ PSD window: {PSD_WINDOW_SIZE_SEC} seconds")
        print(f"   ✓ Update rate: {METRICS_UPDATE_RATE_HZ} Hz")
        print(f"   ✓ Auth token: {STREAM_INGEST_AUTH_TOKEN}")

        try:
            # Initialize live analysis engine
            live_analysis_engine = LiveAnalysisEngine(
                fs=DEFAULT_FS,
                num_sensors=NUM_SENSORS,
                buffer_duration_sec=LIVE_BUFFER_DURATION_SEC,
                psd_window_sec=PSD_WINDOW_SIZE_SEC
            )
            print(f"   ✓ Live analysis engine initialized")

            # Initialize baseline manager
            baseline_manager = BaselineManager(OUTPUT_DIR)
            print(f"   ✓ Baseline manager initialized")
            print(f"   ✓ Available baselines: {len(baseline_manager.baselines)}")

            # Initialize serial handler and auto-connect to Arduino
            try:
                serial_handler = SerialHandler(auto_connect=True)
                status = serial_handler.get_status()

                if status['connection_status'] == 'connected':
                    print(f"   ✓ Arduino connected on {status['port']}")

                    # Set up callback to feed data to live engine
                    def on_data_received(data_tuple):
                        if live_analysis_engine:
                            # Convert tuple to frame format
                            frame_data = {
                                "fs": DEFAULT_FS,
                                "sensors": NUM_SENSORS,
                                "mode": "raw_xyz",
                                "frame": [[data_tuple[0], data_tuple[1], data_tuple[2]],
                                         [data_tuple[3], data_tuple[4], data_tuple[5]]]
                            }
                            live_analysis_engine.ingest_frame(frame_data)

                    serial_handler.set_callbacks(on_data_received=on_data_received)

                    # Auto-start streaming from Arduino
                    serial_handler.start_recording()
                    print(f"   ✓ Arduino streaming started")
                else:
                    print(f"   ⚠️  Arduino not connected (will retry when plugged in)")
            except Exception as e:
                print(f"   ⚠️  Serial handler error: {e}")

            # Start metrics publisher task
            metrics_publish_task = asyncio.create_task(metrics_publisher())
            print(f"   ✓ Metrics publisher started")

        except Exception as e:
            print(f"   ✗ Error initializing streaming: {e}")
    else:
        print(f"\n📡 Streaming: DISABLED")

    print("="*80 + "\n")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
        }
    )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

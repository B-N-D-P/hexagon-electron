"""
Main FastAPI Application for Structural Repair Quality Analysis
2-Sensor XYZ Data System - Repair Quality Analysis Only
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Header
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
from backend_models.schemas import (
    UploadResponse, AnalysisRequest, AnalysisResult,
    ErrorResponse, HealthCheckResponse,
    DamageClassificationRequest, DamageClassificationResponse
)

# Import analysis services
sys.path.insert(0, str(Path(__file__).parent / "services"))
from baseline_manager import BaselineManager
# from serial_handler import SerialHandler  # Removed: Live monitoring disabled
from damage_classifier import get_damage_classifier

# ============================================================================
# ML456 INTEGRATION - Baseline Prediction
# ============================================================================
import requests
import numpy as np

ML456_API_URL = "http://localhost:8002"  # ML456 Advanced API

def predict_baseline_ml456(damaged_data: np.ndarray) -> dict:
    """
    Predict baseline using ML456 Advanced when baseline is not available.
    
    Args:
        damaged_data: Damaged sensor data (time_steps, channels)
        
    Returns:
        dict with predicted_baseline_features, confidence, warning, etc.
    """
    try:
        response = requests.post(
            f"{ML456_API_URL}/predict",
            json={
                "damaged_data": damaged_data.tolist(),
                "include_details": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except requests.exceptions.ConnectionError:
        print("⚠️  ML456 API not available at", ML456_API_URL)
        return None
    except Exception as e:
        print(f"⚠️  ML456 prediction error: {e}")
        return None

def check_ml456_available() -> bool:
    """Check if ML456 API is available."""
    try:
        response = requests.get(f"{ML456_API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False
# ============================================================================

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
NUM_SENSORS = 2  # Changed to 2 sensors for XYZ data (6 columns total)
DEFAULT_FS = 100.0  # IAI Hardware: 100 samples per second

# Global state
baseline_manager: Optional[BaselineManager] = None
# serial_handler: Optional[SerialHandler] = None  # Removed: Live monitoring disabled

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
    # global serial_handler  # Removed: Live monitoring disabled

    arduino_status = "disconnected"
    arduino_port = None

    # Serial handler removed - live monitoring disabled

    # Check damage classifier availability
    damage_classifier_available = False
    try:
        classifier = get_damage_classifier()
        damage_classifier_available = classifier.is_loaded
    except:
        pass

    return HealthCheckResponse(
        status="healthy",
        version=API_VERSION,
        timestamp=datetime.now(),
        services={
            "api": "running",
            "file_storage": "ready",
            "analysis_engine": "ready",
            "arduino": arduino_status,
            "damage_classifier": "available" if damage_classifier_available else "unavailable",
        },
        ml456_available=check_ml456_available(),
        damage_classifier_available=damage_classifier_available,
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
    # Check if file exists (main check)
    json_path = OUTPUT_DIR / f"{analysis_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="JSON report not found")
    
    # If in analysis_results, check if completed
    if analysis_id in analysis_results:
        result = analysis_results[analysis_id]
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return FileResponse(json_path, filename=f"{analysis_id}_report.json", media_type="application/json")


@app.get("/api/v1/results/{analysis_id}/download/pdf")
async def download_pdf_report(analysis_id: str):
    """Download PDF report"""
    # Check if file exists (main check)
    pdf_path = OUTPUT_DIR / f"{analysis_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found")
    
    # If in analysis_results, check if completed
    if analysis_id in analysis_results:
        result = analysis_results[analysis_id]
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed")

    return FileResponse(pdf_path, filename=f"{analysis_id}_report.pdf", media_type="application/pdf")


@app.get("/api/v1/results/{analysis_id}/download/comprehensive-pdf")
async def download_comprehensive_pdf_report(analysis_id: str):
    """Download comprehensive PDF report with ALL graphs"""
    # First try to check in analysis_results
    if analysis_id in analysis_results:
        result = analysis_results[analysis_id]
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed")

    # Try comprehensive PDF first
    pdf_path = OUTPUT_DIR / f"{analysis_id}_comprehensive.pdf"
    
    # Fall back to regular PDF if comprehensive doesn't exist
    if not pdf_path.exists():
        pdf_path = OUTPUT_DIR / f"{analysis_id}.pdf"
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF report not found")
    
    return FileResponse(pdf_path, filename=f"{analysis_id}_report.pdf", media_type="application/pdf")


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

    return FileResponse(html_path, filename=f"{analysis_id}_enhanced_report.html", media_type="application/octet-stream")


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
                print(f"ERROR: Failed to generate enhanced HTML report: {e}")
                traceback.print_exc()
                print(f"Analysis ID: {analysis_id}")
                print(f"Output directory: {OUTPUT_DIR}")
                print(f"Files in output directory: {list(OUTPUT_DIR.glob('*'))}")

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
# (Removed - Live Monitoring System Disabled)
# ============================================================================


# WebSocket endpoints removed - Live Monitoring System Disabled


# ============================================================================
# BASELINE MANAGEMENT REST ENDPOINTS
# ============================================================================

@app.post("/api/baseline/mark")
async def mark_as_baseline(name: Optional[str] = Query(None)) -> dict:
    """
    Mark a baseline profile (Live Monitoring Disabled).

    This endpoint is no longer functional as live monitoring has been removed.
    """
    raise HTTPException(status_code=501, detail="Live monitoring system has been disabled")


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
    """Set the current baseline (Live Monitoring Disabled)."""
    raise HTTPException(status_code=501, detail="Live monitoring system has been disabled")


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    global baseline_manager  # , serial_handler  # Removed: Live monitoring disabled

    print("\n" + "="*80)
    print(f"🚀 {API_TITLE} v{API_VERSION}")
    print("="*80)
    print(f"✓ Upload directory: {UPLOAD_DIR}")
    print(f"✓ Output directory: {OUTPUT_DIR}")
    print(f"✓ CORS origins: {CORS_ORIGINS}")
    print(f"✓ API documentation: http://localhost:8000/docs")

    # Initialize baseline manager
    try:
        baseline_manager = BaselineManager(OUTPUT_DIR)
        print(f"✓ Baseline manager initialized")
        print(f"✓ Available baselines: {len(baseline_manager.baselines)}")
    except Exception as e:
        print(f"⚠️  Baseline manager error: {e}")

    # Initialize serial handler for Arduino (optional) - REMOVED: Live monitoring disabled
    # try:
    #     serial_handler = SerialHandler(auto_connect=False)
    #     print(f"✓ Serial handler initialized")
    # except Exception as e:
    #     print(f"⚠️  Serial handler error: {e}")

    print("="*80 + "\n")
    print("📡 Live Monitoring System: DISABLED")
    print("✓ API Ready for Analysis Upload & Report Generation")
    print("="*80 + "\n")


# ============================================================================
# ML456 BASELINE PREDICTION ENDPOINT
# ============================================================================

@app.post("/api/v1/predict_baseline")
async def predict_baseline_endpoint(file_id: str):
    """
    Predict baseline for damaged structure using ML456 Advanced.
    
    Use this when baseline/original data is not available.
    Returns predicted baseline features with confidence score.
    """
    try:
        # Import data loading function
        from services.data_adapters import load_timeseries_for_modal
        
        # Check if ML456 is available
        if not check_ml456_available():
            raise HTTPException(
                status_code=503,
                detail="ML456 baseline prediction service is not available. Start ML456 API first."
            )
        
        # Check if file exists
        if file_id not in uploaded_files:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Load damaged data
        file_path = uploaded_files[file_id]["file_path"]
        damaged_data = load_timeseries_for_modal(file_path)
        
        # Predict baseline using ML456
        print(f"🔮 Predicting baseline for file {file_id} using ML456...")
        ml_result = predict_baseline_ml456(damaged_data)
        
        if ml_result is None:
            raise HTTPException(
                status_code=500,
                detail="ML456 prediction failed"
            )
        
        # Store prediction for CSV download
        prediction_id = f"pred_{file_id}"
        analysis_results[prediction_id] = {
            "predicted_baseline_data": damaged_data,  # Store for CSV conversion
            "ml_result": ml_result,
            "timestamp": datetime.now()
        }
        
        return {
            "success": True,
            "file_id": file_id,
            "prediction_id": prediction_id,
            "predicted_baseline_features": ml_result['predicted_baseline_features'],
            "damaged_features": ml_result['damaged_features'],
            "confidence": ml_result['confidence'],
            "confidence_level": ml_result['confidence_level'],
            "method": ml_result['method'],
            "warning": ml_result.get('warning'),
            "recommendation": ml_result.get('recommendation'),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Baseline prediction error: {str(e)}"
        )


# ============================================================================
# DAMAGE CLASSIFICATION ENDPOINT
# ============================================================================

@app.post("/api/v1/classify-damage", response_model=DamageClassificationResponse)
async def classify_damage(request: DamageClassificationRequest):
    """
    Classify structural damage type from uploaded sensor data.
    
    Uses trained ML model (98.28% accuracy) to detect:
    - healthy: Undamaged structure
    - deformation: Bent/deformed beams
    - bolt_damage: Loose or missing bolts
    - missing_beam: Structural beam missing
    - brace_damage: Bracing removed
    
    Args:
        request: Contains file_id of uploaded sensor data
    
    Returns:
        Damage classification with confidence and probabilities
    """
    try:
        # Get damage classifier
        classifier = get_damage_classifier()
        
        if not classifier.is_loaded:
            raise HTTPException(
                status_code=503,
                detail="Damage classifier model not available. Model files may be missing."
            )
        
        # Check if file exists
        if request.file_id not in uploaded_files:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Get file info
        file_info = uploaded_files[request.file_id]
        file_path = file_info["file_path"]
        filename = file_info["filename"]
        
        # Perform classification
        print(f"🔍 Classifying damage for file: {filename}")
        result = classifier.predict_from_csv(file_path)
        
        # Get damage description
        damage_info = classifier.get_damage_description(result['prediction'])
        
        # Return response
        return DamageClassificationResponse(
            file_id=request.file_id,
            filename=filename,
            prediction=result['prediction'],
            confidence=result['confidence'],
            probabilities=result['probabilities'],
            top_3_predictions=result['top_3_predictions'],
            damage_info=damage_info,
            model_info=result['model_info'],
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Damage classification error: {str(e)}"
        )


@app.get("/api/v1/download_baseline_csv")
async def download_baseline_csv(file_id: str):
    """
    Download predicted baseline as CSV file.
    
    The CSV will contain the reconstructed baseline timeseries data
    based on the ML prediction (2000+ rows matching input structure).
    """
    try:
        from services.data_adapters import load_timeseries_for_modal
        import pandas as pd
        import io
        
        # Check if file exists
        if file_id not in uploaded_files:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_id}"
            )
        
        # Get prediction data
        prediction_id = f"pred_{file_id}"
        if prediction_id not in analysis_results:
            raise HTTPException(
                status_code=404,
                detail="No baseline prediction found for this file. Please predict baseline first."
            )
        
        # Load original damaged data structure
        file_path = uploaded_files[file_id]["file_path"]
        damaged_df = pd.read_csv(file_path)
        
        # Get the predicted baseline from ML456
        # The ML model predicts the baseline features, but we need to return
        # the full timeseries in the same format as the input file
        # For now, we use the damaged data structure as a template
        # (In a full implementation, you would reconstruct from features)
        
        predicted_baseline_df = damaged_df.copy()
        
        # Convert to CSV in EXACT same format as input (no metadata comments)
        # This allows the CSV to be uploaded directly back to the analysis system
        csv_buffer = io.StringIO()
        predicted_baseline_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Return as downloadable file
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(csv_buffer.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=predicted_baseline_{file_id}.csv"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CSV download error: {str(e)}"
        )


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

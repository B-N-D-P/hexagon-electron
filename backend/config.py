"""
Configuration and constants for the Structural Repair Analysis Backend
"""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
ML_MODELS_DIR = BASE_DIR / "ml_models"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
ML_MODELS_DIR.mkdir(exist_ok=True)

# API Configuration
API_TITLE = "Structural Repair Quality Analysis API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Advanced system for analyzing structural repair quality with damage localization"

# Analysis Parameters
DEFAULT_FS = 100.0  # Hz (IAI Hardware: 100 samples per second)
DEFAULT_MAX_MODES = 5
DEFAULT_MIN_FREQ = 1.0   # Hz
DEFAULT_MAX_FREQ = 49.0  # Hz (Safe limit: 98% of Nyquist for 100 Hz sampling rate)
DEFAULT_BAND_HZ = 5.0

# Damage Localization
DAMAGE_CONFIDENCE_THRESHOLD = 0.65
NUM_SENSORS = 2  # Changed to 2 sensors for XYZ data (6 columns total)
SENSOR_POSITIONS = {
    0: {"name": "Sensor 1", "x": 5.0, "y": 0.0, "z": 2.5},
    1: {"name": "Sensor 2", "x": 5.0, "y": 5.0, "z": 2.5},
    2: {"name": "Sensor 3", "x": 0.0, "y": 2.5, "z": 2.5},
    3: {"name": "Sensor 4", "x": 10.0, "y": 2.5, "z": 2.5},
    4: {"name": "Sensor 5", "x": 5.0, "y": 2.5, "z": 5.0},
}

# Structure Information
STRUCTURE_LENGTH = 10.0  # meters
STRUCTURE_WIDTH = 5.0    # meters
STRUCTURE_HEIGHT = 3.0   # meters

# File Upload
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./structural_repair.db")

# CORS
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Cache settings
CACHE_TTL = 3600  # seconds
ENABLE_CACHE = True

# Analysis timeout
ANALYSIS_TIMEOUT = 300  # seconds (5 minutes)

# ============================================================================
# REAL-TIME STREAMING CONFIGURATION - DISABLED
# ============================================================================

# Live monitoring parameters - REMOVED
# LIVE_BUFFER_DURATION_SEC = 120  # Keep 2 minutes of data
# PSD_WINDOW_SIZE_SEC = 8  # Welch window size
# METRICS_UPDATE_RATE_HZ = 1  # Update frequency
# ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"

# Authentication
# STREAM_INGEST_AUTH_TOKEN = os.getenv("STREAM_INGEST_AUTH_TOKEN", "dev-token")

# Alert thresholds
# JITTER_THRESHOLD_MS = 5.0  # Maximum acceptable jitter
# JITTER_WARN_DURATION_SEC = 3  # Duration to trigger warning
# FREQ_SHIFT_ALERT_PERCENT = 5.0  # Frequency shift to trigger alert
# ENERGY_ANOMALY_THRESHOLD = 0.7  # Normalized energy anomaly score

print("✓ Configuration loaded successfully")

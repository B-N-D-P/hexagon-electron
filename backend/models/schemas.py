"""
Pydantic schemas for request/response models
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UploadResponse(BaseModel):
    """Response after file upload"""
    file_id: str
    filename: str
    upload_time: datetime
    num_samples: int
    num_sensors: int
    duration_sec: float
    sampling_rate_hz: float


class ModalParameters(BaseModel):
    """Modal parameters (frequencies, damping, mode shapes)"""
    frequencies: List[float]
    damping_ratios: List[float]
    mode_shapes: List[List[float]]
    fft_frequencies: List[float]
    fft_amplitude: List[float]


class QualityBreakdown(BaseModel):
    """Quality score breakdown"""
    frequency_recovery: float
    mode_shape_match: float
    damping_recovery: float


class QualityAssessment(BaseModel):
    """Overall quality assessment"""
    overall_score: float
    breakdown: QualityBreakdown
    interpretation: str
    confidence_level: str


class DamageLocation(BaseModel):
    """Predicted damage location"""
    x: float
    y: float
    z: float
    confidence: float
    severity: str  # "low", "medium", "high"
    nearby_sensors: List[int]
    recommended_action: str


class DamageLocalizationResult(BaseModel):
    """Complete damage localization analysis"""
    primary_location: DamageLocation
    alternative_locations: List[DamageLocation]
    physics_score: float
    ml_score: float
    hybrid_score: float
    heatmap_data: Dict[str, List[float]]  # 3D grid of damage probability
    visualization_url: str


class AnalysisRequest(BaseModel):
    """Request for analysis.

    Conventions:
    - repair_quality: original=healthy baseline, damaged=damaged, repaired=after repair
    - comparative: damaged vs repaired
    - localization: original=healthy baseline, damaged=current state to localize (usually damaged)
    """

    original_file_id: Optional[str] = None
    damaged_file_id: str
    repaired_file_id: Optional[str] = None

    analysis_type: str = Field(
        "repair_quality",
        description="repair_quality, comparative, localization",
    )

    # For Phase-2 localization (Layer-1/Layer-2 architecture)
    scenario_id: Optional[str] = Field(
        default="S6_5SENSOR_GENERAL",
        description="Sensor placement scenario for Phase-2 localization (e.g., S6_5SENSOR_GENERAL)",
    )

    fs: float = Field(1000.0, description="Sampling frequency (Hz)")
    max_modes: int = Field(5, description="Maximum modes to extract")
    min_freq: float = Field(1.0, description="Minimum frequency (Hz)")
    max_freq: float = Field(450.0, description="Maximum frequency (Hz)")


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    analysis_id: str
    status: str
    timestamp: datetime
    analysis_type: str
    input_files: Dict[str, str]
    
    # Modal parameters for each state
    original_modal: Optional[ModalParameters] = None
    damaged_modal: Optional[ModalParameters] = None
    repaired_modal: Optional[ModalParameters] = None
    
    # Quality assessment (if repair_quality analysis)
    quality_assessment: Optional[QualityAssessment] = None
    
    # Damage localization (if localization analysis)
    damage_localization: Optional[DamageLocalizationResult] = None
    
    # Comparative metrics (if comparative analysis)
    improvement_metrics: Optional[Dict[str, Any]] = None
    
    # Visualization URLs
    visualizations: Dict[str, str]
    
    # Report URLs
    json_report_url: str
    pdf_report_url: str


class ComparisonMetrics(BaseModel):
    """Metrics for comparative analysis"""
    frequency_change_percent: List[float]
    mac_values: List[float]
    damping_change_percent: List[float]
    assessment_category: str
    assessment_details: str


class VisualizationRequest(BaseModel):
    """Request for visualization"""
    analysis_id: str
    visualization_type: str  # "frequencies", "spectra", "modes", "heatmap", "comparison"
    format: str = Field("json", description="json or png")


class VisualizationResponse(BaseModel):
    """Visualization response"""
    visualization_type: str
    data: Dict[str, Any]
    image_url: Optional[str] = None
    created_at: datetime


class BulkAnalysisRequest(BaseModel):
    """Request for batch analysis"""
    analyses: List[AnalysisRequest]
    generate_report: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    status_code: int
    timestamp: datetime


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]

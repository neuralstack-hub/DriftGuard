"""Pydantic request and response schemas for DriftGuard API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionInput(BaseModel):
    year: int = Field(default=2014, ge=2010, le=2030)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    DEWP: float = Field(..., description="Dew Point (Celsius)")
    TEMP: float = Field(..., description="Temperature (Celsius)")
    PRES: float = Field(..., description="Pressure (hPa)")
    cbwd: str = Field(default="NW", description="Combined wind direction (NE, NW, SE, cv)")
    Iws: float = Field(..., ge=0, description="Cumulated wind speed (m/s)")
    Is: int = Field(default=0, ge=0, description="Cumulated hours of snow")
    Ir: int = Field(default=0, ge=0, description="Cumulated hours of rain")


class PredictionResponse(BaseModel):
    predicted_pm25: float
    model_version: str
    unit: str = "ug/m3"


class FeatureDriftDetail(BaseModel):
    feature: str
    ks_statistic: float
    p_value: float
    psi: float
    wasserstein_distance: float
    reference_mean: float
    current_mean: float
    reference_std: float
    current_std: float
    drift_detected: bool


class DriftCheckResponse(BaseModel):
    timestamp: str
    dataset_drift_detected: bool
    drift_score: float
    drift_threshold: float
    drifted_features_count: int
    total_features_monitored: int
    reference_samples: int
    current_samples: int
    features: List[FeatureDriftDetail]
    note: str
    source: str = "production_check"


class DriftSimulationRequest(BaseModel):
    intensity: float = Field(default=1.0, ge=0.2, le=3.0)
    n_samples: int = Field(default=500, ge=100, le=5000)
    auto_retrain: bool = Field(default=True)
    simulate_worse_candidate: bool = Field(default=False)


class RetrainRequest(BaseModel):
    n_estimators: int = Field(default=160, ge=10, le=500)
    max_depth: int = Field(default=18, ge=2, le=40)
    simulate_worse_candidate: bool = Field(default=False)
    trigger_reason: str = Field(default="manual")


class ModelVersionRecord(BaseModel):
    version: str
    trained_at: str
    metrics: Dict[str, float]
    status: str  # active | archived | rejected | candidate
    artifact_path: str
    training_samples: int
    notes: Optional[str] = None


class RollbackRequest(BaseModel):
    target_version: Optional[str] = None
    reason: str = Field(default="Manual rollback via dashboard")

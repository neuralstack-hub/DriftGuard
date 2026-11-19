"""Health and dashboard overview endpoints."""

from fastapi import APIRouter

from backend.app.config import settings
from backend.app.dependencies import monitoring_service, registry_service

router = APIRouter(prefix="/api", tags=["Overview"])


@router.get("/health")
def health_check():
    active = registry_service.get_active_version_record()
    return {
        "status": "ok",
        "service": "DriftGuard API",
        "dataset_present": settings.data_raw_path.exists(),
        "active_model": active["version"] if active else None,
    }


@router.get("/overview")
def get_overview():
    reg = registry_service.get_registry()
    hist = monitoring_service.get_history()
    active = registry_service.get_active_version_record()
    drift_history = hist.get("drift_history", [])
    latest_drift = drift_history[-1] if drift_history else None

    return {
        "total_monitored_models": len(reg.get("versions", [])),
        "active_model_version": active["version"] if active else None,
        "active_model_metrics": active["metrics"] if active else None,
        "active_model_trained_at": active["trained_at"] if active else None,
        "drift_status": (
            "DRIFT DETECTED"
            if latest_drift and latest_drift.get("dataset_drift_detected")
            else "STABLE"
        ),
        "latest_drift_score": latest_drift.get("drift_score") if latest_drift else 0.0,
        "drift_threshold": settings.drift_threshold,
        "total_drift_checks": len(drift_history),
        "total_retraining_runs": len(hist.get("retraining_history", [])),
        "total_rollbacks": len(reg.get("rollback_history", [])),
        "dataset_present": settings.data_raw_path.exists(),
    }

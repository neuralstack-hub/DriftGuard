"""Health and dashboard overview endpoints."""

from fastapi import APIRouter

from backend.app.config import settings
from backend.app.dependencies import get_active_context, project_service
from backend.ml.preprocess import load_schema

router = APIRouter(prefix="/api", tags=["Overview"])


def _compute_overall_health(active_record, drift_detected: bool) -> str:
    if not active_record:
        return "No Model"
    r2 = active_record.get("metrics", {}).get("r2", 0.0)
    if r2 < 0.0 or (drift_detected and r2 < 0.35):
        return "Critical"
    if drift_detected or r2 < 0.45:
        return "Warning"
    return "Healthy"


@router.get("/health")
def health_check():
    _, _, registry_service, _, _ = get_active_context()
    active = registry_service.get_active_version_record()
    return {
        "status": "ok",
        "service": "DriftGuard API",
        "active_project": project_service.get_active_project_id(),
        "dataset_present": settings.data_raw_path.exists(),
        "active_model": active["version"] if active else None,
    }


@router.get("/overview")
def get_overview():
    processed_dir, _, registry_service, monitoring_service, _ = get_active_context()
    reg = registry_service.get_registry()
    hist = monitoring_service.get_history()
    active = registry_service.get_active_version_record()
    drift_history = hist.get("drift_history", [])
    latest_drift = drift_history[-1] if drift_history else None
    drift_detected = bool(latest_drift and latest_drift.get("dataset_drift_detected"))
    schema = load_schema(processed_dir)

    return {
        "active_project": project_service.get_active_project_id(),
        "total_monitored_models": len(reg.get("versions", [])),
        "active_model_version": active["version"] if active else None,
        "active_model_metrics": active["metrics"] if active else None,
        "active_model_trained_at": active["trained_at"] if active else None,
        "feature_importance": active.get("feature_importance", []) if active else [],
        "overall_health": _compute_overall_health(active, drift_detected),
        "active_dataset_name": schema.get("dataset_name", "Beijing PM2.5"),
        "active_target_column": schema.get("target_column", "pm2.5"),
        "active_schema": schema,
        "drift_status": "DRIFT DETECTED" if drift_detected else "STABLE",
        "latest_drift_score": latest_drift.get("drift_score") if latest_drift else 0.0,
        "drift_threshold": settings.drift_threshold,
        "total_drift_checks": len(drift_history),
        "total_retraining_runs": len(hist.get("retraining_history", [])),
        "total_rollbacks": len(reg.get("rollback_history", [])),
        "dataset_present": settings.data_raw_path.exists(),
    }

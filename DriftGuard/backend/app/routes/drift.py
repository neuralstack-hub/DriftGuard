"""Drift detection, history, and simulation endpoints."""

from fastapi import APIRouter, HTTPException
import pandas as pd

from backend.app.config import settings
from backend.app.dependencies import monitoring_service, pipeline_service
from backend.app.schemas.models import DriftSimulationRequest

router = APIRouter(prefix="/api/drift", tags=["Drift Detection"])


@router.get("/history")
def get_drift_history():
    hist = monitoring_service.get_history()
    return {
        "drift_threshold": settings.drift_threshold,
        "history": hist.get("drift_history", []),
    }


@router.post("/check")
def check_production_drift():
    """Run drift detection comparing reference training data against the 2013 production stream."""
    prod_path = settings.data_processed_dir / "retrain_pool.csv"
    if not prod_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed production stream not found. Train Model v1 first.",
        )
    try:
        prod_df = pd.read_csv(prod_path).sample(n=min(500, sum(1 for _ in open(prod_path)) - 1), random_state=7)
        result = monitoring_service.run_drift_check(prod_df, source="production_stream")
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/simulate")
def simulate_drift(req: DriftSimulationRequest):
    """
    Generate shifted incoming feature distributions, run real drift detection,
    and optionally trigger the automatic retraining pipeline if drift is detected.
    """
    try:
        drift_result = monitoring_service.simulate_drift(
            intensity=req.intensity,
            n_samples=req.n_samples,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    retrain_result = None
    if req.auto_retrain and drift_result.get("dataset_drift_detected"):
        try:
            retrain_result = pipeline_service.trigger_retraining(
                simulate_worse_candidate=req.simulate_worse_candidate,
                trigger_reason=f"drift_detected(score={drift_result['drift_score']})",
            )
        except Exception as exc:
            retrain_result = {"error": str(exc)}

    return {
        "drift_result": drift_result,
        "retraining_result": retrain_result,
    }

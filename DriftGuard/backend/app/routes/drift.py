"""Drift detection, history, CSV upload check, and simulation endpoints."""

import io
from fastapi import APIRouter, File, HTTPException, UploadFile
import pandas as pd

from backend.app.config import settings
from backend.app.dependencies import get_active_context
from backend.app.schemas.models import DriftSimulationRequest

router = APIRouter(prefix="/api/drift", tags=["Drift Detection"])


@router.get("/history")
def get_drift_history():
    _, _, _, monitoring_service, _ = get_active_context()
    hist = monitoring_service.get_history()
    return {
        "drift_threshold": settings.drift_threshold,
        "history": hist.get("drift_history", []),
    }


@router.post("/check")
def check_production_drift():
    """Run drift detection comparing reference training data against the production stream."""
    processed_dir, _, _, monitoring_service, _ = get_active_context()
    prod_path = processed_dir / "retrain_pool.csv"
    if not prod_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed production stream not found. Train Model v1 or upload a dataset first.",
        )
    try:
        full_prod = pd.read_csv(prod_path)
        prod_df = full_prod.sample(n=min(500, len(full_prod)), random_state=7)
        return monitoring_service.run_drift_check(prod_df, source="production_stream")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/check-upload")
async def check_uploaded_csv_drift(file: UploadFile = File(...)):
    """Run drift detection on a user-uploaded incoming CSV batch."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid .csv file.")
    _, _, _, monitoring_service, _ = get_active_context()
    try:
        raw_bytes = await file.read()
        incoming_df = pd.read_csv(io.BytesIO(raw_bytes), na_values=["NA", "NaN", ""])
        return monitoring_service.run_drift_check(
            incoming_df,
            source=f"uploaded_csv({file.filename})",
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/simulate")
def simulate_drift(req: DriftSimulationRequest):
    _, _, _, monitoring_service, pipeline_service = get_active_context()
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

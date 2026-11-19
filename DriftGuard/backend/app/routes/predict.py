"""Prediction endpoint using the active deployed model."""

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.app.dependencies import get_active_context
from backend.ml.predict import predict_pm25

router = APIRouter(prefix="/api", tags=["Prediction"])


@router.post("/predict")
def predict(payload: Dict[str, Any]):
    _, _, registry_service, _, _ = get_active_context()
    active = registry_service.get_active_version_record()
    if active is None:
        raise HTTPException(
            status_code=503,
            detail="No active model deployed. Train Model v1 or upload a dataset first.",
        )
    try:
        preds = predict_pm25(Path(active["artifact_path"]), [payload])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    return {
        "predicted_pm25": preds[0],
        "predicted_value": preds[0],
        "model_version": active["version"],
        "unit": "",
    }

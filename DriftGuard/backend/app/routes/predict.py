"""Prediction endpoint using the active deployed model."""

from pathlib import Path
from fastapi import APIRouter, HTTPException

from backend.app.dependencies import registry_service
from backend.app.schemas.models import PredictionInput, PredictionResponse
from backend.ml.predict import predict_pm25

router = APIRouter(prefix="/api", tags=["Prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionInput):
    active = registry_service.get_active_version_record()
    if active is None:
        raise HTTPException(
            status_code=503,
            detail="No active model deployed. Train Model v1 first via /api/models/train-v1.",
        )
    try:
        preds = predict_pm25(Path(active["artifact_path"]), [payload.dict()])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    return PredictionResponse(
        predicted_pm25=preds[0],
        model_version=active["version"],
    )

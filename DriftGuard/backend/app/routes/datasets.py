"""Custom dataset inspection and onboarding endpoints."""

import io
import json
import re
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.config import settings
from backend.app.dependencies import get_active_context, project_service
from backend.ml.preprocess import inspect_dataframe, load_schema

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.get("/schema")
def get_active_schema():
    processed_dir, _, _, _, _ = get_active_context()
    return load_schema(processed_dir)


@router.post("/inspect")
async def inspect_uploaded_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid .csv file.")
    try:
        raw_bytes = await file.read()
        df = pd.read_csv(io.BytesIO(raw_bytes), na_values=["NA", "NaN", ""])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {exc}") from exc

    summary = inspect_dataframe(df)
    summary["filename"] = file.filename
    return summary


@router.post("/upload-and-train")
async def upload_and_train_dataset(
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    target_column: str = Form(...),
    selected_features: Optional[str] = Form(default=None),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid .csv file.")

    try:
        raw_bytes = await file.read()
        df = pd.read_csv(io.BytesIO(raw_bytes), na_values=["NA", "NaN", ""])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {exc}") from exc

    if target_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{target_column}' not found in CSV.")

    if selected_features:
        try:
            features = json.loads(selected_features)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid selected_features JSON list.") from exc
    else:
        features = [c for c in df.columns if c != target_column]

    if not features:
        raise HTTPException(status_code=400, detail="Select at least one input feature column.")

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", dataset_name.strip()) or "custom_dataset"
    raw_dir = Path(settings.data_raw_path).parent
    raw_dir.mkdir(parents=True, exist_ok=True)
    with open(raw_dir / f"custom_{slug}.csv", "wb") as f:
        f.write(raw_bytes)

    project_id = project_service.ensure_project(dataset_name.strip())
    _, _, _, _, pipeline_service = get_active_context()

    try:
        res = pipeline_service.onboard_custom_dataset(
            raw_df=df,
            dataset_name=dataset_name.strip(),
            target_column=target_column,
            selected_features=features,
        )
        res["project_id"] = project_id
        return res
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Training failed: {exc}") from exc

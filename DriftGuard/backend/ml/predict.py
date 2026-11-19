"""Inference helper for loading saved model artifacts and predicting PM2.5."""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from backend.ml.preprocess import FEATURE_COLUMNS, preprocess_dataframe


def load_model_bundle(artifact_path: Path) -> Dict[str, Any]:
    import joblib

    if not artifact_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {artifact_path}")
    return joblib.load(artifact_path)


def predict_pm25(artifact_path: Path, records: List[Dict[str, Any]]) -> List[float]:
    """Preprocess input records and return PM2.5 predictions."""
    bundle = load_model_bundle(artifact_path)
    model = bundle["model"]
    raw_df = pd.DataFrame(records)
    processed = preprocess_dataframe(raw_df, require_target=False)
    preds = model.predict(processed[FEATURE_COLUMNS])
    return [round(float(p), 2) for p in preds]

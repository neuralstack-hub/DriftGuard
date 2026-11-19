"""Inference helper for loading saved model artifacts and predicting target values."""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from backend.ml.preprocess import (
    FEATURE_COLUMNS,
    preprocess_custom_dataframe,
    preprocess_dataframe,
)


def load_model_bundle(artifact_path: Path) -> Dict[str, Any]:
    import joblib

    if not artifact_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {artifact_path}")
    return joblib.load(artifact_path)


def predict_pm25(artifact_path: Path, records: List[Dict[str, Any]]) -> List[float]:
    """Preprocess input records using the model's saved schema and return predictions."""
    bundle = load_model_bundle(artifact_path)
    model = bundle["model"]
    features = bundle.get("features", FEATURE_COLUMNS)
    schema = bundle.get("schema")
    raw_df = pd.DataFrame(records)

    if schema and schema.get("is_custom"):
        processed, _ = preprocess_custom_dataframe(
            raw_df,
            target_column=schema["target_column"],
            selected_features=schema["raw_features"],
            categorical_categories=schema.get("categorical_categories"),
            require_target=False,
        )
    else:
        processed = preprocess_dataframe(raw_df, require_target=False)

    preds = model.predict(processed[features])
    return [round(float(p), 2) for p in preds]

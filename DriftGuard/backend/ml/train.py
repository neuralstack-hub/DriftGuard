"""Train RandomForestRegressor models and save artifacts with joblib."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.ml.evaluate import evaluate_model
from backend.ml.preprocess import FEATURE_COLUMNS, TARGET_COLUMN, prepare_and_save_splits


def train_random_forest(
    train_df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None,
    target_column: str = TARGET_COLUMN,
    n_estimators: int = 120,
    max_depth: Optional[int] = 16,
    random_state: int = 42,
):
    """Fit a Scikit-learn RandomForestRegressor on labelled tabular data."""
    from sklearn.ensemble import RandomForestRegressor

    cols = feature_columns or FEATURE_COLUMNS
    X_train = train_df[cols]
    y_train = train_df[target_column].values

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=3,
        n_jobs=-1,
        random_state=random_state,
    )
    model.fit(X_train, y_train)
    return model


def extract_feature_importance(model: Any, feature_columns: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
    """Extract sorted feature importances from a fitted RandomForestRegressor."""
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []
    pairs = [
        {"feature": str(col), "importance": round(float(val), 4)}
        for col, val in zip(feature_columns, importances)
    ]
    pairs.sort(key=lambda x: x["importance"], reverse=True)
    return pairs[:top_n]


def train_and_save_version(
    version: str,
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    models_dir: Path,
    feature_columns: Optional[List[str]] = None,
    target_column: str = TARGET_COLUMN,
    schema: Optional[Dict[str, Any]] = None,
    n_estimators: int = 120,
    max_depth: Optional[int] = 16,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Train a model version, evaluate it on fixed validation, and save with joblib."""
    import joblib

    cols = feature_columns or FEATURE_COLUMNS
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = models_dir / f"model_{version}.joblib"

    model = train_random_forest(
        train_df,
        feature_columns=cols,
        target_column=target_column,
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
    )
    metrics = evaluate_model(
        model,
        validation_df,
        feature_columns=cols,
        target_column=target_column,
    )
    feature_importance = extract_feature_importance(model, cols)

    bundle = {
        "version": version,
        "model": model,
        "features": cols,
        "target": target_column,
        "schema": schema,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "training_samples": len(train_df),
    }
    joblib.dump(bundle, artifact_path)

    return {
        "version": version,
        "artifact_path": str(artifact_path),
        "metrics": metrics,
        "feature_importance": feature_importance,
        "training_samples": len(train_df),
    }


def train_initial_v1(
    raw_csv_path: Path,
    processed_dir: Path,
    models_dir: Path,
) -> Dict[str, Any]:
    """Preprocess raw dataset, create splits, and train initial Model v1."""
    prepare_and_save_splits(raw_csv_path, processed_dir)
    train_df = pd.read_csv(processed_dir / "reference_train.csv")
    val_df = pd.read_csv(processed_dir / "fixed_validation.csv")
    return train_and_save_version("v1", train_df, val_df, models_dir)

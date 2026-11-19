"""Data loading, inspection, and preprocessing for Beijing PM2.5 and custom CSV datasets."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

TARGET_COLUMN = "pm2.5"
WIND_DIRECTIONS = ("NE", "NW", "SE", "cv")
NUMERIC_FEATURES = ["month", "day", "hour", "DEWP", "TEMP", "PRES", "Iws", "Is", "Ir"]
FEATURE_COLUMNS = [
    "month",
    "day",
    "hour",
    "DEWP",
    "TEMP",
    "PRES",
    "Iws",
    "Is",
    "Ir",
    "cbwd_NE",
    "cbwd_NW",
    "cbwd_SE",
    "cbwd_cv",
]


def load_raw_dataset(csv_path: Path) -> pd.DataFrame:
    """Load a raw CSV file."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {csv_path}. "
            "Run `python scripts/download_dataset.py` to download PRSA_data_2010.1.1-2014.12.31.csv from UCI."
        )
    return pd.read_csv(csv_path, na_values=["NA", "NaN", ""])


def save_schema(processed_dir: Path, schema: Dict[str, Any]) -> Path:
    processed_dir.mkdir(parents=True, exist_ok=True)
    path = processed_dir / "schema.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    return path


def load_schema(processed_dir: Path) -> Dict[str, Any]:
    path = processed_dir / "schema.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "dataset_name": "Beijing PM2.5",
        "target_column": TARGET_COLUMN,
        "raw_features": NUMERIC_FEATURES + ["cbwd"],
        "encoded_features": FEATURE_COLUMNS,
        "numeric_drift_features": ["DEWP", "TEMP", "PRES", "Iws", "Is", "Ir"],
        "categorical_categories": {"cbwd": list(WIND_DIRECTIONS)},
        "is_custom": False,
    }


def inspect_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspect an uploaded CSV dataframe and summarize columns, types, and missingness."""
    columns = []
    for col in df.columns:
        series = df[col]
        numeric_coerced = pd.to_numeric(series, errors="coerce")
        non_null = series.dropna()
        is_numeric = len(non_null) > 0 and numeric_coerced.notna().sum() >= (0.8 * len(non_null))
        columns.append(
            {
                "name": str(col),
                "dtype": "numeric" if is_numeric else "categorical",
                "missing_count": int(series.isna().sum()),
                "unique_count": int(series.nunique(dropna=True)),
                "sample_values": [str(v) for v in non_null.head(3).tolist()],
            }
        )
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": columns,
    }


def preprocess_dataframe(df: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    """Clean, impute missing values, and one-hot encode wind direction for Beijing PM2.5."""
    data = df.copy()

    if "No" in data.columns:
        data = data.drop(columns=["No"])

    if require_target:
        if TARGET_COLUMN not in data.columns:
            raise ValueError(f"Missing target column '{TARGET_COLUMN}' in dataset.")
        data = data.dropna(subset=[TARGET_COLUMN]).copy()
        data[TARGET_COLUMN] = pd.to_numeric(data[TARGET_COLUMN], errors="coerce")
        data = data.dropna(subset=[TARGET_COLUMN]).copy()

    for col in NUMERIC_FEATURES:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
            median_val = data[col].median()
            data[col] = data[col].fillna(0.0 if np.isnan(median_val) else median_val)
        else:
            data[col] = 0.0

    cbwd_series = data.get("cbwd", pd.Series(["cv"] * len(data), index=data.index)).fillna("cv").astype(str)
    for direction in WIND_DIRECTIONS:
        data[f"cbwd_{direction}"] = (cbwd_series == direction).astype(int)

    cols = list(FEATURE_COLUMNS)
    if "year" in data.columns:
        cols = ["year"] + cols
    if TARGET_COLUMN in data.columns:
        cols = cols + [TARGET_COLUMN]

    return data[cols].reset_index(drop=True)


def preprocess_custom_dataframe(
    df: pd.DataFrame,
    target_column: str,
    selected_features: List[str],
    categorical_categories: Optional[Dict[str, List[str]]] = None,
    require_target: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Dynamically clean and encode any user-uploaded tabular CSV for regression.
    Returns (processed_df, schema_metadata).
    """
    data = df.copy()

    if require_target:
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in uploaded CSV.")
        data[target_column] = pd.to_numeric(data[target_column], errors="coerce")
        data = data.dropna(subset=[target_column]).copy()
        if len(data) < 20:
            raise ValueError("Dataset must have at least 20 valid numeric target rows after cleaning.")

    encoded_cols: List[str] = []
    numeric_drift_features: List[str] = []
    cat_map: Dict[str, List[str]] = {}
    out = pd.DataFrame(index=data.index)

    for col in selected_features:
        if col == target_column:
            continue
        series = data[col] if col in data.columns else pd.Series([0] * len(data), index=data.index)
        numeric_coerced = pd.to_numeric(series, errors="coerce")
        non_null = series.dropna()
        is_numeric = len(non_null) > 0 and numeric_coerced.notna().sum() >= (0.8 * len(non_null))

        if is_numeric or (categorical_categories is not None and col not in categorical_categories):
            median_val = numeric_coerced.median()
            out[col] = numeric_coerced.fillna(0.0 if np.isnan(median_val) else median_val)
            encoded_cols.append(col)
            numeric_drift_features.append(col)
        else:
            cats = (
                categorical_categories[col]
                if categorical_categories and col in categorical_categories
                else [str(c) for c in series.fillna("missing").astype(str).value_counts().head(10).index.tolist()]
            )
            cat_map[col] = cats
            str_series = series.fillna("missing").astype(str)
            for cat in cats:
                enc_name = f"{col}_{cat}"
                out[enc_name] = (str_series == cat).astype(int)
                encoded_cols.append(enc_name)

    if require_target:
        out[target_column] = data[target_column].values

    schema = {
        "target_column": target_column,
        "raw_features": [f for f in selected_features if f != target_column],
        "encoded_features": encoded_cols,
        "numeric_drift_features": numeric_drift_features,
        "categorical_categories": cat_map,
        "is_custom": True,
    }
    return out.reset_index(drop=True), schema


def split_chronological_datasets(
    processed_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split chronologically:
      - Beijing PM2.5: 2010-2012 reference/train, 2013 retrain pool, 2014 fixed validation
      - Custom datasets: 60% reference/train, 20% retrain pool, 20% fixed validation
    """
    if "year" in processed_df.columns and processed_df["year"].nunique() >= 3:
        ref_train = processed_df[processed_df["year"] <= 2012].copy()
        retrain_pool = processed_df[processed_df["year"] == 2013].copy()
        fixed_val = processed_df[processed_df["year"] >= 2014].copy()
        if not ref_train.empty and not retrain_pool.empty and not fixed_val.empty:
            return ref_train, retrain_pool, fixed_val

    n = len(processed_df)
    i1 = int(n * 0.60)
    i2 = int(n * 0.80)
    return (
        processed_df.iloc[:i1].copy(),
        processed_df.iloc[i1:i2].copy(),
        processed_df.iloc[i2:].copy(),
    )


def prepare_and_save_splits(raw_csv_path: Path, processed_dir: Path) -> dict:
    """Run full preprocessing for Beijing PM2.5 and persist splits + schema."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_df = load_raw_dataset(raw_csv_path)
    clean_df = preprocess_dataframe(raw_df, require_target=True)
    ref_train, retrain_pool, fixed_val = split_chronological_datasets(clean_df)

    ref_path = processed_dir / "reference_train.csv"
    retrain_path = processed_dir / "retrain_pool.csv"
    val_path = processed_dir / "fixed_validation.csv"

    ref_train.to_csv(ref_path, index=False)
    retrain_pool.to_csv(retrain_path, index=False)
    fixed_val.to_csv(val_path, index=False)
    save_schema(
        processed_dir,
        {
            "dataset_name": "Beijing PM2.5",
            "target_column": TARGET_COLUMN,
            "raw_features": NUMERIC_FEATURES + ["cbwd"],
            "encoded_features": FEATURE_COLUMNS,
            "numeric_drift_features": ["DEWP", "TEMP", "PRES", "Iws", "Is", "Ir"],
            "categorical_categories": {"cbwd": list(WIND_DIRECTIONS)},
            "is_custom": False,
        },
    )

    return {
        "total_clean_rows": len(clean_df),
        "reference_train_rows": len(ref_train),
        "retrain_pool_rows": len(retrain_pool),
        "fixed_validation_rows": len(fixed_val),
        "reference_path": str(ref_path),
        "retrain_pool_path": str(retrain_path),
        "validation_path": str(val_path),
    }


def prepare_custom_dataset_splits(
    raw_df: pd.DataFrame,
    dataset_name: str,
    target_column: str,
    selected_features: List[str],
    processed_dir: Path,
) -> Dict[str, Any]:
    """Preprocess a user-uploaded CSV, persist train/retrain/validation splits and schema."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    clean_df, schema = preprocess_custom_dataframe(
        raw_df,
        target_column=target_column,
        selected_features=selected_features,
        require_target=True,
    )
    schema["dataset_name"] = dataset_name

    ref_train, retrain_pool, fixed_val = split_chronological_datasets(clean_df)
    ref_train.to_csv(processed_dir / "reference_train.csv", index=False)
    retrain_pool.to_csv(processed_dir / "retrain_pool.csv", index=False)
    fixed_val.to_csv(processed_dir / "fixed_validation.csv", index=False)
    save_schema(processed_dir, schema)

    return {
        "schema": schema,
        "total_clean_rows": len(clean_df),
        "reference_train_rows": len(ref_train),
        "retrain_pool_rows": len(retrain_pool),
        "fixed_validation_rows": len(fixed_val),
    }

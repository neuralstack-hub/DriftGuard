"""Data loading and preprocessing for the Beijing PM2.5 dataset."""

from pathlib import Path
from typing import Tuple

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
    """Load the raw Beijing PM2.5 CSV file."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {csv_path}. "
            "Run `python scripts/download_dataset.py` to download PRSA_data_2010.1.1-2014.12.31.csv from UCI."
        )
    df = pd.read_csv(csv_path, na_values=["NA", "NaN", ""])
    return df


def preprocess_dataframe(df: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    """Clean, impute missing values, and one-hot encode wind direction."""
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


def split_chronological_datasets(
    processed_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split Beijing PM2.5 chronologically to prevent data leakage:
      - Reference / Initial Training (v1): years 2010-2012
      - Labelled Retraining Pool / Production Stream: year 2013
      - Fixed Holdout Validation Set: year 2014 (never used for training)
    Falls back to 60/20/20 chronological split if 'year' column is absent.
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
    """Run full preprocessing and persist train/retrain/validation/reference splits."""
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

    return {
        "total_clean_rows": len(clean_df),
        "reference_train_rows": len(ref_train),
        "retrain_pool_rows": len(retrain_pool),
        "fixed_validation_rows": len(fixed_val),
        "reference_path": str(ref_path),
        "retrain_pool_path": str(retrain_path),
        "validation_path": str(val_path),
    }

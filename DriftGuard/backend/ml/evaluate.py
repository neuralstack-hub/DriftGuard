"""Model evaluation utilities using MAE, RMSE, and R2 on the fixed validation set."""

from typing import Any, Dict

import numpy as np
import pandas as pd

from backend.ml.preprocess import FEATURE_COLUMNS, TARGET_COLUMN


def evaluate_model(model: Any, validation_df: pd.DataFrame) -> Dict[str, float]:
    """Compute MAE, RMSE, and R2 on the fixed validation dataset."""
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    X_val = validation_df[FEATURE_COLUMNS]
    y_val = validation_df[TARGET_COLUMN].values
    preds = model.predict(X_val)

    mae = float(mean_absolute_error(y_val, preds))
    rmse = float(np.sqrt(mean_squared_error(y_val, preds)))
    r2 = float(r2_score(y_val, preds))

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
    }


def is_candidate_better(
    candidate_metrics: Dict[str, float],
    active_metrics: Dict[str, float],
    min_rmse_improvement: float = 0.0,
) -> bool:
    """
    Acceptance gate: candidate must achieve strictly lower RMSE (by at least
    min_rmse_improvement) and R2 >= active_metrics['r2'] - 0.005.
    """
    rmse_ok = candidate_metrics["rmse"] < (active_metrics["rmse"] - min_rmse_improvement)
    r2_ok = candidate_metrics["r2"] >= (active_metrics["r2"] - 0.005)
    return bool(rmse_ok and r2_ok)

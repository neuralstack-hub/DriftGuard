"""Data drift detection comparing reference training data against incoming production data."""

from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, wasserstein_distance

DRIFT_FEATURES = ["DEWP", "TEMP", "PRES", "Iws", "Is", "Ir"]


def compute_psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Calculate Population Stability Index (PSI) between reference and current arrays."""
    ref = np.asarray(reference, dtype=float)
    cur = np.asarray(current, dtype=float)
    ref = ref[~np.isnan(ref)]
    cur = cur[~np.isnan(cur)]
    if len(ref) == 0 or len(cur) == 0:
        return 0.0

    quantiles = np.linspace(0, 100, bins + 1)
    bin_edges = np.unique(np.percentile(ref, quantiles))
    if len(bin_edges) < 2:
        return 0.0

    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    ref_counts, _ = np.histogram(ref, bins=bin_edges)
    cur_counts, _ = np.histogram(cur, bins=bin_edges)

    eps = 1e-4
    ref_pct = np.clip(ref_counts / max(len(ref), 1), eps, None)
    cur_pct = np.clip(cur_counts / max(len(cur), 1), eps, None)

    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    return round(float(psi), 4)


def run_evidently_if_available(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    features: List[str],
) -> Dict[str, Any]:
    """Use Evidently AI DataDriftPreset when installed; otherwise return empty dict."""
    try:
        from evidently.metric_preset import DataDriftPreset
        from evidently.report import Report

        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=reference_df[features], current_data=current_df[features])
        result = report.as_dict()
        drift_info = result["metrics"][0]["result"]
        return {
            "evidently_used": True,
            "evidently_dataset_drift": bool(drift_info.get("dataset_drift", False)),
            "evidently_drift_share": float(drift_info.get("share_of_drifted_columns", 0.0)),
        }
    except Exception:
        return {"evidently_used": False}


def detect_data_drift(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    drift_threshold: float = 0.30,
    ks_alpha: float = 0.05,
    psi_threshold: float = 0.20,
    features: List[str] = None,
) -> Dict[str, Any]:
    """
    Compare reference training data vs incoming production data across key features.
    Returns per-feature KS test, PSI, Wasserstein distance, and overall drift decision.

    Note: Data drift indicates input distribution shift, NOT automatic accuracy loss.
    """
    monitored = features or [f for f in DRIFT_FEATURES if f in reference_df.columns and f in current_df.columns]
    if not monitored:
        raise ValueError("No overlapping monitored features found between reference and current data.")

    feature_results = []
    drifted_count = 0

    for col in monitored:
        ref_vals = pd.to_numeric(reference_df[col], errors="coerce").dropna().values
        cur_vals = pd.to_numeric(current_df[col], errors="coerce").dropna().values

        ks_stat, p_value = ks_2samp(ref_vals, cur_vals)
        psi_val = compute_psi(ref_vals, cur_vals)
        w_dist = float(wasserstein_distance(ref_vals, cur_vals))

        ref_mean = float(np.mean(ref_vals)) if len(ref_vals) else 0.0
        cur_mean = float(np.mean(cur_vals)) if len(cur_vals) else 0.0
        ref_std = float(np.std(ref_vals)) if len(ref_vals) else 0.0
        cur_std = float(np.std(cur_vals)) if len(cur_vals) else 0.0

        is_drifted = bool((p_value < ks_alpha and psi_val >= psi_threshold) or psi_val >= 0.25)
        if is_drifted:
            drifted_count += 1

        feature_results.append(
            {
                "feature": col,
                "ks_statistic": round(float(ks_stat), 4),
                "p_value": round(float(p_value), 6),
                "psi": psi_val,
                "wasserstein_distance": round(w_dist, 4),
                "reference_mean": round(ref_mean, 3),
                "current_mean": round(cur_mean, 3),
                "reference_std": round(ref_std, 3),
                "current_std": round(cur_std, 3),
                "drift_detected": is_drifted,
            }
        )

    drift_score = round(drifted_count / len(monitored), 4)
    dataset_drift_detected = drift_score >= drift_threshold
    evidently_meta = run_evidently_if_available(reference_df, current_df, monitored)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_drift_detected": dataset_drift_detected,
        "drift_score": drift_score,
        "drift_threshold": drift_threshold,
        "drifted_features_count": drifted_count,
        "total_features_monitored": len(monitored),
        "reference_samples": len(reference_df),
        "current_samples": len(current_df),
        "features": feature_results,
        "note": "Data drift indicates input distribution shift; model performance degradation requires labelled validation.",
        **evidently_meta,
    }


def generate_drifted_sample(
    reference_df: pd.DataFrame,
    n_samples: int = 500,
    intensity: float = 1.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Create a realistic shifted incoming production batch from reference samples
    by applying controlled meteorological shifts (e.g., warmer season, lower pressure,
    stronger wind) for drift simulation.
    """
    rng = np.random.default_rng(seed)
    sample = reference_df.sample(n=min(n_samples, len(reference_df)), random_state=seed).copy()

    if "TEMP" in sample.columns:
        sample["TEMP"] = sample["TEMP"] + (9.5 * intensity) + rng.normal(0, 1.5, len(sample))
    if "DEWP" in sample.columns:
        sample["DEWP"] = sample["DEWP"] + (7.0 * intensity) + rng.normal(0, 1.2, len(sample))
    if "PRES" in sample.columns:
        sample["PRES"] = sample["PRES"] - (12.0 * intensity) + rng.normal(0, 1.0, len(sample))
    if "Iws" in sample.columns:
        sample["Iws"] = np.clip(sample["Iws"] * (1.0 + 0.85 * intensity) + (15.0 * intensity), 0, None)

    return sample.reset_index(drop=True)

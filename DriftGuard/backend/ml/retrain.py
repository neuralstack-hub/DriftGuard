"""Automated retraining pipeline using labelled data and fixed validation comparison."""

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from backend.ml.evaluate import evaluate_model, is_candidate_better
from backend.ml.predict import load_model_bundle
from backend.ml.train import train_and_save_version


def run_retraining_pipeline(
    next_version: str,
    active_artifact_path: Path,
    processed_dir: Path,
    models_dir: Path,
    n_estimators: int = 160,
    max_depth: int = 18,
    simulate_worse_candidate: bool = False,
) -> Dict[str, Any]:
    """
    Train a candidate model strictly on labelled training data (reference_train +
    labelled retrain_pool), evaluate both active and candidate models on the SAME
    fixed validation dataset, and decide promotion vs rejection.
    """
    ref_path = processed_dir / "reference_train.csv"
    pool_path = processed_dir / "retrain_pool.csv"
    val_path = processed_dir / "fixed_validation.csv"

    if not ref_path.exists() or not val_path.exists():
        raise FileNotFoundError(
            "Processed splits not found. Run initial training / preprocessing first."
        )

    ref_df = pd.read_csv(ref_path)
    val_df = pd.read_csv(val_path)

    if pool_path.exists():
        pool_df = pd.read_csv(pool_path)
        labelled_train_df = pd.concat([ref_df, pool_df], ignore_index=True)
    else:
        labelled_train_df = ref_df

    # Optionally simulate a degraded candidate (e.g., overly shallow trees) to test rejection gate
    eff_estimators = 5 if simulate_worse_candidate else n_estimators
    eff_depth = 2 if simulate_worse_candidate else max_depth

    candidate_info = train_and_save_version(
        version=next_version,
        train_df=labelled_train_df,
        validation_df=val_df,
        models_dir=models_dir,
        n_estimators=eff_estimators,
        max_depth=eff_depth,
    )

    active_bundle = load_model_bundle(active_artifact_path)
    active_metrics = evaluate_model(active_bundle["model"], val_df)
    candidate_metrics = candidate_info["metrics"]

    promoted = is_candidate_better(candidate_metrics, active_metrics)

    return {
        "candidate_version": next_version,
        "candidate_artifact_path": candidate_info["artifact_path"],
        "candidate_metrics": candidate_metrics,
        "active_metrics_on_fixed_val": active_metrics,
        "training_samples": candidate_info["training_samples"],
        "validation_samples": len(val_df),
        "decision": "promoted" if promoted else "rejected",
        "promoted": promoted,
    }

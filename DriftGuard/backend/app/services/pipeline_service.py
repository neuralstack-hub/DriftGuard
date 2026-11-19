"""Pipeline orchestration service connecting drift detection, retraining, and registry."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from backend.app.config import settings
from backend.app.services.monitoring_service import MonitoringService
from backend.app.services.registry_service import RegistryService
from backend.ml.preprocess import prepare_custom_dataset_splits
from backend.ml.retrain import run_retraining_pipeline
from backend.ml.train import train_and_save_version, train_initial_v1


class PipelineService:
    """Coordinates initial training, custom dataset onboarding, retraining, and promotion/rejection."""

    def __init__(
        self,
        registry: RegistryService,
        monitoring: MonitoringService,
        processed_dir: Path = settings.data_processed_dir,
        models_dir: Path = settings.artifacts_models_dir,
    ):
        self.registry = registry
        self.monitoring = monitoring
        self.processed_dir = processed_dir
        self.models_dir = models_dir

    def bootstrap_v1(self) -> Dict[str, Any]:
        """Train initial Model v1 on Beijing PM2.5 if no model is registered yet."""
        active = self.registry.get_active_version_record()
        if active is not None:
            return {"status": "already_initialized", "model": active}

        result = train_initial_v1(
            raw_csv_path=settings.data_raw_path,
            processed_dir=self.processed_dir,
            models_dir=self.models_dir,
        )
        record = self.registry.register_version(
            version=result["version"],
            metrics=result["metrics"],
            artifact_path=result["artifact_path"],
            training_samples=result["training_samples"],
            status="active",
            notes="Initial baseline RandomForestRegressor trained on 2010-2012 Beijing PM2.5",
            feature_importance=result.get("feature_importance", []),
        )
        self.monitoring.log_deployment(
            version=record["version"],
            action="deploy_initial",
            details=f"Deployed initial Model v1 (RMSE={record['metrics']['rmse']}, R2={record['metrics']['r2']})",
        )
        return {"status": "initialized", "model": record}

    def onboard_custom_dataset(
        self,
        raw_df: pd.DataFrame,
        dataset_name: str,
        target_column: str,
        selected_features: List[str],
    ) -> Dict[str, Any]:
        """Preprocess a user-uploaded CSV, train a new model version, and activate it."""
        split_info = prepare_custom_dataset_splits(
            raw_df=raw_df,
            dataset_name=dataset_name,
            target_column=target_column,
            selected_features=selected_features,
            processed_dir=self.processed_dir,
        )
        schema = split_info["schema"]
        train_df = pd.read_csv(self.processed_dir / "reference_train.csv")
        val_df = pd.read_csv(self.processed_dir / "fixed_validation.csv")

        next_ver = self.registry.next_version_name()
        trained = train_and_save_version(
            version=next_ver,
            train_df=train_df,
            validation_df=val_df,
            models_dir=self.models_dir,
            feature_columns=schema["encoded_features"],
            target_column=schema["target_column"],
            schema=schema,
        )
        record = self.registry.register_version(
            version=next_ver,
            metrics=trained["metrics"],
            artifact_path=trained["artifact_path"],
            training_samples=trained["training_samples"],
            status="active",
            notes=f"Custom dataset '{dataset_name}' (target={target_column})",
            feature_importance=trained.get("feature_importance", []),
        )
        self.monitoring.log_deployment(
            version=record["version"],
            action="deploy_custom_dataset",
            details=f"Trained {next_ver} on '{dataset_name}' ({split_info['total_clean_rows']} rows, RMSE={record['metrics']['rmse']})",
        )
        return {
            "status": "trained",
            "model": record,
            "schema": schema,
            "splits": {
                "total_clean_rows": split_info["total_clean_rows"],
                "reference_train_rows": split_info["reference_train_rows"],
                "retrain_pool_rows": split_info["retrain_pool_rows"],
                "fixed_validation_rows": split_info["fixed_validation_rows"],
            },
        }

    def trigger_retraining(
        self,
        n_estimators: int = 160,
        max_depth: int = 18,
        simulate_worse_candidate: bool = False,
        trigger_reason: str = "manual",
    ) -> Dict[str, Any]:
        active = self.registry.get_active_version_record()
        if active is None:
            raise ValueError("No active model found. Train Model v1 or upload a dataset first.")

        next_ver = self.registry.next_version_name()
        outcome = run_retraining_pipeline(
            next_version=next_ver,
            active_artifact_path=Path(active["artifact_path"]),
            processed_dir=self.processed_dir,
            models_dir=self.models_dir,
            n_estimators=n_estimators,
            max_depth=max_depth,
            simulate_worse_candidate=simulate_worse_candidate,
        )

        record = self.registry.register_version(
            version=next_ver,
            metrics=outcome["candidate_metrics"],
            artifact_path=outcome["candidate_artifact_path"],
            training_samples=outcome["training_samples"],
            status="candidate",
            notes=f"Retrained ({trigger_reason}) on {outcome['training_samples']} labelled rows",
            feature_importance=outcome.get("feature_importance", []),
        )

        if outcome["promoted"]:
            self.registry.promote_version(
                next_ver,
                reason=f"Auto-promoted: RMSE {outcome['candidate_metrics']['rmse']} < {outcome['active_metrics_on_fixed_val']['rmse']}",
            )
            self.monitoring.log_deployment(
                version=next_ver,
                action="promote_candidate",
                details=f"Promoted {next_ver} over {active['version']} (RMSE {outcome['candidate_metrics']['rmse']} vs {outcome['active_metrics_on_fixed_val']['rmse']})",
            )
        else:
            self.registry.reject_version(
                next_ver,
                reason=f"Auto-rejected: RMSE {outcome['candidate_metrics']['rmse']} >= {outcome['active_metrics_on_fixed_val']['rmse']}",
            )
            self.monitoring.log_deployment(
                version=active["version"],
                action="reject_candidate",
                details=f"Rejected {next_ver} (RMSE {outcome['candidate_metrics']['rmse']}); retained {active['version']}",
            )

        retrain_log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trigger_reason": trigger_reason,
            "previous_active_version": active["version"],
            "candidate_version": next_ver,
            "candidate_metrics": outcome["candidate_metrics"],
            "active_metrics_on_fixed_val": outcome["active_metrics_on_fixed_val"],
            "decision": outcome["decision"],
            "promoted": outcome["promoted"],
        }
        self.monitoring.log_retraining(retrain_log)
        gh_dispatch = self.monitoring.trigger_github_actions(retrain_log)

        return {
            **retrain_log,
            "candidate_record": record,
            "github_dispatch": gh_dispatch,
        }

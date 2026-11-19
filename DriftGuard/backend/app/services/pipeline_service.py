"""Pipeline orchestration service connecting drift detection, retraining, and registry."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from backend.app.config import settings
from backend.app.services.monitoring_service import MonitoringService
from backend.app.services.registry_service import RegistryService
from backend.ml.retrain import run_retraining_pipeline
from backend.ml.train import train_initial_v1


class PipelineService:
    """Coordinates initial training, retraining, candidate evaluation, and promotion/rejection."""

    def __init__(self, registry: RegistryService, monitoring: MonitoringService):
        self.registry = registry
        self.monitoring = monitoring

    def bootstrap_v1(self) -> Dict[str, Any]:
        """Train initial Model v1 if no model is registered yet."""
        active = self.registry.get_active_version_record()
        if active is not None:
            return {"status": "already_initialized", "model": active}

        result = train_initial_v1(
            raw_csv_path=settings.data_raw_path,
            processed_dir=settings.data_processed_dir,
            models_dir=settings.artifacts_models_dir,
        )
        record = self.registry.register_version(
            version=result["version"],
            metrics=result["metrics"],
            artifact_path=result["artifact_path"],
            training_samples=result["training_samples"],
            status="active",
            notes="Initial baseline RandomForestRegressor trained on 2010-2012 reference data",
        )
        self.monitoring.log_deployment(
            version=record["version"],
            action="deploy_initial",
            details=f"Deployed initial Model v1 (RMSE={record['metrics']['rmse']}, R2={record['metrics']['r2']})",
        )
        return {"status": "initialized", "model": record}

    def trigger_retraining(
        self,
        n_estimators: int = 160,
        max_depth: int = 18,
        simulate_worse_candidate: bool = False,
        trigger_reason: str = "manual",
    ) -> Dict[str, Any]:
        active = self.registry.get_active_version_record()
        if active is None:
            raise ValueError("No active model found. Train Model v1 first.")

        next_ver = self.registry.next_version_name()
        outcome = run_retraining_pipeline(
            next_version=next_ver,
            active_artifact_path=Path(active["artifact_path"]),
            processed_dir=settings.data_processed_dir,
            models_dir=settings.artifacts_models_dir,
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

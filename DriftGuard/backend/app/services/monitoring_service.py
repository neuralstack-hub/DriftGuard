"""Monitoring service for drift checks, history logging, and GitHub Actions dispatch."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import pandas as pd

from backend.app.config import settings
from backend.ml.drift_detection import detect_data_drift, generate_drifted_sample
from backend.ml.preprocess import load_schema


class MonitoringService:
    """Tracks drift history, deployment logs, retraining runs, and CI/CD dispatches."""

    def __init__(self, monitoring_dir: Path, processed_dir: Path):
        self.monitoring_dir = monitoring_dir
        self.processed_dir = processed_dir
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = self.monitoring_dir / "history.json"
        if not self.history_path.exists():
            self._write_history(
                {
                    "drift_history": [],
                    "retraining_history": [],
                    "deployment_logs": [],
                    "github_actions_runs": [],
                }
            )

    def _read_history(self) -> Dict[str, Any]:
        with open(self.history_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_history(self, data: Dict[str, Any]) -> None:
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_history(self) -> Dict[str, Any]:
        return self._read_history()

    def log_deployment(self, version: str, action: str, details: str) -> Dict[str, Any]:
        hist = self._read_history()
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": version,
            "action": action,
            "details": details,
        }
        hist["deployment_logs"].append(entry)
        self._write_history(hist)
        return entry

    def log_retraining(self, record: Dict[str, Any]) -> None:
        hist = self._read_history()
        hist["retraining_history"].append(record)
        self._write_history(hist)

    def run_drift_check(
        self,
        current_df: pd.DataFrame,
        source: str = "production_check",
        features: Optional[list] = None,
    ) -> Dict[str, Any]:
        ref_path = self.processed_dir / "reference_train.csv"
        if not ref_path.exists():
            raise FileNotFoundError(
                "Reference training dataset not found. Train Model v1 or upload a dataset first."
            )
        ref_df = pd.read_csv(ref_path)
        schema = load_schema(self.processed_dir)
        monitored = features or schema.get("numeric_drift_features")
        result = detect_data_drift(
            reference_df=ref_df,
            current_df=current_df,
            drift_threshold=settings.drift_threshold,
            ks_alpha=settings.ks_alpha,
            psi_threshold=settings.psi_threshold,
            features=monitored,
        )
        result["source"] = source

        hist = self._read_history()
        hist["drift_history"].append(result)
        self._write_history(hist)
        return result

    def simulate_drift(self, intensity: float = 1.0, n_samples: int = 500) -> Dict[str, Any]:
        ref_path = self.processed_dir / "reference_train.csv"
        if not ref_path.exists():
            raise FileNotFoundError(
                "Reference training dataset not found. Train Model v1 or upload a dataset first."
            )
        ref_df = pd.read_csv(ref_path)
        schema = load_schema(self.processed_dir)
        monitored = schema.get("numeric_drift_features")
        drifted_df = generate_drifted_sample(
            ref_df,
            n_samples=n_samples,
            intensity=intensity,
            features=monitored,
        )
        return self.run_drift_check(
            drifted_df,
            source=f"simulation(intensity={intensity})",
            features=monitored,
        )

    def trigger_github_actions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger GitHub Actions repository_dispatch securely via GITHUB_TOKEN env var.
        If credentials are not configured, records local status without failing.
        """
        hist = self._read_history()
        if not settings.github_token or not settings.github_owner or not settings.github_repo:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": settings.github_workflow_event,
                "status": "skipped_unconfigured",
                "message": "GITHUB_TOKEN or GITHUB_OWNER not set in .env; executed local pipeline instead.",
            }
            hist["github_actions_runs"].append(entry)
            self._write_history(hist)
            return entry

        url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/dispatches"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {settings.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            resp = httpx.post(
                url,
                headers=headers,
                json={"event_type": settings.github_workflow_event, "client_payload": payload},
                timeout=15.0,
            )
            status = "dispatched" if resp.status_code in (200, 201, 204) else f"error_{resp.status_code}"
            msg = f"GitHub repository_dispatch returned HTTP {resp.status_code}"
        except Exception as exc:
            status = "request_failed"
            msg = str(exc)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": settings.github_workflow_event,
            "status": status,
            "message": msg,
        }
        hist["github_actions_runs"].append(entry)
        self._write_history(hist)
        return entry

"""Project manager for per-dataset isolation (models, monitoring, processed data)."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from backend.app.config import PROJECT_ROOT, settings
from backend.app.services.monitoring_service import MonitoringService
from backend.app.services.registry_service import RegistryService

DEFAULT_PROJECT_ID = "beijing-pm25"


class ProjectService:
    """Manages isolated workspaces for each dataset/model project."""

    def __init__(self):
        self.projects_root = PROJECT_ROOT / "artifacts" / "projects"
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.projects_root / "projects.json"
        if not self.index_path.exists():
            self._write_index(
                {
                    "active_project": DEFAULT_PROJECT_ID,
                    "projects": [
                        {
                            "id": DEFAULT_PROJECT_ID,
                            "name": "Beijing PM2.5",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ],
                }
            )

    def _read_index(self) -> Dict[str, Any]:
        with open(self.index_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_index(self, data: Dict[str, Any]) -> None:
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def list_projects(self) -> Dict[str, Any]:
        return self._read_index()

    def get_active_project_id(self) -> str:
        return self._read_index().get("active_project", DEFAULT_PROJECT_ID)

    def set_active_project(self, project_id: str) -> Dict[str, Any]:
        idx = self._read_index()
        match = next((p for p in idx["projects"] if p["id"] == project_id), None)
        if not match:
            raise KeyError(f"Project '{project_id}' not found.")
        idx["active_project"] = project_id
        self._write_index(idx)
        return {"active_project": project_id, "project": match}

    def ensure_project(self, name: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-") or "custom-dataset"
        idx = self._read_index()
        if not any(p["id"] == slug for p in idx["projects"]):
            idx["projects"].append(
                {
                    "id": slug,
                    "name": name.strip(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        idx["active_project"] = slug
        self._write_index(idx)
        return slug

    def get_paths(self, project_id: str = None) -> Tuple[Path, Path, Path]:
        pid = project_id or self.get_active_project_id()
        if pid == DEFAULT_PROJECT_ID:
            return (
                settings.data_processed_dir,
                settings.artifacts_models_dir,
                settings.artifacts_monitoring_dir,
            )
        base = self.projects_root / pid
        return (
            settings.data_processed_dir / pid,
            base / "models",
            base / "monitoring",
        )

    def get_services(self, project_id: str = None):
        processed_dir, models_dir, monitoring_dir = self.get_paths(project_id)
        registry = RegistryService(models_dir)
        monitoring = MonitoringService(monitoring_dir, processed_dir)
        return processed_dir, models_dir, registry, monitoring

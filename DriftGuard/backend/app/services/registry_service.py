"""Model version registry service supporting promotion, rejection, and rollback."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class RegistryService:
    """Manages model versions (v1, v2, v3...), active pointer, and rollback history."""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.models_dir / "registry.json"
        if not self.registry_path.exists():
            self._write_registry(
                {
                    "active_version": None,
                    "previous_approved_version": None,
                    "versions": [],
                    "rollback_history": [],
                }
            )

    def _read_registry(self) -> Dict[str, Any]:
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_registry(self, data: Dict[str, Any]) -> None:
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_registry(self) -> Dict[str, Any]:
        return self._read_registry()

    def get_active_version_record(self) -> Optional[Dict[str, Any]]:
        reg = self._read_registry()
        active_ver = reg.get("active_version")
        for item in reg.get("versions", []):
            if item["version"] == active_ver:
                return item
        return None

    def next_version_name(self) -> str:
        reg = self._read_registry()
        versions = reg.get("versions", [])
        if not versions:
            return "v1"
        nums = []
        for v in versions:
            raw = str(v["version"]).lstrip("v")
            if raw.isdigit():
                nums.append(int(raw))
        return f"v{max(nums, default=0) + 1}"

    def register_version(
        self,
        version: str,
        metrics: Dict[str, float],
        artifact_path: str,
        training_samples: int,
        status: str = "candidate",
        notes: str = "",
    ) -> Dict[str, Any]:
        reg = self._read_registry()
        record = {
            "version": version,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "status": status,
            "artifact_path": artifact_path,
            "training_samples": training_samples,
            "notes": notes,
        }
        # Never overwrite an existing approved model entry
        existing = [v for v in reg["versions"] if v["version"] == version]
        if existing:
            raise ValueError(f"Model version '{version}' already exists and cannot be overwritten.")

        reg["versions"].append(record)
        if status == "active":
            prev = reg.get("active_version")
            if prev and prev != version:
                reg["previous_approved_version"] = prev
                for item in reg["versions"]:
                    if item["version"] == prev and item["status"] == "active":
                        item["status"] = "archived"
            reg["active_version"] = version

        self._write_registry(reg)
        return record

    def promote_version(self, version: str, reason: str = "Passed evaluation gate") -> Dict[str, Any]:
        reg = self._read_registry()
        target = None
        for item in reg["versions"]:
            if item["version"] == version:
                target = item
                break
        if target is None:
            raise KeyError(f"Model version '{version}' not found.")

        prev_active = reg.get("active_version")
        if prev_active and prev_active != version:
            reg["previous_approved_version"] = prev_active
            for item in reg["versions"]:
                if item["version"] == prev_active and item["status"] == "active":
                    item["status"] = "archived"

        target["status"] = "active"
        target["notes"] = reason
        reg["active_version"] = version
        self._write_registry(reg)
        return target

    def reject_version(self, version: str, reason: str = "Did not outperform active model") -> Dict[str, Any]:
        reg = self._read_registry()
        for item in reg["versions"]:
            if item["version"] == version:
                if item["status"] == "active":
                    raise ValueError(f"Cannot reject currently active model '{version}'.")
                item["status"] = "rejected"
                item["notes"] = reason
                self._write_registry(reg)
                return item
        raise KeyError(f"Model version '{version}' not found.")

    def rollback(self, target_version: Optional[str] = None, reason: str = "Manual rollback") -> Dict[str, Any]:
        reg = self._read_registry()
        current_active = reg.get("active_version")
        if not current_active:
            raise ValueError("No active model is currently deployed to roll back from.")

        if target_version is None:
            target_version = reg.get("previous_approved_version")
            if not target_version:
                archived = [v["version"] for v in reg["versions"] if v["status"] == "archived"]
                target_version = archived[-1] if archived else None

        if not target_version:
            raise ValueError("No previously approved model version is available for rollback.")
        if target_version == current_active:
            raise ValueError(f"Target version '{target_version}' is already active.")

        target_record = None
        for item in reg["versions"]:
            if item["version"] == target_version:
                target_record = item
                break
        if target_record is None:
            raise KeyError(f"Target rollback version '{target_version}' not found.")

        for item in reg["versions"]:
            if item["version"] == current_active:
                item["status"] = "archived"

        target_record["status"] = "active"
        reg["previous_approved_version"] = current_active
        reg["active_version"] = target_version

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_version": current_active,
            "to_version": target_version,
            "reason": reason,
        }
        reg.setdefault("rollback_history", []).append(event)
        self._write_registry(reg)
        return event

    def list_versions(self) -> List[Dict[str, Any]]:
        return self._read_registry().get("versions", [])

    def get_rollback_history(self) -> List[Dict[str, Any]]:
        return self._read_registry().get("rollback_history", [])

"""Unit tests for model registry versioning, promotion, rejection, and rollback."""

import tempfile
import unittest
from pathlib import Path

from backend.app.services.registry_service import RegistryService


class TestRegistryService(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.registry = RegistryService(Path(self.tmp_dir.name))

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_version_lifecycle_promote_reject_and_rollback(self):
        v1 = self.registry.register_version(
            version="v1",
            metrics={"mae": 32.1, "rmse": 48.5, "r2": 0.72},
            artifact_path="artifacts/models/model_v1.joblib",
            training_samples=20000,
            status="active",
        )
        self.assertEqual(v1["status"], "active")
        self.assertEqual(self.registry.next_version_name(), "v2")

        # Register v2 as candidate and promote it
        self.registry.register_version(
            version="v2",
            metrics={"mae": 28.4, "rmse": 43.2, "r2": 0.78},
            artifact_path="artifacts/models/model_v2.joblib",
            training_samples=28000,
            status="candidate",
        )
        promoted = self.registry.promote_version("v2")
        self.assertEqual(promoted["status"], "active")
        self.assertEqual(self.registry.get_active_version_record()["version"], "v2")

        # Register v3 as worse candidate and reject it
        self.registry.register_version(
            version="v3",
            metrics={"mae": 45.0, "rmse": 65.0, "r2": 0.45},
            artifact_path="artifacts/models/model_v3.joblib",
            training_samples=28000,
            status="candidate",
        )
        rejected = self.registry.reject_version("v3")
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(self.registry.get_active_version_record()["version"], "v2")

        # Rollback from v2 to v1
        rb = self.registry.rollback()
        self.assertEqual(rb["from_version"], "v2")
        self.assertEqual(rb["to_version"], "v1")
        self.assertEqual(self.registry.get_active_version_record()["version"], "v1")

    def test_never_overwrites_existing_version(self):
        self.registry.register_version(
            version="v1",
            metrics={"mae": 30.0, "rmse": 45.0, "r2": 0.75},
            artifact_path="artifacts/models/model_v1.joblib",
            training_samples=1000,
            status="active",
        )
        with self.assertRaises(ValueError):
            self.registry.register_version(
                version="v1",
                metrics={"mae": 25.0, "rmse": 40.0, "r2": 0.80},
                artifact_path="artifacts/models/model_v1.joblib",
                training_samples=1000,
                status="active",
            )


if __name__ == "__main__":
    unittest.main()

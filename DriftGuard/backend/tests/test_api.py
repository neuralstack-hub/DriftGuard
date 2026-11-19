"""Integration tests for FastAPI endpoints using TestClient."""

import io
import unittest
from fastapi.testclient import TestClient

from backend.app.main import app


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_and_overview(self):
        r_health = self.client.get("/api/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["status"], "ok")

        r_overview = self.client.get("/api/overview")
        self.assertEqual(r_overview.status_code, 200)
        data = r_overview.json()
        self.assertIn("total_monitored_models", data)
        self.assertIn("drift_status", data)
        self.assertIn("active_schema", data)

    def test_list_models_and_pipeline_history(self):
        r_models = self.client.get("/api/models")
        self.assertEqual(r_models.status_code, 200)
        self.assertIn("versions", r_models.json())

        r_hist = self.client.get("/api/pipeline/history")
        self.assertEqual(r_hist.status_code, 200)
        self.assertIn("retraining_history", r_hist.json())

        r_drift = self.client.get("/api/drift/history")
        self.assertEqual(r_drift.status_code, 200)
        self.assertIn("history", r_drift.json())

    def test_inspect_uploaded_csv(self):
        csv_bytes = b"area,bedrooms,city,price\n1200,2,Pune,50\n1500,3,Mumbai,85\n"
        res = self.client.post(
            "/api/datasets/inspect",
            files={"file": ("housing.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["row_count"], 2)
        self.assertEqual(body["column_count"], 4)


if __name__ == "__main__":
    unittest.main()

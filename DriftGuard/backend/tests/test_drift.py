"""Unit tests for statistical data drift detection and simulation."""

import unittest
import numpy as np
import pandas as pd

from backend.ml.drift_detection import (
    DRIFT_FEATURES,
    compute_psi,
    detect_data_drift,
    generate_drifted_sample,
)


class TestDriftDetection(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(123)
        self.reference_df = pd.DataFrame(
            {
                "DEWP": rng.normal(2.0, 8.0, 400),
                "TEMP": rng.normal(12.0, 9.0, 400),
                "PRES": rng.normal(1016.0, 8.0, 400),
                "Iws": np.abs(rng.normal(20.0, 15.0, 400)),
                "Is": np.zeros(400),
                "Ir": np.zeros(400),
            }
        )

    def test_no_drift_on_identical_distribution(self):
        result = detect_data_drift(self.reference_df, self.reference_df.copy(), drift_threshold=0.30)
        self.assertFalse(result["dataset_drift_detected"])
        self.assertEqual(result["drift_score"], 0.0)
        self.assertEqual(len(result["features"]), len(DRIFT_FEATURES))

    def test_detects_simulated_drift(self):
        drifted = generate_drifted_sample(self.reference_df, n_samples=300, intensity=1.5)
        result = detect_data_drift(self.reference_df, drifted, drift_threshold=0.30)
        self.assertTrue(result["dataset_drift_detected"])
        self.assertGreaterEqual(result["drift_score"], 0.30)

    def test_psi_increases_on_shifted_array(self):
        base = np.random.default_rng(1).normal(0, 1, 500)
        shifted = np.random.default_rng(2).normal(3.0, 1.0, 500)
        self.assertGreater(compute_psi(base, shifted), 0.25)


if __name__ == "__main__":
    unittest.main()

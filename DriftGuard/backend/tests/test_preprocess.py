"""Unit tests for Beijing PM2.5 preprocessing and chronological splitting."""

import unittest
import pandas as pd

from backend.ml.preprocess import (
    FEATURE_COLUMNS,
    preprocess_dataframe,
    split_chronological_datasets,
)


class TestPreprocess(unittest.TestCase):
    def setUp(self):
        self.sample_raw = pd.DataFrame(
            [
                {"No": 1, "year": 2010, "month": 1, "day": 1, "hour": 0, "pm2.5": 129.0, "DEWP": -21, "TEMP": -11, "PRES": 1021, "cbwd": "NW", "Iws": 1.79, "Is": 0, "Ir": 0},
                {"No": 2, "year": 2011, "month": 6, "day": 15, "hour": 12, "pm2.5": None, "DEWP": 15, "TEMP": 26, "PRES": 1005, "cbwd": "SE", "Iws": 4.2, "Is": 0, "Ir": 1},
                {"No": 3, "year": 2013, "month": 3, "day": 10, "hour": 8, "pm2.5": 88.0, "DEWP": -5, "TEMP": 6, "PRES": 1018, "cbwd": "NE", "Iws": 10.5, "Is": 0, "Ir": 0},
                {"No": 4, "year": 2014, "month": 11, "day": 20, "hour": 18, "pm2.5": 175.0, "DEWP": -8, "TEMP": 2, "PRES": 1024, "cbwd": "cv", "Iws": 2.1, "Is": 0, "Ir": 0},
            ]
        )

    def test_drops_missing_target_and_encodes_wind(self):
        cleaned = preprocess_dataframe(self.sample_raw, require_target=True)
        self.assertEqual(len(cleaned), 3)
        self.assertNotIn("No", cleaned.columns)
        for col in FEATURE_COLUMNS:
            self.assertIn(col, cleaned.columns)
        self.assertEqual(cleaned.iloc[0]["cbwd_NW"], 1)
        self.assertEqual(cleaned.iloc[0]["cbwd_SE"], 0)

    def test_chronological_split(self):
        cleaned = preprocess_dataframe(self.sample_raw, require_target=True)
        ref, pool, val = split_chronological_datasets(cleaned)
        self.assertTrue((ref["year"] <= 2012).all())
        self.assertTrue((pool["year"] == 2013).all())
        self.assertTrue((val["year"] >= 2014).all())


if __name__ == "__main__":
    unittest.main()

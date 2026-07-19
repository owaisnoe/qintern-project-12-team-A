from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "week2" / "scripts"
sys.path.insert(0, str(SCRIPTS))


class BaselineArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = ROOT / "week2" / "baselines" / "CICIoT2023"
        cls.results = json.loads((cls.directory / "results.json").read_text(encoding="utf-8"))
        cls.predictions = pd.read_csv(cls.directory / "predictions.csv")

    def test_persisted_models_reload_with_17_features(self):
        detector = XGBClassifier()
        detector.load_model(self.directory / "xgboost_detector.json")
        isolation_forest = joblib.load(self.directory / "isolation_forest.joblib")
        autoencoder = joblib.load(self.directory / "autoencoder.joblib")

        self.assertEqual(detector.get_booster().num_features(), 17)
        self.assertEqual(isolation_forest.n_features_in_, 17)
        self.assertEqual(autoencoder["scaler"].n_features_in_, 17)
        self.assertEqual(autoencoder["model"].n_features_in_, 17)

    def test_prediction_rows_match_test_and_zeroday_counts(self):
        expected = self.results["row_counts"]
        counts = self.predictions["split"].value_counts().to_dict()
        self.assertEqual(counts["test"], expected["test"])
        self.assertEqual(counts["zeroday"], expected["zeroday"])
        self.assertFalse(self.predictions.isna().any().any())

    def test_saved_predictions_reproduce_primary_metrics(self):
        test = self.predictions[self.predictions["split"] == "test"]
        detector = self.results["detector"]["multiclass"]
        self.assertAlmostEqual(
            accuracy_score(test["true_label_multiclass"], test["xgboost_prediction"]),
            detector["accuracy"],
        )
        self.assertAlmostEqual(
            f1_score(
                test["true_label_multiclass"],
                test["xgboost_prediction"],
                average="macro",
                zero_division=0,
            ),
            detector["f1_macro"],
        )

        novelty_truth = (self.predictions["split"] == "zeroday").astype(np.int64)
        for head_name, metrics in self.results["novelty_heads"].items():
            measured = roc_auc_score(novelty_truth, self.predictions[f"{head_name}_novelty_score"])
            self.assertAlmostEqual(measured, metrics["zero_day_auroc"])

    def test_results_record_no_zero_day_fitting(self):
        contract = self.results["evaluation_contract"]
        self.assertFalse(contract["zero_day_used_for_fitting_or_tuning"])
        self.assertEqual(contract["novelty_score_direction"], "higher means more novel")


class Day13AllDatasetArtifactTests(unittest.TestCase):
    """Day-13 extension: BoT-IoT and UNSW-NB15 carry the three-head, enriched-metric artifacts."""

    DATASETS = ["BoT-IoT", "UNSW-NB15"]

    def _load(self, name):
        directory = ROOT / "week2" / "baselines" / name
        results = json.loads((directory / "results.json").read_text(encoding="utf-8"))
        predictions = pd.read_csv(directory / "predictions.csv")
        return directory, results, predictions

    def test_three_novelty_heads_including_ocsvm(self):
        for name in self.DATASETS:
            with self.subTest(dataset=name):
                _, results, _ = self._load(name)
                self.assertEqual(
                    set(results["novelty_heads"]), {"isolation_forest", "autoencoder", "ocsvm"}
                )

    def test_day13_metric_additions_present(self):
        for name in self.DATASETS:
            with self.subTest(dataset=name):
                _, results, _ = self._load(name)
                multiclass = results["detector"]["multiclass"]
                self.assertIn("balanced_accuracy", multiclass)
                self.assertIn("auprc_ovr_macro", multiclass)
                for head in results["novelty_heads"].values():
                    self.assertIn("zero_day_auprc", head)
                    self.assertIn("balanced_accuracy", head)
                    self.assertTrue(head["per_attack_zero_day"])  # non-empty per-family breakdown

    def test_persisted_heads_reload(self):
        for name in self.DATASETS:
            with self.subTest(dataset=name):
                directory, _, _ = self._load(name)
                detector = XGBClassifier()
                detector.load_model(directory / "xgboost_detector.json")
                self.assertEqual(detector.get_booster().num_features(), 17)
                joblib.load(directory / "isolation_forest.joblib")
                joblib.load(directory / "autoencoder.joblib")
                joblib.load(directory / "ocsvm.joblib")

    def test_saved_predictions_reproduce_zero_day_auroc(self):
        for name in self.DATASETS:
            with self.subTest(dataset=name):
                _, results, predictions = self._load(name)
                novelty_truth = (predictions["split"] == "zeroday").astype(np.int64)
                for head_name, metrics in results["novelty_heads"].items():
                    measured = roc_auc_score(novelty_truth, predictions[f"{head_name}_novelty_score"])
                    self.assertAlmostEqual(measured, metrics["zero_day_auroc"])


if __name__ == "__main__":
    unittest.main()

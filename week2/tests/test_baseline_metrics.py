from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from baseline_metrics import (  # noqa: E402
    binary_metrics,
    conformal_novelty_threshold,
    multiclass_metrics,
    novelty_metrics,
    per_attack_zero_day_metrics,
)


class BaselineMetricsTests(unittest.TestCase):
    def test_conformal_threshold_uses_finite_sample_rank(self):
        scores = np.arange(10, dtype=float)
        self.assertEqual(conformal_novelty_threshold(scores, alpha=0.20), 8.0)

    def test_perfect_multiclass_metrics(self):
        classes = ["a", "b", "c"]
        truth = np.array(["a", "b", "c", "a", "b", "c"])
        probabilities = np.eye(3)[[0, 1, 2, 0, 1, 2]]
        result = multiclass_metrics(truth, truth, probabilities, classes)
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["balanced_accuracy"], 1.0)
        self.assertEqual(result["f1_macro"], 1.0)
        self.assertEqual(result["auroc_ovr_macro"], 1.0)
        self.assertEqual(result["auprc_ovr_macro"], 1.0)

    def test_balanced_accuracy_handles_class_imbalance(self):
        # A degenerate classifier that always predicts the majority class scores 1.0 on
        # plain accuracy for a lopsided support but 0.5 on balanced accuracy.
        classes = ["a", "b"]
        truth = np.array(["a", "a", "a", "b"])
        pred = np.array(["a", "a", "a", "a"])
        proba = np.tile([1.0, 0.0], (4, 1))
        result = multiclass_metrics(truth, pred, proba, classes)
        self.assertEqual(result["balanced_accuracy"], 0.5)
        self.assertGreater(result["accuracy"], result["balanced_accuracy"])

    def test_binary_metrics_use_attack_score(self):
        result = binary_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["f1_macro"], 1.0)
        self.assertEqual(result["auroc"], 1.0)

    def test_novelty_scores_are_oriented_high_is_novel(self):
        result = novelty_metrics([0.1, 0.2, 0.3], [0.8, 0.9], threshold=0.5)
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["balanced_accuracy"], 1.0)
        self.assertEqual(result["f1_macro"], 1.0)
        self.assertEqual(result["zero_day_auroc"], 1.0)
        self.assertEqual(result["zero_day_auprc"], 1.0)
        self.assertEqual(result["known_false_positive_rate"], 0.0)
        self.assertEqual(result["zero_day_true_positive_rate"], 1.0)

    def test_per_attack_zero_day_splits_families(self):
        known = [0.1, 0.2, 0.3]
        zero_day = [0.8, 0.9, 0.85, 0.4]
        families = ["Mirai-a", "Mirai-a", "Mirai-b", "Mirai-b"]
        result = per_attack_zero_day_metrics(known, zero_day, families, threshold=0.5)
        self.assertEqual(sorted(result), ["Mirai-a", "Mirai-b"])
        # Both families are perfectly rank-separable from the known scores.
        self.assertEqual(result["Mirai-a"]["zero_day_auroc"], 1.0)
        self.assertEqual(result["Mirai-b"]["zero_day_auroc"], 1.0)
        # Thresholded detection differs: family a is fully above 0.5, family b only half.
        self.assertEqual(result["Mirai-a"]["detection_rate_at_threshold"], 1.0)
        self.assertEqual(result["Mirai-b"]["detection_rate_at_threshold"], 0.5)
        self.assertEqual(result["Mirai-a"]["zero_day_rows"], 2)

    def test_per_attack_rejects_misaligned_families(self):
        with self.assertRaises(ValueError):
            per_attack_zero_day_metrics([0.1], [0.8, 0.9], ["a"], threshold=0.5)

    def test_invalid_scores_are_rejected(self):
        with self.assertRaises(ValueError):
            conformal_novelty_threshold([0.1, np.nan])


if __name__ == "__main__":
    unittest.main()

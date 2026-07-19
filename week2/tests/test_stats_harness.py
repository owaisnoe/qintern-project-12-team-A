from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from stats_harness import mean_std_ci  # noqa: E402


class StatsHarnessTests(unittest.TestCase):
    def test_mean_std_ci_matches_known_values(self):
        result = mean_std_ci([1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(result["n"], 5)
        self.assertAlmostEqual(result["mean"], 3.0)
        # Sample std (ddof=1) of 1..5 is sqrt(2.5).
        self.assertAlmostEqual(result["std"], np.sqrt(2.5))
        # Symmetric interval around the mean.
        self.assertAlmostEqual(result["ci95_low"] + result["ci95_high"], 6.0)
        self.assertGreater(result["ci95_high"], result["mean"])

    def test_single_value_has_zero_width_interval(self):
        result = mean_std_ci([0.8043])
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["std"], 0.0)
        self.assertEqual(result["ci95_low"], result["ci95_high"])
        self.assertEqual(result["ci95_low"], 0.8043)

    def test_zero_variance_interval_collapses(self):
        result = mean_std_ci([0.5, 0.5, 0.5])
        self.assertEqual(result["std"], 0.0)
        self.assertEqual(result["ci95_half_width"], 0.0)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Week 3 · Day 15 — tests for the CQ-ZDR conformal calibration module.

Pure-math tests always run. Data-backed tests are skipped unless the Day-14 dummy-score interface has been
merged (week2/interface/dummy_scores/CICIoT2023/calibration_scores.parquet). Run: python -m pytest week3/tests -q
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
import conformal_calibrate as cc  # noqa: E402

CIC_CAL = cc.IFACE / "CICIoT2023" / "calibration_scores.parquet"
HAS_IFACE = CIC_CAL.exists()


class TestConformalThreshold(unittest.TestCase):
    """Pure-math: the q = s_(k), k = ceil((1-alpha)(n+1)) order statistic."""

    def test_k_index_and_quantile(self):
        scores = np.arange(1, 101) / 100.0  # 0.01 .. 1.00, n=100
        q, k, n = cc.conformal_threshold(scores, 0.05)
        self.assertEqual(n, 100)
        self.assertEqual(k, 96)                       # ceil(0.95 * 101) = 96
        self.assertAlmostEqual(q, 0.96)               # s_(96) = sorted[95]
        self.assertAlmostEqual(q, float(np.sort(scores)[k - 1]))

    def test_second_alpha_case(self):
        scores = np.arange(1, 51) / 50.0              # n=50
        q, k, n = cc.conformal_threshold(scores, 0.10)
        self.assertEqual(k, int(np.ceil(0.90 * 51)))  # 46
        self.assertAlmostEqual(q, float(np.sort(scores)[k - 1]))

    def test_k_gt_n_returns_inf(self):
        q, k, n = cc.conformal_threshold(np.arange(1, 11) / 10.0, 0.001)  # k = ceil(0.999*11)=11 > 10
        self.assertGreater(k, n)
        self.assertEqual(q, math.inf)

    def test_alpha_monotonic(self):
        rng = np.random.default_rng(42)
        s = rng.random(500)
        q_tight, _, _ = cc.conformal_threshold(s, 0.01)
        q_loose, _, _ = cc.conformal_threshold(s, 0.10)
        self.assertGreaterEqual(q_tight, q_loose)     # smaller alpha => higher (or equal) threshold

    def test_empty(self):
        q, k, n = cc.conformal_threshold([], 0.05)
        self.assertEqual((q, k, n), (math.inf, 0, 0))


@unittest.skipUnless(HAS_IFACE, "Day-14 dummy-score interface not merged yet")
class TestCalibrateDataset(unittest.TestCase):
    """Data-backed: run against the merged CIC dummy interface."""

    @classmethod
    def setUpClass(cls):
        cls.r = cc.calibrate_dataset("CICIoT2023", 0.05, cc.IFACE, mode="marginal")

    def test_schema_and_known_only(self):
        import pandas as pd
        cal = pd.read_parquet(CIC_CAL)
        for col in ("sample_id", "nonconformity", "y_known", "split"):
            self.assertIn(col, cal.columns)
        self.assertGreater(len(cc.fid_columns(cal)), 0)
        self.assertEqual(int(cal["y_known"].min()), 1)     # calibration = known classes only

    def test_nonconformity_recompute_matches_column(self):
        import pandas as pd
        cal = pd.read_parquet(CIC_CAL)
        known = [c[len("fid__"):] for c in cc.fid_columns(cal)]
        recomputed = cc.nonconformity_from_fidelities(cal, known)
        np.testing.assert_allclose(recomputed, cal["nonconformity"].to_numpy(), atol=1e-9)

    def test_coverage_within_alpha(self):
        # the task's headline guarantee: false-zero-day (FPR) <= alpha within finite-sample tolerance
        fpr = self.r["known_test"]["false_zeroday_rate"]
        self.assertLessEqual(fpr, 0.05 + 0.015)
        self.assertTrue(self.r["coverage_ok"])

    def test_first_threshold_q(self):
        self.assertEqual(self.r["k"], 17940)
        self.assertAlmostEqual(self.r["threshold_q"], 0.300551, places=4)

    def test_determinism(self):
        r2 = cc.calibrate_dataset("CICIoT2023", 0.05, cc.IFACE, mode="marginal")
        self.assertEqual(self.r["threshold_q"], r2["threshold_q"])
        self.assertEqual(self.r["known_test"], r2["known_test"])

    def test_zeroday_rejection_sane(self):
        rej = self.r["zeroday"]["rejection_rate"]
        self.assertTrue(0.0 <= rej <= 1.0)
        self.assertGreater(rej, 0.9)                        # dummy CIC: near-total rejection


if __name__ == "__main__":
    unittest.main()

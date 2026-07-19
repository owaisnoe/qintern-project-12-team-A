"""Day-14 dummy-score interface — schema, row-alignment, determinism and conformal self-check."""
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import sys
BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week2" / "scripts"))
import make_dummy_scores as mds  # noqa: E402

PART = BASE / "week2" / "partitions"
IFACE = BASE / "week2" / "interface"
TRIO = mds.TRIO
SPLITS = mds.SPLITS


class TestDummyScoreInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = {d: json.loads((PART / d / "partition_meta.json").read_text()) for d in TRIO}

    def test_files_exist_and_schema(self):
        schema = json.loads((IFACE / "dummy_scores_schema.json").read_text())
        self.assertEqual(schema["schema_version"], mds.SCHEMA_VERSION)
        for d in TRIO:
            known = self.meta[d]["known_classes"]
            for sp in SPLITS:
                df = pd.read_parquet(IFACE / "dummy_scores" / d / f"{sp}_scores.parquet")
                for col in mds.BASE_COLS:
                    self.assertIn(col, df.columns, f"{d}/{sp} missing {col}")
                for c in known:
                    self.assertIn(f"fid__{c}", df.columns, f"{d}/{sp} missing fid__{c}")

    def test_row_alignment(self):
        for d in TRIO:
            for sp in SPLITS:
                part = pd.read_csv(PART / d / f"{sp}.csv", usecols=["label_multiclass"])
                df = pd.read_parquet(IFACE / "dummy_scores" / d / f"{sp}_scores.parquet")
                self.assertEqual(len(df), len(part), f"{d}/{sp} row count")
                self.assertTrue((df["sample_id"].to_numpy() == np.arange(len(df))).all())
                self.assertTrue((df["true_label_multiclass"].to_numpy()
                                 == part["label_multiclass"].to_numpy()).all())

    def test_value_ranges_and_invariants(self):
        for d in TRIO:
            known = self.meta[d]["known_classes"]
            fid_cols = [f"fid__{c}" for c in known]
            for sp in SPLITS:
                df = pd.read_parquet(IFACE / "dummy_scores" / d / f"{sp}_scores.parquet")
                fid = df[fid_cols].to_numpy()
                self.assertTrue((fid >= 0).all() and (fid <= 1).all(), f"{d}/{sp} fid range")
                # nonconformity == 1 - max_fidelity, and max_fidelity == row max of the fid matrix
                np.testing.assert_allclose(df["max_fidelity"], fid.max(axis=1), atol=1e-9)
                np.testing.assert_allclose(df["nonconformity"], 1 - df["max_fidelity"], atol=1e-9)
                self.assertTrue((df["nonconformity"] >= 0).all() and (df["nonconformity"] <= 1).all())
                if sp == "zeroday":
                    self.assertTrue((df["y_known"] == 0).all())
                    self.assertTrue(df["fid_true_class"].isna().all())
                else:
                    self.assertTrue((df["y_known"] == 1).all())

    def test_deterministic(self):
        for d in TRIO:
            known = self.meta[d]["known_classes"]
            a = mds.build_split(d, "calibration", known)
            b = mds.build_split(d, "calibration", known)
            pd.testing.assert_frame_equal(a, b)

    def test_conformal_selfcheck_sane(self):
        sc = json.loads((BASE / "week2" / "reports" / "_generated"
                         / "dummy_score_selfcheck.json").read_text())
        for d in TRIO:
            s = sc["datasets"][d]
            # split-conformal on the dummy calibration must control the known false-flag rate near alpha
            self.assertLess(abs(s["known_test_flag_rate"] - mds.ALPHA), 0.03, f"{d} flag rate")
            self.assertTrue(0.0 <= s["zeroday_rejection_rate"] <= 1.0)


if __name__ == "__main__":
    unittest.main()

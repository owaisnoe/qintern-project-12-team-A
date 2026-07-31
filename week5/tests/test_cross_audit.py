"""Week 5 · Day 30 — tests for the cross-audit (independent re-derivations must match the repo's)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import cross_audit as ca                            # noqa: E402
from conformal_calibrate import conformal_threshold  # noqa: E402
from coverage_harness import coverage_band           # noqa: E402
from stats_protocol import mcnemar_exact             # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
DATA_OK = ((IFACE / "CICIoT2023" / "test_scores.parquet").exists()
           and (BASE / "week2" / "baselines" / "CICIoT2023" / "results.json").exists()
           and (BASE / "week5" / "RESULTS_FROZEN" / "results_frozen_scalars.json").exists())
needs_data = pytest.mark.skipif(not DATA_OK, reason="interface/baselines/freeze not present")


def test_independent_threshold_matches_repo_implementation():
    rng = np.random.default_rng(7)
    for n in (10, 137, 2048):
        s = rng.random(n)
        q1, k1, n1 = ca.independent_threshold(s, 0.05)
        q2, k2, n2 = conformal_threshold(s, 0.05)
        assert (k1, n1) == (k2, n2)
        assert (q1 == q2) or (np.isinf(q1) and np.isinf(q2))


def test_independent_band_matches_repo_band():
    for n, k, m in ((1000, 951, 2000), (18883, 17940, 18883), (50, 49, 200)):
        lo1, hi1 = ca.independent_band(n, k, m, 0.99)
        lo2, hi2, _, _ = coverage_band(n, k, m, 0.99)
        assert (lo1, hi1) == (lo2, hi2)


def test_doubled_exact_tail_matches_day17():
    for n01, n10 in ((0, 0), (3, 10), (869, 1089), (176, 1803)):
        assert abs(ca.doubled_exact_binomial_p(n01, n10) - mcnemar_exact(n10, n01)["p"]) < 1e-15


def test_check_verdict_logic():
    rows = []
    assert ca.check(rows, "a", "-", 1.0, 1.0 + 1e-12) is True
    assert ca.check(rows, "b", "-", 1.0, 1.1) is False
    assert ca.check(rows, "c", "-", "x", "x") is True
    assert [r["verdict"] for r in rows] == [ca.PASS, ca.FAIL, ca.PASS]


@needs_data
def test_raw_rederivation_agrees_with_frozen_scalars():
    import json
    scalars = json.loads((BASE / "week5" / "RESULTS_FROZEN" / "results_frozen_scalars.json")
                         .read_text(encoding="utf-8"))["scalars"]
    raw = ca.raw_scores("CICIoT2023", IFACE)
    q, k, n = ca.independent_threshold(raw["calibration"]["s"], 0.05)
    e = int(np.sum(raw["test"]["s"] > q))
    # the canonical FZR from raw parquet must match the Day-22 integration numbers to 1e-6 rounding
    assert abs(e / raw["test"]["s"].size - 0.048615) < 5e-7
    # QS-Net accuracy re-derived by argmax equals the frozen Table-A scalar
    known = [c[len("fid__"):] for c in raw["test"]["fid_cols"]]
    yhat = np.array(known, dtype=object)[raw["test"]["fid"].argmax(axis=1)].astype(str)
    acc = float(np.mean(yhat == raw["test"]["y"]))
    assert abs(round(acc, 4) - scalars["tableA/CICIoT2023/qsnet/accuracy"]) < 1e-12


@needs_data
def test_main_single_dataset_all_green(tmp_path, monkeypatch):
    monkeypatch.setattr(ca, "GEN", tmp_path)       # never overwrite the real audit artifacts from a test
    monkeypatch.setattr(ca, "REPORTS", tmp_path)
    out = ca.main(["--datasets", "CICIoT2023"])
    assert out["day"] == 30
    assert out["n_fail"] == 0                       # the tree this test runs on must audit green
    assert out["n_warn"] >= 1                       # the week2 known-drift register stays visible
    assert (tmp_path / "w5_07_cross_audit.json").exists()

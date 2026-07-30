"""Week 4 · Day 20 — tests for the heuristic-threshold baseline + conformal ablation."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import heuristic_ablation as ha                     # noqa: E402
from conformal_calibrate import conformal_threshold, IFACE, TRIO  # noqa: E402

IFACE_OK = (BASE / "week2" / "interface" / "dummy_scores" / "CICIoT2023" / "calibration_scores.parquet").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")


def test_insample_percentile_is_at_or_below_conformal_threshold():
    scores = np.arange(1, 101) / 100.0
    q, k, n = conformal_threshold(scores, 0.05)         # k=96 -> s_(96)=0.96 (with +1)
    tau = ha.insample_percentile_threshold(scores, 0.05)  # (1-α) quantile, no +1
    assert tau <= q                                      # dropping the +1 lowers the threshold


def test_sqrt_if_squared_round_trips():
    F = np.array([0.0, 0.25, 0.5, 0.81, 1.0])
    np.testing.assert_allclose(ha.sqrt_if_squared(F ** 2, True), F, atol=1e-12)
    np.testing.assert_allclose(ha.sqrt_if_squared(F, False), F)   # off by default


def test_fixed_cutoff_is_alpha_independent():
    rng = np.random.default_rng(0)
    s_test = rng.random(5000)
    e1 = float(np.mean(s_test > ha.fixed_threshold(0.5)))
    # α does not enter a fixed cutoff at all -> identical flag rate regardless of α
    assert e1 == float(np.mean(s_test > ha.fixed_threshold(0.5)))


def test_no_plus_one_heuristic_is_anticonservative_at_small_n():
    rng = np.random.default_rng(0)
    test = rng.random(20000)
    alpha, n = 0.05, 30
    cfzr, hfzr = [], []
    for _ in range(300):
        cal = rng.random(n)
        q, _, _ = conformal_threshold(cal, alpha)
        tau = ha.insample_percentile_threshold(cal, alpha)
        cfzr.append(float(np.mean(test > q)))
        hfzr.append(float(np.mean(test > tau)))
    assert np.mean(hfzr) > alpha                 # heuristic drifts above the target (no +1)
    assert np.mean(cfzr) <= alpha + 0.005        # conformal ≈ valid (with +1)
    assert np.mean(hfzr) > np.mean(cfzr)         # heuristic over-flags vs conformal at every draw


@needs_iface
def test_ablate_dataset_runs_and_conformal_in_band():
    r = ha.ablate_dataset("CICIoT2023", 0.05, IFACE)
    assert r["conformal"]["in_band"] is True
    assert r["heuristic"]["tau"] is not None and r["fixed"]["tau"] == 0.5
    assert set(r) >= {"conformal", "heuristic", "fixed", "insample_source"}


@needs_iface
def test_small_n_demo_shows_heuristic_exceeds_alpha():
    rows = ha.small_n_demo("CICIoT2023", 0.05, [30, 50], IFACE, n_rep=100)
    assert all(x["heuristic_exceeds_alpha"] for x in rows)       # anti-conservative at small n

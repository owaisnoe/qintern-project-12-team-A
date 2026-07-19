"""Week 3 · Day 17 — tests for the statistical protocol (primitives + dry-run wiring)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import stats_protocol as sp  # noqa: E402

HARNESS_OK = (BASE / "week2" / "reports" / "_generated" / "stats_harness.json").exists()
PREDS_OK = (BASE / "week2" / "baselines" / "CICIoT2023" / "predictions.csv").exists()


def test_summarize_matches_scipy_reference():
    v = [0.71, 0.74, 0.69, 0.73, 0.70]
    s = sp.summarize(v)
    assert s["mean"] == pytest.approx(np.mean(v))
    assert s["std"] == pytest.approx(np.std(v, ddof=1))
    lo, hi = stats.t.interval(0.95, 4, loc=np.mean(v), scale=stats.sem(v))
    assert s["ci95_low"] == pytest.approx(lo) and s["ci95_high"] == pytest.approx(hi)


def test_paired_t_matches_scipy_and_self_is_null():
    a = [0.80, 0.82, 0.79, 0.81, 0.80]
    b = [0.78, 0.80, 0.78, 0.79, 0.77]
    r = sp.paired_t(a, b)
    t_ref, p_ref = stats.ttest_rel(a, b)
    assert r["t"] == pytest.approx(float(t_ref)) and r["p"] == pytest.approx(float(p_ref))
    self_r = sp.paired_t(a, a)
    assert self_r == {"t": 0.0, "df": 4, "p": 1.0, "mean_diff": 0.0,
                      "note": "zero-variance differences"}


def test_cohens_d_paired_known_value():
    a, b = np.array([1.0, 2.0, 3.0]), np.array([0.5, 1.0, 2.5])
    d = a - b                                      # [0.5, 1.0, 0.5] -> mean 2/3, sd 0.288675
    assert sp.cohens_d_paired(a, b) == pytest.approx((2 / 3) / np.std(d, ddof=1))
    assert sp.cohens_d_paired(a, a) == 0.0


def test_mcnemar_exact_hand_computed():
    # n01=1, n10=9: p = 2 * P(X <= 1 | n=10, 1/2) = 2 * 11/1024
    r = sp.mcnemar_exact(1, 9)
    assert r["p"] == pytest.approx(2 * 11 / 1024)
    assert sp.mcnemar_exact(0, 0)["p"] == 1.0
    assert sp.mcnemar_exact(5, 5)["p"] == 1.0      # perfectly balanced -> no evidence


def test_holm_bonferroni_worked_example():
    # classic: p = [0.01, 0.04, 0.03, 0.005], m=4
    # sorted: .005*4=.02, .01*3=.03, .03*2=.06, .04*1=.06 (monotone) -> adjusted [.03, .06, .06, .02]
    r = sp.holm_bonferroni([0.01, 0.04, 0.03, 0.005], alpha=0.05)
    assert r["p_adjusted"] == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert r["reject"] == [True, False, False, True]


def test_holm_is_monotone_and_bounded():
    rng = np.random.default_rng(42)
    p = rng.uniform(size=25)
    adj = np.array(sp.holm_bonferroni(p)["p_adjusted"])
    assert np.all(adj <= 1.0) and np.all(adj >= p - 1e-12)
    order = np.argsort(p)
    assert np.all(np.diff(adj[order]) >= -1e-12)   # adjusted p non-decreasing in raw-p order


@pytest.mark.skipif(not HARNESS_OK, reason="Iwo Day-13 stats_harness.json not present")
def test_crosscheck_reproduces_iwo_statistics():
    n = sp.crosscheck_summaries(sp.load_harness())
    assert n >= 30                                  # every (dataset, head, metric) cell re-derived


@pytest.mark.skipif(not (HARNESS_OK and PREDS_OK), reason="week2 artifacts not present")
def test_dryrun_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, "GEN", tmp_path)
    out = sp.main([])
    assert out["crosscheck_cells"] >= 30
    assert all(r["p"] == 1.0 for r in out["sanity_self_tests"])
    assert (tmp_path / "w3_03_significance_dryrun.json").exists()
    assert (tmp_path / "w3_03_significance_dryrun.csv").exists()
    m = out["holm"]["m"]
    assert m == len(out["head_pair_tests"]) and m > 0

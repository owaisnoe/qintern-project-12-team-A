"""Week 3 · Day 16 — tests for the coverage-verification harness (exact band + α-sweep).

Synthetic tests exercise the finite-sample law and verdict logic with no data dependency; the
interface-backed tests (marked) run against the Day-14 dummy scores shipped in the repo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import coverage_harness as ch                       # noqa: E402
from conformal_calibrate import conformal_threshold  # noqa: E402

IFACE_OK = (BASE / "week2" / "interface" / "dummy_scores" / "CICIoT2023" / "calibration_scores.parquet").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")

RNG = np.random.default_rng(42)


def _flags(s_cal, s_test, alpha):
    q, k, n = conformal_threshold(s_cal, alpha)
    return int(np.sum(s_test > q)), q, k, n


# ------------------------------------------------------------------ exact law

def test_betabinom_pmf_is_a_distribution_with_the_conformal_mean():
    m, a, b = 500, 26, 475                      # n=500 cal, k=475 -> a = n+1-k = 26
    pmf = ch.betabinom_pmf(m, a, b)
    assert pmf.shape == (m + 1,)
    assert abs(pmf.sum() - 1.0) < 1e-12
    mean = float((np.arange(m + 1) * pmf).sum())
    assert abs(mean - m * a / (a + b)) < 1e-8    # E[E] = m·a/(a+b)


def test_band_contains_monte_carlo_flags():
    """~99% of exchangeable draws must land inside the exact 99% band."""
    n, m, alpha, trials = 150, 150, 0.10, 1500
    hits = 0
    for _ in range(trials):
        s = RNG.uniform(size=n + m)
        e, q, k, _ = _flags(s[:n], s[n:], alpha)
        lo, hi, _, _ = ch.coverage_band(n, k, m, level=0.99)
        hits += int(lo <= e <= hi)
    assert hits / trials >= 0.97                 # exact-law band, allow MC slack


def test_degenerate_alpha_never_flags():
    lo, hi, mean, pmf = ch.coverage_band(n=5, k=6, m=100)   # k > n -> q = +inf
    assert (lo, hi, mean) == (0, 0, 0.0) and pmf is None
    e, q, _, _ = _flags(np.arange(5) / 5.0, RNG.uniform(size=100), alpha=0.01)
    assert np.isinf(q) and e == 0


# ------------------------------------------------------------------ verdict logic on synthetic scores

def _mini_verify(s_cal, s_test, alpha, level=0.99):
    e, q, k, n = _flags(s_cal, s_test, alpha)
    lo, hi, mean, pmf = ch.coverage_band(n, k, s_test.size, level)
    return {"e": e, "lo": lo, "hi": hi, "p": ch.tail_p_value(pmf, e), "ok": e <= hi}


def test_exchangeable_scores_pass_across_grid():
    s = RNG.normal(size=4000)
    s_cal, s_test = s[:2000], s[2000:]
    for alpha in (0.01, 0.05, 0.10, 0.20):
        assert _mini_verify(s_cal, s_test, alpha)["ok"]


def test_broken_exchangeability_fails():
    """A genuinely shifted test distribution must be caught — that is the harness's whole job."""
    s_cal = RNG.normal(size=3000)
    s_test = RNG.normal(size=3000) + 0.35        # test scores systematically more novel
    v = _mini_verify(s_cal, s_test, 0.05)
    assert not v["ok"] and v["p"] < 1e-4


def test_q_monotone_and_fzr_monotone_in_alpha():
    s_cal, s_test = RNG.uniform(size=2000), RNG.uniform(size=2000)
    qs, es = [], []
    for alpha in (0.01, 0.05, 0.10, 0.15, 0.20):
        e, q, _, _ = _flags(s_cal, s_test, alpha)
        qs.append(q), es.append(e)
    assert all(a >= b for a, b in zip(qs, qs[1:]))   # larger α -> smaller (or equal) threshold
    assert all(a <= b for a, b in zip(es, es[1:]))   # larger α -> more (or equal) flags


# ------------------------------------------------------------------ interface-backed (repo data)

@needs_iface
def test_headline_matches_day15_threshold():
    r = ch.verify_dataset("CICIoT2023", 0.05, str(ch.IFACE))
    assert r["q"] == pytest.approx(0.300551, abs=1e-6)      # AK's Day-15 first threshold
    assert r["fzr_observed"] == pytest.approx(0.0486, abs=1e-4)
    assert r["verdict"] == "PASS"


@needs_iface
def test_bot_expectation_bound_fails_but_exact_band_passes():
    """Day-15 flagged BoT (dummy) at FZR 0.0530 > α; the exact law says ordinary sampling noise."""
    r = ch.verify_dataset("BoT-IoT", 0.05, str(ch.IFACE))
    assert not r["expectation_ok"]
    assert r["finite_sample_ok"] and r["verdict"] == "PASS"
    assert r["p_value_upper"] > ch.FAIL_P


@needs_iface
def test_cli_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(ch, "GEN", tmp_path / "_generated")
    monkeypatch.setattr(ch, "FIG", tmp_path / "figures")
    out = ch.main(["--datasets", "CICIoT2023", "--sweep", "0.05", "0.15", "0.05", "--no-figure"])
    assert (tmp_path / "_generated" / "w3_02_coverage_verification.json").exists()
    assert (tmp_path / "_generated" / "w3_02_alpha_sweep.csv").exists()
    assert out["headline"][0]["dataset"] == "CICIoT2023"
    assert out["sweep_all_pass"] in (True, False)

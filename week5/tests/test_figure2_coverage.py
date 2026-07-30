"""Week 5 · Day 27 — tests for Figure 2 (coverage headline)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import figure2_coverage as f2                       # noqa: E402
from coverage_harness import coverage_band          # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
IFACE_OK = (IFACE / "CICIoT2023" / "test_scores.parquet").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")


def test_band_tracks_the_diagonal():
    # the exact band's expected rate ~ (n+1-k)/(n+1) ~ alpha, so the band brackets the diagonal y=alpha
    n, alpha = 1000, 0.05
    import numpy as np
    k = int(np.ceil((1 - alpha) * (n + 1)))
    lo, hi, exp, _ = coverage_band(n, k, 2000, 0.99)
    assert lo / 2000 <= alpha <= hi / 2000
    assert abs(exp - alpha) < 0.01


@needs_iface
def test_five_seed_points_structure_and_in_band():
    p = f2.five_seed_points("CICIoT2023", IFACE, 0.05, f2.SEEDS)
    assert p["seeds"] == f2.SEEDS and len(p["per_seed"]) == 5
    assert p["min_fzr"] <= p["mean_fzr"] <= p["max_fzr"]
    # the 5-seed spread sits inside the exact band on the i.i.d. dummy interface
    assert p["band_lo_rate"] <= p["min_fzr"] and p["max_fzr"] <= p["band_hi_rate"]


@needs_iface
def test_main_writes_figure_and_sweep(tmp_path, monkeypatch):
    monkeypatch.setattr(f2, "GEN", tmp_path)
    monkeypatch.setattr(f2, "REPORTS", tmp_path)
    monkeypatch.setattr(f2, "FIG", tmp_path)
    out = f2.main(["--datasets", "CICIoT2023", "BoT-IoT", "UNSW-NB15", "--alpha", "0.05",
                   "--sweep", "0.01", "0.20", "0.01"])
    assert len(out["points"]) == 3
    assert (tmp_path / "w5_fig2_coverage.png").exists()
    assert (tmp_path / "w5_03_figure2_data.csv").exists()
    # sweep grid is 0.01..0.20 step 0.01 = 20 points x 3 datasets
    assert len(out["sweep_grid"]) == 20

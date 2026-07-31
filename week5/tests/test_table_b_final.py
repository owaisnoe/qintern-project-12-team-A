"""Week 5 · Day 28 — tests for Table B FINAL (all-seed coverage CIs + assembly reuse)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import table_b_final as tbf                        # noqa: E402
from stats_protocol import summarize               # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
IFACE_OK = (IFACE / "CICIoT2023" / "test_scores.parquet").exists()
ART_OK = ((BASE / "week4" / "INTEGRATION" / "frozen_thresholds.json").exists()
          and (BASE / "week4" / "reports" / "_generated" / "w4_03_conformal_integration.json").exists()
          and (BASE / "week4" / "reports" / "_generated" / "w4_01_zeroday_recall.json").exists()
          and (BASE / "week4" / "reports" / "_generated" / "w4_04_live_coverage.json").exists())
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")
needs_artifacts = pytest.mark.skipif(not ART_OK, reason="Day-19/21/22/23 artifacts not present")


@needs_iface
def test_all_seed_ci_structure_and_determinism():
    a = tbf.all_seed_ci("CICIoT2023", IFACE, 0.05)
    b = tbf.all_seed_ci("CICIoT2023", IFACE, 0.05)
    assert a == b                                                  # seeded -> fully reproducible
    assert a["seeds"] == tbf.SEEDS and len(a["per_seed"]) == 5
    f5 = a["fzr_5seed"]
    assert f5["ci95_low"] <= f5["mean"] <= f5["ci95_high"]
    # t-based CI must match the Day-17 summarize() convention exactly
    ref = summarize([r["fzr"] for r in a["per_seed"]])
    assert abs(f5["mean"] - round(ref["mean"], 6)) < 1e-12
    assert abs(f5["ci95_low"] - round(ref["ci95_low"], 6)) < 1e-12


@needs_iface
def test_all_seed_ci_recall_uses_fixed_zeroday_pool():
    a = tbf.all_seed_ci("CICIoT2023", IFACE, 0.05)
    n_zd = {r["n_zeroday"] for r in a["per_seed"]}
    assert len(n_zd) == 1                                          # the zero-day pool never re-splits
    for r in a["per_seed"]:
        assert 0.0 <= r["zeroday_recall"] <= 1.0
        assert r["zeroday_detected"] <= r["n_zeroday"]


@needs_iface
def test_all_seed_ci_guarantee_holds_on_dummy():
    # the dummy interface is i.i.d. by construction -> every re-split lands inside its own exact band
    a = tbf.all_seed_ci("CICIoT2023", IFACE, 0.05)
    assert a["n_in_band"] == 5 and a["all_in_band"] is True
    assert a["fzr_ci_covers_alpha"] is True


@needs_iface
@needs_artifacts
def test_main_writes_final_table_and_crosschecks(tmp_path, monkeypatch):
    monkeypatch.setattr(tbf, "GEN", tmp_path)
    monkeypatch.setattr(tbf, "REPORTS", tmp_path)
    out = tbf.main(["--datasets", "CICIoT2023", "--alpha", "0.05"])
    assert out["day"] == 28
    (r,) = out["table_b_final"]
    # Day-24 canonical cells preserved ...
    for key in ("threshold_q", "achieved_alpha", "band", "guarantee_held", "qsnet_recall"):
        assert key in r
    # ... plus the Day-28 CI blocks with provisional status
    assert r["status"]["fzr_5seed"] == tbf.PROVISIONAL
    assert r["fzr_5seed"]["ci95_low"] <= r["fzr_5seed"]["mean"] <= r["fzr_5seed"]["ci95_high"]
    assert (tmp_path / "w5_04_table_b.tex").exists()
    assert (tmp_path / "w5_04_allseed_ci.csv").exists()
    # cross-module consistency: 5-seed FZR mean == Table A all-seed mean (same seeds + machinery)
    cc = out["crosscheck_table_a"]
    if cc.get("checked"):
        assert cc["all_agree"] is True


@needs_iface
@needs_artifacts
def test_tex_has_constant_column_count(tmp_path, monkeypatch):
    monkeypatch.setattr(tbf, "GEN", tmp_path)
    monkeypatch.setattr(tbf, "REPORTS", tmp_path)
    out = tbf.main(["--datasets", "CICIoT2023", "BoT-IoT"])
    tex = (tmp_path / "w5_04_table_b.tex").read_text(encoding="utf-8")
    body = tex.split(r"\midrule")[1].split(r"\bottomrule")[0]
    data_rows = [ln for ln in body.splitlines() if ln.strip().endswith(r"\\")]
    assert len(data_rows) == len(out["table_b_final"])
    for ln in data_rows:
        assert ln.count("&") == 9                                  # 10 columns => 9 ampersands

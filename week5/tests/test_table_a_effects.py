"""Week 5 · Day 29 — tests for Table A FINAL (significance vs every baseline + effect sizes)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import table_a_effects as tae                      # noqa: E402
from stats_protocol import cohens_d_paired          # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
IFACE_OK = (IFACE / "CICIoT2023" / "test_scores.parquet").exists()
BASE_OK = (BASE / "week2" / "baselines" / "CICIoT2023" / "results.json").exists()
DEC_OK = (BASE / "week4" / "reports" / "_generated" / "w4_03_decisions_CICIoT2023.csv").exists()
needs_data = pytest.mark.skipif(not (IFACE_OK and BASE_OK), reason="interface/baselines not present")
needs_decisions = pytest.mark.skipif(not (BASE_OK and DEC_OK), reason="Day-22 decisions not present")


def test_dz_matches_day17_convention():
    a = np.array([1, 1, 0, 1, 0, 1], dtype=float)
    b = np.array([1, 0, 0, 1, 1, 1], dtype=float)
    assert tae._dz(a, b) == round(float(cohens_d_paired(a, b)), 4)
    assert tae._dz(a, a) == 0.0                                   # zero variance -> 0 by convention


def test_apply_holm_is_monotone_and_marks_family():
    rows = [{"p_raw": 0.001}, {"p_raw": 0.04}, {"p_raw": 0.9}]
    rows, holm = tae.apply_holm(rows, alpha=0.05)
    assert holm["m"] == 3
    for r in rows:
        assert r["p_holm"] >= r["p_raw"] - 1e-12                   # Holm never decreases a p-value
    assert rows[0]["significant"] is True and rows[2]["significant"] is False


@needs_data
def test_closed_set_row_effects_and_consistency():
    c = tae.closed_set_row("CICIoT2023", IFACE)
    # sign convention: QS-Net below XGBoost on the dummy -> negative gap, negative h and d_z
    assert c["acc_diff"] < 0 and c["cohens_h"] < 0 and c["cohens_dz"] < 0
    # acc values must agree with the Day-26 rows (same inputs, same rounding)
    import table_a as ta
    assert c["acc_xgboost"] == ta.xgboost_row("CICIoT2023")["accuracy"]
    assert c["acc_qsnet"] == ta.qsnet_row("CICIoT2023", IFACE, "dummy")["accuracy"]
    assert 0.0 <= c["p_raw"] <= 1.0


@needs_decisions
def test_known_fa_rows_cover_every_head_and_are_known_only():
    rows = tae.known_fa_rows("CICIoT2023")
    names = {r["baseline"] for r in rows}
    assert names == {"Isolation Forest", "Autoencoder"}            # CIC has no OC-SVM (real absence)
    for r in rows:
        assert r["n_pairs"] == 18883                               # KNOWN test rows only, no zero-day
        assert 0.0 <= r["fa_rate_qsnet"] <= 1.0 and 0.0 <= r["fa_rate_baseline"] <= 1.0


@needs_decisions
def test_known_fa_rows_bot_includes_ocsvm():
    rows = tae.known_fa_rows("BoT-IoT")
    assert {r["baseline"] for r in rows} == {"Isolation Forest", "Autoencoder", "OC-SVM"}


@needs_data
@needs_decisions
def test_main_families_holm_and_files(tmp_path, monkeypatch):
    monkeypatch.setattr(tae, "GEN", tmp_path)
    monkeypatch.setattr(tae, "REPORTS", tmp_path)
    out = tae.main(["--datasets", "CICIoT2023", "BoT-IoT", "UNSW-NB15"])
    assert out["day"] == 29
    assert out["closed_set"]["holm"]["m"] == 3                     # one per dataset
    assert out["known_fa"]["holm"]["m"] == 8                       # 2 + 3 + 3 heads
    # closed-set p_holm must agree with the Day-26 McNemar family (same pairing, same Holm family)
    import table_a as ta
    _, mc26, *_ = ta.build_table_a(["CICIoT2023", "BoT-IoT", "UNSW-NB15"], IFACE, "dummy", 0.05)
    p26 = {m["dataset"]: m["p_holm"] for m in mc26}
    for c in out["closed_set"]["rows"]:
        assert abs(c["p_holm"] - p26[c["dataset"]]) < 1e-12
    for f in ("w5_05_table_a.tex", "w5_05_table_a.md", "w5_05_known_fa.csv",
              "w5_05_table_a_effects.json", "w5_05_table_a_effects.csv"):
        assert (tmp_path / f).exists()


@needs_data
@needs_decisions
def test_tex_has_constant_column_count(tmp_path, monkeypatch):
    monkeypatch.setattr(tae, "GEN", tmp_path)
    monkeypatch.setattr(tae, "REPORTS", tmp_path)
    out = tae.main(["--datasets", "CICIoT2023"])
    tex = (tmp_path / "w5_05_table_a.tex").read_text(encoding="utf-8")
    body = tex.split(r"\midrule")[1].split(r"\bottomrule")[0]
    data_rows = [ln for ln in body.splitlines() if ln.strip().endswith(r"\\")]
    assert len(data_rows) == len(out["rows"])
    for ln in data_rows:
        assert ln.count("&") == 7                                  # 8 columns => 7 ampersands

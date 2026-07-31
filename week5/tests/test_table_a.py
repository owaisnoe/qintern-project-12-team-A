"""Week 5 · Day 26 — tests for Table A (RQ1), significance, and the coverage diagnostics."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import table_a as ta                               # noqa: E402
from coverage_harness import coverage_band          # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
IFACE_OK = (IFACE / "CICIoT2023" / "test_scores.parquet").exists()
BASE_OK = (BASE / "week2" / "baselines" / "CICIoT2023" / "results.json").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")
needs_baselines = pytest.mark.skipif(not BASE_OK, reason="frozen Day-12 baselines not present")


def test_auroc_pure_math():
    assert ta._auroc([1.0, 1.0], [0.0, 0.0]) == 1.0
    assert ta._auroc([0.5], [0.5]) == 0.5
    assert ta._auroc([], [1.0]) is None


def test_macro_f1_identity():
    from sklearn.metrics import f1_score
    y = np.array(["a", "b", "a", "c", "b"])
    assert f1_score(y, y, labels=["a", "b", "c"], average="macro", zero_division=0) == 1.0


def test_per_class_band_is_deterministic_and_ordered():
    lo1, hi1, exp1, _ = coverage_band(1000, 951, 200, 0.99)
    lo2, hi2, exp2, _ = coverage_band(1000, 951, 200, 0.99)
    assert (lo1, hi1) == (lo2, hi2) and lo1 <= hi1
    assert 0.0 <= exp1 <= 1.0 and exp1 == exp2


@needs_baselines
def test_xgboost_numbers_are_copied_not_recomputed():
    mc = json.loads((BASE / "week2" / "baselines" / "CICIoT2023" / "results.json")
                    .read_text())["detector"]["multiclass"]
    row = ta.xgboost_row("CICIoT2023")
    assert row["source_kind"] == "real" and row["arm"] == "classical"
    assert row["accuracy"] == round(float(mc["accuracy"]), 4)
    assert row["macro_f1"] == round(float(mc["f1_macro"]), 4)
    assert row["auroc_ovr_macro"] == round(float(mc["auroc_ovr_macro"]), 4)


@needs_iface
def test_qsnet_row_is_provisional_and_in_range():
    r = ta.qsnet_row("CICIoT2023", IFACE, "dummy")
    assert r["arm"] == "quantum" and r["source_kind"] == "dummy"
    for m in ("accuracy", "macro_f1", "auroc_ovr_macro"):
        assert 0.0 <= r[m] <= 1.0


@needs_iface
@needs_baselines
def test_mcnemar_row_alignment_guard_and_counts():
    qs, xgb = ta.paired_correct("CICIoT2023", IFACE)              # raises if not row-aligned
    assert qs.shape == xgb.shape and qs.dtype == bool
    m = ta.mcnemar_row("CICIoT2023", IFACE)
    assert m["n_pairs"] == qs.size
    assert 0.0 <= m["p_raw"] <= 1.0


@needs_iface
def test_all_seed_coverage_five_seeds_in_band():
    c = ta.all_seed_coverage("CICIoT2023", IFACE, 0.05)
    assert c["seeds"] == ta.SEEDS and len(c["per_seed"]) == 5
    assert c["n_seeds"] == 5
    # the dummy interface is i.i.d. by construction -> the guarantee holds on every re-split
    assert c["n_in_band"] == 5 and c["all_in_band"] is True


@needs_iface
def test_per_class_fzr_structure_and_own_band():
    pc = ta.per_class_fzr("CICIoT2023", IFACE, 0.05)
    assert pc["n_classes"] == len(pc["per_class"]) > 0
    assert pc["conditional_floor"] == int(np.ceil(1.0 / 0.05)) - 1   # ⌈1/α⌉−1 = 19
    for r in pc["per_class"]:
        assert r["band_lo_rate"] <= r["band_hi_rate"]
        # in_band is judged on counts; dividing by m_c preserves order, so it must agree with the rates
        assert r["in_band"] == bool(r["band_lo_rate"] - 1e-9 <= r["fzr"] <= r["band_hi_rate"] + 1e-9)


@needs_iface
@needs_baselines
def test_tex_has_constant_column_count():
    rows, mcnemar, *_ = ta.build_table_a(["CICIoT2023", "BoT-IoT"], IFACE, "dummy", 0.05)
    tex = ta.render_table_a_tex(rows, mcnemar, 0.05, "dummy")
    body = tex.split(r"\midrule")[1].split(r"\bottomrule")[0]
    data_rows = [ln for ln in body.splitlines() if ln.strip().endswith(r"\\")]
    assert len(data_rows) == len(rows)                              # one line per system-dataset row
    for ln in data_rows:
        assert ln.count("&") == 4                                   # 5 columns => 4 ampersands


@needs_iface
@needs_baselines
def test_holm_applied_over_dataset_family(tmp_path, monkeypatch):
    monkeypatch.setattr(ta, "GEN", tmp_path)
    monkeypatch.setattr(ta, "REPORTS", tmp_path)
    out = ta.main(["--datasets", "CICIoT2023", "BoT-IoT", "UNSW-NB15", "--alpha", "0.05"])
    assert out["holm"]["m"] == 3                                    # 3 McNemar comparisons in the family
    for m in out["mcnemar"]:
        assert m["p_holm"] >= m["p_raw"] - 1e-12                     # Holm never decreases a p-value
    assert (tmp_path / "w5_02_table_a.tex").exists()

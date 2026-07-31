"""Week 5 · Day 29 — tests for the conformal ablation asset + RQ5 honesty compilation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import ablation_rq5 as ab                          # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
IFACE_OK = (IFACE / "CICIoT2023" / "test_scores.parquet").exists()
SIG_OK = (BASE / "week4" / "reports" / "_generated" / "w4_06_significance.json").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")
needs_sig = pytest.mark.skipif(not SIG_OK, reason="Day-25 significance suite not present")


@needs_sig
def test_load_rq5_faithful_to_day25():
    rq5 = ab.load_rq5()
    doc = json.loads((BASE / "week4" / "reports" / "_generated" / "w4_06_significance.json")
                     .read_text(encoding="utf-8"))
    # a compilation must not alter the verdicts: same rows, same counts, same margin
    assert rq5["verdicts"] == doc["rq5_verdicts"]
    assert rq5["margin"] == doc["equivalence_margin"]
    n = rq5["counts"]
    assert (n["n_quantum_ahead"] + n["n_quantum_behind"] + n["n_equivalent"]
            + n["n_unresolved"]) == len(rq5["verdicts"])


@needs_iface
def test_ablation_conformal_in_band_heuristic_unbadged():
    r = ab.ablate_dataset("CICIoT2023", 0.05, IFACE, fixed_cutoff=ab.FIXED_CUTOFF)
    # the conformal rule owns the certificate; on the i.i.d. dummy it must land inside its band
    assert r["conformal"]["in_band"] is True
    # the three rules produce three thresholds (fixed differs by construction)
    assert r["fixed"]["tau"] == ab.FIXED_CUTOFF
    assert r["conformal"]["tau"] != r["fixed"]["tau"]


@needs_iface
def test_small_n_ordering_and_anticonservatism():
    rows = ab.small_n_demo("CICIoT2023", 0.05, (20, 50), IFACE)
    assert len(rows) == 2
    for r in rows:
        # deterministic +1 ordering: q_conf = s_(k) with k = ceil((1-a)(n+1)) is >= the in-sample
        # (1-a) 'lower' quantile of the SAME subsample, so conformal FZR <= heuristic FZR per draw
        # and therefore in the mean. (The conformal MEAN may still sit a hair above alpha at tiny n
        # -- Monte-Carlo noise on an expectation guarantee -- so no blanket <= alpha assert here.)
        assert r["conformal_mean_fzr"] <= r["heuristic_mean_fzr"] + 1e-12
    # the missing +1 is clearly visible where theory says: the smallest n
    assert rows[0]["heuristic_exceeds_alpha"] is True
    assert rows[0]["heuristic_mean_fzr"] > 1.5 * 0.05              # ~2x the budget at n=20


@needs_iface
@needs_sig
def test_main_writes_assets_and_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(ab, "GEN", tmp_path)
    monkeypatch.setattr(ab, "REPORTS", tmp_path)
    monkeypatch.setattr(ab, "FIG", tmp_path)
    out = ab.main(["--datasets", "CICIoT2023", "--sweep", "0.05", "0.10", "0.05"])
    assert out["day"] == 29
    assert len(out["ablation"]) == 1
    # per-cell: conformal mean never exceeds the heuristic mean (the +1 ordering, deterministic)
    for r in out["small_n"]:
        assert r["conformal_mean_fzr"] <= r["heuristic_mean_fzr"] + 1e-12
    assert out["heuristic_anticonservative_cells"] >= 1             # visible at the small-n end
    for f in ("w5_06_ablation.md", "w5_06_ablation.tex", "w5_06_ablation.csv",
              "w5_06_small_n.csv", "w5_06_rq5_honesty.md", "w5_06_ablation_rq5.json",
              "w5_fig3_ablation.png"):
        assert (tmp_path / f).exists(), f
    # RQ5 verdict rows flow through unaltered
    assert len(out["rq5_verdicts"]) == sum(out["rq5"]["counts"].values())


@needs_iface
@needs_sig
def test_tex_table_shape(tmp_path, monkeypatch):
    monkeypatch.setattr(ab, "GEN", tmp_path)
    monkeypatch.setattr(ab, "REPORTS", tmp_path)
    monkeypatch.setattr(ab, "FIG", tmp_path)
    out = ab.main(["--datasets", "CICIoT2023", "BoT-IoT", "--sweep", "0.05", "0.10", "0.05",
                   "--no-figure"])
    tex = (tmp_path / "w5_06_ablation.tex").read_text(encoding="utf-8")
    body = tex.split(r"\toprule")[1].split(r"\bottomrule")[0]
    data_rows = [ln for ln in body.splitlines() if ln.strip().endswith(r"\\")]
    # 3 rules per dataset (+1 header row also ends in \\)
    assert len(data_rows) == 3 * len(out["ablation"]) + 1
    for ln in data_rows:
        assert ln.count("&") == 5                                  # 6 columns => 5 ampersands

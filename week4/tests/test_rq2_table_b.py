"""Week 4 · Day 24 — tests for the RQ2 assembly + Table B (zero-day guarantee) skeleton."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))

import rq2_table_b as rq2                                # noqa: E402
from coverage_harness import coverage_band                # noqa: E402

ALPHA = 0.05

SOURCES_OK = all((BASE / rel).exists() for rel in rq2.SOURCES.values())
needs_sources = pytest.mark.skipif(
    not SOURCES_OK, reason="Day 19/21/22/23 artifacts not present (run those days first)")


@needs_sources
def test_table_b_assembles_one_row_per_dataset_with_both_halves():
    art = rq2.load_artifacts()
    rows, missing = rq2.build_rq2(art, list(rq2.TRIO), ALPHA)
    assert not missing, missing
    table = rq2.build_table_b(rows, rq2.exchangeability_by_dataset(art["live"]))

    assert [r["dataset"] for r in table] == list(rq2.TRIO)
    for r in table:
        # guarantee half
        assert r["band"][0] < r["band"][1]
        assert r["guarantee_held"] == (r["band"][0] <= r["achieved_alpha"] <= r["band"][1])
        assert r["target_alpha"] == ALPHA
        # power half — reported beside coverage, never instead of it (Prop 3 §5.2)
        assert 0.0 <= r["qsnet_recall"] <= 1.0
        assert r["n_zeroday"] > 0
        assert r["best_classical"] is not None
        assert r["recall_delta"] == pytest.approx(
            r["qsnet_recall"] - r["best_classical_recall"], abs=1e-9)


@needs_sources
def test_numbers_are_copied_from_the_source_artifacts_not_recomputed():
    """Table B must not silently disagree with the reports it summarises."""
    art = rq2.load_artifacts()
    rows, _ = rq2.build_rq2(art, list(rq2.TRIO), ALPHA)
    table = rq2.build_table_b(rows, rq2.exchangeability_by_dataset(art["live"]))

    frozen = art["frozen"]["datasets"]
    integ = {s["dataset"]: s for s in art["integration"]["datasets"]}
    for r in table:
        ds = r["dataset"]
        assert r["threshold_q"] == frozen[ds]["threshold_q"]          # Day 21
        assert r["n_cal"] == frozen[ds]["n_cal"]
        assert r["achieved_alpha"] == integ[ds]["known_test"]["false_zeroday_rate"]   # Day 22
        assert r["qsnet_recall"] == integ[ds]["zeroday"]["recall"]
        assert r["n_zeroday"] == integ[ds]["zeroday"]["n"]

    # ...and against the Day-23 live-coverage run, which verified the same frozen q independently
    live = {r["dataset"]: r for r in art["live"]["live_coverage"]}
    for r in table:
        f = live[r["dataset"]]["frozen"]
        assert r["achieved_alpha"] == pytest.approx(f["fzr_observed"], abs=1e-9)
        assert r["band"] == [f["band_lo_rate"], f["band_hi_rate"]]


def test_band_depends_only_on_split_sizes_not_on_scores():
    """The claim Table B makes about its own final columns: the acceptance region is score-free."""
    n, k, m = 18883, 17940, 18883
    a = coverage_band(n, k, m, rq2.DEFAULT_BAND)[:2]
    b = coverage_band(n, k, m, rq2.DEFAULT_BAND)[:2]
    assert a == b                                        # deterministic
    # widening the calibration set tightens the band; nothing about the scores enters
    wide = coverage_band(n * 4, int(round(k * 4)), m, rq2.DEFAULT_BAND)[:2]
    assert (wide[1] - wide[0]) <= (a[1] - a[0])


@needs_sources
def test_status_marks_dummy_cells_and_leaves_split_geometry_final():
    art = rq2.load_artifacts()
    rows, _ = rq2.build_rq2(art, list(rq2.TRIO), ALPHA)
    table = rq2.build_table_b(rows, rq2.exchangeability_by_dataset(art["live"]))
    st = table[0]["status"]
    for col in ("n_cal", "k", "m_test", "n_zeroday", "band", "best_classical_recall"):
        assert st[col] == rq2.FINAL, f"{col} should not move when Team B lands real scores"
    for col in ("threshold_q", "achieved_alpha", "qsnet_recall", "exchangeability"):
        assert st[col] == rq2.PROVISIONAL, f"{col} rides the dummy interface"


@needs_sources
def test_classical_arms_share_the_calibration_split_and_alpha():
    """Like-for-like: one primary alpha, one calibration split, or Day 25 is not comparable."""
    art = rq2.load_artifacts()
    rows, _ = rq2.build_rq2(art, list(rq2.TRIO), ALPHA)
    for ds in rq2.TRIO:
        group = [r for r in rows if r["dataset"] == ds]
        assert len({r["n_cal"] for r in group}) == 1
        assert len({r["m_test"] for r in group}) == 1
        assert {r["target_alpha"] for r in group} == {ALPHA}
        assert sum(r["arm"] == "quantum" for r in group) == 1
    # CIC has no OC-SVM head (Day-12 shipped IF + AE) — it must be absent, not synthesised
    cic = {r["system"] for r in rows if r["dataset"] == "CICIoT2023"}
    assert "OC-SVM" not in cic and "OC-SVM" in {r["system"] for r in rows
                                                if r["dataset"] == "BoT-IoT"}


@needs_sources
def test_missing_day23_audit_downgrades_the_column_instead_of_failing(monkeypatch):
    art = rq2.load_artifacts()
    rows, _ = rq2.build_rq2(art, list(rq2.TRIO), ALPHA)
    table = rq2.build_table_b(rows, rq2.exchangeability_by_dataset(None))
    assert {r["exchangeability"] for r in table} == {"not audited"}


@needs_sources
def test_rendered_table_b_marks_every_provisional_cell():
    art = rq2.load_artifacts()
    rows, _ = rq2.build_rq2(art, list(rq2.TRIO), ALPHA)
    table = rq2.build_table_b(rows, rq2.exchangeability_by_dataset(art["live"]))

    md = rq2.render_table_b_md(table, ALPHA, "dummy")
    assert "Table B" in md and "Zero-Day Guarantee" in md
    assert md.count("‡") >= 5 * len(table)               # the provisional cells, plus the legend
    assert "dummy" in md

    tex = rq2.render_table_b_tex(table, ALPHA, "dummy")
    assert tex.count(r"\toprule") == 1 and tex.count(r"\bottomrule") == 1
    assert tex.count(r"\ddag") >= 2 * len(table)
    # column count must match the tabular spec or LaTeX will not compile
    spec = tex.split(r"\begin{tabular}{")[1].split("}")[0]
    n_cols = len(spec)
    for line in tex.splitlines():
        if line.strip().endswith(r"\\"):
            assert line.count("&") == n_cols - 1, f"wrong column count: {line}"


@needs_sources
def test_cli_writes_every_declared_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(rq2, "GEN", tmp_path / "_generated")
    monkeypatch.setattr(rq2, "REPORTS", tmp_path)
    monkeypatch.setattr(rq2, "FIG", tmp_path / "figures")
    out = rq2.main(["--no-figure"])

    assert out["day"] == 24 and out["all_guarantees_held"]
    assert len(out["table_b"]) == 3 and len(out["rq2_results"]) == 11
    for f in ("_generated/w4_05_rq2_results.json", "_generated/w4_05_rq2_results.csv",
              "_generated/w4_05_table_b.md", "_generated/w4_05_table_b.tex",
              "w4_05_rq2_table_b.md"):
        assert (tmp_path / f).exists(), f
    saved = json.loads((tmp_path / "_generated" / "w4_05_rq2_results.json").read_text())
    assert saved["research_question"].startswith("RQ2")
    report = (tmp_path / "w4_05_rq2_table_b.md").read_text()
    assert "Day 24" in report and "Table B" in report
    # the report must carry both halves and the honesty caveat
    assert "true-zero-day recall" in report and "not a result" in report

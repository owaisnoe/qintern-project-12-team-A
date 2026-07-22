"""Week 3 · Day 18 — tests for the coverage-table assembler (single-source vs coverage_harness)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import coverage_table as ct                       # noqa: E402
from coverage_harness import verify_dataset        # noqa: E402
from conformal_calibrate import IFACE, TRIO        # noqa: E402

IFACE_OK = (BASE / "week2" / "interface" / "dummy_scores" / "CICIoT2023" / "calibration_scores.parquet").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")


@needs_iface
def test_table_has_a_row_per_dataset_with_required_columns():
    df = ct.build_table(TRIO, 0.05, IFACE)
    assert list(df["dataset"]) == TRIO
    for col in ("n_cal", "k", "q", "target_alpha", "fzr_observed", "band_lo_rate", "band_hi_rate", "verdict"):
        assert col in df.columns


@needs_iface
def test_cic_headline_values_and_pass():
    df = ct.build_table(["CICIoT2023"], 0.05, IFACE)
    r = df.iloc[0]
    assert r["k"] == 17940
    assert abs(r["q"] - 0.300551) < 1e-4
    assert r["verdict"] == "PASS"


@needs_iface
def test_table_is_single_source_of_verify_dataset():
    # every q/band in the table must equal the live harness (no drift from a stale CSV)
    for ds in TRIO:
        row = ct.build_table([ds], 0.05, IFACE).iloc[0]
        ref = verify_dataset(ds, 0.05, IFACE)
        assert row["q"] == ref["q"]
        assert row["band_lo_rate"] == ref["band_lo_rate"]
        assert row["verdict"] == ref["verdict"]


@needs_iface
def test_cli_writes_report_and_generated(tmp_path, monkeypatch):
    monkeypatch.setattr(ct, "GEN", tmp_path)
    monkeypatch.setattr(ct, "REPORTS", tmp_path)
    ct.main(["--alpha", "0.05", "--datasets", "CICIoT2023", "--sweep-csv", str(tmp_path / "none.csv")])
    md = (tmp_path / "w3_04_coverage_table.md").read_text(encoding="utf-8")
    assert "Coverage Table v1" in md and "CICIoT2023" in md
    assert (tmp_path / "w3_04_coverage_table.csv").exists()

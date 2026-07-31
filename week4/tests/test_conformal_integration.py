"""Week 4 · Day 22 — tests for the conformal↔inference integration adapter."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import freeze_integration as fi                                   # noqa: E402
import conformal_integration as ci                                # noqa: E402
from conformal_calibrate import calibrate_dataset, IFACE          # noqa: E402

IFACE_OK = (BASE / "week2" / "interface" / "dummy_scores" / "CICIoT2023" / "calibration_scores.parquet").exists()
FROZEN_OK = (BASE / "week4" / "INTEGRATION" / "frozen_thresholds.json").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")
needs_frozen = pytest.mark.skipif(not FROZEN_OK, reason="Day-21 freeze not present (run freeze_integration.py)")


def test_scores_from_fidelities_squared_flag():
    """s = 1 - max F; with F^2 input the sqrt() must recover the same s."""
    import pandas as pd
    df = pd.DataFrame({"fid__a": [0.36, 0.81], "fid__b": [0.49, 0.64]})   # F^2 values
    s_sq = ci.scores_from_fidelities(df, ["a", "b"], assume_squared=True)
    # sqrt -> F = [[0.6,0.7],[0.9,0.8]]; max = [0.7, 0.9]; s = [0.3, 0.1]
    assert s_sq == pytest.approx([0.3, 0.1])
    s_raw = ci.scores_from_fidelities(df, ["a", "b"], assume_squared=False)
    assert s_raw == pytest.approx([1 - 0.49, 1 - 0.81])


@needs_iface
@needs_frozen
def test_score_contract_holds_on_dummy_interface():
    """Gate 1: recomputed s = 1 - max_c F matches the interface's precomputed nonconformity."""
    frozen = ci.load_frozen_thresholds()
    summary, _ = ci.integrate_dataset("CICIoT2023", frozen, str(IFACE), assume_squared=False, alpha=0.05)
    assert summary["score_contract_ok"]
    assert summary["score_contract_max_abs_err"] <= ci.CONTRACT_TOL


@needs_iface
@needs_frozen
def test_applies_frozen_threshold_and_reproduces_coverage():
    """Gate 2 + 3: applied q equals the frozen q, and achieved coverage reproduces the frozen value."""
    frozen = ci.load_frozen_thresholds()
    q_frozen = frozen["datasets"]["CICIoT2023"]["threshold_q"]
    summary, _ = ci.integrate_dataset("CICIoT2023", frozen, str(IFACE), assume_squared=False, alpha=0.05)
    assert summary["applied_q"] == pytest.approx(q_frozen, abs=1e-9)
    assert summary["coverage_reproduces_frozen"]
    # cross-check against Day-15 directly (calibrate_dataset rounds FZR to 4dp, adapter to 6dp)
    r = calibrate_dataset("CICIoT2023", 0.05, str(IFACE))
    assert summary["known_test"]["false_zeroday_rate"] == pytest.approx(
        r["known_test"]["false_zeroday_rate"], abs=1e-4)


@needs_iface
@needs_frozen
def test_confusion_matrix_partitions_all_rows():
    frozen = ci.load_frozen_thresholds()
    summary, per_row = ci.integrate_dataset("CICIoT2023", frozen, str(IFACE), assume_squared=False, alpha=0.05)
    cm = summary["confusion_known_vs_zeroday"]
    assert cm["tn_known_kept"] + cm["fp_known_flagged"] == summary["known_test"]["n"]
    assert cm["fn_zeroday_missed"] + cm["tp_zeroday_detected"] == summary["zeroday"]["n"]
    # per-row decisions cover every test + zeroday row, only two decision labels
    assert len(per_row) == summary["known_test"]["n"] + summary["zeroday"]["n"]
    assert set(per_row["decision"].unique()) <= {"KNOWN", "ZERO_DAY"}


@needs_iface
@needs_frozen
def test_drift_between_freeze_and_audit_is_caught(monkeypatch):
    """If the frozen q disagrees with a fresh audit recompute, the adapter must assert (no silent drift)."""
    frozen = ci.load_frozen_thresholds()
    tampered = {**frozen, "datasets": {**frozen["datasets"],
                "CICIoT2023": {**frozen["datasets"]["CICIoT2023"], "threshold_q": 0.9}}}
    with pytest.raises(AssertionError):
        ci.integrate_dataset("CICIoT2023", tampered, str(IFACE), assume_squared=False, alpha=0.05)


@needs_iface
@needs_frozen
def test_cli_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(ci, "GEN", tmp_path / "_generated")
    monkeypatch.setattr(ci, "REPORTS", tmp_path / "reports")
    out = ci.main(["--datasets", "CICIoT2023"])
    assert out["datasets"][0]["dataset"] == "CICIoT2023"
    assert (tmp_path / "_generated" / "w4_03_conformal_integration.json").exists()
    assert (tmp_path / "_generated" / "w4_03_decisions_CICIoT2023.csv").exists()
    assert (tmp_path / "reports" / "w4_03_conformal_integration.md").exists()

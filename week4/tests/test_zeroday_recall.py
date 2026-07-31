"""Week 4 · Day 19 — tests for zero-day recall + quantum-vs-classical."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import zeroday_recall as zr                         # noqa: E402
from conformal_calibrate import calibrate_dataset, conformal_threshold, IFACE  # noqa: E402

IFACE_OK = (BASE / "week2" / "interface" / "dummy_scores" / "CICIoT2023" / "calibration_scores.parquet").exists()
CIC_IF = (BASE / "week2" / "baselines" / "CICIoT2023" / "isolation_forest.joblib").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")
needs_baselines = pytest.mark.skipif(not CIC_IF, reason="frozen baseline models not present")


@needs_iface
def test_quantum_recall_equals_calibrate_dataset_rejection():
    q = zr.quantum_recall("CICIoT2023", 0.05, IFACE)
    r = calibrate_dataset("CICIoT2023", 0.05, IFACE)
    assert q["zeroday_recall"] == r["zeroday"]["rejection_rate"]
    assert q["coverage"] == r["known_test"]["coverage"]          # coverage reported alongside recall
    assert q["source_kind"] == "dummy"


@needs_baselines
def test_cic_has_no_ocsvm_head():
    assert zr.classical_head_recall("CICIoT2023", "ocsvm", 0.05) is None   # Day-12 skipped OC-SVM for CIC


@needs_baselines
def test_classical_head_reproduces_conformal_threshold():
    import joblib
    from classical_baselines import load_bundle, score_isolation_forest
    r = zr.classical_head_recall("CICIoT2023", "isolation_forest", 0.05)
    assert r is not None and r["source_kind"] == "real"
    b = load_bundle("CICIoT2023")
    s_cal = np.asarray(score_isolation_forest(joblib.load(BASE / "week2" / "baselines" / "CICIoT2023" /
                                              "isolation_forest.joblib"), b.calibration, b.features), float)
    q, k, n = conformal_threshold(s_cal, 0.05)
    assert abs(r["q"] - round(float(q), 6)) < 1e-9
    # both coverage and recall present, in range
    assert 0.0 <= r["zeroday_recall"] <= 1.0 and 0.0 <= r["coverage"] <= 1.0


@needs_baselines
def test_same_alpha_coverage_holds_for_classical():
    # open-item-4: classical re-thresholded at the same α => false-zero-day ≈ α (within finite-sample slack)
    r = zr.classical_head_recall("BoT-IoT", "isolation_forest", 0.05)
    assert r["false_zeroday_rate"] <= 0.05 + 0.02


@needs_iface
@needs_baselines
def test_compare_dataset_reports_quantum_and_classical_together():
    rows, notes = zr.compare_dataset("CICIoT2023", 0.05, IFACE, ["isolation_forest", "ocsvm", "autoencoder"])
    systems = {r["system"] for r in rows}
    assert "quantum_cqzdr" in systems and "classical_isolation_forest" in systems
    assert "classical_ocsvm" not in systems                      # CIC has no OC-SVM
    assert any("ocsvm" in n for n in notes)
    for r in rows:                                                # coverage AND recall on every row
        assert "coverage" in r and "zeroday_recall" in r

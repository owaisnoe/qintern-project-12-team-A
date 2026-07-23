"""Week 4 · Day 21 — tests for the integration freeze (frozen thresholds + manifest + verify)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import freeze_integration as fi                                   # noqa: E402
from conformal_calibrate import calibrate_dataset, IFACE          # noqa: E402

IFACE_OK = (BASE / "week2" / "interface" / "dummy_scores" / "CICIoT2023" / "calibration_scores.parquet").exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 dummy interface not present")


@needs_iface
def test_frozen_threshold_equals_day15_calibration():
    """The frozen q must equal the Day-15 calibrate_dataset q at the same α — no independent re-derivation."""
    t = fi.compute_frozen_thresholds(["CICIoT2023"], 0.05, str(IFACE), "dummy")["CICIoT2023"]
    r = calibrate_dataset("CICIoT2023", 0.05, str(IFACE))
    assert t["threshold_q"] == r["threshold_q"] == pytest.approx(0.300551, abs=1e-6)
    assert t["k"] == r["k"] and t["n_cal"] == r["calibration_n"]
    assert t["coverage_verdict"] == "PASS"


@needs_iface
def test_freeze_writes_package_and_verifies():
    """A real freeze (deterministic, idempotent) must round-trip through --verify with 0 mismatch."""
    m = fi.freeze(["CICIoT2023", "BoT-IoT", "UNSW-NB15"], 0.05, str(IFACE), "dummy")
    for name in ("frozen_thresholds.json", "interface_contract.json", "INTEGRATION_PACKAGE.md", "VERSION"):
        assert (fi.INTEG / name).exists()
    assert m["n_files"] == len(m["files"]) and m["n_files"] > 0
    assert fi.verify() == 0                                        # 0 mismatch on an untouched freeze


@needs_iface
def test_verify_detects_tamper(tmp_path, monkeypatch):
    """Corrupt a stored hash in a throwaway manifest copy; verify() must report CHANGED (no real file touched)."""
    fi.freeze(["CICIoT2023"], 0.05, str(IFACE), "dummy")           # ensure a real manifest exists
    manifest = json.loads(fi.MANIFEST.read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "0" * 64                      # corrupt one pin
    tampered = tmp_path / "integration_manifest_v1.0.json"
    tampered.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(fi, "MANIFEST", tampered)
    assert fi.verify() == 1                                        # CHANGED detected


@needs_iface
def test_interface_contract_flags_nonsquared_fidelity(tmp_path, monkeypatch):
    monkeypatch.setattr(fi, "INTEG", tmp_path)
    fi.write_interface_contract()
    c = json.loads((tmp_path / "interface_contract.json").read_text(encoding="utf-8"))
    assert "NON-SQUARED" in c["fidelity_convention"]
    assert c["nonconformity"].startswith("1 - max_fidelity") or "1 - max" in c["nonconformity"]
    assert c["primary_alpha"] == 0.05


@needs_iface
def test_manifest_pins_the_four_core_modules(tmp_path, monkeypatch):
    monkeypatch.setattr(fi, "INTEG", tmp_path)
    monkeypatch.setattr(fi, "MANIFEST", tmp_path / f"integration_manifest_v{fi.VERSION}.json")
    m = fi.freeze(["CICIoT2023"], 0.05, str(IFACE), "dummy")
    pinned = {r["path"] for r in m["files"]}
    for mod in fi.CORE_MODULES:
        assert mod in pinned, f"core module not pinned: {mod}"
    assert "week4/INTEGRATION/frozen_thresholds.json" in pinned

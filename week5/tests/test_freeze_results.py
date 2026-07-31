"""Week 5 · Day 26 — tests for the results freeze (LF gate, round-trip verify, tamper detection)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import freeze_results as fr                         # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
IFACE_OK = (IFACE / "CICIoT2023" / "test_scores.parquet").exists()
BASE_OK = (BASE / "week2" / "baselines" / "CICIoT2023" / "results.json").exists()
needs_data = pytest.mark.skipif(not (IFACE_OK and BASE_OK),
                                reason="Day-14 interface / Day-12 baselines not present")


def _redirect_mains_to_tmp(monkeypatch, tmp_path):
    """Point the three result mains' output dirs at a tmp dir so freeze()'s `run_all` does NOT overwrite
    the committed full-trio artefacts with the CIC-only test run. `freeze` still hashes the REAL pinned
    files (they exist in the checkout) and captures scalars from the in-memory return values, so the
    freeze/verify/reproduce logic is exercised unchanged — only the destructive side effect is removed."""
    gen, reports, fig = tmp_path / "_generated", tmp_path / "reports", tmp_path / "figures"
    for d in (gen, reports, fig):
        d.mkdir(parents=True, exist_ok=True)
    for mod, attr, dest in ((fr.dis, "GEN", gen), (fr.dis, "REPORTS", reports),
                            (fr.ta, "GEN", gen), (fr.ta, "REPORTS", reports),
                            (fr.fig2, "GEN", gen), (fr.fig2, "REPORTS", reports), (fr.fig2, "FIG", fig)):
        monkeypatch.setattr(mod, attr, dest)


def test_assert_lf_rejects_crlf(tmp_path):
    crlf = tmp_path / "bad.md"
    crlf.write_bytes(b"line one\r\nline two\r\n")
    with pytest.raises(SystemExit):
        fr._assert_lf(crlf)


def test_assert_lf_passes_lf_and_ignores_binaries(tmp_path):
    lf = tmp_path / "good.md"
    lf.write_bytes(b"line one\nline two\n")
    fr._assert_lf(lf)                                 # no raise
    binary = tmp_path / "img.png"
    binary.write_bytes(b"\x89PNG\r\n\x1a\n stuff")     # CRLF inside a binary must be ignored
    fr._assert_lf(binary)                             # no raise (suffix not in TEXT_SUFFIXES)


def test_text_suffixes_cover_the_pinned_text_files():
    for rel in fr.PINNED:
        suf = Path(rel).suffix.lower()
        assert (suf in fr.TEXT_SUFFIXES) or suf == ".png"   # every pinned file is text or the figure PNG


@needs_data
def test_freeze_roundtrip_verify_ok_then_tamper_fails(tmp_path, monkeypatch):
    results_dir = tmp_path / "RESULTS_FROZEN"
    manifest = results_dir / "results_manifest_v1.0.json"
    scalars = results_dir / "results_frozen_scalars.json"
    monkeypatch.setattr(fr, "RESULTS", results_dir)
    monkeypatch.setattr(fr, "MANIFEST", manifest)
    monkeypatch.setattr(fr, "SCALARS", scalars)
    _redirect_mains_to_tmp(monkeypatch, tmp_path)      # don't overwrite the committed full-trio artefacts

    fr.freeze(["CICIoT2023"], 0.05, IFACE, "dummy")   # runs the 3 mains, pins real artefacts into tmp manifest
    assert manifest.exists() and scalars.exists()
    assert fr.verify() == 0                            # fresh freeze re-hashes clean

    # tamper the tmp manifest's stored hash for one file -> verify must report CHANGED (returns 1).
    # (only the tmp manifest is edited; the real pinned artefacts are untouched.)
    doc = json.loads(manifest.read_text())
    doc["files"][0]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    assert fr.verify() == 1


@needs_data
def test_reproduce_check_passes_after_freeze(tmp_path, monkeypatch):
    results_dir = tmp_path / "RESULTS_FROZEN"
    monkeypatch.setattr(fr, "RESULTS", results_dir)
    monkeypatch.setattr(fr, "MANIFEST", results_dir / "results_manifest_v1.0.json")
    monkeypatch.setattr(fr, "SCALARS", results_dir / "results_frozen_scalars.json")
    _redirect_mains_to_tmp(monkeypatch, tmp_path)      # don't overwrite the committed full-trio artefacts
    fr.freeze(["CICIoT2023"], 0.05, IFACE, "dummy")
    # deterministic mains (seed 42) -> every frozen scalar reproduces to 1e-9
    assert fr.reproduce_check(["CICIoT2023"], 0.05, IFACE, "dummy") == 0

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


@pytest.fixture
def _sandbox_mains(tmp_path, monkeypatch):
    """Redirect the three result mains' output dirs to tmp so a test that RUNS them (reproduce) never
    overwrites the committed full-trio artefacts. The freeze round-trip no longer needs this — it uses
    freeze(regenerate=False), so freeze() does not run the mains at all."""
    gen, rep, fig = tmp_path / "_generated", tmp_path / "reports", tmp_path / "figures"
    for d in (gen, rep, fig):
        d.mkdir(parents=True, exist_ok=True)
    for m in (fr.dis, fr.ta, fr.fig2):
        monkeypatch.setattr(m, "GEN", gen)
        monkeypatch.setattr(m, "REPORTS", rep)
    monkeypatch.setattr(fr.fig2, "FIG", fig)


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

    # regenerate=False pins the on-disk full-trio artefacts WITHOUT re-running the mains, so the test
    # cannot clobber the committed outputs; manifest/scalars go to tmp.
    fr.freeze(fr.TRIO, 0.05, IFACE, "dummy", regenerate=False)
    assert manifest.exists() and scalars.exists()
    assert fr.verify() == 0                            # pinned real artefacts re-hash clean

    # tamper the tmp manifest's stored hash for one file -> verify must report CHANGED (returns 1).
    # (only the tmp manifest is edited; the real pinned artefacts are untouched.)
    doc = json.loads(manifest.read_text())
    doc["files"][0]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    assert fr.verify() == 1


@needs_data
def test_reproduce_check_passes_after_freeze(tmp_path, monkeypatch, _sandbox_mains):
    results_dir = tmp_path / "RESULTS_FROZEN"
    monkeypatch.setattr(fr, "RESULTS", results_dir)
    monkeypatch.setattr(fr, "MANIFEST", results_dir / "results_manifest_v1.0.json")
    monkeypatch.setattr(fr, "SCALARS", results_dir / "results_frozen_scalars.json")
    # pin the on-disk full-trio scalars (regenerate=False, no clobber), then reproduce_check re-runs the
    # mains — sandboxed to tmp by _sandbox_mains — and must match every frozen scalar to 1e-9.
    fr.freeze(fr.TRIO, 0.05, IFACE, "dummy", regenerate=False)
    assert fr.reproduce_check(fr.TRIO, 0.05, IFACE, "dummy") == 0


@needs_data
def test_regenerate_false_never_runs_the_mains(tmp_path, monkeypatch):
    """The CIC-only clobber guard: freeze(regenerate=False) must NOT invoke the mains even when handed a
    single dataset, so it can never overwrite the committed full-trio reports/figure on disk."""
    monkeypatch.setattr(fr, "RESULTS", tmp_path / "RESULTS_FROZEN")
    monkeypatch.setattr(fr, "MANIFEST", tmp_path / "m.json")
    monkeypatch.setattr(fr, "SCALARS", tmp_path / "s.json")

    def _boom(*a, **k):
        raise AssertionError("regenerate=False must not run the mains")
    monkeypatch.setattr(fr, "run_all", _boom)

    fr.freeze(["CICIoT2023"], 0.05, IFACE, "dummy", regenerate=False)   # no raise => mains not run
    # and it pinned the real committed full-trio figure (3 datasets), not a CIC-only run
    fig = json.loads((BASE / "week5" / "reports" / "_generated" / "w5_03_figure2.json").read_text())
    assert [p["dataset"] for p in fig["points"]] == ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]

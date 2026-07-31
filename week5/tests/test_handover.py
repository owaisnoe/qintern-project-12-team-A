"""Week 5 · Day 30 — tests for the Team-B hand-off package (audit gate, round-trip verify, tamper)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week5" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))

import handover_teamB as ho                        # noqa: E402

ASSETS_OK = all((BASE / rel).exists()
                for _, rels in ho.ASSETS.values() for rel in rels)
AUDIT_OK = (BASE / "week5" / "reports" / "_generated" / "w5_07_cross_audit.json").exists()
needs_assets = pytest.mark.skipif(not (ASSETS_OK and AUDIT_OK),
                                  reason="hand-off assets / audit not present")


def test_asset_list_is_repo_relative_and_unique():
    rels = [rel for _, rels in ho.ASSETS.values() for rel in rels]
    assert len(rels) == len(set(rels))                              # no double-pinned file
    for rel in rels:
        assert not Path(rel).is_absolute()


def test_refuses_to_cut_on_red_audit(monkeypatch, tmp_path):
    monkeypatch.setattr(ho, "HAND", tmp_path / "HANDOVER")
    monkeypatch.setattr(ho, "audit_is_green", lambda: (False, "2 FAIL"))
    with pytest.raises(SystemExit):
        ho.freeze("dummy")


@needs_assets
def test_freeze_roundtrip_verify_then_tamper(monkeypatch, tmp_path):
    hand = tmp_path / "HANDOVER"
    monkeypatch.setattr(ho, "HAND", hand)
    manifest = ho.freeze("dummy")
    assert manifest["n_files"] == len([r for _, rels in ho.ASSETS.values() for r in rels])
    assert (hand / ho.MANIFEST_NAME).exists() and (hand / "HANDOVER.md").exists()
    assert ho.verify() == 0                                        # fresh cut re-hashes clean

    doc = json.loads((hand / ho.MANIFEST_NAME).read_text(encoding="utf-8"))
    doc["files"][0]["sha256"] = "0" * 64
    (hand / ho.MANIFEST_NAME).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    assert ho.verify() == 1                                        # tamper must be caught


@needs_assets
def test_manifest_records_audit_and_status(monkeypatch, tmp_path):
    monkeypatch.setattr(ho, "HAND", tmp_path / "HANDOVER")
    manifest = ho.freeze("dummy")
    assert "PASS" in manifest["audit"]
    for r in manifest["files"]:
        assert r["deliverable"] and r["status"]                    # every pinned file carries provenance

"""Week 5 · Day 32 — tests for the final sign-off (gate logic, scalar coverage, tree neutrality).

The expensive gate (G1, which re-runs the five mains) is exercised once behind `needs_data`; the rest of
the suite tests the comparison and gate logic on synthetic inputs so it stays fast and hermetic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
for w in ("week3", "week4", "week5"):
    sys.path.insert(0, str(BASE / w / "scripts"))

import signoff as so                                   # noqa: E402
import freeze_results as fr                            # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
IFACE_OK = (IFACE / "CICIoT2023" / "test_scores.parquet").exists()
BASE_OK = (BASE / "week2" / "baselines" / "CICIoT2023" / "results.json").exists()
COMMITTED_OK = all(p.exists() for p in so.COMMITTED.values())
needs_data = pytest.mark.skipif(not (IFACE_OK and BASE_OK and COMMITTED_OK),
                                reason="Day-14 interface / Day-12 baselines / committed artifacts absent")


# ---------------------------------------------------------------- comparison logic

def test_compare_floats_within_tolerance():
    assert so._compare("k", 1.0, 1.0 + 1e-12, 1e-9)[0] == "PASS"
    assert so._compare("k", 1.0, 1.0 + 1e-6, 1e-9)[0] == "FAIL"


def test_compare_is_bit_exact_at_zero_tolerance():
    """--tol 0 must catch the ULP drift the Day-31 appendix documents."""
    a = 7.26273412199973e-07
    b = 7.26273412199952e-07
    assert so._compare("p", a, b, 1e-9)[0] == "PASS"      # far below any reported digit
    assert so._compare("p", a, b, 0.0)[0] == "FAIL"       # but not bit-equal
    assert so._compare("p", a, b, 0.0)[1] > 0


def test_compare_bools_and_strings_are_exact():
    assert so._compare("v", True, True, 1e-9)[0] == "PASS"
    assert so._compare("v", True, False, 1e9)[0] == "FAIL"     # a huge tol must not rescue a bool
    assert so._compare("v", "quantum ahead", "quantum behind", 1e9)[0] == "FAIL"


def test_compare_none_is_handled():
    assert so._compare("v", None, None, 1e-9)[0] == "PASS"
    assert so._compare("v", None, 0.0, 1e-9)[0] == "FAIL"


# ---------------------------------------------------------------- gate logic

def test_gate_neutral_passes_when_hashes_match():
    h = {"a.json": "abc", "b.png": "def"}
    checks = so.gate_neutral(h, dict(h))
    assert all(c["verdict"] == "PASS" for c in checks)


def test_gate_neutral_flags_a_changed_pinned_file():
    before = {"a.json": "abc", "b.png": "def"}
    after = {"a.json": "abc", "b.png": "CHANGED"}
    checks = so.gate_neutral(before, after)
    assert any(c["verdict"] == "FAIL" for c in checks)
    assert any("b.png" in c["check"] for c in checks if c["verdict"] == "FAIL")


def test_gate_neutral_flags_a_vanished_pinned_file():
    checks = so.gate_neutral({"a.json": "abc"}, {})
    assert any(c["verdict"] == "FAIL" for c in checks)


def test_gate_complete_flags_a_missing_deliverable(monkeypatch):
    monkeypatch.setitem(so.DELIVERABLES, "synthetic", ["week5/does_not_exist.md"])
    checks = so.gate_complete()
    bad = [c for c in checks if c["scope"] == "synthetic"]
    assert bad and bad[0]["verdict"] == "FAIL" and bad[0]["observed"] == "MISSING"


# ---------------------------------------------------------------- scalar extraction

@needs_data
def test_extract_covers_every_research_question():
    docs = {n: json.loads(p.read_text()) for n, p in so.COMMITTED.items()}
    s = so.extract_scalars(docs)
    scopes = {k.split("/")[0] for k in s}
    # RQ2 and RQ5 are the two the Day-32 task names explicitly and the two the Day-26 freeze omits.
    assert {"RQ1", "RQ2", "RQ3", "RQ5", "FIG2"} <= scopes
    assert sum(k.startswith("RQ2/") for k in s) > 50
    assert sum(k.startswith("RQ5/") for k in s) > 40


@needs_data
def test_extract_includes_the_table_b_headline_cells():
    docs = {n: json.loads(p.read_text()) for n, p in so.COMMITTED.items()}
    s = so.extract_scalars(docs)
    for ds in ("CICIoT2023", "BoT-IoT", "UNSW-NB15"):
        for f in ("threshold_q", "achieved_alpha", "qsnet_recall", "fzr_5seed/mean", "recall_5seed/mean"):
            assert f"RQ2/{ds}/{f}" in s, f"Table B cell missing from the sign-off: RQ2/{ds}/{f}"
        assert s[f"RQ2/{ds}/guarantee_held"] is True


@needs_data
def test_extract_includes_every_rq5_verdict():
    docs = {n: json.loads(p.read_text()) for n, p in so.COMMITTED.items()}
    s = so.extract_scalars(docs)
    n_verdicts = sum(k.endswith("/verdict") for k in s)
    assert n_verdicts == len(docs["abl"]["rq5_verdicts"])


# ---------------------------------------------------------------- the sandbox contract

@needs_data
def test_sandbox_restores_the_real_output_dirs():
    """freeze_results.sandboxed_outputs must leave the module globals exactly as it found them."""
    import disentanglement as dis, table_a as ta, figure2_coverage as fig2
    before = [(m, a, getattr(m, a)) for m, a in
              ((dis, "GEN"), (dis, "REPORTS"), (ta, "GEN"), (ta, "REPORTS"),
               (fig2, "GEN"), (fig2, "REPORTS"), (fig2, "FIG"))]
    with fr.sandboxed_outputs() as root:
        assert root.exists()
        assert fig2.GEN != before[4][2]                 # redirected inside the block
    for mod, attr, orig in before:
        assert getattr(mod, attr) == orig               # restored after it


@needs_data
def test_sandbox_directory_is_removed_on_exit():
    with fr.sandboxed_outputs() as root:
        pass
    assert not root.exists()


# ---------------------------------------------------------------- end-to-end (one dataset, fast path)

def test_provenance_marks_table_b_canonical_cells_as_passthrough():
    """Table B's canonical cells are read from the Day-21/22/19 arms, not recomputed (Day-28 report).
    Counting them as re-derivations would make the sign-off measure its own plumbing."""
    for f in ("threshold_q", "achieved_alpha", "qsnet_recall", "best_classical_recall", "n_cal"):
        assert so.provenance(f"RQ2/CICIoT2023/{f}") == "passthrough"


def test_provenance_marks_recomputed_cells_correctly():
    # 5-seed CIs and per-seed points ARE derived from the raw scores on each run.
    assert so.provenance("RQ2/CICIoT2023/fzr_5seed/mean") == "recomputed"
    assert so.provenance("RQ2/CICIoT2023/per_seed/42/fzr") == "recomputed"
    assert so.provenance("RQ5/CICIoT2023/conformal/false_zeroday_rate") == "recomputed"
    assert so.provenance("RQ3/CICIoT2023/separation/auroc") == "recomputed"
    assert so.provenance("FIG2/CICIoT2023/mean_fzr") == "recomputed"


def test_provenance_splits_table_a_arms():
    """The classical arm is read from the Day-12 results.json; the quantum arm is recomputed."""
    assert so.provenance("RQ1/CICIoT2023/xgboost/accuracy") == "passthrough"
    assert so.provenance("RQ1/CICIoT2023/qsnet/accuracy") == "recomputed"


def test_provenance_marks_rq5_verdicts_as_passthrough():
    """RQ5 verdicts are re-emitted from the Day-25 significance JSON by `load_rq5`."""
    assert so.provenance("RQ5/BoT-IoT/Autoencoder/verdict") == "passthrough"
    assert so.provenance("RQ5/BoT-IoT/Autoencoder/cohens_h") == "passthrough"


def test_rel_never_leaks_an_absolute_checkout_path():
    """Regression: the emitted doc stored `str(scores_root)` verbatim, which the Day-30 audit's
    absolute-path leak scan correctly failed on."""
    assert so._rel(BASE / "week2" / "interface") == "week2/interface"
    assert not so._rel(BASE / "week2" / "interface").startswith("/")


@needs_data
def test_signoff_doc_has_no_absolute_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(so, "GEN", tmp_path / "_generated")
    monkeypatch.setattr(so, "REPORTS", tmp_path / "reports")
    so.main(["--datasets", "CICIoT2023"])
    for name in ("_generated/w5_11_signoff.json", "_generated/w5_11_signoff.csv",
                 "reports/w5_11_signoff.md"):
        text = (tmp_path / name).read_text()
        assert str(BASE) not in text, f"absolute checkout path leaked into {name}"


@needs_data
def test_signoff_end_to_end_writes_report_and_leaves_pinned_files_untouched(tmp_path, monkeypatch):
    """The full run on one dataset: G1 must not touch any pinned artifact (that is G4's whole point)."""
    monkeypatch.setattr(so, "GEN", tmp_path / "_generated")
    monkeypatch.setattr(so, "REPORTS", tmp_path / "reports")

    before = so.pinned_hashes()
    assert before, "no pinned artifacts found — the manifests should cover the frozen surface"

    doc = so.main(["--datasets", "CICIoT2023"])

    after = so.pinned_hashes()
    assert after == before, "the sign-off run modified a pinned artifact"

    assert (tmp_path / "reports" / "w5_11_signoff.md").exists()
    assert (tmp_path / "_generated" / "w5_11_signoff.csv").exists()
    assert doc["gates"]["G4 NEUTRAL"]["fail"] == 0
    # G1 must cover the RQ2 / RQ5 scalars, not just RQ1/RQ3/Figure 2.
    scopes = {c["scope"] for c in doc["checks"] if c["gate"] == "G1 REPRODUCE"}
    assert {"RQ2", "RQ5"} <= scopes
    # G5 must run the independent re-derivation that covers G1's pass-through rows.
    assert doc["gates"]["G5 AUDIT"]["fail"] == 0
    # and every G1 row must carry a provenance tag, so nothing is silently counted as re-derived.
    g1 = [c for c in doc["checks"] if c["gate"] == "G1 REPRODUCE"]
    assert all(c["provenance"] in ("recomputed", "passthrough") for c in g1)
    assert any(c["provenance"] == "passthrough" for c in g1), "provenance split collapsed"

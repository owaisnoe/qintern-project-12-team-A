"""Week 4 · Day 25 — tests for significance testing QS-Net vs baselines + RQ5 honesty."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week2" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))

import significance as sg                              # noqa: E402
from stats_protocol import mcnemar_exact               # noqa: E402

TRIO = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
INPUTS_OK = all((sg.GEN / f"w4_03_decisions_{d}.csv").exists() for d in TRIO) and \
            all((sg.BASELINES / d / "predictions.csv").exists() for d in TRIO)
needs_inputs = pytest.mark.skipif(
    not INPUTS_OK, reason="Day-22 decisions or Day-12 predictions absent (run those days first)")


# ------------------------------------------------------------------ effect sizes / detection floor

def test_cohens_h_is_zero_for_equal_proportions_and_signed():
    assert sg.cohens_h(0.5, 0.5) == pytest.approx(0.0, abs=1e-12)
    assert sg.cohens_h(0.8, 0.2) > 0 and sg.cohens_h(0.2, 0.8) < 0
    assert sg.cohens_h(0.8, 0.2) == pytest.approx(-sg.cohens_h(0.2, 0.8), abs=1e-12)
    # closed form: 2*asin(sqrt(p1)) - 2*asin(sqrt(p2))
    assert sg.cohens_h(0.65, 0.35) == pytest.approx(
        2 * np.arcsin(np.sqrt(0.65)) - 2 * np.arcsin(np.sqrt(0.35)), abs=1e-12)
    assert sg.cohens_h(0.65, 0.35) == pytest.approx(0.6094, abs=1e-3)   # ~ Cohen's "medium"


def test_detection_floor_is_a_property_of_n_alone():
    d_sig, d_pow = sg.min_detectable_dz(5, 0.05, 0.80)
    assert d_sig == pytest.approx(1.242, abs=1e-2)      # t_crit(df=4)/sqrt(5)
    assert d_pow > d_sig                                 # 80% power costs more than bare significance
    # more seeds -> a smaller effect becomes detectable
    assert sg.min_detectable_dz(20, 0.05, 0.80)[1] < d_pow


# ------------------------------------------------------------------ the paired bootstrap

def test_bootstrap_recovers_the_paired_mean_and_brackets_it():
    rng = np.random.default_rng(0)
    d = rng.choice([-1, 0, 1], size=4000, p=[0.1, 0.6, 0.3])
    bs = sg.bootstrap_recall_diff(d, n_boot=2000, seed=42)
    assert bs["mean"] == pytest.approx(d.mean(), abs=1e-12)
    assert bs["ci_low"] < bs["mean"] < bs["ci_high"]
    assert bs["p_gt_0"] > 0.99                            # a genuine +0.2 shift
    # an all-zero difference vector is a point mass at 0
    z = sg.bootstrap_recall_diff(np.zeros(500, dtype=int), n_boot=500, seed=42)
    assert z["mean"] == 0.0 and z["ci_low"] == 0.0 and z["ci_high"] == 0.0


def test_bootstrap_is_deterministic_under_seed():
    d = np.random.default_rng(3).choice([-1, 0, 1], size=1000)
    a = sg.bootstrap_recall_diff(d, n_boot=500, seed=42)
    b = sg.bootstrap_recall_diff(d, n_boot=500, seed=42)
    assert a == b


# ------------------------------------------------------------------ McNemar on real paired decisions

@needs_inputs
def test_decisions_and_predictions_are_row_aligned():
    """The whole paired design rests on this; load_paired_decisions asserts it, so it must hold."""
    for ds in TRIO:
        flags, truth, n = sg.load_paired_decisions(ds)
        assert sg.QUANTUM in flags and len(flags) >= 3       # quantum + at least two heads
        assert all(v.shape == (n,) for v in flags.values())
        assert truth.shape == (n,) and 0 < truth.sum() < n   # both known and zero-day rows present


@needs_inputs
def test_zeroday_mcnemar_counts_are_the_recall_discordances():
    """On zero-day rows 'correct' == 'flagged', so n10/n01 must be exactly the catch/miss split."""
    ds = "UNSW-NB15"
    flags, truth, _ = sg.load_paired_decisions(ds)
    rows = sg.mcnemar_rows(ds, zeroday_only=True)
    q = flags[sg.QUANTUM][truth]
    for r in rows:
        b = flags[r["baseline"]][truth]
        assert r["n10_qsnet_only"] == int(np.sum(q & ~b))
        assert r["n01_baseline_only"] == int(np.sum(~q & b))
        assert r["rate_qsnet"] == pytest.approx(q.mean(), abs=1e-6)
        assert r["rate_diff"] == pytest.approx(q.mean() - b.mean(), abs=1e-6)
        # the reported p is the Day-17 exact test on those counts, not a re-derivation
        assert r["p_raw"] == mcnemar_exact(r["n01_baseline_only"], r["n10_qsnet_only"])["p"]


@needs_inputs
def test_zeroday_mcnemar_agrees_with_the_day24_recall_gap():
    """Day 25 must not disagree with the Table B column it is testing."""
    tb_path = sg.GEN / "w4_05_rq2_results.json"
    if not tb_path.exists():
        pytest.skip("Day-24 RQ2 results absent")
    tb = {r["dataset"]: r for r in json.loads(tb_path.read_text())["table_b"]}
    rows = [r for ds in TRIO for r in sg.mcnemar_rows(ds, zeroday_only=True)]
    for ds, t in tb.items():
        qs = {r["rate_qsnet"] for r in rows if r["dataset"] == ds}
        assert len(qs) == 1                                   # one QS-Net recall per dataset
        assert qs.pop() == pytest.approx(t["qsnet_recall"], abs=1e-4)


# ------------------------------------------------------------------ verdicts

def _verdict(delta, lo, hi, sig):
    mc = [{"dataset": "D", "baseline": "B", "rate_diff": delta, "cohens_h": 0.0,
           "significant": sig, "p_holm": 0.01 if sig else 0.9,
           "n01_baseline_only": 1, "n10_qsnet_only": 2}]
    bt = [{"dataset": "D", "baseline": "B", "delta_recall": delta,
           "ci95_low": lo, "ci95_high": hi, "excludes_zero": lo > 0 or hi < 0}]
    return sg.rq5_verdicts(mc, bt)[0]


def test_verdict_needs_test_and_interval_to_agree():
    assert _verdict(+0.30, 0.25, 0.35, True)["quantum_helps"] is True
    assert _verdict(-0.30, -0.35, -0.25, True)["quantum_helps"] is False
    # a tight interval around zero is EQUIVALENCE, a positive finding — not "unresolved"
    eq = _verdict(0.0002, -0.0004, 0.0009, False)
    assert eq["quantum_helps"] == "equivalent" and "equivalent" in eq["verdict"]
    # significant test but a wide interval straddling zero: the data do not decide
    un = _verdict(+0.30, -0.10, 0.70, True)
    assert un["quantum_helps"] is None and "unresolved" in un["verdict"]


def test_equivalence_margin_is_respected():
    wide = _verdict(0.0, -0.049, 0.049, False)                 # inside the default 0.05 margin
    assert wide["quantum_helps"] == "equivalent"
    outside = _verdict(0.0, -0.20, 0.20, False)                # too wide to claim equivalence
    assert outside["quantum_helps"] is None


# ------------------------------------------------------------------ the rejected design is recorded

@needs_inputs
def test_calibration_draw_diagnostic_documents_its_own_degeneracy():
    """The rejected design must be reported with numbers, not just asserted to be bad."""
    rows = sg.calibration_draw_diagnostic("BoT-IoT", str(sg.IFACE), 0.05, 5)
    assert rows
    for r in rows:
        assert r["std_recall_qsnet"] < 0.01                    # the draw barely moves recall
        # which is exactly why the effect size it would report is absurd
        assert abs(r["inflated_d_z"]) > 10


# ------------------------------------------------------------------ CLI

@needs_inputs
def test_cli_writes_every_declared_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(sg, "GEN_OUT", tmp_path / "_generated", raising=False)
    monkeypatch.setattr(sg, "REPORTS", tmp_path)
    monkeypatch.setattr(sg, "FIG", tmp_path / "figures")
    real_gen = sg.GEN
    monkeypatch.setattr(sg, "GEN", tmp_path / "_generated")
    # inputs are read from the real _generated dir; copy the decisions the module needs
    (tmp_path / "_generated").mkdir(parents=True, exist_ok=True)
    for ds in TRIO:
        (tmp_path / "_generated" / f"w4_03_decisions_{ds}.csv").write_bytes(
            (real_gen / f"w4_03_decisions_{ds}.csv").read_bytes())

    out = sg.main(["--no-figure", "--no-diagnostic", "--n-boot", "200"])
    assert out["day"] == 25
    assert len(out["mcnemar_all"]["rows"]) == len(out["mcnemar_zeroday"]["rows"]) == 8
    assert out["quantum_seed_arm"]["available"] is False       # the reported gap, not hidden
    for f in ("_generated/w4_06_significance.json", "_generated/w4_06_significance.csv",
              "_generated/w4_06_rq5_honesty.md", "w4_06_significance.md"):
        assert (tmp_path / f).exists(), f
    rq5 = (tmp_path / "_generated" / "w4_06_rq5_honesty.md").read_text()
    assert "do NOT establish" in rq5 and "placeholder" in rq5
    report = (tmp_path / "w4_06_significance.md").read_text()
    assert "Day 25" in report and "RQ5" in report
    # the three families must each be declared with their own Holm count
    saved = json.loads((tmp_path / "_generated" / "w4_06_significance.json").read_text())
    assert set(saved["families"]) == {"mcnemar_all", "mcnemar_zeroday", "paired_t_seeds"}
    assert saved["mcnemar_all"]["holm"]["m"] == 8

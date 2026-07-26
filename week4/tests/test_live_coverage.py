"""Week 4 · Day 23 — tests for live coverage verification + the exchangeability audit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))

import freeze_integration as fzi                     # noqa: E402
import live_coverage as lc                           # noqa: E402
from conformal_calibrate import conformal_threshold   # noqa: E402

IFACE = BASE / "week2" / "interface" / "dummy_scores"
ALPHA = 0.05

IFACE_OK = (IFACE / "BoT-IoT" / "calibration_scores.parquet").exists()
FROZEN_OK = lc.frozen_package_path().exists() and fzi.MANIFEST.exists()
needs_iface = pytest.mark.skipif(not IFACE_OK, reason="Day-14 score interface not present")
needs_frozen = pytest.mark.skipif(not FROZEN_OK,
                                  reason="Day-21 freeze not present (run freeze_integration.py)")


# ------------------------------------------------------------------ the conformal p-value / flag identity

def test_conformal_pvalues_are_the_deployed_flag_rule():
    """p_i <= alpha  <=>  s_i > q = s_(k). The audit must test the object the pipeline flags on."""
    rng = np.random.default_rng(0)
    for n, m in ((199, 500), (1000, 2000)):
        s_cal, s_test = rng.random(n), rng.random(m)
        q, k, _ = conformal_threshold(s_cal, ALPHA)
        p = lc.conformal_pvalues(s_cal, s_test)
        assert np.array_equal(p <= ALPHA, s_test > q)
        assert k == int(np.ceil((1 - ALPHA) * (n + 1)))
        # super-uniform, and never zero (the +1 in the numerator)
        assert p.min() >= 1.0 / (n + 1) - 1e-12 and p.max() <= 1.0


def test_conformal_pvalues_are_uniform_on_exchangeable_data():
    rng = np.random.default_rng(7)
    p = lc.conformal_pvalues(rng.normal(size=5000), rng.normal(size=5000))
    assert abs(p.mean() - 0.5) < 0.02
    assert abs(np.mean(p <= ALPHA) - ALPHA) < 0.01


# ------------------------------------------------------------------ coverage at a given threshold

def test_coverage_at_matches_the_exact_band_and_both_verdicts():
    rng = np.random.default_rng(1)
    n = 2000
    s_cal = rng.random(n)
    q, k, _ = conformal_threshold(s_cal, ALPHA)
    r = lc.coverage_at(q, rng.random(4000), n, k, alpha=ALPHA)
    assert r["false_flags"] == int(round(r["fzr_observed"] * r["m_test"]))
    assert r["band_lo_rate"] <= r["fzr_expected"] <= r["band_hi_rate"]
    assert r["finite_sample_ok"] and r["verdict"] == "PASS"
    # a threshold far below q flags almost everything: the band verdict must FAIL, not shrug
    bad = lc.coverage_at(0.05, rng.random(4000), n, k, alpha=ALPHA)
    assert not bad["finite_sample_ok"] and not bad["fzr_le_alpha"] and bad["verdict"] == "FAIL"


# ------------------------------------------------------------------ audit power + remediation

def test_audit_catches_a_shift_and_a_class_skew():
    rng = np.random.default_rng(3)
    n = 4000
    s_cal, s_test = rng.random(n), rng.random(n)
    y_cal = np.array(["A"] * (n // 2) + ["B"] * (n // 2), dtype=object)
    y_test = y_cal.copy()

    clean = lc._mini_audit(s_cal, y_cal, s_test, y_test, ALPHA)
    assert clean["n_flagged_tests"] == 0

    for kind, mag in (("cal_trim", 0.05), ("test_shift", 0.05), ("class_mix", 0.8)):
        sc, yc, st, yt, description = lc._inject(kind, s_cal, y_cal, s_test, y_test, mag)
        assert description
        assert lc._mini_audit(sc, yc, st, yt, ALPHA)["n_flagged_tests"] > 0, f"{kind} not detected"


def test_fix_splits_restores_exchangeability_and_preserves_the_pool():
    rng = np.random.default_rng(4)
    n, m = 3000, 3000
    s_cal, s_test = rng.random(n), rng.random(m) + 0.30            # a blatant shift
    y_cal = np.array(["A"] * n, dtype=object)
    y_test = np.array(["A"] * m, dtype=object)
    assert lc._mini_audit(s_cal, y_cal, s_test, y_test, ALPHA)["n_flagged_tests"] > 0

    sc, yc, st, yt = lc.fix_splits(s_cal, y_cal, s_test, y_test)
    assert sc.size == n and st.size == m                            # sizes preserved
    assert np.allclose(np.sort(np.concatenate([sc, st])),
                       np.sort(np.concatenate([s_cal, s_test])))    # pool preserved, nothing invented
    assert lc._mini_audit(sc, yc, st, yt, ALPHA)["n_flagged_tests"] == 0
    assert lc.fix_splits(s_cal, y_cal, s_test, y_test, seed=7)[0][0] != sc[0]   # seed actually varies


def test_mini_audit_holm_controls_false_alarms_on_exchangeable_resplits():
    """The remediation check must not read as failed on chance: >= 90% of exchangeable re-splits clean."""
    rng = np.random.default_rng(11)
    pool_s, pool_y = rng.random(6000), np.array(["A", "B"] * 3000, dtype=object)
    clean = 0
    for seed in range(40):
        sc, yc, st, yt = lc.fix_splits(pool_s[:3000], pool_y[:3000], pool_s[3000:], pool_y[3000:],
                                       seed=seed)
        clean += lc._mini_audit(sc, yc, st, yt, ALPHA)["n_flagged_tests"] == 0
    assert clean >= 36, f"only {clean}/40 exchangeable re-splits came back clean"


# ------------------------------------------------------------------ live run against the frozen contract

@needs_frozen
def test_frozen_contract_rehashes_the_day21_whitelist():
    st = lc.frozen_contract_status()
    assert st["contract_ok"], f"pinned files drifted: {st['changed']} / missing {st['missing']}"
    assert st["n_pinned"] > 0
    # the Day-21 manifest is a whitelist, so post-freeze work (this module) is never registered
    # as drift — only a pinned file going missing or changing is a break
    pinned = {r["path"] for r in json.loads(fzi.MANIFEST.read_text())["files"]}
    assert "week4/scripts/live_coverage.py" not in pinned
    assert "week3/scripts/conformal_calibrate.py" in pinned          # Day-15 module is contract
    assert "week4/INTEGRATION/frozen_thresholds.json" in pinned      # the deployed q is contract


@needs_frozen
def test_tampered_pinned_file_breaks_the_contract(monkeypatch):
    original = fzi._sha256
    victim = BASE / "week3" / "scripts" / "conformal_calibrate.py"

    def tampered(path):
        if Path(path) == victim:
            return "0" * 64
        return original(path)

    monkeypatch.setattr(fzi, "_sha256", tampered)
    st = lc.frozen_contract_status()
    assert not st["contract_ok"]
    assert "week3/scripts/conformal_calibrate.py" in st["changed"]


@needs_iface
@needs_frozen
def test_live_coverage_runs_through_the_day22_adapter():
    package = lc.load_frozen_package()
    for ds in package["datasets"]:                                    # frozen datasets only
        splits, _ = lc.live_frames(ds, IFACE)
        r = lc.live_coverage_dataset(ds, package, splits, ALPHA, IFACE)
        f = r["frozen"]
        assert f["finite_sample_ok"], f"{ds}: FZR {f['fzr_observed']} outside {f['band_hi_rate']}"
        assert f["verdict"] == "PASS"
        # the Day-22 adapter's own gates must have passed for the row to exist, and be recorded
        g = r["adapter_gates"]
        assert g["score_contract_ok"] and g["coverage_reproduces_frozen"]
        assert r["via"].startswith("conformal_integration")
        # dummy-in / dummy-out: the only drift allowed is the package's 6-dp rounding of q
        assert r["q_drift_is_rounding_only"] and r["n_cal_matches_freeze"]


@needs_iface
@needs_frozen
def test_decisions_on_disk_agree_with_the_adapter():
    package = lc.load_frozen_package()
    ds = next(iter(package["datasets"]))
    splits, _ = lc.live_frames(ds, IFACE)
    r = lc.live_coverage_dataset(ds, package, splits, ALPHA, IFACE)
    d = r["decisions_on_disk"]
    if d.get("present"):                # committed by Day 22; if absent the row says so instead
        assert d["agrees"], f"{ds}: decisions CSV is stale — {d}"
        assert d["flags_on_disk"] == r["frozen"]["false_flags"]


@needs_iface
def test_live_audit_is_clean_on_the_exchangeable_dummy_interface():
    splits, known = lc.live_frames("UNSW-NB15", IFACE)
    q, _, _ = conformal_threshold(splits["calibration"][1], ALPHA)   # UNSW is audit-only until Day 24
    rows, diag, p_conf = lc.audit_dataset("UNSW-NB15", splits, ALPHA, float(q), known)
    rows, holm = lc.holm_over_family(rows)
    assert holm["m"] == 6, "six inferential tests belong to the family"
    # the uniformity row is reported but deliberately outside the family (dependent p-values)
    descriptive = [r for r in rows if r["p_raw"] is None]
    assert len(descriptive) == 1 and "uniformity" in descriptive[0]["test"]
    assert not [r for r in rows if r["violation"]]
    assert diag["fidelity_in_unit_interval"] and abs(diag["conformal_pvalue_mean"] - 0.5) < 0.02
    assert p_conf.size == splits["test"][1].size


@needs_iface
@needs_frozen
def test_cli_writes_every_declared_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(lc, "GEN", tmp_path / "_generated")
    monkeypatch.setattr(lc, "REPORTS", tmp_path)
    monkeypatch.setattr(lc, "FIG", tmp_path / "figures")
    asked = ["CICIoT2023", "BoT-IoT"]
    out = lc.main(["--datasets", *asked, "--alpha", "0.05", "--no-figure"])

    assert out["day"] == 23 and out["all_finite_sample_ok"] and out["exchangeable"]
    # every requested dataset is accounted for: coverage-verified if the freeze covers it,
    # audit-only if not. Which bucket a dataset lands in depends on the freeze's current scope
    # (Day 24 extended it to the trio), so assert the partition, not a fixed membership.
    assert out["datasets_verified"] + out["datasets_not_frozen"] == asked
    assert not set(out["datasets_verified"]) & set(out["datasets_not_frozen"])
    assert out["datasets_verified"], "nothing verified — is the Day-21 freeze empty?"
    assert out["scores_root"].startswith("week2/")          # repo-relative, no home directory leaked
    for f in ("_generated/w4_04_live_coverage.json", "_generated/w4_04_live_coverage.csv",
              "_generated/w4_04_exchangeability_audit.csv", "w4_04_live_coverage.md"):
        assert (tmp_path / f).exists(), f
    saved = json.loads((tmp_path / "_generated" / "w4_04_live_coverage.json").read_text())
    assert saved["frozen_contract"]["contract_ok"]
    # the audit covers every requested dataset, frozen or not
    assert {r["dataset"] for r in saved["exchangeability_audit"]} == set(asked)
    md = (tmp_path / "w4_04_live_coverage.md").read_text()
    assert "Day 23" in md and "Exchangeability Audit" in md
    # the scope caveat appears exactly when something was audited but not verified
    assert ("not in the frozen package" in md) == bool(out["datasets_not_frozen"])


@needs_iface
@needs_frozen
def test_drill_reports_detection_and_recovery():
    splits, _ = lc.live_frames("BoT-IoT", IFACE)
    d = lc.violation_drill("BoT-IoT", splits, ALPHA, "cal_trim", 0.05, n_repeats=3)
    assert d["audit_detected"] and d["coverage_broke"]
    assert d["violated"]["fzr_observed"] > d["clean"]["fzr_observed"]
    assert d["fix_restored_coverage"] and d["fix_repeats"]["n_finite_sample_ok"] == 3

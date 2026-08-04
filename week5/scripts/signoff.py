#!/usr/bin/env python3
"""
Week 5 · Day 32 (Team A) — FINAL SIGN-OFF: one script, every RQ2 / RQ5 number and Figure 2 reproducible.

Task (`qi26_12_Week_5.pdf`): *Final sign-off: every RQ2 / RQ5 number and Figure 2 reproducible from one
script. Confirm all Team-A deliverables are frozen for writing.* Deliverables: **all Team-A results &
figures COMPLETE** + **repro sign-off**.

What this module is for
-----------------------
Days 26-30 produced the result surface across seven modules; Day 31 wrote the methods text and the
reproducibility appendix. What did NOT exist until now is the *one script* the task asks for: a single
entry point that re-derives every headline number from the raw inputs and checks it against what is
committed. `freeze_results.py --reproduce` is the closest predecessor, but it pins only the 39 Day-26/27
scalars — RQ1, RQ3 and Figure 2. **RQ2 (Table B) and RQ5 (the ablation + honesty verdicts) were never in
that set.** This module widens the comparison to the whole surface and adds the gates that make
"frozen for writing" a checkable claim rather than an assertion.

Five gates
----------
  G1  REPRODUCE   Re-run the five result mains (deterministic, seed 42) with their outputs sandboxed, and
                  compare every extracted scalar against the COMMITTED artifact that quotes it. Covers
                  RQ1, RQ2, RQ3, RQ5 and Figure 2. Floats to `--tol` (default 1e-9); ints/bools exact.
  G2  FREEZE      The three SHA-256 manifests re-hash clean: week4/INTEGRATION (34), week5/RESULTS_FROZEN
                  (16), week5/HANDOVER (41).
  G3  COMPLETE    Every declared Team-A deliverable exists and is non-empty — the "results & figures
                  COMPLETE" half of the task.
  G4  NEUTRAL     No pinned artifact changed *during this run*. Hashes are taken before G1 and re-taken
                  after G4's own re-hash, so the sign-off proves it did not itself move the numbers it
                  signs off.
  G5  AUDIT       Runs the Day-30 cross-audit sandboxed and requires 0 FAIL. This is what actually covers
                  the pass-through cells — see below.

Recomputed vs pass-through — the honest scope of G1
---------------------------------------------------
Not every scalar in the result artifacts is *computed* by the module that emits it, and G1 must not claim
otherwise. Two provenances exist, and every G1 check is tagged with which one applies:

  `recomputed`   The emitting module derives the number from the raw scores/partitions on this run — the
                 5-seed CIs and per-seed coverage points (RQ2), the ablation rules (RQ5), the QS-Net arm
                 of Table A (RQ1), the disentanglement AUROCs (RQ3) and the Figure-2 sweep. For these,
                 G1 is a genuine re-derivation.
  `passthrough`  The module reads the number from an upstream frozen artifact and re-emits it: Table B's
                 canonical cells come from the Day-21 freeze / Day-22 adapter / Day-19 recall arms (the
                 Day-28 report says so explicitly — "never recomputed here"), the RQ5 verdicts come from
                 the Day-25 significance JSON, and Table A's classical arm is read from the Day-12
                 `results.json`. For these, G1 proves the **assembly path is stable** — a broken or
                 silently-rewired pass-through fails it — but it does NOT re-derive the numeric.

The numerics behind the pass-through cells are re-derived independently by `cross_audit.py`, which
recomputes the order-statistic threshold, the flag counts, the recall and the Beta-Binomial band from the
raw inputs with a separate implementation. G5 runs it, so the sign-off as a whole covers both provenances
— but the two gates prove different things and are reported separately rather than pooled.

Why the mains are sandboxed
---------------------------
The mains write as well as return. Re-running them into the real tree would rewrite the artifacts this
script is comparing against — the failure documented in the Day-31 appendix and closed for
`freeze_results.py --reproduce` on Day 32. G1 redirects their output dirs to a temp tree and reads the
in-memory return values, so G4 is a meaningful check rather than a tautology.

Exit status: 0 if all four gates pass, 1 otherwise (CI-usable).

Run:     python week5/scripts/signoff.py
Strict:  python week5/scripts/signoff.py --tol 0            # bit-exact scalars (expect ULP failures; see
                                                            # the Day-31 appendix section 7)
Reprice: python week5/scripts/signoff.py --source real --scores-root <team-B dir>
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))
sys.path.insert(0, str(BASE / "week5" / "scripts"))

from conformal_calibrate import IFACE, TRIO              # noqa: E402
from freeze_integration import _sha256                    # noqa: E402  (Day-21 hash helper)
import freeze_results as fr                               # noqa: E402  (Day-26 freeze + sandbox helper)
import freeze_integration as fi                           # noqa: E402  (Day-21 integration freeze)
import handover_teamB as ho                               # noqa: E402  (Day-30 manuscript package)
import disentanglement as dis                             # noqa: E402  (RQ3)
import table_a as ta                                      # noqa: E402  (RQ1 + coverage diagnostics)
import figure2_coverage as fig2                           # noqa: E402  (Figure 2)
import table_b_final as tbf                               # noqa: E402  (RQ2)
import ablation_rq5 as abl                                # noqa: E402  (RQ5 + conformal ablation)
import cross_audit as ca                                  # noqa: E402  (Day-30 independent re-derivation)

GEN = BASE / "week5" / "reports" / "_generated"
REPORTS = BASE / "week5" / "reports"
SEED = 42
PRIMARY_ALPHA = 0.05
DEFAULT_TOL = 1e-9

# The committed artifacts G1 compares the re-run against, keyed by the doc name the extractor expects.
COMMITTED = {
    "dis": GEN / "w5_01_disentanglement.json",
    "ta": GEN / "w5_02_table_a.json",
    "fig2": GEN / "w5_03_figure2.json",
    "tb": GEN / "w5_04_table_b.json",
    "abl": GEN / "w5_06_ablation_rq5.json",
}

# The three freeze manifests whose pinned files G4 watches.
MANIFESTS = [
    BASE / "week4" / "INTEGRATION" / "integration_manifest_v1.0.json",
    BASE / "week5" / "RESULTS_FROZEN" / "results_manifest_v1.0.json",
    BASE / "week5" / "HANDOVER" / "handover_manifest_v1.0.json",
]

# "All Team-A deliverables" — the surface the manuscript writes against (repo-relative).
DELIVERABLES = {
    "Table A (RQ1)": ["week5/reports/_generated/w5_02_table_a.md",
                      "week5/reports/_generated/w5_02_table_a.tex",
                      "week5/reports/_generated/w5_05_table_a.md",
                      "week5/reports/_generated/w5_05_table_a.tex",
                      "week5/reports/_generated/w5_05_table_a_effects.csv",
                      "week5/reports/_generated/w5_05_known_fa.csv"],
    "Table B (RQ2)": ["week5/reports/_generated/w5_04_table_b.md",
                      "week5/reports/_generated/w5_04_table_b.tex",
                      "week5/reports/_generated/w5_04_allseed_ci.csv",
                      "week4/reports/_generated/w4_05_table_b.md"],
    "Figure 2 (coverage)": ["week5/reports/figures/w5_fig2_coverage.png",
                            "week5/reports/_generated/w5_03_figure2_data.csv"],
    "Figure 3 (ablation)": ["week5/reports/figures/w5_fig3_ablation.png",
                            "week5/reports/_generated/w5_06_ablation.md",
                            "week5/reports/_generated/w5_06_ablation.tex"],
    "RQ3 disentanglement": ["week5/reports/_generated/w5_01_disentanglement.csv"],
    "RQ5 honesty": ["week5/reports/_generated/w5_06_rq5_honesty.md",
                    "week4/reports/_generated/w4_06_rq5_honesty.md"],
    "Coverage diagnostics": ["week5/reports/_generated/w5_02_per_class_fzr.csv",
                             "week4/reports/_generated/w4_04_live_coverage.json"],
    "Cross-audit (Day 30)": ["week5/reports/_generated/w5_07_cross_audit.csv",
                             "week5/reports/_generated/w5_07_cross_audit.json"],
    "Methods + repro appendix (Day 31)": ["week5/reports/w5_09_methods_data_stats.md",
                                          "week5/reports/w5_10_repro_appendix.md",
                                          "week5/reports/_generated/w5_09_methods.tex",
                                          "week5/reports/_generated/w5_10_repro_appendix.tex"],
    "Freeze packages": ["week4/INTEGRATION/frozen_thresholds.json",
                        "week4/INTEGRATION/interface_contract.json",
                        "week5/RESULTS_FROZEN/results_frozen_scalars.json",
                        "week5/HANDOVER/HANDOVER.md"],
}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _rel(p) -> str:
    """Repo-relative POSIX path — never leak an absolute checkout path into a committed artifact.

    The Day-30 audit's `absolute-path leak scan` gates on this; storing `str(scores_root)` verbatim is the
    exact regression it caught in `coverage_harness.py`.
    """
    try:
        return Path(p).resolve().relative_to(BASE).as_posix()
    except (ValueError, OSError):
        return str(p)


# ---------------------------------------------------------------- scalar extraction

# Scalars the emitting module READS from an upstream frozen artifact rather than deriving on this run.
# Matched as (scope, suffix-or-field) against the flattened key. See the module docstring.
PASSTHROUGH_RQ2_FIELDS = {"n_cal", "k", "m_test", "n_zeroday", "threshold_q", "achieved_alpha",
                          "qsnet_recall", "best_classical_recall", "recall_delta",
                          "band_lo", "band_hi", "guarantee_held"}
PASSTHROUGH_RQ5_FIELDS = {"delta_recall", "cohens_h", "mcnemar_p_holm", "quantum_helps", "verdict"}


def provenance(key: str) -> str:
    """`recomputed` if this run derived the number from raw inputs, else `passthrough`.

    Provenance is a property of the *emitting module*, documented in the Day-26/28/29 reports:
      - Table B canonical cells      <- Day-21 freeze / Day-22 adapter / Day-19 recall  (never recomputed)
      - RQ5 verdicts                 <- Day-25 w4_06_significance.json
      - Table A classical arm        <- Day-12 baselines/<ds>/results.json
    Everything else is derived from the score interface on this run.
    """
    parts = key.split("/")
    scope = parts[0]
    tail = parts[-1]
    if scope == "RQ2" and tail in PASSTHROUGH_RQ2_FIELDS:
        return "passthrough"
    if scope == "RQ5" and tail in PASSTHROUGH_RQ5_FIELDS:
        return "passthrough"
    if scope == "RQ1" and "/xgboost/" in key:
        return "passthrough"
    return "recomputed"


def extract_scalars(docs: dict) -> dict:
    """Flatten the five result docs to `key -> scalar`.

    Works identically on the in-memory return values and on the committed JSON, because the mains write
    exactly what they return — which is itself the property being asserted.
    """
    s: dict[str, object] = {}

    # --- RQ3: separation / novelty AUROC panels ---------------------------------
    for ds, r in docs["dis"]["results"].items():
        for p in r["panels"]:
            s[f"RQ3/{ds}/{p['panel']}/auroc"] = p["auroc"]
            s[f"RQ3/{ds}/{p['panel']}/ci95_low"] = p["ci95_low"]
            s[f"RQ3/{ds}/{p['panel']}/ci95_high"] = p["ci95_high"]

    # --- RQ1: Table A rows, McNemar, all-seed coverage, per-class diagnostic -----
    for r in docs["ta"]["rows"]:
        tag = "xgboost" if r["arm"] == "classical" else "qsnet"
        for m in ("accuracy", "macro_f1", "auroc_ovr_macro"):
            s[f"RQ1/{r['dataset']}/{tag}/{m}"] = r[m]
    for m in docs["ta"]["mcnemar"]:
        s[f"RQ1/{m['dataset']}/mcnemar/p_holm"] = m["p_holm"]
        s[f"RQ1/{m['dataset']}/mcnemar/n10"] = m["qsnet_only_right"]
        s[f"RQ1/{m['dataset']}/mcnemar/n01"] = m["xgboost_only_right"]
    for c in docs["ta"]["coverage_all_seed"]:
        s[f"RQ1/{c['dataset']}/allseed/mean_fzr"] = c["mean_fzr"]
        s[f"RQ1/{c['dataset']}/allseed/n_in_band"] = c["n_in_band"]
    for pc in docs["ta"]["per_class_fzr"]:
        s[f"RQ1/{pc['dataset']}/perclass/n_out_of_band"] = pc["n_out_of_band"]
        s[f"RQ1/{pc['dataset']}/perclass/n_classes"] = pc["n_classes"]

    # --- RQ2: Table B final + all-seed CIs (the task's headline) ------------------
    for r in docs["tb"]["table_b_final"]:
        ds = r["dataset"]
        for f in ("n_cal", "k", "m_test", "n_zeroday", "threshold_q", "achieved_alpha",
                  "qsnet_recall", "best_classical_recall", "recall_delta", "n_in_band"):
            s[f"RQ2/{ds}/{f}"] = r[f]
        s[f"RQ2/{ds}/band_lo"], s[f"RQ2/{ds}/band_hi"] = r["band"][0], r["band"][1]
        s[f"RQ2/{ds}/guarantee_held"] = r["guarantee_held"]
        for blk in ("fzr_5seed", "recall_5seed"):
            for stat in ("mean", "std", "ci95_low", "ci95_high"):
                s[f"RQ2/{ds}/{blk}/{stat}"] = r[blk][stat]
    for c in docs["tb"]["allseed_ci"]:
        s[f"RQ2/{c['dataset']}/ci_covers_alpha"] = c["fzr_ci_covers_alpha"]
        for pe in c["per_seed"]:
            s[f"RQ2/{c['dataset']}/per_seed/{pe['seed']}/fzr"] = pe["fzr"]
    s["RQ2/all_guarantees_held"] = docs["tb"]["all_guarantees_held"]
    s["RQ2/all_seeds_in_band"] = docs["tb"]["all_seeds_in_band"]
    s["RQ2/all_ci_cover_alpha"] = docs["tb"]["all_ci_cover_alpha"]

    # --- RQ5: conformal-vs-heuristic ablation + honesty verdicts ------------------
    for a in docs["abl"]["ablation"]:
        ds = a["dataset"]
        for rule in ("conformal", "heuristic", "fixed"):
            s[f"RQ5/{ds}/{rule}/tau"] = a[rule]["tau"]
            s[f"RQ5/{ds}/{rule}/false_zeroday_rate"] = a[rule]["false_zeroday_rate"]
            s[f"RQ5/{ds}/{rule}/false_flags"] = a[rule]["false_flags"]
        s[f"RQ5/{ds}/band_lo_rate"] = a["band_lo_rate"]
        s[f"RQ5/{ds}/band_hi_rate"] = a["band_hi_rate"]
    for v in docs["abl"]["rq5_verdicts"]:
        key = f"RQ5/{v['dataset']}/{v['baseline'].replace(' ', '_')}"
        s[f"{key}/delta_recall"] = v["delta_recall"]
        s[f"{key}/cohens_h"] = v["cohens_h"]
        s[f"{key}/mcnemar_p_holm"] = v["mcnemar_zeroday_p_holm"]
        s[f"{key}/quantum_helps"] = v["quantum_helps"]
        s[f"{key}/verdict"] = v["verdict"]
    for sn in docs["abl"]["small_n"]:
        s[f"RQ5/{sn['dataset']}/small_n/{sn['n_sub']}/conformal_mean_fzr"] = sn["conformal_mean_fzr"]
        s[f"RQ5/{sn['dataset']}/small_n/{sn['n_sub']}/heuristic_mean_fzr"] = sn["heuristic_mean_fzr"]
    s["RQ5/heuristic_anticonservative_cells"] = docs["abl"]["heuristic_anticonservative_cells"]
    s["RQ5/conformal_le_alpha_cells"] = docs["abl"]["conformal_le_alpha_cells"]

    # --- Figure 2: the headline coverage plot's data -----------------------------
    for p in docs["fig2"]["points"]:
        ds = p["dataset"]
        for f in ("mean_fzr", "min_fzr", "max_fzr", "std_fzr", "band_lo_rate", "band_hi_rate"):
            s[f"FIG2/{ds}/{f}"] = p[f]
        for pe in p["per_seed"]:
            s[f"FIG2/{ds}/per_seed/{pe['seed']}/fzr"] = pe["fzr"]
    s["FIG2/figure_written"] = docs["fig2"]["figure_written"]
    return s


def _compare(key, committed, observed, tol):
    """Return (verdict, delta). Floats to `tol`; everything else exact."""
    if isinstance(committed, bool) or isinstance(observed, bool) or committed is None or observed is None:
        return ("PASS" if committed == observed else "FAIL"), 0.0
    if isinstance(committed, (int, float)) and isinstance(observed, (int, float)):
        d = abs(float(observed) - float(committed))
        return ("PASS" if d <= tol else "FAIL"), d
    return ("PASS" if committed == observed else "FAIL"), 0.0


# ---------------------------------------------------------------- gates

def gate_reproduce(datasets, alpha, scores_root, source, tol):
    """G1 — re-run the five mains sandboxed and diff every scalar against the committed artifacts."""
    missing = [n for n, p in COMMITTED.items() if not p.exists()]
    if missing:
        return [{"gate": "G1 REPRODUCE", "check": f"committed artifact absent: {missing}",
                 "scope": "-", "expected": "present", "observed": "missing", "delta": None,
                 "tol": tol, "verdict": "FAIL"}], {}, {}

    committed_docs = {n: json.loads(p.read_text()) for n, p in COMMITTED.items()}
    common = ["--datasets", *datasets, "--alpha", str(alpha),
              "--scores-root", str(scores_root), "--source", source]

    log("re-running the five result mains (seed 42, outputs sandboxed) ...")
    with fr.sandboxed_outputs():
        # figure2/ablation also write PNGs; FIG is redirected for fig2 by the helper, and for the
        # ablation module here, so nothing in week5/reports/figures/ is touched.
        abl_fig, abl_gen, abl_reports = abl.FIG, abl.GEN, abl.REPORTS
        tbf_gen, tbf_reports = tbf.GEN, tbf.REPORTS
        abl.FIG, abl.GEN, abl.REPORTS = fig2.FIG, fig2.GEN, fig2.REPORTS
        tbf.GEN, tbf.REPORTS = fig2.GEN, fig2.REPORTS
        try:
            live = {
                "dis": dis.main(common),
                "ta": ta.main(common),
                "fig2": fig2.main(common + ["--sweep", "0.01", "0.20", "0.01"]),
                "tb": tbf.main(common),
                "abl": abl.main(["--alpha", str(alpha), "--scores-root", str(scores_root),
                                 "--source", source, "--datasets", *datasets,
                                 "--sweep", "0.01", "0.20", "0.01"]),
            }
        finally:
            abl.FIG, abl.GEN, abl.REPORTS = abl_fig, abl_gen, abl_reports
            tbf.GEN, tbf.REPORTS = tbf_gen, tbf_reports

    want = extract_scalars(committed_docs)
    got = extract_scalars(live)

    checks = []
    for key in sorted(want):
        if key not in got:
            checks.append({"gate": "G1 REPRODUCE", "check": key, "scope": key.split("/")[0],
                           "provenance": provenance(key), "expected": want[key],
                           "observed": "MISSING", "delta": None, "tol": tol, "verdict": "FAIL"})
            continue
        verdict, delta = _compare(key, want[key], got[key], tol)
        checks.append({"gate": "G1 REPRODUCE", "check": key, "scope": key.split("/")[0],
                       "provenance": provenance(key), "expected": want[key], "observed": got[key],
                       "delta": delta, "tol": tol, "verdict": verdict})
    for key in sorted(set(got) - set(want)):
        checks.append({"gate": "G1 REPRODUCE", "check": key, "scope": key.split("/")[0],
                       "provenance": provenance(key), "expected": "ABSENT", "observed": got[key],
                       "delta": None, "tol": tol, "verdict": "FAIL"})
    return checks, want, got


def gate_audit(datasets, alpha, scores_root, source):
    """G5 — the Day-30 cross-audit, run sandboxed: the independent re-derivation of the pass-through cells.

    `cross_audit.py` recomputes the order-statistic threshold, flag counts, recall and Beta-Binomial band
    from the raw inputs with a separate implementation, so it covers exactly what G1's `passthrough` rows
    cannot. Its outputs are redirected to a temp tree so G4 stays meaningful.
    """
    import tempfile
    saved = [(ca, "GEN", ca.GEN), (ca, "REPORTS", ca.REPORTS)]
    with tempfile.TemporaryDirectory(prefix="qsnet-audit-") as td:
        for mod, attr, _ in saved:
            setattr(mod, attr, Path(td))
        try:
            out = ca.main(["--datasets", *datasets, "--alpha", str(alpha),
                           "--scores-root", str(scores_root), "--source", source])
        finally:
            for mod, attr, orig in saved:
                setattr(mod, attr, orig)
    ok = out["n_fail"] == 0
    return [{"gate": "G5 AUDIT", "check": "cross-audit independent re-derivation (0 FAIL required)",
             "scope": "passthrough cells", "provenance": "independent",
             "expected": "0 FAIL", "observed": f"{out['n_pass']} PASS / {out['n_fail']} FAIL / "
                                               f"{out['n_warn']} WARN over {out['n_checks']} checks",
             "delta": None, "tol": None, "verdict": "PASS" if ok else "FAIL"}]


def gate_freeze():
    """G2 — the three SHA-256 manifests re-hash clean."""
    checks = []
    for label, fn, n_expected in (("week4/INTEGRATION", fi.verify, 34),
                                  ("week5/RESULTS_FROZEN", fr.verify, 16),
                                  ("week5/HANDOVER", ho.verify, 41)):
        rc = fn()
        checks.append({"gate": "G2 FREEZE", "check": f"manifest verify: {label}", "scope": label,
                       "expected": "0 mismatch", "observed": f"rc={rc}", "delta": None,
                       "tol": None, "verdict": "PASS" if rc == 0 else "FAIL"})
    return checks


def gate_complete():
    """G3 — every declared Team-A deliverable exists and is non-empty."""
    checks = []
    for group, rels in DELIVERABLES.items():
        for rel in rels:
            p = BASE / rel
            ok = p.exists() and p.stat().st_size > 0
            checks.append({"gate": "G3 COMPLETE", "check": rel, "scope": group,
                           "expected": "present, non-empty",
                           "observed": f"{p.stat().st_size} B" if p.exists() else "MISSING",
                           "delta": None, "tol": None, "verdict": "PASS" if ok else "FAIL"})
    return checks


def pinned_hashes():
    """SHA-256 of every file pinned by the three manifests (for the G4 before/after comparison)."""
    out = {}
    for man in MANIFESTS:
        if not man.exists():
            continue
        for rec in json.loads(man.read_text())["files"]:
            p = BASE / rec["path"]
            if p.exists():
                out[rec["path"]] = _sha256(p)
    return out


def gate_neutral(before, after):
    """G4 — no pinned artifact changed while this script ran."""
    changed = sorted(k for k in before if k in after and before[k] != after[k])
    vanished = sorted(set(before) - set(after))
    checks = [{"gate": "G4 NEUTRAL", "check": "pinned artifacts unchanged during sign-off",
               "scope": f"{len(before)} pinned files", "expected": "0 changed",
               "observed": f"{len(changed)} changed, {len(vanished)} missing", "delta": None,
               "tol": None, "verdict": "PASS" if not changed and not vanished else "FAIL"}]
    for c in changed + vanished:
        checks.append({"gate": "G4 NEUTRAL", "check": f"changed during run: {c}", "scope": "-",
                       "expected": "unchanged", "observed": "CHANGED", "delta": None,
                       "tol": None, "verdict": "FAIL"})
    return checks


# ---------------------------------------------------------------- report

def render_markdown(doc, checks_df):
    n_pass = int((checks_df["verdict"] == "PASS").sum())
    n_fail = int((checks_df["verdict"] == "FAIL").sum())
    verdict = "**SIGNED OFF**" if n_fail == 0 else "**NOT SIGNED OFF**"
    prov = " · scores **dummy** (PROVISIONAL)" if doc["source_kind"] == "dummy" else " · scores **real**"
    L = [f"# Week 5 · Day 32 — Final Sign-Off: One-Script Reproducibility + Frozen Deliverables", "",
         f"Task (`qi26_12_Week_5.pdf`): *final sign-off — every RQ2 / RQ5 number and Figure 2 reproducible "
         f"from one script; confirm all Team-A deliverables are frozen for writing.* "
         f"Seed {doc['seed']} · α = {doc['alpha']} · trio {', '.join(doc['datasets'])}{prov}.", "",
         f"Produced by [`../scripts/signoff.py`](../scripts/signoff.py) — the single entry point the task "
         f"asks for. It re-runs the five result mains from the raw inputs with their outputs sandboxed, "
         f"then diffs **every** extracted scalar against the committed artifact that quotes it.", "",
         f"## Verdict: {verdict} — {n_pass} PASS · {n_fail} FAIL "
         f"({len(checks_df)} checks, tol {doc['tol']:g})", ""]

    L += ["## Gates", "", "| Gate | What it proves | Checks | PASS | FAIL |", "|---|---|---:|---:|---:|"]
    meaning = {"G1 REPRODUCE": "every RQ1/RQ2/RQ3/RQ5/Figure-2 scalar matches the artifact that quotes it",
               "G2 FREEZE": "the three SHA-256 manifests re-hash clean",
               "G3 COMPLETE": "every declared Team-A deliverable is present and non-empty",
               "G4 NEUTRAL": "this sign-off run did not itself modify any pinned artifact",
               "G5 AUDIT": "the pass-through cells re-derive under an independent implementation"}
    for g in ["G1 REPRODUCE", "G2 FREEZE", "G3 COMPLETE", "G4 NEUTRAL", "G5 AUDIT"]:
        sub = checks_df[checks_df["gate"] == g]
        L.append(f"| **{g}** | {meaning[g]} | {len(sub)} | {int((sub['verdict'] == 'PASS').sum())} | "
                 f"{int((sub['verdict'] == 'FAIL').sum())} |")

    g1 = checks_df[checks_df["gate"] == "G1 REPRODUCE"]
    n_recomp = int((g1["provenance"] == "recomputed").sum())
    n_pass_thru = int((g1["provenance"] == "passthrough").sum())

    L += ["", "## G1 — by research question, split by provenance", "",
          f"Of {len(g1)} scalars, **{n_recomp} are recomputed** from the raw scores on this run and "
          f"**{n_pass_thru} are pass-throughs** the emitting module reads from an upstream frozen artifact "
          "(Table B's canonical cells from the Day-21/22/19 arms, the RQ5 verdicts from the Day-25 "
          "significance JSON, Table A's classical arm from the Day-12 `results.json`). For the "
          "pass-throughs G1 proves the **assembly path is stable**, not that the numeric re-derives — "
          "that is G5's job, and the two are reported separately rather than pooled.", "",
          "| Scope | Scalars | recomputed | pass-through | PASS | FAIL | max \\|Δ\\| |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for scope in ["RQ1", "RQ2", "RQ3", "RQ5", "FIG2"]:
        sub = g1[g1["scope"] == scope]
        if not len(sub):
            continue
        dmax = pd.to_numeric(sub["delta"], errors="coerce").max()
        L.append(f"| **{scope}** | {len(sub)} | {int((sub['provenance'] == 'recomputed').sum())} | "
                 f"{int((sub['provenance'] == 'passthrough').sum())} | "
                 f"{int((sub['verdict'] == 'PASS').sum())} | {int((sub['verdict'] == 'FAIL').sum())} | "
                 f"{'—' if pd.isna(dmax) else f'{dmax:.2e}'} |")

    fails = checks_df[checks_df["verdict"] == "FAIL"]
    if len(fails):
        L += ["", "## Failures", "", "| Gate | Check | Expected | Observed |", "|---|---|---|---|"]
        for _, r in fails.head(40).iterrows():
            L.append(f"| {r['gate']} | `{r['check']}` | {r['expected']} | {r['observed']} |")
        if len(fails) > 40:
            L.append(f"| … | *{len(fails) - 40} further failures — see the CSV* | | |")

    L += ["", "## G3 — deliverables frozen for writing", "",
          "| Deliverable group | Files | All present |", "|---|---:|:--:|"]
    g3 = checks_df[checks_df["gate"] == "G3 COMPLETE"]
    for group in DELIVERABLES:
        sub = g3[g3["scope"] == group]
        ok = bool(len(sub)) and not (sub["verdict"] == "FAIL").any()
        L.append(f"| {group} | {len(sub)} | {'✅' if ok else '❌'} |")

    L += ["", "## Notes", "",
          "- **Tolerance.** Floats compare to "
          f"{doc['tol']:g}; ints, bools and verdict strings compare exactly. The Day-31 appendix (§7) "
          "records why bit-equality is the wrong gate: re-runs differ by 1-2 ULP in the scipy "
          "exact-binomial tail across library builds, far below any reported digit. `--tol 0` reproduces "
          "that finding on demand.",
          "- **Sandboxing.** G1 redirects the mains' output dirs to a temp tree, so G4 is a real check "
          "rather than a tautology. The same fix landed in `freeze_results.py --reproduce` on Day 32, "
          "closing the open item the Day-31 appendix logged.",
          "- **Scope widened.** `freeze_results.py --reproduce` pins 39 scalars covering RQ1, RQ3 and "
          "Figure 2 only. This module additionally covers **RQ2 (Table B, including every per-seed "
          "coverage point and both 5-seed CIs) and RQ5 (the ablation rules and every honesty verdict)** — "
          "the two the task names explicitly, and the two that had never been inside a reproducibility "
          "gate.",
          "- **Provenance is not decoration.** A sign-off that counted pass-throughs as re-derivations "
          "would be measuring its own plumbing. The split above, plus G5, is what makes the claim "
          "checkable: *recomputed* cells re-derive here, *pass-through* cells re-derive under "
          "`cross_audit.py`'s separate implementation.",
          f"- **Provenance.** Quantum-side cells ride the "
          f"{'Day-14 dummy fidelity interface and remain PROVISIONAL' if doc['source_kind'] == 'dummy' else 'real prototype scores'}. "
          "Re-run with `--source real --scores-root <dir>` to sign off the repriced surface.", ""]
    L += [f"CSV: [`_generated/w5_11_signoff.csv`](_generated/w5_11_signoff.csv) · "
          f"JSON: [`_generated/w5_11_signoff.json`](_generated/w5_11_signoff.json)."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-32 final sign-off — one-script reproducibility + freeze")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=PRIMARY_ALPHA)
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--tol", type=float, default=DEFAULT_TOL,
                    help="float tolerance for the scalar diff (0 = bit-exact)")
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    log(f"Day-32 sign-off: seed {SEED}, alpha {args.alpha}, source {args.source}, tol {args.tol:g}")
    before = pinned_hashes()
    log(f"G4: recorded {len(before)} pinned artifact hashes")

    checks, _, _ = gate_reproduce(args.datasets, args.alpha, args.scores_root, args.source, args.tol)
    log(f"G1 REPRODUCE: {sum(c['verdict'] == 'PASS' for c in checks)}/{len(checks)} scalars re-derived")

    g2 = gate_freeze()
    checks += g2
    log(f"G2 FREEZE: {sum(c['verdict'] == 'PASS' for c in g2)}/{len(g2)} manifests clean")

    g3 = gate_complete()
    checks += g3
    log(f"G3 COMPLETE: {sum(c['verdict'] == 'PASS' for c in g3)}/{len(g3)} deliverables present")

    g5 = gate_audit(args.datasets, args.alpha, args.scores_root, args.source)
    checks += g5
    log(f"G5 AUDIT: {g5[0]['observed']}")

    after = pinned_hashes()
    g4 = gate_neutral(before, after)
    checks += g4
    log(f"G4 NEUTRAL: {'clean' if all(c['verdict'] == 'PASS' for c in g4) else 'DRIFT DETECTED'}")

    df = pd.DataFrame(checks)
    n_fail = int((df["verdict"] == "FAIL").sum())
    doc = {"schema_version": "1.0", "day": 32, "seed": SEED, "alpha": args.alpha,
           "source_kind": args.source, "scores_root": _rel(args.scores_root),
           "datasets": list(args.datasets), "tol": args.tol,
           "n_checks": len(df), "n_pass": int((df["verdict"] == "PASS").sum()), "n_fail": n_fail,
           "signed_off": n_fail == 0,
           "gates": {g: {"n": int((df["gate"] == g).sum()),
                         "pass": int(((df["gate"] == g) & (df["verdict"] == "PASS")).sum()),
                         "fail": int(((df["gate"] == g) & (df["verdict"] == "FAIL")).sum())}
                     for g in sorted(df["gate"].unique())},
           "checks": checks}

    (GEN / "w5_11_signoff.json").write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    df.to_csv(GEN / "w5_11_signoff.csv", index=False)
    (REPORTS / "w5_11_signoff.md").write_text(render_markdown(doc, df), encoding="utf-8")

    log(f"done -> w5_11_signoff.md + .{{json,csv}} | {doc['n_pass']} PASS / {n_fail} FAIL")
    print(f"\n{'SIGN-OFF OK' if n_fail == 0 else 'SIGN-OFF FAILED'} — "
          f"{doc['n_pass']}/{doc['n_checks']} checks pass (tol {args.tol:g}).")
    return doc


if __name__ == "__main__":
    sys.exit(0 if main()["signed_off"] else 1)

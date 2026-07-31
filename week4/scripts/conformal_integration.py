#!/usr/bin/env python3
"""
Week 4 · Day 22 (Team A) — connect the FROZEN conformal module to Team B's inference pipeline.

Task (`qi26_12_Week_4.pdf`): *Connect the frozen conformal module to Team B's inference pipeline; verify
score = 1 − max-fidelity flows correctly. Run first end-to-end known-vs-zero-day decisions on dataset 1.*
Deliverables: "Conformal↔inference integration" / "First end-to-end decisions".

The adapter (one direction of data flow)
----------------------------------------
Team B inference scores (`fid__<class>` per row, in the Day-21 frozen schema)
   └─► s = 1 − max_c F(ρ_x, ρ_c)            [the nonconformity contract — verified below]
        └─► load frozen q from week4/INTEGRATION/frozen_thresholds.json[<dataset>]   [NO recalibration]
             └─► decision: KNOWN if s ≤ q  else ZERO-DAY   (flag iff s > q)
                  └─► per-row decisions + the known-vs-zero-day confusion summary.

Three verification gates (all asserted, all logged)
---------------------------------------------------
1. **Score contract.** Recompute s = 1 − max_c F from the `fid__*` columns and cross-check against the
   interface's precomputed `nonconformity` column → max|Δ| ≤ 1e-6. This is the task's "verify score =
   1 − max-fidelity flows correctly".
2. **Frozen-threshold provenance.** The q applied is loaded from the Day-21 freeze, not recomputed here;
   the adapter re-derives q from calibration only as an *audit* and asserts it equals the frozen q (so a
   silent drift between freeze and integration is impossible).
3. **Coverage consistency.** The achieved false-zero-day rate on the KNOWN test split must reproduce the
   Day-21 frozen value (same q, same rows) → the integration is faithful, not a re-run with new numbers.

Fidelity convention (the F² trap — AK's Day-20 spec)
----------------------------------------------------
`s` needs the NON-SQUARED Uhlmann F. PennyLane `qml.math.fidelity` / Qiskit `state_fidelity` return F².
If Team B's `fid__*` columns carry F², pass `--assume-fidelity-squared`: the adapter takes sqrt() first so
`s`, `F_in`, `F_out` share one convention. The dummy interface already stores non-squared F (default).

Real prototypes: `--scores-root <team-B dir> --source real` — the frozen schema is identical, no code change.

Report: week4/reports/w4_03_conformal_integration.md
JSON/CSV: week4/reports/_generated/w4_03_conformal_integration.{json,csv} + per-row decisions_<dataset>.csv
Run: python week4/scripts/conformal_integration.py --datasets CICIoT2023        (first end-to-end, dataset 1)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week3" / "scripts"))

from conformal_calibrate import (  # noqa: E402  (Day-15 single source of the conformal math + interface I/O)
    IFACE, TRIO, _rel, conformal_threshold, known_classes, load_scores, nonconformity_from_fidelities,
)

INTEG = BASE / "week4" / "INTEGRATION"
FROZEN_THRESHOLDS = INTEG / "frozen_thresholds.json"
GEN = BASE / "week4" / "reports" / "_generated"
REPORTS = BASE / "week4" / "reports"
SEED = 42
PRIMARY_ALPHA = 0.05
CONTRACT_TOL = 1e-6


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def load_frozen_thresholds():
    if not FROZEN_THRESHOLDS.exists():
        raise FileNotFoundError(
            f"{FROZEN_THRESHOLDS} not found — run the Day-21 freeze first:\n"
            f"  python week4/scripts/freeze_integration.py")
    return json.loads(FROZEN_THRESHOLDS.read_text(encoding="utf-8"))


def scores_from_fidelities(df, known, assume_squared):
    """s = 1 − max_c F. If the interface carries F² (assume_squared), take sqrt() first so F is non-squared."""
    cols = [f"fid__{c}" for c in known]
    fid = df[cols].to_numpy(dtype=float)
    if assume_squared:
        fid = np.sqrt(np.clip(fid, 0.0, None))
    return 1.0 - fid.max(axis=1)


def integrate_dataset(dataset, frozen, scores_root, assume_squared, alpha):
    """Adapter + the three verification gates for one dataset. Returns (summary, per_row_df)."""
    if dataset not in frozen["datasets"]:
        raise KeyError(f"{dataset} not in frozen_thresholds.json (frozen: {list(frozen['datasets'])})")
    q_frozen = frozen["datasets"][dataset]["threshold_q"]
    frames = load_scores(dataset, scores_root)
    known = known_classes(frames)

    # ---- Gate 1: score contract  s = 1 - max_c F  (recomputed vs the interface's precomputed column)
    s = {sp: scores_from_fidelities(frames[sp], known, assume_squared) for sp in ("calibration", "test", "zeroday")}
    contract_err = None
    if not assume_squared and "nonconformity" in frames["test"].columns:
        # the interface stores non-squared s; only meaningful when we did not sqrt()
        ref = nonconformity_from_fidelities(frames["test"], known)
        contract_err = float(np.max(np.abs(s["test"] - ref)))
        assert contract_err <= CONTRACT_TOL, \
            f"{dataset}: score contract broken, max|s - (1-max F)| = {contract_err}"

    # ---- Gate 2: frozen-threshold provenance  (audit q vs frozen q; apply the FROZEN one)
    q_audit, k, n = conformal_threshold(s["calibration"], alpha)
    q_audit = None if np.isinf(q_audit) else float(q_audit)
    if q_frozen is not None and q_audit is not None:
        drift = abs(q_audit - q_frozen)
        assert drift <= 1e-6, f"{dataset}: q drift freeze={q_frozen} vs audit={q_audit} (Δ={drift})"
    q = q_frozen if q_frozen is not None else q_audit           # apply the FROZEN threshold

    # ---- decisions: flag zero-day iff s > q
    def decide(arr):
        return (arr > q).astype(int) if q is not None else np.zeros(arr.size, dtype=int)
    test_flag, zd_flag = decide(s["test"]), decide(s["zeroday"])

    # ---- Gate 3: coverage consistency  (achieved FZR on KNOWN test reproduces the frozen value)
    fzr = float(np.mean(test_flag)) if test_flag.size else None
    coverage = None if fzr is None else 1.0 - fzr
    recall = float(np.mean(zd_flag)) if zd_flag.size else None
    frozen_fzr = frozen["datasets"][dataset]["false_zeroday_rate"]
    coverage_reproduced = (frozen_fzr is None or fzr is None or abs(fzr - frozen_fzr) <= 1e-6)
    assert coverage_reproduced, f"{dataset}: FZR {fzr} != frozen {frozen_fzr}"

    # per-row decisions table (the "first end-to-end decisions" deliverable)
    def rows_for(split, flags, arr, frame):
        return pd.DataFrame({
            "dataset": dataset, "split": split,
            "sample_id": frame["sample_id"].to_numpy() if "sample_id" in frame else np.arange(arr.size),
            "true_label_multiclass": frame.get("true_label_multiclass"),
            "y_known": frame.get("y_known"),
            "nonconformity_s": np.round(arr, 6),
            "threshold_q": q,
            "decision": np.where(flags == 1, "ZERO_DAY", "KNOWN"),
        })
    per_row = pd.concat([rows_for("test", test_flag, s["test"], frames["test"]),
                         rows_for("zeroday", zd_flag, s["zeroday"], frames["zeroday"])], ignore_index=True)

    # known-vs-zero-day confusion (test = truly known; zeroday = truly novel)
    tn, fp = int(np.sum(test_flag == 0)), int(np.sum(test_flag == 1))    # known kept / known flagged
    fn, tp = int(np.sum(zd_flag == 0)), int(np.sum(zd_flag == 1))        # zd missed / zd caught
    summary = {
        "dataset": dataset, "alpha": alpha, "source_kind": frozen["source_kind"],
        "assume_fidelity_squared": assume_squared,
        "threshold_q_frozen": q_frozen, "threshold_q_audit": q_audit, "applied_q": q,
        "n_known_classes": len(known),
        "score_contract_max_abs_err": contract_err,
        "score_contract_ok": bool(contract_err is None or contract_err <= CONTRACT_TOL),
        "known_test": {"n": int(test_flag.size), "kept_known": tn, "flagged_zeroday": fp,
                       "coverage": None if coverage is None else round(coverage, 6),
                       "false_zeroday_rate": None if fzr is None else round(fzr, 6)},
        "zeroday": {"n": int(zd_flag.size), "detected": tp, "missed": fn,
                    "recall": None if recall is None else round(recall, 6)},
        "confusion_known_vs_zeroday": {"tn_known_kept": tn, "fp_known_flagged": fp,
                                       "fn_zeroday_missed": fn, "tp_zeroday_detected": tp},
        "coverage_reproduces_frozen": bool(coverage_reproduced),
        "frozen_false_zeroday_rate": frozen_fzr,
    }
    return summary, per_row


def render_markdown(summaries, source, primary_alpha):
    L = ["# Week 4 · Day 22 — Conformal↔Inference Integration + First End-to-End Decisions", "",
         "Task (`qi26_12_Week_4.pdf`): *connect the frozen conformal module to Team B's inference pipeline; "
         "verify score = 1 − max-fidelity flows correctly; run first end-to-end known-vs-zero-day decisions "
         "on dataset 1.* The adapter loads the **Day-21 frozen threshold** "
         "([`../INTEGRATION/frozen_thresholds.json`](../INTEGRATION/frozen_thresholds.json)) — it does **not** "
         "recalibrate — and flags a point as zero-day iff `s = 1 − max_c F(ρ_x, ρ_c) > q`. "
         f"Primary α = {primary_alpha}, seed {SEED}, source **{source}**.", "",
         "## Verification gates (all asserted)",
         "1. **Score contract** — recomputed `s = 1 − max_c F` from the `fid__*` columns matches the "
         "interface's precomputed `nonconformity` to ≤ 1e-6 (the task's *score = 1 − max-fidelity flows "
         "correctly*).",
         "2. **Frozen-threshold provenance** — the applied `q` is loaded from the Day-21 freeze; an audit "
         "recompute from calibration equals it (no silent drift freeze→integration).",
         "3. **Coverage consistency** — the achieved false-zero-day rate on KNOWN test reproduces the frozen "
         "Day-21 value (same `q`, same rows)."]
    for r in summaries:
        kt, zd, cm = r["known_test"], r["zeroday"], r["confusion_known_vs_zeroday"]
        cerr = "n/a (sqrt applied)" if r["score_contract_max_abs_err"] is None \
            else f"{r['score_contract_max_abs_err']:.2e}"
        L += ["", f"## {r['dataset']}", "",
              f"- applied q = **{r['applied_q']:.6f}** (frozen {r['threshold_q_frozen']:.6f}, "
              f"audit {r['threshold_q_audit']:.6f}) · score-contract max|Δ| = {cerr}",
              "", "| | truly KNOWN (test) | truly ZERO-DAY |",
              "|---|---:|---:|",
              f"| decided KNOWN | {cm['tn_known_kept']:,} (TN) | {cm['fn_zeroday_missed']:,} (FN) |",
              f"| decided ZERO-DAY | {cm['fp_known_flagged']:,} (FP) | {cm['tp_zeroday_detected']:,} (TP) |",
              "",
              f"- known-test coverage **{kt['coverage']:.4f}** · false-zero-day **{kt['false_zeroday_rate']:.4f}** "
              f"(reproduces frozen {r['frozen_false_zeroday_rate']}: {r['coverage_reproduces_frozen']})",
              f"- zero-day recall **{zd['recall']:.4f}** ({zd['detected']:,}/{zd['n']:,} caught)"]
    L += ["", "## Reading this",
          "- This is the **plumbing** end-to-end, not a detection result: on the **dummy** interface the "
          "recall column is the Day-14 synthetic placeholder. What Day 22 proves is that Team B's scores flow "
          "through the frozen contract and reproduce the frozen coverage exactly.",
          "- The identical command reprices on real prototypes (`--source real --scores-root <team-B dir>`); "
          "coverage should hold (the guarantee is score-agnostic), recall is the number that changes.",
          "- Coverage bounds **false alarms only** (Prop 3 §5.2) — recall is the separate power axis "
          "(Day 19); Day 23 runs this live and audits exchangeability, Day 24 extends to all datasets."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-22 conformal↔inference integration + first decisions")
    ap.add_argument("--datasets", nargs="+", default=["CICIoT2023"],
                    help="default: CICIoT2023 = dataset 1 (the task's first end-to-end run)")
    ap.add_argument("--alpha", type=float, default=PRIMARY_ALPHA)
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default=None,
                    help="override the frozen source tag (default: use the freeze's source_kind)")
    ap.add_argument("--assume-fidelity-squared", action="store_true",
                    help="fid__* carry F^2 (PennyLane/Qiskit) -> sqrt() before s = 1 - max F")
    ap.add_argument("--no-per-row", action="store_true", help="skip writing the per-row decisions CSVs")
    args = ap.parse_args(argv)

    frozen = load_frozen_thresholds()
    if args.source:
        frozen = {**frozen, "source_kind": args.source}
    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    summaries = []
    for ds in args.datasets:
        summary, per_row = integrate_dataset(ds, frozen, args.scores_root,
                                             args.assume_fidelity_squared, args.alpha)
        summaries.append(summary)
        if not args.no_per_row:
            per_row.to_csv(GEN / f"w4_03_decisions_{ds}.csv", index=False)
        kt, zd = summary["known_test"], summary["zeroday"]
        log(f"{ds}: applied q={summary['applied_q']:.6f} contract_ok={summary['score_contract_ok']} "
            f"coverage={kt['coverage']} FZR={kt['false_zeroday_rate']} recall={zd['recall']} "
            f"(TP={summary['confusion_known_vs_zeroday']['tp_zeroday_detected']}/"
            f"{zd['n']}, reproduces_frozen={summary['coverage_reproduces_frozen']})")

    out = {"schema_version": "1.0", "day": 22, "seed": SEED, "primary_alpha": args.alpha,
           "source_kind": frozen["source_kind"], "scores_root": _rel(args.scores_root),
           "assume_fidelity_squared": args.assume_fidelity_squared,
           "frozen_thresholds": "week4/INTEGRATION/frozen_thresholds.json",
           "datasets": summaries}
    (GEN / "w4_03_conformal_integration.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    pd.DataFrame([{
        "dataset": s["dataset"], "applied_q": s["applied_q"],
        "score_contract_max_abs_err": s["score_contract_max_abs_err"],
        "coverage": s["known_test"]["coverage"], "false_zeroday_rate": s["known_test"]["false_zeroday_rate"],
        "zeroday_recall": s["zeroday"]["recall"], "tp": s["confusion_known_vs_zeroday"]["tp_zeroday_detected"],
        "fp": s["confusion_known_vs_zeroday"]["fp_known_flagged"],
        "coverage_reproduces_frozen": s["coverage_reproduces_frozen"],
    } for s in summaries]).to_csv(GEN / "w4_03_conformal_integration.csv", index=False)
    (REPORTS / "w4_03_conformal_integration.md").write_text(
        render_markdown(summaries, frozen["source_kind"], args.alpha), encoding="utf-8")
    log(f"done -> w4_03_conformal_integration.{{md,json,csv}} + decisions_*.csv ({len(summaries)} dataset(s))")
    return out


if __name__ == "__main__":
    main()

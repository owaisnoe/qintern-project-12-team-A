#!/usr/bin/env python3
"""
Week 3 · Day 15 (Team A) — CQ-ZDR conformal calibration module (Algorithm 2).

Task (`qi26_12_week3.pdf`): *Implement Algorithm 2 (CQ-ZDR): nonconformity score s = 1 − max_c F(ρ(x), ρ_c);
threshold q = s_(k), k = ⌈(1−α)(n+1)⌉. Test Q on Team B's real prototypes for dataset 1 at α = 0.05.*
Deliverables: "Conformal calibration module" + "First threshold q (dataset 1)".

What this does
--------------
Split-conformal novelty calibration for zero-day detection. For each sample the nonconformity score is the
Algorithm-2 score  s(x) = 1 − max_c F(ρ_x, ρ_c)  (higher ⇒ lower fidelity to every known-class prototype
⇒ more novel). The threshold is the finite-sample split-conformal quantile of s over the KNOWN-class
calibration set:

    k = ⌈(1 − α)(n + 1)⌉        q = s_(k)   (the k-th smallest calibration score; +∞ if k > n)

At test time a point is flagged zero-day iff  s > q. Under exchangeability of the known-class calibration
and test points this gives a finite-sample marginal guarantee  P(false-flag) ≤ α  (Angelopoulos & Bates,
2023, Thm 1; Bates, Candès, Lei, Romano & Sesia, *Testing for Outliers with Conformal p-values*, 2023),
with 1 − α ≤ coverage ≤ 1 − α + 1/(n+1). The zero-day class is *meant* to be non-exchangeable — that is the
detection signal — so coverage is reported on the KNOWN test set and detection is reported separately on the
held-out zero-day set (a coverage curve is not a power curve).

Marginal vs Mondrian
--------------------
Default is **marginal** (one pooled threshold). Class-conditional / Mondrian thresholds are mathematically
degenerate for CIC-IoT2023: a class with fewer than ⌈1/α⌉ − 1 calibration points forces q_c = +∞ (Ding,
Angelopoulos, Bates, Jordan & Tibshirani, *Class-Conditional Conformal Prediction with Many Classes*,
NeurIPS 2023) — at α = 0.05 that floor is 19/class, and CIC has four ≤ 9-row known classes. See
`week2/reports/w2_02_split_integrity.md` §Concerns. `--mode mondrian` is provided for BoT/UNSW and ablation
only, with a per-class floor that sets sparse-class thresholds to +∞.

Input interface (Team B swaps real prototypes in at the SAME schema — no code change)
------------------------------------------------------------------------------------
`week2/interface/dummy_scores/<name>/{calibration,test,zeroday}_scores.parquet` — one row per partition row,
carrying the prototype-fidelity vector `fid__<class>` (+ a precomputed `nonconformity`, which this module
recomputes from `fid__*` as a literal check). Built by `week2/scripts/make_dummy_scores.py` (Day 14).
Point `--scores-root` at Team B's real-score directory (same schema) with `--source real` to reprice q.

NOTE on the order statistic: the Day-9 smoke test in `week2/scripts/split_integrity.py` (and
`make_dummy_scores.py`) use `np.quantile(s, ⌈(n+1)(1−α)⌉/n, method="higher")`, which returns s_(k+1) — one
order statistic higher than this module's canonical `q = s_(k)`. Both satisfy coverage ≥ 1 − α; this module
follows the task's exact `q = s_(k)` definition. `split_integrity.py` is another member's file — not edited.

Report: week3/reports/w3_01_conformal_calibration.md
JSON/CSV: week3/reports/_generated/w3_01_conformal_calibration.{json,csv}
Run (venv, after the Day-14 interface exists): python week3/scripts/conformal_calibrate.py --datasets CICIoT2023 --alpha 0.05
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
IFACE = BASE / "week2" / "interface" / "dummy_scores"
SCHEMA = BASE / "week2" / "interface" / "dummy_scores_schema.json"
GEN = BASE / "week3" / "reports" / "_generated"

SEED = 42
TRIO = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
SPLITS = ["calibration", "test", "zeroday"]
DEFAULT_ALPHA = 0.05


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ---------------------------------------------------------------------------- core conformal math

def conformal_threshold(scores, alpha):
    """Canonical split-conformal / CQ-ZDR threshold (Algorithm 2).

    k = ceil((1 - alpha) * (n + 1));  q = s_(k)  (k-th smallest calibration score, 1-indexed).
    Returns (q, k, n). If k > n (alpha too small for this n) the threshold is +inf: never flag.
    """
    s = np.sort(np.asarray(scores, dtype=float))
    n = int(s.size)
    if n == 0:
        return math.inf, 0, 0
    k = int(np.ceil((1.0 - alpha) * (n + 1)))
    q = math.inf if k > n else float(s[k - 1])
    return q, k, n


def fid_columns(df):
    return [c for c in df.columns if c.startswith("fid__")]


def nonconformity_from_fidelities(df, known):
    """Algorithm-2 score s = 1 - max_c F(rho_x, rho_c), computed directly from the fid__<class> vector."""
    cols = [f"fid__{c}" for c in known]
    return 1.0 - df[cols].to_numpy(dtype=float).max(axis=1)


# ---------------------------------------------------------------------------- io

def load_scores(dataset, scores_root):
    root = Path(scores_root) / dataset
    frames = {}
    for sp in SPLITS:
        f = root / f"{sp}_scores.parquet"
        if not f.exists():
            raise FileNotFoundError(
                f"score interface not found: {f}\n"
                f"  -> merge Iwo's Day-14 package or run: python week2/scripts/make_dummy_scores.py"
            )
        frames[sp] = pd.read_parquet(f)
    return frames


def known_classes(frames):
    """Known classes = the fid__<class> columns (one prototype per known class)."""
    return [c[len("fid__"):] for c in fid_columns(frames["calibration"])]


# ---------------------------------------------------------------------------- calibration

def _rates(s_known_test, s_zeroday, q):
    cov = float(np.mean(s_known_test <= q)) if s_known_test.size else None          # stayed inside the set
    false_zd = float(np.mean(s_known_test > q)) if s_known_test.size else None      # known flagged as novel
    rej = float(np.mean(s_zeroday > q)) if s_zeroday.size else None                 # zero-day correctly flagged
    return cov, false_zd, rej


def mondrian_thresholds(cal_df, s_cal, known, alpha, min_per_class):
    """Per-known-class thresholds q_c (diagnostic / ablation). Sparse classes (n_c < min_per_class) -> +inf.

    A class needs >= ceil(1/alpha) - 1 calibration points for a finite class-conditional quantile
    (Ding et al. 2023); below that the class-conditional threshold is degenerate.
    """
    floor = max(min_per_class, int(np.ceil(1.0 / alpha)) - 1)
    y = cal_df["true_label_multiclass"].to_numpy()
    out = {}
    for c in known:
        sc = s_cal[y == c]
        q_c, k_c, n_c = conformal_threshold(sc, alpha)
        out[c] = {"q": (None if q_c == math.inf else round(q_c, 6)), "n_cal": n_c,
                  "degenerate": (n_c < floor)}
    n_degenerate = sum(1 for v in out.values() if v["degenerate"])
    return {"floor_per_class": floor, "n_classes": len(known), "n_degenerate": n_degenerate, "per_class": out}


def calibrate_dataset(dataset, alpha, scores_root, mode="marginal", min_per_class=20, tol=1e-9):
    frames = load_scores(dataset, scores_root)
    known = known_classes(frames)

    cal, test, zd = frames["calibration"], frames["test"], frames["zeroday"]
    # calibration is KNOWN-classes-only by construction; guard it.
    if "y_known" in cal.columns:
        assert int(cal["y_known"].min()) == 1, f"{dataset}: calibration contains non-known (y_known=0) rows"

    # Algorithm-2 score from fidelities, and cross-check vs the interface's precomputed column.
    s_cal = nonconformity_from_fidelities(cal, known)
    s_test = nonconformity_from_fidelities(test, known)
    s_zd = nonconformity_from_fidelities(zd, known)
    crosscheck = None
    if "nonconformity" in cal.columns:
        crosscheck = float(np.max(np.abs(s_cal - cal["nonconformity"].to_numpy(dtype=float))))
        assert crosscheck <= 1e-6, f"{dataset}: recomputed s != interface nonconformity ({crosscheck})"

    q, k, n = conformal_threshold(s_cal, alpha)
    cov, false_zd, rej = _rates(s_test, s_zd, q)

    # per-known-class FPR on test — a DIAGNOSTIC only (marginal conformal does not guarantee per-class).
    per_class_fpr = {}
    yt = test["true_label_multiclass"].to_numpy()
    for c in known:
        m = yt == c
        if m.any():
            per_class_fpr[c] = round(float(np.mean(s_test[m] > q)), 4)

    res = {
        "dataset": dataset, "alpha": alpha, "mode": mode,
        "n_known_classes": len(known),
        "calibration_n": n, "k": k, "threshold_q": (None if q == math.inf else round(q, 6)),
        "target_coverage": round(1 - alpha, 4),
        "known_test": {"n": int(s_test.size), "coverage": None if cov is None else round(cov, 4),
                       "false_zeroday_rate": None if false_zd is None else round(false_zd, 4)},
        "zeroday": {"n": int(s_zd.size), "rejection_rate": None if rej is None else round(rej, 4),
                    "families": sorted(map(str, zd["true_label_family"].unique()))
                                if "true_label_family" in zd.columns else []},
        "coverage_ok": (None if cov is None else bool(false_zd <= alpha + 1.0 / (n + 1) + 1e-9)),
        "nonconformity_crosscheck_max_abs_err": crosscheck,
        "per_class_test_fpr_diagnostic": per_class_fpr,
    }
    if mode == "mondrian":
        res["mondrian"] = mondrian_thresholds(cal, s_cal, known, alpha, min_per_class)
    return res


def alpha_sweep(dataset, alphas, scores_root, mode="marginal"):
    """Day-16 hook: repeat calibration across a grid of alpha to build the coverage curve later."""
    rows = []
    for a in alphas:
        r = calibrate_dataset(dataset, a, scores_root, mode=mode)
        rows.append({"dataset": dataset, "alpha": a, "k": r["k"], "q": r["threshold_q"],
                     "known_coverage": r["known_test"]["coverage"],
                     "false_zeroday_rate": r["known_test"]["false_zeroday_rate"],
                     "zeroday_rejection_rate": r["zeroday"]["rejection_rate"]})
    return rows


# ---------------------------------------------------------------------------- cli

def _flat_row(r):
    return {"dataset": r["dataset"], "alpha": r["alpha"], "mode": r["mode"],
            "n_cal": r["calibration_n"], "k": r["k"], "q": r["threshold_q"],
            "target_coverage": r["target_coverage"], "known_coverage": r["known_test"]["coverage"],
            "false_zeroday_rate": r["known_test"]["false_zeroday_rate"],
            "zeroday_rejection_rate": r["zeroday"]["rejection_rate"],
            "coverage_ok": r["coverage_ok"], "source_kind": r["source_kind"]}


def main():
    ap = argparse.ArgumentParser(description="Week-3 Day-15 CQ-ZDR conformal calibration (Algorithm 2)")
    ap.add_argument("--datasets", nargs="+", default=["CICIoT2023"],
                    help="datasets to calibrate (default: CICIoT2023 = dataset 1)")
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA, help="target miscoverage (Day 15: 0.05)")
    ap.add_argument("--mode", choices=["marginal", "mondrian"], default="marginal",
                    help="marginal (default; required for CIC) or class-conditional/mondrian")
    ap.add_argument("--scores-root", default=str(IFACE),
                    help="dir of <name>/*_scores.parquet (default: Day-14 dummy interface)")
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy",
                    help="provenance tag written into outputs")
    ap.add_argument("--min-per-class", type=int, default=20, help="mondrian sparse-class floor")
    ap.add_argument("--alpha-sweep", nargs=3, type=float, metavar=("LO", "HI", "STEP"),
                    help="Day-16 hook: also write an alpha-sweep coverage table")
    ap.add_argument("--no-summary", action="store_true", help="suppress the stdout table")
    args = ap.parse_args()

    GEN.mkdir(parents=True, exist_ok=True)
    out = {"schema_version": "1.0", "day": 15, "algorithm": "CQ-ZDR (Algorithm 2)", "seed": SEED,
           "mode": args.mode, "source_kind": args.source,
           "scores_root": str(Path(args.scores_root)),
           "nonconformity_def": "s = 1 - max_c F(rho_x, rho_c)",
           "q_index_formula": "k = ceil((1-alpha)*(n+1)); q = s_(k)",
           "datasets": {}}
    for ds in args.datasets:
        r = calibrate_dataset(ds, args.alpha, args.scores_root, mode=args.mode,
                              min_per_class=args.min_per_class)
        r["source_kind"] = args.source
        out["datasets"][ds] = r
        if not args.no_summary:
            kt, zd = r["known_test"], r["zeroday"]
            log(f"{ds}  n_cal={r['calibration_n']}  k={r['k']}  q={r['threshold_q']}  "
                f"known_coverage={kt['coverage']}  false_zeroday={kt['false_zeroday_rate']}  "
                f"zeroday_rejection={zd['rejection_rate']}  (target coverage {r['target_coverage']}, "
                f"coverage_ok={r['coverage_ok']})")

    (GEN / "w3_01_conformal_calibration.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    flat = pd.DataFrame([_flat_row({**out["datasets"][d], "source_kind": args.source}) for d in args.datasets])
    flat.to_csv(GEN / "w3_01_conformal_calibration.csv", index=False)

    if args.alpha_sweep:
        lo, hi, step = args.alpha_sweep
        grid = [round(a, 4) for a in np.arange(lo, hi + 1e-9, step)]
        sweep = [row for ds in args.datasets for row in alpha_sweep(ds, grid, args.scores_root, args.mode)]
        pd.DataFrame(sweep).to_csv(GEN / "w3_01_alpha_sweep.csv", index=False)
        log(f"alpha-sweep [{lo},{hi}] step {step} -> w3_01_alpha_sweep.csv ({len(sweep)} rows)")

    log(f"done -> w3_01_conformal_calibration.json/.csv | first q ({args.datasets[0]}, {args.source}): "
        f"{out['datasets'][args.datasets[0]]['threshold_q']}")


if __name__ == "__main__":
    main()

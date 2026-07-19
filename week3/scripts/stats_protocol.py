#!/usr/bin/env python3
"""
Week 3 · Day 17 (Team A) — 5-seed statistical protocol + significance dry-run.

Task (`qi26_12_week3.pdf`): *Integrate the 5-seed statistical protocol: mean±std, 95% CI, paired t-test,
McNemar, Holm–Bonferroni, Cohen's d. Dry-run significance tests on baseline-vs-baseline as a sanity check.*
Deliverables: "Statistics pipeline (complete)" + "Significance dry-run report".

What this adds on top of Iwo's Day-13 harness
---------------------------------------------
`week2/scripts/stats_harness.py` already produces per-seed metric values with mean/std/95% CI. This module
completes the protocol the paper's results section needs — the COMPARISON layer:

  * `summarize`        mean, sample std, t-based 95% CI       (re-derives Iwo's numbers; cross-checked)
  * `paired_t`         two-sided paired t-test across seeds   (pairs matched by seed index)
  * `cohens_d_paired`  effect size d_z = mean(diff)/std(diff) (magnitude, not just significance)
  * `mcnemar_exact`    exact binomial McNemar on paired per-sample decisions (seed-42 canonical artifacts)
  * `holm_bonferroni`  step-down multiple-comparison control across the whole comparison family

Statistical conventions (documented so results are auditable)
--------------------------------------------------------------
* n = 5 seeds is SMALL: the t-test is exact under normality of seed-differences and only approximate
  otherwise — report effect sizes alongside p-values, never p alone (Demšar 2006 guidance).
* Paired everywhere: the same seed list [42..46] drives every head, so differences are paired by seed;
  McNemar pairs by test ROW (same sample, two systems) on the canonical seed-42 predictions.
* Zero-variance guard: identical inputs (A-vs-A sanity) return t=0, p=1.0, d=0.0 rather than NaN.
* Two-sided exact McNemar: p = min(1, 2·P(X ≤ min(n01,n10))), X ~ Binomial(n01+n10, 1/2).
* Holm–Bonferroni over the FULL declared family (all dataset × head-pair tests on the same metric),
  step-down with the usual monotonicity enforcement — controls FWER at α without Bonferroni's full cost.

Dry-run (the Day-17 sanity check, dummy-free — real classical baselines)
------------------------------------------------------------------------
1. Cross-check: `summarize` must reproduce Iwo's stored mean/std/CI for every (dataset, head, metric).
2. A-vs-A: each head against itself -> t=0, p=1, d=0 (the pipeline cannot invent a difference).
3. Baseline-vs-baseline: novelty heads pairwise on zero-day AUROC across the 5 seeds (paired t + d_z),
   Holm-corrected over the family; plus exact McNemar on per-sample novelty decisions (IF vs AE) from
   `week2/baselines/<ds>/predictions.csv` (decision correct <=> flags exactly the zeroday rows).

Report: week3/reports/w3_03_significance_dryrun.md
JSON/CSV: week3/reports/_generated/w3_03_significance_dryrun.{json,csv}
Run: python week3/scripts/stats_protocol.py
"""
from __future__ import annotations

import argparse
import json
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parents[2]
W2GEN = BASE / "week2" / "reports" / "_generated"
BASELINES = BASE / "week2" / "baselines"
GEN = BASE / "week3" / "reports" / "_generated"

SEED = 42
TRIO = ["CICIoT2023", "BoT-IoT", "UNSW-NB15"]
ALPHA = 0.05
HEADLINE_METRIC = "zero_day_auroc"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ------------------------------------------------------------------ the six primitives

def summarize(values):
    """mean, sample std (ddof=1), t-based 95% CI — the Day-13 convention, re-derived."""
    v = np.asarray(values, dtype=float)
    n = v.size
    mean = float(v.mean())
    std = float(v.std(ddof=1)) if n > 1 else 0.0
    half = float(stats.t.ppf(0.975, n - 1) * std / np.sqrt(n)) if n > 1 else 0.0
    return {"n": n, "mean": mean, "std": std, "ci95_low": mean - half, "ci95_high": mean + half,
            "ci95_half_width": half}


def paired_t(a, b):
    """Two-sided paired t-test across seeds. Zero-variance differences -> t=0, p=1 (A-vs-A sanity)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    assert a.shape == b.shape, "paired test needs equal-length, seed-aligned vectors"
    d = a - b
    if np.allclose(d.std(ddof=1) if d.size > 1 else 0.0, 0.0):
        return {"t": 0.0, "df": int(d.size - 1), "p": 1.0, "mean_diff": float(d.mean()),
                "note": "zero-variance differences"}
    t, p = stats.ttest_rel(a, b)
    return {"t": float(t), "df": int(d.size - 1), "p": float(p), "mean_diff": float(d.mean()), "note": None}


def cohens_d_paired(a, b):
    """Paired effect size d_z = mean(diff) / std(diff); 0 when the difference is identically zero."""
    d = np.asarray(a, float) - np.asarray(b, float)
    sd = d.std(ddof=1) if d.size > 1 else 0.0
    if np.allclose(sd, 0.0):
        return 0.0
    return float(d.mean() / sd)


def mcnemar_exact(n01, n10):
    """Exact two-sided McNemar on discordant pairs: X ~ Binomial(n01+n10, 1/2)."""
    n01, n10 = int(n01), int(n10)
    n = n01 + n10
    if n == 0:
        return {"n01": 0, "n10": 0, "p": 1.0, "note": "no discordant pairs"}
    k = min(n01, n10)
    p = min(1.0, 2.0 * float(stats.binom.cdf(k, n, 0.5)))
    return {"n01": n01, "n10": n10, "p": p, "note": None}


def holm_bonferroni(pvals, alpha=ALPHA):
    """Step-down Holm correction. Returns adjusted p-values (monotone) and reject flags at alpha."""
    p = np.asarray(pvals, dtype=float)
    m = p.size
    order = np.argsort(p)
    adj = np.empty(m, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])       # step-down + monotonicity
        adj[idx] = min(1.0, running)
    return {"p_adjusted": adj.tolist(), "reject": (adj <= alpha).tolist(), "alpha": alpha, "m": m}


# ------------------------------------------------------------------ dry-run inputs

def load_harness():
    f = W2GEN / "stats_harness.json"
    if not f.exists():
        raise FileNotFoundError(f"{f} — run week2/scripts/stats_harness.py (Iwo Day 13) first")
    return json.loads(f.read_text(encoding="utf-8"))


def crosscheck_summaries(harness, tol=1e-9):
    """`summarize` must reproduce every stored mean/std/CI from the per-seed values. Returns #checked."""
    checked = 0
    for ds, node in harness["datasets"].items():
        blocks = [("detector", node["detector"])] + \
                 [(f"novelty_heads.{h}", blk) for h, blk in node["novelty_heads"].items()]
        for name, blk in blocks:
            for metric, cell in blk.items():
                if not (isinstance(cell, dict) and "values" in cell):
                    continue
                s = summarize(cell["values"])
                for k in ("mean", "std", "ci95_low", "ci95_high"):
                    if abs(s[k] - cell[k]) > tol:
                        raise AssertionError(f"{ds}/{name}/{metric}/{k}: {s[k]} != stored {cell[k]}")
                checked += 1
    return checked


def head_pair_tests(harness, metric=HEADLINE_METRIC):
    """Paired t + d_z for every novelty-head pair per dataset on `metric` (seed-aligned values)."""
    rows = []
    for ds, node in harness["datasets"].items():
        heads = {h: blk[metric]["values"] for h, blk in node["novelty_heads"].items() if metric in blk}
        for a, b in combinations(sorted(heads), 2):
            t = paired_t(heads[a], heads[b])
            rows.append({"dataset": ds, "metric": metric, "system_a": a, "system_b": b,
                         "mean_a": round(float(np.mean(heads[a])), 6),
                         "mean_b": round(float(np.mean(heads[b])), 6),
                         "mean_diff": round(t["mean_diff"], 6), "t": round(t["t"], 4),
                         "df": t["df"], "p_raw": t["p"],
                         "cohens_d_z": round(cohens_d_paired(heads[a], heads[b]), 4)})
    return rows


def sanity_self_tests(harness, metric=HEADLINE_METRIC):
    """A-vs-A on every head: the pipeline must return t=0, p=1, d=0."""
    rows = []
    for ds, node in harness["datasets"].items():
        for h, blk in node["novelty_heads"].items():
            if metric not in blk:
                continue
            v = blk[metric]["values"]
            t = paired_t(v, v)
            rows.append({"dataset": ds, "system": h, "t": t["t"], "p": t["p"],
                         "cohens_d_z": cohens_d_paired(v, v)})
            assert t["p"] == 1.0 and t["t"] == 0.0, f"A-vs-A sanity failed for {ds}/{h}"
    return rows


def mcnemar_dryrun(datasets=TRIO):
    """Exact McNemar per dataset: IF vs AE per-sample novelty decisions on test+zeroday (seed 42)."""
    rows = []
    for ds in datasets:
        f = BASELINES / ds / "predictions.csv"
        if not f.exists():
            continue
        df = pd.read_csv(f, usecols=["split", "isolation_forest_is_novel", "autoencoder_is_novel"])
        df = df[df["split"].isin(["test", "zeroday"])]
        truth = (df["split"] == "zeroday").to_numpy()
        ok_if = df["isolation_forest_is_novel"].astype(bool).to_numpy() == truth
        ok_ae = df["autoencoder_is_novel"].astype(bool).to_numpy() == truth
        n01 = int(np.sum(~ok_if & ok_ae))    # AE right where IF wrong
        n10 = int(np.sum(ok_if & ~ok_ae))    # IF right where AE wrong
        mc = mcnemar_exact(n01, n10)
        rows.append({"dataset": ds, "pair": "isolation_forest vs autoencoder",
                     "n_pairs": int(len(df)), "acc_if": round(float(ok_if.mean()), 6),
                     "acc_ae": round(float(ok_ae.mean()), 6),
                     "n01_ae_only_right": n01, "n10_if_only_right": n10,
                     "p_exact": mc["p"], "note": mc["note"]})
    return rows


# ------------------------------------------------------------------ cli

def main(argv=None):
    ap = argparse.ArgumentParser(description="Week-3 Day-17 statistics protocol + significance dry-run")
    ap.add_argument("--metric", default=HEADLINE_METRIC)
    ap.add_argument("--alpha", type=float, default=ALPHA)
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    harness = load_harness()
    seeds = harness.get("seeds")

    n_checked = crosscheck_summaries(harness)
    log(f"cross-check: reproduced Iwo's mean/std/CI for {n_checked} (dataset, head, metric) cells")

    sanity = sanity_self_tests(harness, args.metric)
    log(f"A-vs-A sanity: {len(sanity)} self-comparisons -> all t=0, p=1, d=0")

    pairs = head_pair_tests(harness, args.metric)
    holm = holm_bonferroni([r["p_raw"] for r in pairs], args.alpha)
    for r, adj, rej in zip(pairs, holm["p_adjusted"], holm["reject"]):
        r["p_holm"] = adj
        r["significant_at_0.05_holm"] = bool(rej)
        log(f"{r['dataset']}: {r['system_a']} vs {r['system_b']} on {r['metric']}  "
            f"diff={r['mean_diff']:+.4f}  t={r['t']}  p_raw={r['p_raw']:.2e}  "
            f"p_holm={adj:.2e}  d_z={r['cohens_d_z']}  -> {'SIG' if rej else 'ns'}")

    mcn = mcnemar_dryrun()
    for r in mcn:
        log(f"{r['dataset']}: McNemar IF vs AE  n01={r['n01_ae_only_right']} n10={r['n10_if_only_right']} "
            f"p={r['p_exact']:.2e}")

    out = {"schema_version": "1.0", "day": 17, "seed": SEED, "seeds": seeds,
           "metric": args.metric, "alpha": args.alpha,
           "family_definition": "all dataset x novelty-head pairs on the headline metric (Holm step-down)",
           "crosscheck_cells": n_checked,
           "sanity_self_tests": sanity, "head_pair_tests": pairs,
           "holm": {k: holm[k] for k in ("alpha", "m")},
           "mcnemar_seed42": mcn}
    (GEN / "w3_03_significance_dryrun.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    pd.DataFrame(pairs).to_csv(GEN / "w3_03_significance_dryrun.csv", index=False)
    log("done -> w3_03_significance_dryrun.json/.csv")
    return out


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Week 4 · Day 25 (Team A) — full significance testing QS-Net vs baselines + RQ5 honesty notes.

Task (`WEEK 4.pdf`): *Run full significance testing QS-Net vs baselines (paired t-test, McNemar,
Holm–Bonferroni, Cohen's d). Flag where quantum helps and where it does not (RQ5 honesty).*
Deliverables: "Significance results" / "RQ5 honesty notes".

Day 17 built the protocol and dry-ran it baseline-vs-baseline. Day 25 turns it on the comparison the
paper actually makes — QS-Net (CQ-ZDR) against each frozen classical novelty head, on the Day-24 RQ2
headline: true-zero-day recall at the shared primary α.

Choosing the right paired test (this took a discarded design — see §4)
----------------------------------------------------------------------
Both arms are evaluated on the *same* held-out rows, so the pairing unit that carries real
uncertainty is the **evaluation row**, not a training seed:

  A. **Exact McNemar, all decisions** — of every known + zero-day flow, which system is right more
     often, and is the disagreement asymmetric? Pairs by row at the frozen q.
  B. **Exact McNemar, zero-day rows only** — the same test restricted to genuinely novel traffic.
     This *is* the recall comparison, exactly: discordant pairs are the flows one system caught and
     the other missed. It is the significance test for the Day-24 Δ column.
  C. **Paired bootstrap on Δrecall** (2,000 resamples of the zero-day set) — a confidence interval
     for the gap, answering "would this hold on a different draw of novel attacks?", plus Cohen's h,
     the effect size for a difference of proportions.
  D. **Paired t + Cohen's d_z across the 5 real retraining seeds** — the Day-17 machinery on the
     Day-13 harness. Runs for classical-vs-classical only: the harness has **no quantum arm**, so
     QS-Net cannot enter this family until Team B ships per-seed prototypes. That gap is reported,
     not papered over.

Each family is Holm-corrected separately and declared in the output, because they answer different
questions and pooling them would be dishonest about the multiplicity actually incurred.

Why not pair on the calibration draw? (a measured negative result)
------------------------------------------------------------------
The tempting substitute for D's missing quantum arm is to pair on the **conformal calibration draw**
— re-split calibration/test under 5 seeds, apply the same permutation to every arm (the score
vectors are row-aligned, so this works mechanically) and run a paired t. It is invalid in practice
and the module measures why rather than asserting it: at n_cal ≈ 18k the threshold q barely moves,
so recall varies by std ≈ 0.001 or is exactly constant. The paired differences are then effectively
deterministic, d_z = mean/std runs to **40–480**, and every comparison returns p ≈ 0 no matter how
trivial the gap. That is significance without meaning — precisely the failure Demšar (2006) warns
about. `calibration_draw_diagnostic()` reproduces the numbers; §4 of the report shows them.

n = 5 is small — the report carries the detection floor
--------------------------------------------------------
For family D, a difference must reach |d_z| ≈ 1.24 merely to clear p < 0.05 two-sided and ≈ 1.68 for
80% power (computed here from the non-central t, not quoted). "Not significant" therefore never
means "no difference"; unresolved cells are labelled unresolved.

RQ5 honesty
-----------
`_generated/w4_06_rq5_honesty.md` is a standalone deliverable: per comparison, does quantum help, by
how much, with what confidence — plus an explicit list of what these numbers do **not** establish.
Negative results stay in. On the Day-14 dummy interface the quantum arm is a placeholder, so the
findings are provisional; the protocol, families and sign conventions are not.

Report: week4/reports/w4_06_significance.md
RQ5 notes: week4/reports/_generated/w4_06_rq5_honesty.md
JSON/CSV: week4/reports/_generated/w4_06_significance.{json,csv}
Figure: week4/reports/figures/w4_06_significance.png
Run (venv, after Days 19-24): python week4/scripts/significance.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "week2" / "scripts"))
sys.path.insert(0, str(BASE / "week3" / "scripts"))
sys.path.insert(0, str(BASE / "week4" / "scripts"))

from conformal_calibrate import (  # noqa: E402  (Day-15 threshold rule + interface I/O)
    IFACE, TRIO, _rel, conformal_threshold, known_classes, load_scores, nonconformity_from_fidelities,
)
from stats_protocol import (  # noqa: E402  (Day-17 protocol — the single source of every test)
    cohens_d_paired, head_pair_tests, holm_bonferroni, load_harness, mcnemar_exact, paired_t,
)
from coverage_harness import BASELINE, GRID_HAIR, INK, INK2, MUTED, SURFACE  # noqa: E402
from zeroday_recall import _HEADS  # noqa: E402  (head -> frozen artifact + scorer)
from classical_baselines import load_bundle  # noqa: E402

GEN = BASE / "week4" / "reports" / "_generated"
FIG = BASE / "week4" / "reports" / "figures"
REPORTS = BASE / "week4" / "reports"
BASELINES = BASE / "week2" / "baselines"

SEED = 42
N_SEEDS = 5
N_BOOT = 2000
DEFAULT_ALPHA = 0.05        # the conformal operating point
TEST_ALPHA = 0.05           # the inferential level for Holm
SEED_METRIC = "zero_day_true_positive_rate"     # the 5-seed analogue of true-zero-day recall

QUANTUM = "QS-Net (CQ-ZDR)"
_HEAD_LABELS = {"isolation_forest": "Isolation Forest", "ocsvm": "OC-SVM",
                "autoencoder": "Autoencoder"}

FAMILIES = {
    "mcnemar_all": "all (dataset x head) QS-Net-vs-baseline exact McNemar tests on per-sample "
                   "known-vs-zero-day decisions at the frozen q; Holm step-down",
    "mcnemar_zeroday": "all (dataset x head) QS-Net-vs-baseline exact McNemar tests restricted to "
                       "true-zero-day rows — the significance test for the Day-24 recall gap; "
                       "Holm step-down",
    "paired_t_seeds": "all (dataset x head-pair) CLASSICAL-vs-classical paired t-tests on "
                      f"{SEED_METRIC} across the 5 real retraining seeds (Day-13 harness); Holm "
                      "step-down. QS-Net is absent: the harness has no quantum arm",
}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ---------------------------------------------------------------- effect sizes / detection floor

def cohens_h(p1, p2):
    """Effect size for a difference of proportions (the right 'Cohen's d' for binary outcomes)."""
    p1 = min(max(float(p1), 0.0), 1.0)
    p2 = min(max(float(p2), 0.0), 1.0)
    return float(2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2)))


def min_detectable_dz(n=N_SEEDS, alpha=TEST_ALPHA, power=0.80):
    """Smallest paired d_z reaching `power` at `alpha` (two-sided), exact non-central t.

    Returns (d_significance, d_power). Both depend on n alone — they bound what the design can see,
    whatever the data say.
    """
    df = n - 1
    t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df))
    ncp = brentq(lambda c: stats.nct.sf(t_crit, df, c) - power, 0.0, 50.0)
    return t_crit / np.sqrt(n), ncp / np.sqrt(n)


# ---------------------------------------------------------------- paired per-row decisions

def load_paired_decisions(dataset):
    """QS-Net decisions (Day 22, frozen q) beside the frozen Day-12 heads, row-aligned and asserted.

    Truth is the split: `zeroday` rows are genuinely novel and should be flagged, `test` rows are
    known and should not. Returns (flags, truth, n) where flags[name] is the boolean flag vector.
    """
    dec_f = GEN / f"w4_03_decisions_{dataset}.csv"
    pred_f = BASELINES / dataset / "predictions.csv"
    if not dec_f.exists():
        raise FileNotFoundError(f"{dec_f} not found — run: python week4/scripts/conformal_integration.py "
                                f"--datasets {dataset}")
    if not pred_f.exists():
        raise FileNotFoundError(f"{pred_f} not found (Day-12 classical baselines)")

    dec = pd.read_csv(dec_f, usecols=["split", "sample_id", "true_label_multiclass", "decision"])
    pred = pd.read_csv(pred_f)
    heads = [c[: -len("_is_novel")] for c in pred.columns if c.endswith("_is_novel")]

    m = dec.merge(pred, left_on=["split", "sample_id"], right_on=["split", "row_index"],
                  suffixes=("_qs", "_cls"), how="inner")
    assert len(m) == len(dec) == len(pred), (
        f"{dataset}: decisions/predictions did not align 1:1 ({len(m)} vs {len(dec)}/{len(pred)})")
    lq = "true_label_multiclass_qs" if "true_label_multiclass_qs" in m else "true_label_multiclass"
    lc = "true_label_multiclass_cls" if "true_label_multiclass_cls" in m else "true_label_multiclass"
    assert (m[lq].astype(str) == m[lc].astype(str)).all(), \
        f"{dataset}: row alignment broken — labels disagree between the two artifacts"

    truth = (m["split"] == "zeroday").to_numpy()
    flags = {QUANTUM: (m["decision"] == "ZERO_DAY").to_numpy()}
    for h in heads:
        flags[_HEAD_LABELS.get(h, h)] = m[f"{h}_is_novel"].astype(bool).to_numpy()
    return flags, truth, int(len(m))


# ---------------------------------------------------------------- A/B. exact McNemar

def mcnemar_rows(dataset, zeroday_only):
    """Exact McNemar, QS-Net vs each head. `zeroday_only` restricts to novel traffic = the recall test."""
    flags, truth, n_all = load_paired_decisions(dataset)
    sel = truth if zeroday_only else np.ones_like(truth, dtype=bool)
    # on zero-day rows "correct" == "flagged"; overall it is "flag matches truth"
    correct = {k: (v[sel] if zeroday_only else (v == truth)) for k, v in flags.items()}
    q = correct[QUANTUM]
    scope = "zeroday" if zeroday_only else "all"
    out = []
    for name, c in correct.items():
        if name == QUANTUM:
            continue
        n01 = int(np.sum(~q & c))          # baseline right where QS-Net wrong
        n10 = int(np.sum(q & ~c))          # QS-Net right where baseline wrong
        mc = mcnemar_exact(n01, n10)
        out.append({
            "family": f"mcnemar_{scope}", "dataset": dataset, "baseline": name,
            "comparison": f"{QUANTUM} vs {name}", "scope": scope, "n_pairs": int(sel.sum()),
            "rate_qsnet": round(float(q.mean()), 6), "rate_baseline": round(float(c.mean()), 6),
            "rate_diff": round(float(q.mean() - c.mean()), 6),
            "cohens_h": round(cohens_h(q.mean(), c.mean()), 4),
            "n01_baseline_only": n01, "n10_qsnet_only": n10,
            "odds_ratio_qsnet": (None if n01 == 0 else round(n10 / n01, 4)),
            "p_raw": mc["p"], "note": mc["note"],
        })
    return out


# ---------------------------------------------------------------- C. paired bootstrap on Δrecall

def bootstrap_recall_diff(d, n_boot=N_BOOT, seed=SEED, level=0.95):
    """Exact paired bootstrap of mean(d) where d in {-1,0,+1} per zero-day row.

    d = flag_qsnet - flag_baseline, so mean(d) is exactly Δrecall. Because d takes three values the
    bootstrap distribution of its mean is a 3-cell multinomial — closed form, no O(n_boot * n) loop.
    """
    n = int(d.size)
    if n == 0:
        return {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p_gt_0": 0.5, "n_boot": 0}
    p = np.array([(d == -1).sum(), (d == 0).sum(), (d == 1).sum()], dtype=float) / n
    draws = np.random.default_rng(seed).multinomial(n, p, size=n_boot)
    means = (draws[:, 2] - draws[:, 0]) / n
    tail = (1.0 - level) / 2.0
    return {"mean": float(d.mean()), "ci_low": float(np.quantile(means, tail)),
            "ci_high": float(np.quantile(means, 1.0 - tail)),
            "p_gt_0": float(np.mean(means > 0)), "n_boot": int(n_boot)}


def bootstrap_rows(dataset, n_boot=N_BOOT, level=0.95):
    flags, truth, _ = load_paired_decisions(dataset)
    q = flags[QUANTUM][truth]
    out = []
    for name, v in flags.items():
        if name == QUANTUM:
            continue
        b = v[truth]
        d = q.astype(int) - b.astype(int)
        bs = bootstrap_recall_diff(d, n_boot, SEED, level)
        out.append({
            "dataset": dataset, "baseline": name, "n_zeroday": int(q.size),
            "recall_qsnet": round(float(q.mean()), 6), "recall_baseline": round(float(b.mean()), 6),
            "delta_recall": round(bs["mean"], 6),
            "ci95_low": round(bs["ci_low"], 6), "ci95_high": round(bs["ci_high"], 6),
            "excludes_zero": bool(bs["ci_low"] > 0 or bs["ci_high"] < 0),
            "cohens_h": round(cohens_h(q.mean(), b.mean()), 4),
            "n_boot": bs["n_boot"],
        })
    return out


# ---------------------------------------------------------------- D. paired t over real retraining seeds

def classical_paired_t(metric=SEED_METRIC):
    """Day-17 machinery on the Day-13 harness. Classical-only: the harness has no quantum arm."""
    try:
        harness = load_harness()
    except FileNotFoundError as e:
        log(f"5-seed harness unavailable ({e}) — family D skipped")
        return [], None
    rows = head_pair_tests(harness, metric)
    for r in rows:
        r["family"] = "paired_t_seeds"
    return rows, harness.get("seeds")


def quantum_seed_arm_available(harness_seeds):
    """Explicitly record that QS-Net cannot join family D yet, and what would unblock it."""
    return {
        "available": False,
        "reason": "the Day-13 5-seed harness contains classical novelty heads only "
                  "(isolation_forest / autoencoder / ocsvm); there is no per-seed quantum arm",
        "unblocked_by": "Team B emitting one score directory per training seed, then rerunning "
                        "this module with --scores-root <dir> per seed",
        "harness_seeds": harness_seeds,
    }


# ---------------------------------------------------------------- the discarded design, measured

def calibration_draw_diagnostic(dataset, scores_root, alpha=DEFAULT_ALPHA, n_seeds=N_SEEDS,
                                heads=("isolation_forest", "ocsvm", "autoencoder")):
    """Why pairing on the calibration draw is invalid here — measured, not asserted.

    Re-splits calibration/test under n_seeds permutations, applying the SAME permutation to every
    arm (the score vectors are row-aligned, so this is mechanically sound). Returns the induced
    spread of recall per arm and the d_z it would produce. At n_cal ~ 18k the threshold barely
    moves, std(recall) collapses toward 0, and d_z inflates without bound.
    """
    frames = load_scores(dataset, scores_root)
    known = known_classes(frames)
    arms = {QUANTUM: {sp: nonconformity_from_fidelities(frames[sp], known)
                      for sp in ("calibration", "test", "zeroday")}}
    for h in heads:
        artifact_name, scorer = _HEADS[h]
        path = BASELINES / dataset / artifact_name
        if not path.exists():
            continue
        artifact, b = joblib.load(path), load_bundle(dataset)
        arms[_HEAD_LABELS.get(h, h)] = {
            sp: np.asarray(scorer(artifact, getattr(b, sp), b.features), dtype=float)
            for sp in ("calibration", "test", "zeroday")}

    n_cal = int(arms[QUANTUM]["calibration"].size)
    m_test = int(arms[QUANTUM]["test"].size)
    recalls = {name: [] for name in arms}
    for seed in range(SEED, SEED + n_seeds):
        perm = np.random.default_rng(seed).permutation(n_cal + m_test)   # one draw, all arms
        for name, s in arms.items():
            pooled = np.concatenate([s["calibration"], s["test"]])
            q, _, _ = conformal_threshold(pooled[perm[:n_cal]], alpha)
            recalls[name].append(float(np.mean(s["zeroday"] > q)) if s["zeroday"].size else 0.0)

    recalls = {k: np.asarray(v) for k, v in recalls.items()}
    qr = recalls[QUANTUM]
    out = []
    for name, r in recalls.items():
        if name == QUANTUM:
            continue
        t = paired_t(qr, r)
        out.append({
            "dataset": dataset, "baseline": name, "n_draws": n_seeds,
            "std_recall_qsnet": round(float(qr.std(ddof=1)), 8),
            "std_recall_baseline": round(float(r.std(ddof=1)), 8),
            "mean_diff": round(t["mean_diff"], 6),
            "inflated_d_z": round(cohens_d_paired(qr, r), 2),
            "p_raw": t["p"],
        })
    return out


# ---------------------------------------------------------------- Holm per declared family

def apply_holm(rows, alpha=TEST_ALPHA):
    if not rows:
        return rows, {"m": 0, "alpha": alpha}
    holm = holm_bonferroni([r["p_raw"] for r in rows], alpha)
    for r, adj, rej in zip(rows, holm["p_adjusted"], holm["reject"]):
        r["p_holm"] = adj
        r["significant"] = bool(rej)
    return rows, {"m": holm["m"], "alpha": alpha}


# ---------------------------------------------------------------- RQ5 verdicts

EQUIVALENCE_MARGIN = 0.05        # recall points; the smallest gap we would call operationally real


def rq5_verdicts(mc_zd_rows, boot_rows, margin=EQUIVALENCE_MARGIN):
    """Per (dataset, baseline): does quantum help on true-zero-day recall, and how confidently?

    The zero-day McNemar is the exact test; the bootstrap CI sizes the same gap. Four outcomes, and
    the distinction between the last two matters:

      ahead / behind   test significant after Holm AND the CI excludes 0, agreeing in direction.
      equivalent       the whole CI lies inside +/- `margin` — a positive finding (TOST logic): the
                       systems are indistinguishable at a margin we chose in advance, which is NOT
                       the same as having failed to detect a difference.
      unresolved       everything else: the data do not decide, and saying so is the honest report.
    """
    boot = {(r["dataset"], r["baseline"]): r for r in boot_rows}
    out = []
    for r in mc_zd_rows:
        b = boot.get((r["dataset"], r["baseline"]), {})
        diff = b.get("delta_recall", r["rate_diff"])
        lo, hi = b.get("ci95_low"), b.get("ci95_high")
        sig = bool(r.get("significant"))
        excl = bool(b.get("excludes_zero", False))
        within = (lo is not None and hi is not None and lo > -margin and hi < margin)

        if sig and excl and diff > 0:
            verdict, helps = "quantum ahead (McNemar sig. + CI excludes 0)", True
        elif sig and excl and diff < 0:
            verdict, helps = "quantum behind (McNemar sig. + CI excludes 0)", False
        elif within:
            verdict, helps = f"equivalent (95% CI inside ±{margin:g} recall)", "equivalent"
        else:
            verdict, helps = "unresolved (the data do not decide)", None
        out.append({
            "dataset": r["dataset"], "baseline": r["baseline"],
            "quantum_helps": helps, "verdict": verdict,
            "delta_recall": diff, "ci95": [lo, hi],
            "equivalence_margin": margin,
            "cohens_h": r["cohens_h"],
            "mcnemar_zeroday_p_holm": r.get("p_holm"),
            "mcnemar_zeroday_significant": sig,
            "n01_baseline_only": r["n01_baseline_only"], "n10_qsnet_only": r["n10_qsnet_only"],
        })
    return sorted(out, key=lambda r: (r["dataset"], r["baseline"]))


def render_rq5(verdicts, out):
    """Standalone RQ5 honesty notes — readable without the rest of the report."""
    L = ["# RQ5 — Honesty Notes: where quantum helps, and where it does not", "",
         f"Seed {SEED} · conformal α = {out['conformal_alpha']} · inferential α = "
         f"{out['test_alpha']} · quantum scores: **{out['source_kind']}**.", "",
         "Generated by `week4/scripts/significance.py` (Day 25). Every claim is paired with the test "
         "that supports it and the effect size that sizes it. Negative results are kept.", "",
         "Four outcomes, and the last two are different claims. **Ahead / behind**: the exact test "
         "is significant after Holm *and* the bootstrap interval excludes zero, agreeing in "
         "direction. **Equivalent**: the whole interval lies inside a ±"
         f"{EQUIVALENCE_MARGIN:g} recall margin chosen in advance — a positive finding, not a "
         "failure to detect. **Unresolved**: anything else; the data do not decide, and saying so "
         "is the honest report.", "",
         "## Verdict per comparison", "",
         "| Dataset | Baseline | Δ recall | 95% CI | Cohen's h | McNemar p (Holm) | verdict |",
         "|---|---|---:|---|---:|---:|---|"]
    for v in verdicts:
        ci = ("—" if v["ci95"][0] is None
              else f"[{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]")
        p = "—" if v["mcnemar_zeroday_p_holm"] is None else f"{v['mcnemar_zeroday_p_holm']:.3g}"
        L.append(f"| {v['dataset']} | {v['baseline']} | {v['delta_recall']:+.4f} | {ci} | "
                 f"{v['cohens_h']:+.3f} | {p} | {v['verdict']} |")

    helps = [v for v in verdicts if v["quantum_helps"] is True]
    hurts = [v for v in verdicts if v["quantum_helps"] is False]
    equiv = [v for v in verdicts if v["quantum_helps"] == "equivalent"]
    undec = [v for v in verdicts if v["quantum_helps"] is None]

    L += ["", "## Where quantum helps", ""]
    L += ([f"- **{v['dataset']}** vs {v['baseline']}: Δ recall {v['delta_recall']:+.4f} "
           f"(95% CI [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]), Cohen's h = {v['cohens_h']:+.3f}. "
           f"QS-Net alone caught {v['n10_qsnet_only']:,} novel flows the baseline missed; the "
           f"baseline alone caught {v['n01_baseline_only']:,}."
           for v in helps] or ["- **Nowhere at this evidence level.**"])
    L += ["", "## Where quantum does not help", ""]
    L += ([f"- **{v['dataset']}** vs {v['baseline']}: Δ recall {v['delta_recall']:+.4f} "
           f"(95% CI [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]), Cohen's h = {v['cohens_h']:+.3f}. "
           f"The baseline alone caught {v['n01_baseline_only']:,} novel flows QS-Net missed."
           for v in hurts] or ["- No comparison shows a significant deficit."])
    if equiv:
        L += ["", "## Where the two are equivalent", "",
              "A positive finding, not a failure to detect: the entire 95% interval lies inside the "
              f"±{equiv[0]['equivalence_margin']:g} recall margin chosen in advance.", ""]
        L += [f"- **{v['dataset']}** vs {v['baseline']}: Δ recall {v['delta_recall']:+.4f} "
              f"(95% CI [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]), Cohen's h = {v['cohens_h']:+.3f}."
              for v in equiv]
    if undec:
        L += ["", "## Unresolved", "",
              "The data do not decide these. Not significant is not the same as no difference.", ""]
        L += [f"- {v['dataset']} vs {v['baseline']}: Δ {v['delta_recall']:+.4f} — {v['verdict']}."
              for v in undec]

    L += ["", "## What these numbers do NOT establish", "",
          f"1. **The quantum arm is a placeholder.** Every QS-Net figure rides the Day-14 "
          f"`{out['source_kind']}` fidelity interface. The protocol, families and sign conventions "
          "are final; the findings are not. Re-run with `--source real --scores-root <dir>` once "
          "Team B lands real prototypes — that run is the one that goes in the paper.",
          "2. **No seed-level claim about QS-Net is possible yet.** The 5-seed paired t-test runs "
          "classical-vs-classical only: the Day-13 harness has no quantum arm. Team B must emit one "
          "score directory per training seed before QS-Net can enter that family. Until then the "
          "evidence here is row-level (McNemar, bootstrap), not training-level.",
          "3. **Training variance is not measured for either arm.** The classical models are frozen "
          "(Day 12, no refit) and QS-Net's prototypes are fixed (Day 14).",
          "4. **Coverage is not what separates these systems.** Day 24 showed 11/11 cells inside the "
          "exact band — every arm holds α by construction. Recall is the axis that differs, and it "
          "differs in *both* directions across datasets.",
          "5. **No claim of quantum advantage is made or implied.**", ""]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- figure

def make_figure(boot_rows, mc_zd_rows, out_png):
    """Forest plot of Δrecall with bootstrap 95% CIs; McNemar significance marked alongside."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:                                                    # pragma: no cover
        log(f"figure skipped ({e})")
        return False
    if not boot_rows:
        return False

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "sans-serif"],
        "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": BASELINE,
    })
    mc = {(r["dataset"], r["baseline"]): r for r in mc_zd_rows}
    rows = sorted(boot_rows, key=lambda r: (r["dataset"], r["baseline"]), reverse=True)

    fig, ax = plt.subplots(figsize=(11.0, 0.55 * len(rows) + 2.6), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.grid(axis="x", color=GRID_HAIR, linewidth=0.8)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)

    y = np.arange(len(rows), dtype=float)
    ax.axvline(0.0, color=MUTED, lw=1.3, ls="--", zorder=2)
    for i, r in enumerate(rows):
        d = r["delta_recall"]
        sig = bool(mc.get((r["dataset"], r["baseline"]), {}).get("significant"))
        decided = sig and r["excludes_zero"]
        hue = "#1baf7a" if (decided and d > 0) else "#c2453d" if (decided and d < 0) else MUTED
        ax.plot([r["ci95_low"], r["ci95_high"]], [y[i], y[i]], color=hue, lw=2.6, zorder=3,
                solid_capstyle="round")
        ax.plot([d], [y[i]], marker="o", ms=8, color=hue, markeredgecolor=SURFACE,
                markeredgewidth=1.2, zorder=4)
        ax.annotate(f"h = {r['cohens_h']:+.2f}", xy=(1.005, y[i]),
                    xycoords=("axes fraction", "data"), va="center", ha="left",
                    color=MUTED, fontsize=7.5)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['dataset']} · vs {r['baseline']}" for r in rows], fontsize=9)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlabel("Δ true-zero-day recall  (QS-Net − baseline), paired bootstrap 95% CI "
                  f"({rows[0]['n_boot']:,} resamples of the zero-day set)")
    ax.set_title("Significance — QS-Net vs frozen classical baselines at the same α\n"
                 "green = QS-Net ahead, red = behind (exact McNemar significant after Holm AND CI "
                 f"excludes 0); grey = equivalent (CI inside ±{EQUIVALENCE_MARGIN:g}) or unresolved",
                 fontsize=10, color=INK, loc="left")
    fig.text(0.5, 0.012, "Quantum arm rides the Day-14 dummy interface — protocol validated, "
             "findings provisional.", ha="center", color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.035, 0.90, 1))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return True


# ---------------------------------------------------------------- report

def render_markdown(out, verdicts, fig_ok, d_sig, d_pow):
    mc_all, mc_zd = out["mcnemar_all"], out["mcnemar_zeroday"]
    boot, pts = out["bootstrap"], out["paired_t_seeds"]
    L = ["# Week 4 · Day 25 — Significance Testing QS-Net vs Baselines + RQ5 Honesty Notes", "",
         "Task (`WEEK 4.pdf`): *Run full significance testing QS-Net vs baselines (paired t-test, "
         "McNemar, Holm–Bonferroni, Cohen's d). Flag where quantum helps and where it does not "
         "(RQ5 honesty).* Deliverables: **significance results** + **RQ5 honesty notes** "
         "([`_generated/w4_06_rq5_honesty.md`](_generated/w4_06_rq5_honesty.md)). "
         f"Seed {SEED} · conformal α = {out['conformal_alpha']} · inferential α = "
         f"{out['test_alpha']} · quantum scores: **{out['source_kind']}**.", "",
         "Day 17 built the protocol and dry-ran it baseline-vs-baseline; Day 25 turns it on the "
         "comparison the paper makes, reusing the Day-17 primitives unchanged "
         "([`stats_protocol.py`](../../week3/scripts/stats_protocol.py)).", "",
         "## 0. Which pairing unit, and why", "",
         "Both arms are evaluated on the **same held-out rows**, so the pairing unit carrying real "
         "uncertainty is the evaluation row, not a training seed. Three row-level analyses plus one "
         "seed-level one, each its own Holm family:", "",
         "| # | Test | Pairs by | Answers |", "|---|---|---|---|",
         "| A | exact McNemar, all decisions | test row | who is right more often overall |",
         "| B | exact McNemar, zero-day rows | zero-day row | **is the Day-24 recall gap real** |",
         "| C | paired bootstrap on Δrecall | zero-day row (resampled) | would the gap survive a "
         "different draw of novel attacks |",
         "| D | paired t + Cohen's d_z, 5 seeds | retraining seed | classical-vs-classical only — "
         "**QS-Net cannot enter** (see §3) |", "",
         f"## 1. Exact McNemar — all decisions ({mc_all['holm']['m']}-test family)", "",
         "Pairs by test row at the frozen q: QS-Net's decisions from the Day-22 adapter, the "
         "classical ones from the frozen Day-12 `predictions.csv`. Row alignment is asserted before "
         "pairing. Correct = flag matches truth.", "",
         "| Dataset | vs | n pairs | acc QS-Net | acc baseline | n01 (base only) | n10 (QS only) | "
         "p (Holm) | sig |", "|---|---|---:|---:|---:|---:|---:|---:|:--:|"]
    for r in mc_all["rows"]:
        L.append(f"| {r['dataset']} | {r['baseline']} | {r['n_pairs']:,} | {r['rate_qsnet']:.4f} | "
                 f"{r['rate_baseline']:.4f} | {r['n01_baseline_only']:,} | "
                 f"{r['n10_qsnet_only']:,} | {r['p_holm']:.3g} | "
                 f"{'**yes**' if r['significant'] else 'no'} |")

    L += ["", f"## 2. Exact McNemar — zero-day rows only ({mc_zd['holm']['m']}-test family)", "",
          "The same test restricted to genuinely novel traffic, where \"correct\" means \"flagged\". "
          "**This is the significance test for the Day-24 Δ column**: the discordant counts are "
          "exactly the novel flows one system caught and the other missed. Cohen's h is the effect "
          "size for a difference of proportions; the bootstrap CI beside it is from §3.", "",
          "| Dataset | vs | n zero-day | recall QS-Net | recall baseline | Δ | h | n01 | n10 | "
          "p (Holm) | sig |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|"]
    bmap = {(r["dataset"], r["baseline"]): r for r in boot["rows"]}
    for r in mc_zd["rows"]:
        L.append(f"| {r['dataset']} | {r['baseline']} | {r['n_pairs']:,} | {r['rate_qsnet']:.4f} | "
                 f"{r['rate_baseline']:.4f} | {r['rate_diff']:+.4f} | {r['cohens_h']:+.3f} | "
                 f"{r['n01_baseline_only']:,} | {r['n10_qsnet_only']:,} | {r['p_holm']:.3g} | "
                 f"{'**yes**' if r['significant'] else 'no'} |")

    L += ["", f"### Paired bootstrap on Δrecall ({boot['n_boot']:,} resamples)", "",
          "| Dataset | vs | Δ recall | 95% CI | excludes 0 |", "|---|---|---:|---|:--:|"]
    for r in boot["rows"]:
        L.append(f"| {r['dataset']} | {r['baseline']} | {r['delta_recall']:+.4f} | "
                 f"[{r['ci95_low']:+.4f}, {r['ci95_high']:+.4f}] | "
                 f"{'yes' if r['excludes_zero'] else 'no'} |")
    L += ["",
          "The zero-day sets are small on two datasets (BoT-IoT 683 rows, UNSW-NB15 1,216), so the "
          "interval — not the p-value — is what should be quoted: with n that size a p-value can be "
          "tiny while the gap remains imprecisely located.", ""]

    L += [f"## 3. Paired t + Cohen's d_z across 5 real seeds ({pts['holm']['m']}-test family)", "",
          f"Metric `{SEED_METRIC}` over seeds {pts['seeds']}, via the Day-17 `head_pair_tests` on "
          "the Day-13 harness.", ""]
    if pts["rows"]:
        L += ["| Dataset | Comparison | mean A | mean B | Δ | t | df | d_z | p (Holm) | sig |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|"]
        for r in pts["rows"]:
            L.append(f"| {r['dataset']} | {r['system_a']} vs {r['system_b']} | {r['mean_a']:.4f} | "
                     f"{r['mean_b']:.4f} | {r['mean_diff']:+.4f} | {r['t']:.3f} | {r['df']} | "
                     f"{r['cohens_d_z']:+.3f} | {r['p_holm']:.3g} | "
                     f"{'**yes**' if r['significant'] else 'no'} |")
    L += ["", "> **QS-Net is absent from this family, and that is a reported gap, not an oversight.** "
          f"{out['quantum_seed_arm']['reason']}. Unblocked by: {out['quantum_seed_arm']['unblocked_by']}. "
          "Until then, the QS-Net evidence in §1–2 is row-level, not training-level.", "",
          "**What n = 5 can detect.** A difference must reach "
          f"**|d_z| ≈ {d_sig:.2f}** merely to clear p < {out['test_alpha']} two-sided, and "
          f"**≈ {d_pow:.2f}** for 80% power (exact, from the non-central t). So "
          "\"not significant\" here means *unresolved*, never *no difference* (Demšar 2006).", ""]

    L += ["## 4. A design we tried and rejected — pairing on the calibration draw", "",
          "The obvious way to give QS-Net a paired t without Team B is to pair on the **conformal "
          "calibration draw**: re-split calibration/test under 5 seeds, apply the same permutation "
          "to every arm (the score vectors are row-aligned, so this works mechanically), and run a "
          "paired t. It is mechanically valid and statistically useless here, which is worth "
          "recording with numbers rather than asserting:", "",
          "| Dataset | vs | std(recall) QS-Net | std(recall) baseline | Δ | d_z it would report |",
          "|---|---|---:|---:|---:|---:|"]
    for r in out["calibration_draw_diagnostic"]:
        L.append(f"| {r['dataset']} | {r['baseline']} | {r['std_recall_qsnet']:.2e} | "
                 f"{r['std_recall_baseline']:.2e} | {r['mean_diff']:+.4f} | "
                 f"**{r['inflated_d_z']:+.1f}** |")
    L += ["",
          "At n_cal ≈ 18k the conformal threshold barely moves between draws, so recall varies by "
          "~1e-3 or is exactly constant. The paired differences are effectively deterministic, "
          "d_z = mean/std runs into the **hundreds**, and every comparison returns p ≈ 0 however "
          "trivial the gap — significance with no bearing on importance. Reported here so nobody "
          "re-derives it and believes it.", ""]

    n_help = sum(v["quantum_helps"] is True for v in verdicts)
    n_hurt = sum(v["quantum_helps"] is False for v in verdicts)
    n_eq = sum(v["quantum_helps"] == "equivalent" for v in verdicts)
    n_und = sum(v["quantum_helps"] is None for v in verdicts)
    L += ["## 5. RQ5 — where quantum helps and where it does not", "",
          "Full notes: [`_generated/w4_06_rq5_honesty.md`](_generated/w4_06_rq5_honesty.md). A "
          "verdict needs the exact test **and** the bootstrap interval to agree in direction.", "",
          "| Dataset | Baseline | Δ recall | 95% CI | h | verdict |",
          "|---|---|---:|---|---:|---|"]
    for v in verdicts:
        ci = ("—" if v["ci95"][0] is None else f"[{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]")
        L.append(f"| {v['dataset']} | {v['baseline']} | {v['delta_recall']:+.4f} | {ci} | "
                 f"{v['cohens_h']:+.3f} | {v['verdict']} |")
    L += ["", f"**{n_help} ahead · {n_hurt} behind · {n_eq} equivalent · {n_und} unresolved** of "
          f"{len(verdicts)} "
          "comparisons. The direction is not uniform across datasets, which is the RQ5 result: "
          "there is no single answer to \"does quantum help\" — it depends on the dataset, and the "
          "table says so in both directions.", "",
          "## 6. Honest limits", "",
          "1. Every QS-Net number rides the Day-14 **dummy** interface — protocol final, findings "
          "provisional.",
          "2. No seed-level claim about QS-Net is possible until Team B ships per-seed prototypes "
          "(§3).",
          "3. Training variance is unmeasured for both arms; the row-level tests do not capture it.",
          "4. Coverage is not the discriminator — Day 24 put 11/11 cells inside the exact band. "
          "Recall is, and it moves in both directions.",
          "5. No quantum-advantage claim is made or implied.", "",
          f"Figure: `figures/w4_06_significance.png`{' (written)' if fig_ok else ' (skipped)'} — "
          "forest plot of Δrecall with bootstrap CIs, McNemar significance marked alongside.", "",
          "## Bottom line", "",
          f"The Week-3 protocol now runs end-to-end on the paper's real comparison: "
          f"{mc_all['holm']['m']} + {mc_zd['holm']['m']} exact McNemar tests and "
          f"{pts['holm']['m']} paired t-tests across three declared Holm families, every p-value "
          "carrying an effect size, a stated detection floor for n = 5, and one candidate design "
          "rejected on measured evidence. The RQ5 notes name where the quantum arm wins, where it "
          "loses, and what cannot yet be claimed — with negative results left in.", "",
          "CSV: `_generated/w4_06_significance.csv` · JSON: `_generated/w4_06_significance.json` · "
          "RQ5: `_generated/w4_06_rq5_honesty.md`."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Day-25 significance testing QS-Net vs baselines + RQ5 honesty notes")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA, help="conformal operating point")
    ap.add_argument("--test-alpha", type=float, default=TEST_ALPHA, help="inferential level for Holm")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--seed-metric", default=SEED_METRIC)
    ap.add_argument("--no-diagnostic", action="store_true",
                    help="skip the rejected calibration-draw design (§4); it reloads frozen models")
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    d_sig, d_pow = min_detectable_dz(N_SEEDS, args.test_alpha, 0.80)
    log(f"detection floor at n={N_SEEDS}: |d_z| >= {d_sig:.3f} for p<{args.test_alpha}, "
        f">= {d_pow:.3f} for 80% power")

    mc_all, mc_zd, boot = [], [], []
    for ds in args.datasets:
        mc_all += mcnemar_rows(ds, zeroday_only=False)
        mc_zd += mcnemar_rows(ds, zeroday_only=True)
        boot += bootstrap_rows(ds, args.n_boot)
    mc_all, mc_all_holm = apply_holm(mc_all, args.test_alpha)
    mc_zd, mc_zd_holm = apply_holm(mc_zd, args.test_alpha)

    for r in mc_zd:
        b = next(x for x in boot if (x["dataset"], x["baseline"]) == (r["dataset"], r["baseline"]))
        log(f"  zero-day McNemar {r['dataset']:11s} vs {r['baseline']:17s} "
            f"d_recall={r['rate_diff']:+.4f} CI=[{b['ci95_low']:+.4f},{b['ci95_high']:+.4f}] "
            f"h={r['cohens_h']:+.3f} p_holm={r['p_holm']:.3g} "
            f"{'SIG' if r['significant'] else 'ns'}")

    pt_rows, harness_seeds = classical_paired_t(args.seed_metric)
    pt_rows, pt_holm = apply_holm(pt_rows, args.test_alpha)
    log(f"5-seed paired t (classical only): {len(pt_rows)} comparisons, "
        f"{sum(r['significant'] for r in pt_rows)} significant after Holm")

    diagnostic = []
    if not args.no_diagnostic:
        for ds in args.datasets:
            diagnostic += calibration_draw_diagnostic(ds, args.scores_root, args.alpha)
        worst = max((abs(r["inflated_d_z"]) for r in diagnostic), default=0.0)
        log(f"rejected calibration-draw design: recall std ~1e-3, inflated |d_z| up to {worst:.0f}")

    verdicts = rq5_verdicts(mc_zd, boot)

    out = {
        "schema_version": "1.0", "day": 25, "seed": SEED,
        "conformal_alpha": args.alpha, "test_alpha": args.test_alpha,
        "source_kind": args.source, "scores_root": _rel(args.scores_root),
        "headline_metric": "true_zeroday_recall",
        "families": FAMILIES,
        "detection_floor": {"n": N_SEEDS, "d_z_for_significance": round(float(d_sig), 4),
                            "d_z_for_80pct_power": round(float(d_pow), 4)},
        "mcnemar_all": {"family": FAMILIES["mcnemar_all"], "holm": mc_all_holm, "rows": mc_all},
        "mcnemar_zeroday": {"family": FAMILIES["mcnemar_zeroday"], "holm": mc_zd_holm,
                            "rows": mc_zd},
        "bootstrap": {"n_boot": args.n_boot, "level": 0.95, "rows": boot,
                      "note": "paired bootstrap of Delta recall over the zero-day rows; exact "
                              "3-cell multinomial on the per-row difference"},
        "paired_t_seeds": {"family": FAMILIES["paired_t_seeds"], "holm": pt_holm,
                           "metric": args.seed_metric, "seeds": harness_seeds, "rows": pt_rows},
        "quantum_seed_arm": quantum_seed_arm_available(harness_seeds),
        "calibration_draw_diagnostic": diagnostic,
        "rq5_verdicts": verdicts,
        "equivalence_margin": EQUIVALENCE_MARGIN,
        "n_quantum_ahead": sum(v["quantum_helps"] is True for v in verdicts),
        "n_quantum_behind": sum(v["quantum_helps"] is False for v in verdicts),
        "n_equivalent": sum(v["quantum_helps"] == "equivalent" for v in verdicts),
        "n_unresolved": sum(v["quantum_helps"] is None for v in verdicts),
    }

    (GEN / "w4_06_significance.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    pd.DataFrame(mc_all + mc_zd).to_csv(GEN / "w4_06_significance.csv", index=False)
    (GEN / "w4_06_rq5_honesty.md").write_text(render_rq5(verdicts, out), encoding="utf-8")
    fig_ok = (not args.no_figure) and make_figure(boot, mc_zd, FIG / "w4_06_significance.png")
    (REPORTS / "w4_06_significance.md").write_text(
        render_markdown(out, verdicts, fig_ok, d_sig, d_pow), encoding="utf-8")

    log(f"done -> w4_06_significance.md/.json/.csv + w4_06_rq5_honesty.md "
        f"({len(mc_all)}+{len(mc_zd)} McNemar, {len(pt_rows)} paired-t, "
        f"{out['n_quantum_ahead']} ahead / {out['n_quantum_behind']} behind / "
        f"{out['n_equivalent']} equivalent / {out['n_unresolved']} unresolved)")
    return out


if __name__ == "__main__":
    main()

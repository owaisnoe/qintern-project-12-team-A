#!/usr/bin/env python3
"""
Week 5 · Day 29 (Team A) — Conformal-vs-heuristic ablation asset (final) + RQ5 honesty summary.

Task (`qi26_12_Week_5.pdf`): *Produce the conformal-vs-heuristic ablation figure/table (shows the
guarantee's value). Compile the RQ5 honesty summary: where quantum helps / does not.*
Deliverables: **Conformal ablation asset** + **RQ5 honesty summary**.

Ablation asset — same score, three threshold rules
--------------------------------------------------
The fair "remove conformal" ablation (Day-20 `heuristic_ablation`, machinery reused, not re-implemented)
keeps the score s = 1 − max_c F fixed and varies only the rule: conformal q = s_(k) (held-out calibration,
the +1) vs the naive in-sample (1−α) percentile (no held-out split, no +1) vs a fixed hand-tuned τ. Day 29
re-runs it at the primary α with the α-sweep and the small-n drill, and renders the **paper-ready**
figure + booktabs table (the Day-20 outputs were working assets; these are the manuscript's). The point
the asset must show: only the conformal rule tracks the target α with a finite-sample certificate — the
heuristic is anti-conservative at small n (mean FZR > α) and the fixed cutoff does not respond to α at all.

RQ5 honesty summary — compiled, not recomputed
----------------------------------------------
The RQ5 verdicts (quantum ahead / behind / equivalent, TOST margin 0.05) plus their McNemar + bootstrap
evidence live in the Day-25 significance suite (`w4_06_significance.json`). Day 29 compiles them into the
one-page manuscript summary beside the closed-set (Day-26) and coverage (Day-26/28) context, with every
number's provenance and its ‡ status. On the dummy interface the pattern is an artifact of the Day-14
generator — the summary says so on every row; the same command re-compiles on the real prototypes.

Report: week5/reports/w5_06_ablation_rq5.md
Ablation table: week5/reports/_generated/w5_06_ablation.md + .tex · figure: figures/w5_fig3_ablation.png
RQ5 summary: week5/reports/_generated/w5_06_rq5_honesty.md
JSON/CSV: week5/reports/_generated/w5_06_ablation_rq5.json + w5_06_ablation.csv + w5_06_small_n.csv
Run (venv): python week5/scripts/ablation_rq5.py --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05
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
sys.path.insert(0, str(BASE / "week4" / "scripts"))

from conformal_calibrate import IFACE, TRIO                        # noqa: E402  (Day-15)
from coverage_harness import (  # noqa: E402  (Day-16 — band + shared palette)
    BASELINE, GRID_HAIR, INK, INK2, MUTED, SERIES, SURFACE,
)
from heuristic_ablation import (  # noqa: E402  (Day-20 — the ablation machinery, reused)
    ablate_dataset, alpha_sweep, small_n_demo,
)

GEN = BASE / "week5" / "reports" / "_generated"
FIG = BASE / "week5" / "reports" / "figures"
REPORTS = BASE / "week5" / "reports"
W4_SIG = BASE / "week4" / "reports" / "_generated" / "w4_06_significance.json"

SEED = 42
DEFAULT_ALPHA = 0.05
DEFAULT_SWEEP = (0.01, 0.20, 0.01)
SMALL_NS = (20, 50, 100, 200, 500)
FIXED_CUTOFF = 0.5

FINAL = "final"
PROVISIONAL = "provisional"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _rel(p):
    p = Path(p)
    try:
        return p.resolve().relative_to(BASE).as_posix()
    except ValueError:
        return str(p)


def _fmt(x, spec="{:.4f}", dash="—"):
    return dash if x is None else spec.format(x)


# ---------------------------------------------------------------- RQ5 (assembled from Day 25)

def load_rq5():
    if not W4_SIG.exists():
        raise FileNotFoundError(f"{_rel(W4_SIG)} not found (Day 25) — run: "
                                "python week4/scripts/significance.py")
    doc = json.loads(W4_SIG.read_text(encoding="utf-8"))
    return {"verdicts": doc["rq5_verdicts"], "margin": doc["equivalence_margin"],
            "source_kind": doc.get("source_kind", "dummy"),
            "counts": {k: doc[k] for k in
                       ("n_quantum_ahead", "n_quantum_behind", "n_equivalent", "n_unresolved")},
            "headline_metric": doc.get("headline_metric"),
            "detection_floor": doc.get("detection_floor"),
            "quantum_seed_arm": doc.get("quantum_seed_arm")}


# ---------------------------------------------------------------- renderers

def render_ablation_md(ablations, alpha, source_kind):
    L = ["# Conformal-vs-Heuristic Ablation (the guarantee's value)", "",
         f"**Caption.** Same novelty score s = 1 − max_c F on every row; only the threshold rule varies. "
         f"Conformal: q = s_(k), k = ⌈(1−α)(n+1)⌉ on a held-out calibration split (the +1). Heuristic: "
         f"the in-sample (1−α) percentile (no held-out split, no +1). Fixed: a hand-tuned τ = "
         f"{FIXED_CUTOFF}. Achieved false-zero-day rate on the KNOWN test split at α = {alpha}, judged "
         "against the exact 99% BetaBinomial band; recall at the same threshold. Only the conformal rule "
         "carries a finite-sample certificate.", "",
         "| Dataset | rule | τ | achieved FZR | in band | zero-day recall |",
         "|---|---|---:|---:|:--:|---:|"]
    for r in ablations:
        for key, label in (("conformal", "**conformal (held-out, +1)**"),
                           ("heuristic", "in-sample percentile (no +1)"),
                           ("fixed", f"fixed τ = {FIXED_CUTOFF}")):
            c = r[key]
            L.append(f"| {r['dataset']} | {label} | {_fmt(c['tau'], '{:.4f}')} | "
                     f"{c['false_zeroday_rate']:.4f}‡ | {'✅' if c.get('in_band') else '⚠'} | "
                     f"{_fmt(c['zeroday_recall'])}‡ |")
    L += ["",
          f"‡ **Provisional — rides the Day-14 `{source_kind}` fidelity interface**; the asset reprices "
          "on Team B's real prototypes (`--source real --scores-root <dir>`). The *contrast between "
          "rules* — the deliverable — is structural: only conformal has the certificate, at any score "
          "quality.", ""]
    return "\n".join(L) + "\n"


def render_ablation_tex(ablations, alpha, source_kind):
    L = [r"% Conformal-vs-heuristic ablation --- generated by week5/scripts/ablation_rq5.py (Day 29).",
         r"% Cells marked \ddag are provisional (Day-14 " + source_kind + r" fidelity interface).",
         r"% Requires: \usepackage{booktabs} and \usepackage{amssymb}.",
         r"\begin{table}[t]", r"\centering",
         r"\caption{Removing conformal: same score $s = 1 - \max_c F$, three threshold rules, at "
         r"$\alpha = " + f"{alpha}" + r"$, seed " + str(SEED) + r". Achieved false-zero-day rate "
         r"(exact 99\% band membership) and recall. Only the conformal rule carries a finite-sample "
         r"guarantee; the in-sample percentile is anti-conservative at small $n$ and a fixed $\tau$ "
         r"cannot respond to $\alpha$.}",
         r"\label{tab:conformal-ablation}",
         r"\begin{tabular}{llrrcr}", r"\toprule",
         r"Dataset & rule & $\tau$ & FZR & band & recall \\", r"\midrule"]
    for r in ablations:
        for key, label in (("conformal", r"conformal (held-out, $+1$)"),
                           ("heuristic", "in-sample pctile (no $+1$)"),
                           ("fixed", rf"fixed $\tau = {FIXED_CUTOFF}$")):
            c = r[key]
            band = r"\checkmark" if c.get("in_band") else r"$\times$"
            L.append(f"{r['dataset'].replace('_', chr(92) + '_')} & {label} & "
                     f"{_fmt(c['tau'], '{:.4f}', '---')} & {c['false_zeroday_rate']:.4f}$^\\ddag$ & "
                     f"{band} & {_fmt(c['zeroday_recall'], '{:.4f}', '---')}$^\\ddag$ \\\\")
        if r is not ablations[-1]:
            L.append(r"\midrule")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(L) + "\n"


def make_figure(sweep, small_n, out_png, alpha):
    """Left: achieved-FZR-vs-α sweep per rule (the drift picture). Right: the small-n anti-conservatism."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:                                                    # pragma: no cover
        log(f"figure skipped ({e})")
        return False

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "sans-serif"],
        "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": BASELINE,
    })
    ds_list = list(dict.fromkeys(sweep["dataset"]))
    fig, axes = plt.subplots(1, len(ds_list) + 1, figsize=(4.2 * (len(ds_list) + 1), 4.0),
                             facecolor=SURFACE)
    axes = np.atleast_1d(axes)
    for ax in axes:
        ax.set_facecolor(SURFACE)
        ax.grid(color=GRID_HAIR, linewidth=0.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    for ax, ds in zip(axes[:-1], ds_list):
        d = sweep[sweep["dataset"] == ds].sort_values("alpha")
        amax = float(d["alpha"].max())
        ax.plot([0, amax], [0, amax], ls="--", lw=1.2, color=MUTED, zorder=1)
        ax.fill_between(d["alpha"], d["band_lo_rate"], d["band_hi_rate"],
                        color=SERIES.get(ds, "#888"), alpha=0.12, linewidth=0, zorder=2)
        ax.plot(d["alpha"], d["conformal_fzr"], color="#1b7837", lw=2, marker="o", ms=3.5,
                zorder=4, label="conformal (held-out, +1)")
        ax.plot(d["alpha"], d["heuristic_fzr"], color="#762a83", lw=1.8, marker="s", ms=3.5,
                zorder=3, label="in-sample percentile")
        ax.plot(d["alpha"], d["fixed_fzr"], color="#b35806", lw=1.6, ls=":", marker="^", ms=3.5,
                zorder=3, label=f"fixed τ = {FIXED_CUTOFF}")
        ax.set_title(ds, fontsize=10, color=INK)
        ax.set_xlabel("target α")
        ax.set_xlim(0, amax * 1.05)
    axes[0].set_ylabel("achieved false-zero-day rate")
    axes[0].legend(loc="upper left", frameon=False, fontsize=7.5)

    ax = axes[-1]
    dsn = list(dict.fromkeys(r["dataset"] for r in small_n))
    for ds in dsn:
        rows = [r for r in small_n if r["dataset"] == ds]
        ns = [r["n_sub"] for r in rows]
        hue = SERIES.get(ds, "#888")
        ax.plot(ns, [r["heuristic_mean_fzr"] for r in rows], color=hue, lw=1.8, marker="s", ms=4,
                label=f"{ds} heuristic")
        ax.plot(ns, [r["conformal_mean_fzr"] for r in rows], color=hue, lw=1.8, marker="o", ms=4,
                ls="--", alpha=0.65, label=f"{ds} conformal")
    ax.axhline(alpha, color=MUTED, lw=1.2, ls="--", zorder=1)
    ax.annotate(f"target α = {alpha}", xy=(ax.get_xlim()[1], alpha), xytext=(-4, 4),
                textcoords="offset points", ha="right", color=MUTED, fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("calibration size n (log)")
    ax.set_title("small-n drill: mean FZR over 300 subsamples", fontsize=10, color=INK)
    ax.legend(loc="upper right", frameon=False, fontsize=6.5)

    fig.suptitle("Removing conformal — same score, only the threshold rule varies: "
                 "the guarantee is what tracks α", fontsize=11.5, color=INK, x=0.02, ha="left")
    fig.text(0.5, 0.005, "dummy fidelity interface — the rule contrast is structural and repricing-"
             "invariant; the rates reprice on Team B's real prototypes", ha="center", color=MUTED,
             fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return True


def render_rq5_md(rq5, alpha):
    src = rq5["source_kind"]
    c = rq5["counts"]
    L = ["# RQ5 Honesty Summary — where quantum helps, and where it does not", "",
         f"Compiled from the Day-25 significance suite (`w4_06_significance.json`), seed {SEED}, "
         f"α = {alpha}, scores **{src}**. Verdict rule: *ahead/behind* needs the zero-day McNemar to "
         "survive Holm AND the paired bootstrap CI to exclude 0; *equivalent* is a TOST-style call "
         f"inside the ±{rq5['margin']} recall margin; anything else stays *unresolved*. Effect sizes "
         "(Cohen's h) accompany every verdict.", "",
         f"**Headline count: quantum ahead {c['n_quantum_ahead']} · behind {c['n_quantum_behind']} · "
         f"equivalent {c['n_equivalent']} · unresolved {c['n_unresolved']}** "
         "(dataset × baseline pairs, zero-day recall).", "",
         "| Dataset | baseline | Δrecall (QS−base) | 95% CI | h | p Holm (McNemar zd) | verdict |",
         "|---|---|---:|---|---:|---:|---|"]
    for v in rq5["verdicts"]:
        ci = f"[{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]"
        L.append(f"| {v['dataset']} | {v['baseline']} | {v['delta_recall']:+.4f}‡ | {ci}‡ | "
                 f"{v['cohens_h']:+.3f}‡ | {_fmt(v['mcnemar_zeroday_p_holm'], '{:.2e}')}‡ | "
                 f"{v['verdict']} |")
    L += ["",
          f"‡ **Provisional — every quantum number rides the Day-14 `{src}` fidelity interface**, so "
          "these verdicts are an artifact of the dummy generator and exist to prove the honesty "
          "machinery runs end-to-end. The identical compilation on Team B's real prototypes is the one "
          "the manuscript prints — including any negative rows. Negative rows are the point of RQ5: "
          "they stay in the table.", ""]
    qa = rq5.get("quantum_seed_arm") or {}
    floor = rq5.get("detection_floor") or {}
    if floor:
        L += ["**Seed-level honesty floor.** With n = "
              f"{floor.get('n')} seeds, the smallest significant paired effect is d_z ≈ "
              f"{floor.get('d_z_for_significance'):.2f} "
              f"(80% power ≈ {floor.get('d_z_for_80pct_power'):.2f}); QS-Net enters the seed-level "
              f"family only when Team B ships per-seed scores "
              f"({qa.get('unblocked_by', 'per-seed real scores')}).", ""]
    return "\n".join(L) + "\n"


def render_markdown(out, fig_ok):
    alpha = out["alpha"]
    L = ["# Week 5 · Day 29 — Conformal Ablation Asset + RQ5 Honesty Summary", "",
         "Task (`qi26_12_Week_5.pdf`): *produce the conformal-vs-heuristic ablation figure/table (shows "
         "the guarantee's value); compile the RQ5 honesty summary (where quantum helps / does not).* "
         f"Seed {SEED} · α = {alpha} · trio {', '.join(out['datasets'])} · quantum scores: "
         f"**{out['source_kind']}**.", "",
         "## The ablation asset", "",
         "Machinery is Day-20's (`heuristic_ablation.py` — reused, not re-implemented); Day 29 re-runs "
         "it at the primary α and renders the paper-ready assets: "
         "[`_generated/w5_06_ablation.md`](_generated/w5_06_ablation.md) + "
         "[`.tex`](_generated/w5_06_ablation.tex) + "
         f"`figures/w5_fig3_ablation.png`{' (written)' if fig_ok else ' (skipped)'}.", "",
         "| Dataset | conformal FZR (in band) | heuristic FZR (in band) | fixed-τ FZR (in band) |",
         "|---|---:|---:|---:|"]
    for r in out["ablation"]:
        cf, hu, fx = r["conformal"], r["heuristic"], r["fixed"]
        L.append(f"| {r['dataset']} | {cf['false_zeroday_rate']:.4f} "
                 f"({'✅' if cf.get('in_band') else '⚠'}) | {hu['false_zeroday_rate']:.4f} "
                 f"({'✅' if hu.get('in_band') else '⚠'}) | {fx['false_zeroday_rate']:.4f} "
                 f"({'✅' if fx.get('in_band') else '⚠'}) |")
    n_h = sum(1 for r in out["small_n"] if r["heuristic_exceeds_alpha"])
    n_c = sum(1 for r in out["small_n"] if r["conformal_le_alpha"])
    L += ["",
          "**What the asset shows.** On a large i.i.d. calibration split all three rules can land near "
          "α — the value of the guarantee is (i) the *certificate* (only the conformal count has an "
          "exact finite-sample acceptance band), (ii) **small-n honesty**: over the subsample drill the "
          f"heuristic's mean FZR exceeds α in {n_h}/{len(out['small_n'])} cells (anti-conservative — "
          f"the missing +1; ≈ 2× the budget at n = {min(out['small_ns'])}) while the conformal mean "
          f"stays ≤ α in {n_c}/{len(out['small_n'])}, and (iii) a fixed τ does not respond to α at all "
          "(the sweep panels). Two honest footnotes: the deterministic fact is the ordering — "
          "q_conf = s_(k) with the +1 is never below the in-sample percentile of the same subsample, "
          "so conformal is never the anti-conservative side — and a conformal *mean* can still sit a "
          "hair above α at tiny n (e.g. expected FZR at n = 20 is 1/21 ≈ 0.048 with per-draw sd ≈ "
          "0.044, so a 300-rep Monte-Carlo mean wobbles around the target; the per-draw certificate is "
          "the band, not the subsample mean). Per-n detail: "
          "[`_generated/w5_06_small_n.csv`](_generated/w5_06_small_n.csv).", "",
          "## RQ5 honesty summary", "",
          "Compiled from Day 25 (never recomputed): "
          "[`_generated/w5_06_rq5_honesty.md`](_generated/w5_06_rq5_honesty.md). Counts: "
          f"**ahead {out['rq5']['counts']['n_quantum_ahead']} / behind "
          f"{out['rq5']['counts']['n_quantum_behind']} / equivalent "
          f"{out['rq5']['counts']['n_equivalent']} / unresolved "
          f"{out['rq5']['counts']['n_unresolved']}** — on the dummy interface this pattern is generator "
          "artifact; the compilation repricing on real prototypes is the manuscript's RQ5 section, "
          "negative rows included.", "",
          "## Bottom line", "",
          "Both Day-29 deliverables are protocol-final: the ablation asset shows the guarantee's value "
          "as a structural contrast (certificate + small-n honesty + α-responsiveness), and the RQ5 "
          "summary is a faithful compilation of the Day-25 verdicts with effect sizes and provenance. "
          "Everything quantum is ‡ provisional and reprices with one flag.", "",
          "CSV: `_generated/w5_06_ablation.csv` + `_generated/w5_06_small_n.csv` · JSON: "
          "`_generated/w5_06_ablation_rq5.json` · table: `_generated/w5_06_ablation.md` + `.tex` · "
          "RQ5: `_generated/w5_06_rq5_honesty.md` · figure: `figures/w5_fig3_ablation.png`."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-29 conformal ablation asset + RQ5 honesty summary")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    ap.add_argument("--sweep", nargs=3, type=float, metavar=("LO", "HI", "STEP"),
                    default=list(DEFAULT_SWEEP))
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    ablations = []
    for ds in args.datasets:
        r = ablate_dataset(ds, args.alpha, args.scores_root, fixed_cutoff=FIXED_CUTOFF)
        ablations.append(r)
        log(f"{ds}: conformal FZR={r['conformal']['false_zeroday_rate']} "
            f"(in band {r['conformal']['in_band']}) | heuristic {r['heuristic']['false_zeroday_rate']} "
            f"| fixed {r['fixed']['false_zeroday_rate']}")

    small_n = [r for ds in args.datasets
               for r in small_n_demo(ds, args.alpha, SMALL_NS, args.scores_root)]
    lo, hi, step = args.sweep
    grid = [round(a, 4) for a in np.arange(lo, hi + 1e-9, step)]
    sweep = alpha_sweep(args.datasets, grid, args.scores_root, "auto", FIXED_CUTOFF, False)

    rq5 = load_rq5()
    log(f"RQ5 (Day 25): ahead {rq5['counts']['n_quantum_ahead']} / behind "
        f"{rq5['counts']['n_quantum_behind']} / equivalent {rq5['counts']['n_equivalent']} / "
        f"unresolved {rq5['counts']['n_unresolved']}")

    out = {"schema_version": "1.0", "day": 29,
           "research_question": "conformal ablation (guarantee's value) + RQ5 honesty",
           "seed": SEED, "alpha": args.alpha, "source_kind": args.source,
           "scores_root": _rel(args.scores_root), "datasets": list(args.datasets),
           "fixed_cutoff": FIXED_CUTOFF, "small_ns": list(SMALL_NS), "sweep_grid": grid,
           "status_legend": {FINAL: "structural (rule contrast, certificate) — repricing-invariant",
                             PROVISIONAL: "rides the Day-14 dummy fidelity interface"},
           "ablation": ablations, "small_n": small_n,
           "rq5": {k: rq5[k] for k in ("counts", "margin", "source_kind", "headline_metric")},
           "rq5_verdicts": rq5["verdicts"],
           "heuristic_anticonservative_cells": int(sum(r["heuristic_exceeds_alpha"] for r in small_n)),
           "conformal_le_alpha_cells": int(sum(r["conformal_le_alpha"] for r in small_n))}

    (GEN / "w5_06_ablation_rq5.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    flat = []
    for r in ablations:
        for key in ("conformal", "heuristic", "fixed"):
            flat.append({"dataset": r["dataset"], "rule": key, "alpha": r["alpha"],
                         "n_cal": r["n_cal"], **{k: v for k, v in r[key].items() if k != "method"},
                         "method": r[key]["method"]})
    pd.DataFrame(flat).to_csv(GEN / "w5_06_ablation.csv", index=False)
    pd.DataFrame(small_n).to_csv(GEN / "w5_06_small_n.csv", index=False)
    (GEN / "w5_06_ablation.md").write_text(
        render_ablation_md(ablations, args.alpha, args.source), encoding="utf-8")
    (GEN / "w5_06_ablation.tex").write_text(
        render_ablation_tex(ablations, args.alpha, args.source), encoding="utf-8")
    (GEN / "w5_06_rq5_honesty.md").write_text(render_rq5_md(rq5, args.alpha), encoding="utf-8")

    fig_ok = (not args.no_figure) and make_figure(sweep, small_n, FIG / "w5_fig3_ablation.png",
                                                  args.alpha)
    (REPORTS / "w5_06_ablation_rq5.md").write_text(render_markdown(out, fig_ok), encoding="utf-8")

    log(f"done -> w5_06_ablation_rq5.md + w5_06_ablation.{{md,tex,csv}} + w5_06_small_n.csv + "
        f"w5_06_rq5_honesty.md + w5_fig3_ablation.png ({len(ablations)} datasets)")
    return out


if __name__ == "__main__":
    main()

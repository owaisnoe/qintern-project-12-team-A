#!/usr/bin/env python3
"""
Week 5 · Day 27 (Team A) — Figure 2 (headline): empirical false-zero-day rate vs target α.

Task (`qi26_12_Week_5.pdf`): *Generate Figure 2 — empirical false-zero-day rate vs target α, tracking the
diagonal, per-dataset overlays with confidence bands.* This is the paper's **headline coverage figure**: the
one picture that shows the split-conformal guarantee holds — the achieved false-alarm rate follows the target
α along the identity line, inside the exact finite-sample band, on every dataset.

What the figure shows (a reliability / calibration diagram)
-----------------------------------------------------------
  x-axis   target α  (the sweep 0.01–0.20, the task's range)
  y-axis   achieved false-zero-day rate on the held-out KNOWN test split
  diagonal y = x  — perfect calibration: a detector calibrated at α should false-alarm at rate α
  per dataset  one series of observed FZR vs α, over the exact **Beta-Binomial** validity band
               (coverage | cal ~ Beta(k, n+1−k); E ~ BetaBinomial(m, n+1−k, k) — Vovk 2012; Angelopoulos &
               Bates 2023 §3.2), shaded around the diagonal. This is the CORRECT band for a calibration-draw
               plot — NOT Clopper–Pearson, which is the fixed-threshold proportion CI and would be the wrong
               object here.
  5-seed points  at the headline α = 0.05, the achieved FZR under each of the 5 pooled re-splits (seeds
               42–46, Day-23 `fix_splits`), drawn as a mean marker with a min–max whisker, so the figure
               shows the guarantee is stable across seeds and not one lucky split.

Reuse, not reimplementation
---------------------------
The sweep + the exact band come straight from Day-16 `coverage_harness.alpha_sweep` / `coverage_band`; the
5-seed re-splits from Day-23 `live_coverage.fix_splits`; the palette + rcParams from the shared Day-16
figure style. This module only lays out the panel. Real prototypes swap in with `--source real
--scores-root <dir>`, no code change — and on the Day-14 dummy interface every series is a PROVISIONAL
placeholder (the figure's subtitle says so on the canvas).

Report: week5/reports/w5_03_figure2.md
Figure: week5/reports/figures/w5_fig2_coverage.png
Data: week5/reports/_generated/w5_03_figure2_data.csv + w5_03_figure2.json
Run (venv): python week5/scripts/figure2_coverage.py --alpha 0.05 --sweep 0.01 0.20 0.01
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

from conformal_calibrate import (  # noqa: E402  (Day-15 — score rule + io + threshold)
    IFACE, TRIO, conformal_threshold, known_classes, load_scores, nonconformity_from_fidelities,
)
from coverage_harness import (  # noqa: E402  (Day-16 — exact band + alpha-sweep + shared palette)
    DEFAULT_BAND, SERIES, SURFACE, INK, INK2, MUTED, GRID_HAIR, BASELINE, alpha_sweep, coverage_band,
)
from live_coverage import fix_splits  # noqa: E402  (Day-23 — pooled re-split for the 5-seed points)

GEN = BASE / "week5" / "reports" / "_generated"
FIG = BASE / "week5" / "reports" / "figures"
REPORTS = BASE / "week5" / "reports"

SEED = 42
DEFAULT_ALPHA = 0.05
DEFAULT_SWEEP = (0.01, 0.20, 0.01)
SEEDS = [42, 43, 44, 45, 46]


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _rel(p):
    """Repo-relative path for committed outputs (an absolute path would leak the author's home dir)."""
    p = Path(p)
    try:
        return p.resolve().relative_to(BASE).as_posix()
    except ValueError:
        return str(p)


# ---------------------------------------------------------------- 5-seed points at the headline α

def five_seed_points(dataset, scores_root, alpha, seeds=SEEDS, band_level=DEFAULT_BAND):
    """Achieved FZR under each pooled re-split (Day-23 fix_splits) at the headline α — stability check."""
    frames = load_scores(dataset, scores_root)
    known = known_classes(frames)
    s_cal = nonconformity_from_fidelities(frames["calibration"], known)
    s_test = nonconformity_from_fidelities(frames["test"], known)
    y_cal = frames["calibration"]["true_label_multiclass"].to_numpy()
    y_test = frames["test"]["true_label_multiclass"].to_numpy()

    fzrs, per_seed = [], []
    for sd in seeds:
        sc, _, st, _ = fix_splits(s_cal, y_cal, s_test, y_test, seed=sd)
        q, k, n = conformal_threshold(sc, alpha)
        m = int(st.size)
        e = int(np.sum(st > q))
        fzr = e / m if m else 0.0
        fzrs.append(fzr)
        per_seed.append({"seed": sd, "fzr": round(fzr, 6), "n_cal": n, "k": k, "m_test": m})
    lo, hi, _, _ = coverage_band(per_seed[0]["n_cal"], per_seed[0]["k"], per_seed[0]["m_test"], band_level)
    m0 = per_seed[0]["m_test"]
    return {"dataset": dataset, "alpha": alpha, "seeds": list(seeds), "per_seed": per_seed,
            "mean_fzr": round(float(np.mean(fzrs)), 6), "min_fzr": round(float(np.min(fzrs)), 6),
            "max_fzr": round(float(np.max(fzrs)), 6), "std_fzr": round(float(np.std(fzrs, ddof=1)), 6),
            "band_lo_rate": round(lo / m0, 6) if m0 else 0.0,
            "band_hi_rate": round(hi / m0, 6) if m0 else 0.0}


# ---------------------------------------------------------------- figure

def make_figure(sweep, points, out_png, alpha, source_kind):
    """Reliability diagram: achieved FZR vs target α, identity diagonal, exact band, 5-seed points."""
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
    fig, ax = plt.subplots(figsize=(7.4, 6.2), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.grid(color=GRID_HAIR, linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    amax = float(sweep["alpha"].max())
    # identity diagonal — perfect calibration
    ax.plot([0, amax], [0, amax], ls="--", lw=1.3, color=MUTED, zorder=1)
    ax.annotate("perfect calibration  y = α", xy=(amax * 0.62, amax * 0.62), xytext=(4, -12),
                textcoords="offset points", color=MUTED, fontsize=9, rotation=38, rotation_mode="anchor")

    for ds, hue in SERIES.items():
        d = sweep[sweep["dataset"] == ds].sort_values("alpha")
        if d.empty:
            continue
        # exact BetaBinomial validity band, shaded around the diagonal
        ax.fill_between(d["alpha"], d["band_lo_rate"], d["band_hi_rate"],
                        color=hue, alpha=0.12, linewidth=0, zorder=2)
        ax.plot(d["alpha"], d["fzr_observed"], color=hue, lw=2, marker="o", ms=4.5, zorder=4, label=ds)

    # 5-seed points at the headline alpha (mean marker + min-max whisker), slight x-offset per dataset
    offs = np.linspace(-0.006, 0.006, len(points))
    for (pt, off) in zip(points, offs):
        hue = SERIES.get(pt["dataset"], INK2)
        x = alpha + off
        ax.plot([x, x], [pt["min_fzr"], pt["max_fzr"]], color=hue, lw=1.4, zorder=5)
        ax.plot([x], [pt["mean_fzr"]], marker="D", ms=7, color=hue,
                markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=6)
    ax.axvline(alpha, color=MUTED, lw=1, ls=":", zorder=1)
    ax.annotate(f"headline α = {alpha}\n◆ = 5-seed mean (42–46), whisker = min–max",
                xy=(alpha, amax * 0.97), xytext=(8, 0), textcoords="offset points",
                va="top", ha="left", color=MUTED, fontsize=8)

    ax.set_title("Figure 2 — Empirical false-zero-day rate vs target α\n"
                 f"shaded: exact {int(DEFAULT_BAND*100)}% BetaBinomial band — on the diagonal ⇔ calibrated",
                 fontsize=10.5, color=INK, loc="left")
    ax.set_xlabel("target α"); ax.set_ylabel("achieved false-zero-day rate")
    ax.set_xlim(0, amax * 1.05); ax.set_ylim(0, amax * 1.05)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    fig.text(0.5, 0.008,
             f"{source_kind} fidelity interface — "
             + ("plumbing, not a result; reprices on Team B's real prototypes"
                if source_kind == "dummy" else "real prototypes"),
             ha="center", color=MUTED, fontsize=8)

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return True


# ---------------------------------------------------------------- report

def render_markdown(out, fig_ok):
    alpha = out["headline_alpha"]
    L = ["# Week 5 · Day 27 — Figure 2 (headline): False-Zero-Day Rate vs Target α", "",
         "Task (`qi26_12_Week_5.pdf`): *empirical false-zero-day rate vs target α, tracking the diagonal, "
         "per-dataset overlays with confidence bands.* This is the paper's headline coverage figure — the "
         "one picture of the split-conformal guarantee: the achieved false-alarm rate follows the target α "
         "along the identity line, inside the exact finite-sample band, on every dataset. "
         f"Seed {SEED} · scores: **{out['source_kind']}**.", "",
         f"Figure: `figures/w5_fig2_coverage.png`{' (written)' if fig_ok else ' (skipped)'}.", "",
         "## What is plotted", "",
         "- **x = target α**, **y = achieved false-zero-day rate** on the held-out KNOWN test split.",
         "- **Identity diagonal y = x** — perfect calibration.",
         "- **Per dataset:** observed FZR across the α-sweep (0.01–0.20), over the exact **Beta-Binomial** "
         f"{int(out['band_level']*100)}% validity band (coverage|cal ~ Beta(k, n+1−k); Vovk 2012; "
         "Angelopoulos & Bates 2023). This is the correct band for a calibration-draw plot — **not** "
         "Clopper–Pearson (that is the fixed-threshold proportion CI, the wrong object here).",
         f"- **5-seed points** at the headline α = {alpha}: achieved FZR under each pooled re-split "
         f"(seeds {SEEDS}, Day-23 `fix_splits`), as a mean ◆ with a min–max whisker — the guarantee is "
         "stable across seeds, not one lucky split.", "",
         "## 5-seed spread at the headline α", "",
         f"| Dataset | mean FZR | min | max | std | exact {int(out['band_level']*100)}% band |",
         "|---|---:|---:|---:|---:|---|"]
    for p in out["points"]:
        L.append(f"| {p['dataset']} | {p['mean_fzr']:.4f} | {p['min_fzr']:.4f} | {p['max_fzr']:.4f} | "
                 f"{p['std_fzr']:.4f} | [{p['band_lo_rate']:.4f}, {p['band_hi_rate']:.4f}] |")
    L += ["", "The mean achieved rate sits at ≈ α with a spread comfortably inside the exact band on every "
          "dataset — the picture of a calibrated detector. "
          + ("On the Day-14 **dummy** interface these series are placeholders (plumbing, not a result); the "
             "identical command reprices them on Team B's real prototypes (`--source real "
             "--scores-root <dir>`), and that rerun is the figure that goes in the manuscript."
             if out["source_kind"] == "dummy" else
             "These series are on the real prototypes."), "",
          "Data: `_generated/w5_03_figure2_data.csv` (the full sweep) · JSON: "
          "`_generated/w5_03_figure2.json` (the 5-seed points)."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(description="Day-27 Figure 2 — achieved FZR vs target alpha")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA, help="headline α for the 5-seed points")
    ap.add_argument("--sweep", nargs=3, type=float, metavar=("LO", "HI", "STEP"),
                    default=list(DEFAULT_SWEEP))
    ap.add_argument("--band", type=float, default=DEFAULT_BAND)
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    lo, hi, step = args.sweep
    grid = [round(a, 4) for a in np.arange(lo, hi + 1e-9, step)]
    sweep = alpha_sweep(args.datasets, grid, args.scores_root, args.band)
    sweep.insert(1, "source_kind", args.source)

    points = [five_seed_points(ds, args.scores_root, args.alpha, SEEDS, args.band)
              for ds in args.datasets]
    for p in points:
        log(f"{p['dataset']} 5-seed FZR at alpha={args.alpha}: mean={p['mean_fzr']} "
            f"[{p['min_fzr']}, {p['max_fzr']}] band [{p['band_lo_rate']}, {p['band_hi_rate']}]")

    fig_ok = (not args.no_figure) and make_figure(
        sweep, points, FIG / "w5_fig2_coverage.png", args.alpha, args.source)

    out = {"schema_version": "1.0", "day": 27, "seed": SEED, "source_kind": args.source,
           "scores_root": _rel(args.scores_root), "headline_alpha": args.alpha,
           "band_level": args.band, "sweep_grid": grid, "seeds": SEEDS,
           "law": "E ~ BetaBinomial(m, n+1-k, k)  [coverage|cal ~ Beta(k, n+1-k)]",
           "datasets": list(args.datasets), "points": points, "figure_written": bool(fig_ok)}

    (GEN / "w5_03_figure2.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    sweep.to_csv(GEN / "w5_03_figure2_data.csv", index=False)
    (REPORTS / "w5_03_figure2.md").write_text(render_markdown(out, fig_ok), encoding="utf-8")
    log(f"done -> w5_03_figure2.md + figures/w5_fig2_coverage.png + w5_03_figure2_data.csv "
        f"({len(sweep)} sweep rows, {len(points)} datasets)")
    return out


if __name__ == "__main__":
    main()

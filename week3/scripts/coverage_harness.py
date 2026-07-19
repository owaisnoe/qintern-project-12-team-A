#!/usr/bin/env python3
"""
Week 3 · Day 16 (Team A) — Coverage-verification harness + α-sweep (CQ-ZDR / Algorithm 2).

Task (`qi26_12_week3.pdf`): *Build the coverage-verification harness: empirical false-zero-day rate on a
held-out KNOWN set must be ≤ α. Add α-sweep (0.01–0.20) to produce the headline coverage curve later.*
Deliverables: "Coverage-verification harness" + "α-sweep scaffold".

Why a harness needs more than "FZR ≤ α"
---------------------------------------
The split-conformal guarantee is on the EXPECTATION: E[false-zero-day rate] ≤ α, marginally over the draw of
the calibration AND test sets. On any finite test set the empirical rate fluctuates around (n+1−k)/(n+1), so
a naive `fzr <= alpha` assertion randomly fails on perfectly sound systems — Day 15 already hit this: BoT-IoT
(dummy) shows FZR 0.0530 > α = 0.05 and trips the simple expectation bound, yet is statistically ordinary.
The correct check uses the exact finite-sample law (continuous scores, exchangeability):

    coverage | calibration  ~  Beta(k, n+1−k)                (Vovk 2012; Angelopoulos & Bates 2023, §3.2)
    #false-flags E on m test points  ~  BetaBinomial(m, a=n+1−k, b=k)     (Binomial mixed over the Beta)

The harness therefore reports, per (dataset, α):
  * the observed FZR and the EXACT central predictive band for it at `--band` level (default 99%),
  * a one-sided tail p-value  P(E ≥ e_obs)  under the Beta-Binomial law,
  * verdicts:  `expectation_ok`  (Day-15's fzr ≤ α + 1/(n+1), kept for continuity) and
               `finite_sample_ok` (e_obs ≤ upper band edge — the harness verdict; a FAIL means the
               guarantee is genuinely violated, not merely unlucky),
  * a `conservative_note` when e_obs sits BELOW the lower band edge (ties/discreteness or a broken
    interface make the test over-conservative — worth eyes, but not a violation).

Validity vs power (do not conflate — AK's Day-15 note)
------------------------------------------------------
The band applies to the KNOWN test set only. The zero-day set is *meant* to be non-exchangeable, so its
rejection rate is reported alongside as the POWER curve — no band, no guarantee, and on the Day-14 dummy
interface it is a synthetic placeholder (real power waits for Team B prototypes).

α-sweep scaffold (Day-16 second deliverable)
--------------------------------------------
`--sweep LO HI STEP` (default 0.01 0.20 0.01 = the task's range) repeats the full verification at each α and
writes the tidy table the Day-18 "coverage table v1" and the paper's headline coverage curve read from:
    week3/reports/_generated/w3_02_alpha_sweep.csv
plus the figure  week3/reports/figures/w3_02_coverage_curve.png  (validity panel + power panel).

Reuse, not reimplementation: the conformal math (`conformal_threshold`, score recompute, interface I/O) is
imported from AK's Day-15 `conformal_calibrate.py`; this file adds only the verification layer. Real
prototypes swap in with the same `--scores-root/--source` flags, no code change (Day-18 = `--datasets` all).

Report: week3/reports/w3_02_coverage_harness.md
JSON/CSV: week3/reports/_generated/w3_02_coverage_verification.json + w3_02_alpha_sweep.csv
Run: python week3/scripts/coverage_harness.py            (trio, α=0.05 headline + 0.01–0.20 sweep + figure)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import betaln, gammaln

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from conformal_calibrate import (  # noqa: E402  (AK's Day-15 module — single source of the conformal math)
    IFACE, TRIO, conformal_threshold, known_classes, load_scores, nonconformity_from_fidelities,
)

BASE = Path(__file__).resolve().parents[2]
GEN = BASE / "week3" / "reports" / "_generated"
FIG = BASE / "week3" / "reports" / "figures"

SEED = 42
DEFAULT_ALPHA = 0.05
DEFAULT_SWEEP = (0.01, 0.20, 0.01)
DEFAULT_BAND = 0.99
FAIL_P = 0.005                       # one-sided tail below this ⇒ genuine coverage violation


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ------------------------------------------------------------------ exact finite-sample law

def _log_binom(m, j):
    return gammaln(m + 1) - gammaln(j + 1) - gammaln(m - j + 1)


def betabinom_pmf(m, a, b):
    """Exact pmf of E ~ BetaBinomial(m, a, b) over e = 0..m (log-space, renormalised)."""
    j = np.arange(m + 1, dtype=float)
    logpmf = _log_binom(m, j) + betaln(j + a, m - j + b) - betaln(a, b)
    p = np.exp(logpmf - logpmf.max())
    return p / p.sum()


def coverage_band(n, k, m, level=DEFAULT_BAND):
    """Exact central predictive band for the number of false flags E on m known-test points.

    Under exchangeability + continuous scores:  E ~ BetaBinomial(m, a=n+1−k, b=k).
    Returns (lo, hi, mean_rate, pmf). Degenerate k > n (q = +inf): never flags, band = [0, 0].
    """
    a = n + 1 - k
    if a <= 0 or m <= 0:
        return 0, 0, 0.0, None
    pmf = betabinom_pmf(m, a, k)
    cdf = np.cumsum(pmf)
    tail = (1.0 - level) / 2.0
    lo = int(np.searchsorted(cdf, tail))
    hi = int(np.searchsorted(cdf, 1.0 - tail))
    return lo, hi, float(a / (n + 1)), pmf


def tail_p_value(pmf, e_obs):
    """One-sided P(E >= e_obs) under the exact law (None if the law is degenerate)."""
    if pmf is None:
        return None
    e = min(int(e_obs), pmf.size - 1)
    return float(pmf[e:].sum())


# ------------------------------------------------------------------ verification core

_SCORES_CACHE: dict = {}


def _scores(dataset, scores_root):
    """(s_cal, s_test, s_zd) for one dataset — cached so the 60-point sweep loads parquet once."""
    key = (dataset, str(scores_root))
    if key not in _SCORES_CACHE:
        frames = load_scores(dataset, scores_root)
        known = known_classes(frames)
        _SCORES_CACHE[key] = tuple(nonconformity_from_fidelities(frames[sp], known)
                                   for sp in ("calibration", "test", "zeroday"))
    return _SCORES_CACHE[key]


def verify_dataset(dataset, alpha, scores_root, band_level=DEFAULT_BAND):
    """Full Day-16 verification for one (dataset, α): threshold -> observed FZR -> exact-band verdict."""
    s_cal, s_test, s_zd = _scores(dataset, scores_root)

    q, k, n = conformal_threshold(s_cal, alpha)
    m = int(s_test.size)
    e_obs = int(np.sum(s_test > q))
    fzr = e_obs / m if m else 0.0

    lo, hi, fzr_expected, pmf = coverage_band(n, k, m, band_level)
    p_upper = tail_p_value(pmf, e_obs)

    expectation_ok = fzr <= alpha + 1.0 / (n + 1) + 1e-12          # Day-15 continuity bound
    finite_sample_ok = e_obs <= hi                                  # the harness verdict
    conservative = e_obs < lo                                       # below-band: over-conservative, not a FAIL

    return {
        "dataset": dataset, "alpha": alpha,
        "n_cal": n, "k": k, "q": (None if np.isinf(q) else round(float(q), 6)),
        "m_test": m, "false_flags": e_obs,
        "fzr_observed": round(fzr, 6), "fzr_expected": round(fzr_expected, 6),
        "band_level": band_level,
        "band_lo_rate": round(lo / m, 6) if m else 0.0,
        "band_hi_rate": round(hi / m, 6) if m else 0.0,
        "p_value_upper": (None if p_upper is None else round(p_upper, 6)),
        "expectation_ok": bool(expectation_ok),
        "finite_sample_ok": bool(finite_sample_ok),
        "conservative_note": bool(conservative),
        "verdict": "PASS" if finite_sample_ok else "FAIL",
        "known_coverage": round(1.0 - fzr, 6),
        "zeroday_n": int(s_zd.size),
        "zeroday_rejection_rate": round(float(np.mean(s_zd > q)), 6) if s_zd.size else None,
    }


def alpha_sweep(datasets, grid, scores_root, band_level=DEFAULT_BAND):
    rows = []
    for ds in datasets:
        for a in grid:
            rows.append(verify_dataset(ds, a, scores_root, band_level))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ figure (headline coverage curve)

# Reference dataviz palette (validated: worst adjacent CVD dE 24.2, light surface #fcfcfb).
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID_HAIR, BASELINE = "#e1e0d9", "#c3c2b7"
SERIES = {"CICIoT2023": "#2a78d6", "BoT-IoT": "#1baf7a", "UNSW-NB15": "#eda100"}  # fixed slot order


def make_figure(sweep: pd.DataFrame, out_png: Path, source_kind: str):
    """Two panels: validity (observed FZR vs α, exact band, diagonal) and power (zero-day rejection vs α)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "sans-serif"],
        "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": BASELINE,
    })
    fig, (ax_v, ax_p) = plt.subplots(1, 2, figsize=(11.5, 4.6), facecolor=SURFACE)

    for ax in (ax_v, ax_p):
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID_HAIR, linewidth=0.8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    amax = float(sweep["alpha"].max())
    ax_v.plot([0, amax], [0, amax], ls="--", lw=1.2, color=MUTED, zorder=1)
    ax_v.annotate("target  y = α", xy=(0.165, 0.150), ha="left", va="top",
                  color=MUTED, fontsize=8.5)

    for ds, hue in SERIES.items():
        d = sweep[sweep["dataset"] == ds].sort_values("alpha")
        if d.empty:
            continue
        ax_v.fill_between(d["alpha"], d["band_lo_rate"], d["band_hi_rate"],
                          color=hue, alpha=0.13, linewidth=0, zorder=2)
        ax_v.plot(d["alpha"], d["fzr_observed"], color=hue, lw=2, marker="o", ms=4.5, zorder=3)
        ax_p.plot(d["alpha"], d["zeroday_rejection_rate"], color=hue, lw=2, marker="o", ms=4.5, zorder=3)
        last = d.iloc[-1]
        ax_p.annotate(ds, xy=(last["alpha"], last["zeroday_rejection_rate"]),
                      xytext=(6, 0), textcoords="offset points",
                      va="center", color=INK2, fontsize=8.5)

    ax_v.set_title("Validity — observed false-zero-day rate on held-out KNOWN test\n"
                   f"shaded: exact {int(DEFAULT_BAND*100)}% finite-sample band (BetaBinomial)",
                   fontsize=10, color=INK, loc="left")
    ax_v.set_xlabel("target α"); ax_v.set_ylabel("false-zero-day rate")
    ax_p.set_title(f"Power — zero-day rejection rate ({source_kind} scores; no guarantee)\n"
                   "reported separately: a coverage curve is not a power curve",
                   fontsize=10, color=INK, loc="left")
    ax_p.set_xlabel("target α"); ax_p.set_ylabel("zero-day rejection rate")
    ax_p.set_ylim(-0.02, 1.02)
    for ax in (ax_v, ax_p):
        ax.set_xlim(0, amax * 1.14)
    handles = [plt.Line2D([], [], color=h, lw=2, marker="o", ms=4.5, label=d) for d, h in SERIES.items()]
    ax_v.legend(handles=handles, loc="upper left", frameon=False, fontsize=8.5)

    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150, facecolor=SURFACE)
    plt.close(fig)


# ------------------------------------------------------------------ cli

def main(argv=None):
    ap = argparse.ArgumentParser(description="Week-3 Day-16 coverage-verification harness + alpha-sweep")
    ap.add_argument("--datasets", nargs="+", default=list(TRIO))
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA, help="headline verification α (0.05)")
    ap.add_argument("--sweep", nargs=3, type=float, metavar=("LO", "HI", "STEP"),
                    default=list(DEFAULT_SWEEP), help="α-sweep grid (task range 0.01–0.20)")
    ap.add_argument("--band", type=float, default=DEFAULT_BAND, help="central band level (default 0.99)")
    ap.add_argument("--scores-root", default=str(IFACE))
    ap.add_argument("--source", choices=["dummy", "real"], default="dummy")
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args(argv)

    GEN.mkdir(parents=True, exist_ok=True)

    headline = []
    for ds in args.datasets:
        r = verify_dataset(ds, args.alpha, args.scores_root, args.band)
        r["source_kind"] = args.source
        headline.append(r)
        log(f"{ds}  alpha={args.alpha}  q={r['q']}  fzr={r['fzr_observed']} "
            f"(expected {r['fzr_expected']}, band [{r['band_lo_rate']}, {r['band_hi_rate']}])  "
            f"p_upper={r['p_value_upper']}  expectation_ok={r['expectation_ok']}  -> {r['verdict']}")

    lo, hi, step = args.sweep
    grid = [round(a, 4) for a in np.arange(lo, hi + 1e-9, step)]
    sweep = alpha_sweep(args.datasets, grid, args.scores_root, args.band)
    sweep.insert(1, "source_kind", args.source)

    n_fail = int((sweep["verdict"] == "FAIL").sum())
    log(f"alpha-sweep [{lo}, {hi}] step {step}: {len(sweep)} rows, "
        f"finite-sample verdicts: {len(sweep) - n_fail} PASS / {n_fail} FAIL")

    out = {"schema_version": "1.0", "day": 16, "seed": SEED, "source_kind": args.source,
           "scores_root": str(Path(args.scores_root)),
           "band_level": args.band, "fail_p": FAIL_P,
           "law": "E ~ BetaBinomial(m, n+1-k, k)  [coverage|cal ~ Beta(k, n+1-k); Vovk 2012, A&B 2023 s3.2]",
           "headline_alpha": args.alpha, "headline": headline,
           "sweep_grid": grid,
           "sweep_all_pass": bool(n_fail == 0)}
    (GEN / "w3_02_coverage_verification.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    sweep.to_csv(GEN / "w3_02_alpha_sweep.csv", index=False)

    if not args.no_figure:
        make_figure(sweep, FIG / "w3_02_coverage_curve.png", args.source)
        log(f"figure -> {FIG / 'w3_02_coverage_curve.png'}")
    log("done -> w3_02_coverage_verification.json + w3_02_alpha_sweep.csv")
    return out


if __name__ == "__main__":
    main()

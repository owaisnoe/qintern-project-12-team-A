# Week 5 · Day 27 — Figure 2 (headline): False-Zero-Day Rate vs Target α

Task (`qi26_12_Week_5.pdf`): *empirical false-zero-day rate vs target α, tracking the diagonal, per-dataset overlays with confidence bands.* This is the paper's headline coverage figure — the one picture of the split-conformal guarantee: the achieved false-alarm rate follows the target α along the identity line, inside the exact finite-sample band, on every dataset. Seed 42 · scores: **dummy**.

Figure: `figures/w5_fig2_coverage.png` (written).

## What is plotted

- **x = target α**, **y = achieved false-zero-day rate** on the held-out KNOWN test split.
- **Identity diagonal y = x** — perfect calibration.
- **Per dataset:** observed FZR across the α-sweep (0.01–0.20), over the exact **Beta-Binomial** 99% validity band (coverage|cal ~ Beta(k, n+1−k); Vovk 2012; Angelopoulos & Bates 2023). This is the correct band for a calibration-draw plot — **not** Clopper–Pearson (that is the fixed-threshold proportion CI, the wrong object here).
- **5-seed points** at the headline α = 0.05: achieved FZR under each pooled re-split (seeds [42, 43, 44, 45, 46], Day-23 `fix_splits`), as a mean ◆ with a min–max whisker — the guarantee is stable across seeds, not one lucky split.

## 5-seed spread at the headline α

| Dataset | mean FZR | min | max | std | exact 99% band |
|---|---:|---:|---:|---:|---|
| CICIoT2023 | 0.0517 | 0.0497 | 0.0539 | 0.0016 | [0.0443, 0.0559] |

The mean achieved rate sits at ≈ α with a spread comfortably inside the exact band on every dataset — the picture of a calibrated detector. On the Day-14 **dummy** interface these series are placeholders (plumbing, not a result); the identical command reprices them on Team B's real prototypes (`--source real --scores-root <dir>`), and that rerun is the figure that goes in the manuscript.

Data: `_generated/w5_03_figure2_data.csv` (the full sweep) · JSON: `_generated/w5_03_figure2.json` (the 5-seed points).

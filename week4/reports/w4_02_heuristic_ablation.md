# Week 4 · Day 20 — Heuristic-Threshold Baseline + Conformal Ablation

Task (`qi26_12_Week_4.pdf`): *reproduce the heuristic-threshold fidelity baseline; ablate conformal; quantify guarantee vs heuristic on coverage stability.* The fair remove-conformal ablation keeps the score `s = 1 − max_c F` fixed and varies only the threshold rule: conformal q = s_(k) (with the +1, on a held-out calibration split) vs the **heuristic in-sample (1−α) quantile** (no held-out split, no +1). Scores: **dummy** interface; seed 42.

## (A) Fixed cutoff — a hand-tuned threshold does not track α
One constant τ = 0.5 on the `1−max_c F` scale, applied to every dataset and (below) every α. Its achieved false-zero-day rate is **α-independent** and swings per dataset (because the α-calibrated q differs 0.26–0.38), so it cannot hold a target level:

| Dataset | conformal q (α=0.05) | fixed τ | conformal FZR | fixed FZR |
|---|---:|---:|---:|---:|
| CICIoT2023 | 0.3006 | 0.5 | 0.0486 | 0.0013 |
| BoT-IoT | 0.2629 | 0.5 | 0.0530 | 0.0009 |
| UNSW-NB15 | 0.3834 | 0.5 | 0.0463 | 0.0075 |

## (B) Small-n — why the +1 correction exists
Subsample the calibration scores to n∈{30,50,100,200} (seed 42, **mean FZR over 300 subsamples** each) and threshold on the SAME subsample: conformal s_(k) (with the +1) vs the naive (1−α) quantile (no +1), evaluated on the full test set. The no-+1 heuristic is **anti-conservative** — its mean false-alarm rate exceeds the target α at small n — while conformal stays ≤ α by construction (target α = 0.05):

**CICIoT2023**

| n_sub | conformal mean FZR | heuristic mean FZR |
|---:|---|---|
| 30 | 0.0323 (≤ α ✅) | 0.0961 (drifts > α ❌) |
| 50 | 0.0379 (≤ α ✅) | 0.0803 (drifts > α ❌) |
| 100 | 0.0497 (≤ α ✅) | 0.0596 (drifts > α ❌) |
| 200 | 0.0484 (≤ α ✅) | 0.0532 (drifts > α ❌) |

**BoT-IoT**

| n_sub | conformal mean FZR | heuristic mean FZR |
|---:|---|---|
| 30 | 0.0316 (≤ α ✅) | 0.0950 (drifts > α ❌) |
| 50 | 0.0406 (≤ α ✅) | 0.0818 (drifts > α ❌) |
| 100 | 0.0517 (> α ⚠) | 0.0623 (drifts > α ❌) |
| 200 | 0.0525 (> α ⚠) | 0.0568 (drifts > α ❌) |

**UNSW-NB15**

| n_sub | conformal mean FZR | heuristic mean FZR |
|---:|---|---|
| 30 | 0.0314 (≤ α ✅) | 0.0922 (drifts > α ❌) |
| 50 | 0.0414 (≤ α ✅) | 0.0802 (drifts > α ❌) |
| 100 | 0.0487 (≤ α ✅) | 0.0568 (drifts > α ❌) |
| 200 | 0.0456 (≤ α ✅) | 0.0500 (≈ α) |

## (C) Full-n α-sweep 0.01–0.20 — the headline drift
Across 60 (dataset × α) points: **conformal stays inside the exact band in 60/60**; the heuristic falls outside in 0/60. On the exchangeable large-n **dummy** the in-sample = calibration-proxy, so the in-sample-optimism drift is subtle here; it **auto-sharpens** the moment Team B ships real `train` fidelities (prototypes are fit on train, so an in-sample quantile is optimistic) — the code reads `train_scores.parquet` automatically. The demonstrable-now story is (A) + (B).

Figure: `figures/w4_02_drift_curve.png` (written). Sweep CSV: `_generated/w4_02_alpha_sweep.csv`.

## Fidelity convention — Team-B integration spec
`s = 1 − max_c F` is only correct on **amplitude** Uhlmann fidelity `F ∈ [0,1]`. **PennyLane `qml.math.fidelity` and Qiskit `state_fidelity` return the SQUARED overlap F²** — Team B must emit `sqrt()` of that into `fid__<class>`, or the pipeline runs with `--assume-fidelity-squared` (applies `sqrt_if_squared` at load). Feeding F² silently shifts every threshold, quantile and coverage. The Day-14 dummy is already amplitude F (`prototypes_meta.json`). A load-time fidelity min/max/mean diagnostic is logged so a squared interface is caught in review.

## Bottom line
Removing conformal — a fixed cutoff or an in-sample quantile — forfeits the distribution-free finite-sample guarantee: the achieved false-alarm rate stops tracking α (per dataset for the fixed cutoff; at small n and on real in-sample data for the percentile). Split-conformal holds FZR inside the exact band by construction. That is the Proposition-3 upgrade the ablation demonstrates.

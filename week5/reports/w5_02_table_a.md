# Week 5 · Day 26 — Table A (In-Distribution Detection, RQ1) + Significance + Coverage

Task (`qi26_12_Week_5.pdf`): *finalise Table A (in-distribution detection) with significance markers and an all-seed coverage check.* Seed 42 · α = 0.05 · trio CICIoT2023 · quantum scores: **dummy**.

Table A is the closed-set complement to Table B's zero-day guarantee: how well each system classifies KNOWN traffic (RQ1). XGBoost is real and final; QS-Net rides the Day-14 dummy interface and is provisional. Rendered standalone for the manuscript in [`_generated/w5_02_table_a.md`](_generated/w5_02_table_a.md) + [`.tex`](_generated/w5_02_table_a.tex). Reproduced here:

| Dataset | System | scores | accuracy | macro-F1 | OVR-AUROC | McNemar vs XGBoost (p Holm) |
|---|---|---|---:|---:|---:|---:|
| CICIoT2023 | XGBoost (detector) | real | 0.9896 | 0.8043 | 0.9990 | — (reference) |
| CICIoT2023 | QS-Net (CQ-ZDR) | dummy | 0.9034*‡ | 0.6598‡ | 0.9438‡ | 0.00e+00‡ |

‡ provisional (Day-14 **dummy** fidelity interface); `*` = McNemar significant at α = 0.05 after Holm. 

## Which cells are already final

| Column | Status | Why |
|---|---|---|
| XGBoost accuracy / macro-F1 / OVR-AUROC | **final** | real frozen Day-12 detector on real features (read from `results.json`, never recomputed) |
| QS-Net accuracy / macro-F1 / OVR-AUROC | provisional | Day-14 dummy fidelity interface |
| McNemar QS-Net vs XGBoost | provisional | one arm is the dummy interface |

## All-seed coverage check

The split-conformal guarantee is marginal over the calibration/test draw, so it must hold across seeds, not one split. Pooled KNOWN calibration ∪ test re-drawn at the original sizes under seeds [42, 43, 44, 45, 46] (Day-23 `fix_splits`); each re-split's achieved false-zero-day rate judged against its own exact 99% BetaBinomial band (Day-16).

| Dataset | mean FZR (5 seeds) | max FZR | in band | target α |
|---|---:|---:|:--:|---:|
| CICIoT2023 | 0.0517 | 0.0539 | 5/5 | 0.05 |

**1/1 datasets hold the exact band on all 5 seeds** — the conformal false-alarm control is stable across the 5-seed convention, not an artifact of one split.

## Per-class achieved-FZR diagnostic

Marginal conformal controls the false-alarm rate over the KNOWN **mixture**; it gives **no per-class guarantee**. (This is the precise answer to the concern that class imbalance might undermine the threshold: rare classes contribute few pooled points and do **not** skew the marginal q — the mixture guarantee holds — but an individual class can still be under- or over-covered.) Each known class's test flag count is judged against **its own** exact band `coverage_band(n_cal, k, m_c)`.

| Dataset | classes | classes out of their own band | conditional floor ⌈1/α⌉−1 | note |
|---|---:|---:|---:|---|
| CICIoT2023 | 31 | 0 | 19 | all classes inside their own band |

Per-class detail (every class, its m_test, achieved FZR, own band, and in-band verdict) is in [`_generated/w5_02_per_class_fzr.csv`](_generated/w5_02_per_class_fzr.csv). Where a class falls outside its band, the fix is **clustered conformal** (Ding et al. 2023) — grouping the rare classes into a few clusters with enough calibration mass each — **not** fully class-conditional conformal, since several classes sit far below the ⌈1/α⌉−1 floor (19 at α = 0.05) needed for a finite class-conditional quantile.

## Bottom line

Table A's structure, provenance split, significance convention (McNemar + Holm), and the two coverage diagnostics are final and publishable; the QS-Net cells and the McNemar comparing them to the real detector reprice on Team B's real prototypes, and that rerun is the one that goes in the manuscript.

CSV: `_generated/w5_02_table_a.csv` · per-class: `_generated/w5_02_per_class_fzr.csv` · JSON: `_generated/w5_02_table_a.json` · Table A: `_generated/w5_02_table_a.md` + `.tex`.

# Week 4 · Day 25 — Significance Testing QS-Net vs Baselines + RQ5 Honesty Notes

Task (`WEEK 4.pdf`): *Run full significance testing QS-Net vs baselines (paired t-test, McNemar, Holm–Bonferroni, Cohen's d). Flag where quantum helps and where it does not (RQ5 honesty).* Deliverables: **significance results** + **RQ5 honesty notes** ([`_generated/w4_06_rq5_honesty.md`](_generated/w4_06_rq5_honesty.md)). Seed 42 · conformal α = 0.05 · inferential α = 0.05 · quantum scores: **dummy**.

Day 17 built the protocol and dry-ran it baseline-vs-baseline; Day 25 turns it on the comparison the paper makes, reusing the Day-17 primitives unchanged ([`stats_protocol.py`](../../week3/scripts/stats_protocol.py)).

## 0. Which pairing unit, and why

Both arms are evaluated on the **same held-out rows**, so the pairing unit carrying real uncertainty is the evaluation row, not a training seed. Three row-level analyses plus one seed-level one, each its own Holm family:

| # | Test | Pairs by | Answers |
|---|---|---|---|
| A | exact McNemar, all decisions | test row | who is right more often overall |
| B | exact McNemar, zero-day rows | zero-day row | **is the Day-24 recall gap real** |
| C | paired bootstrap on Δrecall | zero-day row (resampled) | would the gap survive a different draw of novel attacks |
| D | paired t + Cohen's d_z, 5 seeds | retraining seed | classical-vs-classical only — **QS-Net cannot enter** (see §3) |

## 1. Exact McNemar — all decisions (8-test family)

Pairs by test row at the frozen q: QS-Net's decisions from the Day-22 adapter, the classical ones from the frozen Day-12 `predictions.csv`. Row alignment is asserted before pairing. Correct = flag matches truth.

| Dataset | vs | n pairs | acc QS-Net | acc baseline | n01 (base only) | n10 (QS only) | p (Holm) | sig |
|---|---|---:|---:|---:|---:|---:|---:|:--:|
| CICIoT2023 | Isolation Forest | 29,867 | 0.9692 | 0.9359 | 823 | 1,816 | 2.08e-84 | **yes** |
| CICIoT2023 | Autoencoder | 29,867 | 0.9692 | 0.8113 | 831 | 5,548 | 0 | **yes** |
| BoT-IoT | Isolation Forest | 19,274 | 0.9168 | 0.8958 | 1,323 | 1,727 | 5.44e-13 | **yes** |
| BoT-IoT | Autoencoder | 19,274 | 0.9168 | 0.8934 | 1,263 | 1,714 | 4.26e-16 | **yes** |
| BoT-IoT | OC-SVM | 19,274 | 0.9168 | 0.8969 | 1,345 | 1,729 | 4.62e-12 | **yes** |
| UNSW-NB15 | Isolation Forest | 11,302 | 0.8926 | 0.8109 | 470 | 1,393 | 5.8e-105 | **yes** |
| UNSW-NB15 | Autoencoder | 11,302 | 0.8926 | 0.8299 | 607 | 1,315 | 2.98e-59 | **yes** |
| UNSW-NB15 | OC-SVM | 11,302 | 0.8926 | 0.8038 | 449 | 1,452 | 4.93e-122 | **yes** |

## 2. Exact McNemar — zero-day rows only (8-test family)

The same test restricted to genuinely novel traffic, where "correct" means "flagged". **This is the significance test for the Day-24 Δ column**: the discordant counts are exactly the novel flows one system caught and the other missed. Cohen's h is the effect size for a difference of proportions; the bootstrap CI beside it is from §3.

| Dataset | vs | n zero-day | recall QS-Net | recall baseline | Δ | h | n01 | n10 | p (Holm) | sig |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| CICIoT2023 | Isolation Forest | 10,984 | 0.9998 | 0.9998 | +0.0000 | +0.000 | 2 | 2 | 1 | no |
| CICIoT2023 | Autoencoder | 10,984 | 0.9998 | 0.6611 | +0.3388 | +1.216 | 1 | 3,722 | 0 | **yes** |
| BoT-IoT | Isolation Forest | 683 | 0.0952 | 0.7233 | -0.6281 | -1.407 | 448 | 19 | 9.72e-107 | **yes** |
| BoT-IoT | Autoencoder | 683 | 0.0952 | 0.6252 | -0.5300 | -1.197 | 386 | 24 | 1.33e-84 | **yes** |
| BoT-IoT | OC-SVM | 683 | 0.0952 | 0.7335 | -0.6384 | -1.429 | 455 | 19 | 1.18e-108 | **yes** |
| UNSW-NB15 | Isolation Forest | 1,216 | 0.3857 | 0.0666 | +0.3191 | +0.818 | 50 | 438 | 5.45e-78 | **yes** |
| UNSW-NB15 | Autoencoder | 1,216 | 0.3857 | 0.2681 | +0.1176 | +0.252 | 187 | 330 | 6.58e-10 | **yes** |
| UNSW-NB15 | OC-SVM | 1,216 | 0.3857 | 0.0387 | +0.3470 | +0.944 | 22 | 444 | 1.5e-102 | **yes** |

### Paired bootstrap on Δrecall (2,000 resamples)

| Dataset | vs | Δ recall | 95% CI | excludes 0 |
|---|---|---:|---|:--:|
| CICIoT2023 | Isolation Forest | +0.0000 | [-0.0004, +0.0004] | no |
| CICIoT2023 | Autoencoder | +0.3388 | [+0.3298, +0.3476] | yes |
| BoT-IoT | Isolation Forest | -0.6281 | [-0.6706, -0.5886] | yes |
| BoT-IoT | Autoencoder | -0.5300 | [-0.5710, -0.4876] | yes |
| BoT-IoT | OC-SVM | -0.6384 | [-0.6779, -0.5988] | yes |
| UNSW-NB15 | Isolation Forest | +0.3191 | [+0.2878, +0.3495] | yes |
| UNSW-NB15 | Autoencoder | +0.1176 | [+0.0831, +0.1538] | yes |
| UNSW-NB15 | OC-SVM | +0.3470 | [+0.3183, +0.3766] | yes |

The zero-day sets are small on two datasets (BoT-IoT 683 rows, UNSW-NB15 1,216), so the interval — not the p-value — is what should be quoted: with n that size a p-value can be tiny while the gap remains imprecisely located.

## 3. Paired t + Cohen's d_z across 5 real seeds (9-test family)

Metric `zero_day_true_positive_rate` over seeds [42, 43, 44, 45, 46], via the Day-17 `head_pair_tests` on the Day-13 harness.

| Dataset | Comparison | mean A | mean B | Δ | t | df | d_z | p (Holm) | sig |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| CICIoT2023 | autoencoder vs isolation_forest | 0.7975 | 0.9999 | -0.2024 | -2.685 | 4 | -1.201 | 0.33 | no |
| CICIoT2023 | autoencoder vs ocsvm | 0.7975 | 0.8726 | -0.0751 | -1.072 | 4 | -0.480 | 1 | no |
| CICIoT2023 | isolation_forest vs ocsvm | 0.9999 | 0.8726 | +0.1273 | 16.658 | 4 | +7.449 | 0.000685 | **yes** |
| BoT-IoT | autoencoder vs isolation_forest | 0.6861 | 0.7233 | -0.0372 | -1.112 | 4 | -0.497 | 1 | no |
| BoT-IoT | autoencoder vs ocsvm | 0.6861 | 0.7490 | -0.0630 | -2.004 | 4 | -0.896 | 0.578 | no |
| BoT-IoT | isolation_forest vs ocsvm | 0.7233 | 0.7490 | -0.0258 | -2.842 | 4 | -1.271 | 0.328 | no |
| UNSW-NB15 | autoencoder vs isolation_forest | 0.0655 | 0.0607 | +0.0048 | 0.096 | 4 | +0.043 | 1 | no |
| UNSW-NB15 | autoencoder vs ocsvm | 0.0655 | 0.0393 | +0.0262 | 0.511 | 4 | +0.229 | 1 | no |
| UNSW-NB15 | isolation_forest vs ocsvm | 0.0607 | 0.0393 | +0.0214 | 5.660 | 4 | +2.531 | 0.0384 | **yes** |

> **QS-Net is absent from this family, and that is a reported gap, not an oversight.** the Day-13 5-seed harness contains classical novelty heads only (isolation_forest / autoencoder / ocsvm); there is no per-seed quantum arm. Unblocked by: Team B emitting one score directory per training seed, then rerunning this module with --scores-root <dir> per seed. Until then, the QS-Net evidence in §1–2 is row-level, not training-level.

**What n = 5 can detect.** A difference must reach **|d_z| ≈ 1.24** merely to clear p < 0.05 two-sided, and **≈ 1.68** for 80% power (exact, from the non-central t). So "not significant" here means *unresolved*, never *no difference* (Demšar 2006).

## 4. A design we tried and rejected — pairing on the calibration draw

The obvious way to give QS-Net a paired t without Team B is to pair on the **conformal calibration draw**: re-split calibration/test under 5 seeds, apply the same permutation to every arm (the score vectors are row-aligned, so this works mechanically), and run a paired t. It is mechanically valid and statistically useless here, which is worth recording with numbers rather than asserting:

| Dataset | vs | std(recall) QS-Net | std(recall) baseline | Δ | d_z it would report |
|---|---|---:|---:|---:|---:|
| CICIoT2023 | Isolation Forest | 0.00e+00 | 4.99e-05 | +0.0020 | **+40.9** |
| CICIoT2023 | Autoencoder | 0.00e+00 | 4.10e-03 | +0.4949 | **+120.7** |
| BoT-IoT | Isolation Forest | 1.31e-03 | 0.00e+00 | -0.6305 | **-481.4** |
| BoT-IoT | OC-SVM | 1.31e-03 | 1.31e-03 | -0.6284 | **-289.4** |
| BoT-IoT | Autoencoder | 1.31e-03 | 1.96e-03 | -0.4480 | **-249.8** |
| UNSW-NB15 | Isolation Forest | 3.65e-03 | 3.68e-04 | +0.3928 | **+116.5** |
| UNSW-NB15 | OC-SVM | 3.65e-03 | 3.68e-04 | +0.3898 | **+111.7** |
| UNSW-NB15 | Autoencoder | 3.65e-03 | 0.00e+00 | +0.1273 | **+34.9** |

At n_cal ≈ 18k the conformal threshold barely moves between draws, so recall varies by ~1e-3 or is exactly constant. The paired differences are effectively deterministic, d_z = mean/std runs into the **hundreds**, and every comparison returns p ≈ 0 however trivial the gap — significance with no bearing on importance. Reported here so nobody re-derives it and believes it.

## 5. RQ5 — where quantum helps and where it does not

Full notes: [`_generated/w4_06_rq5_honesty.md`](_generated/w4_06_rq5_honesty.md). A verdict needs the exact test **and** the bootstrap interval to agree in direction.

| Dataset | Baseline | Δ recall | 95% CI | h | verdict |
|---|---|---:|---|---:|---|
| BoT-IoT | Autoencoder | -0.5300 | [-0.5710, -0.4876] | -1.197 | quantum behind (McNemar sig. + CI excludes 0) |
| BoT-IoT | Isolation Forest | -0.6281 | [-0.6706, -0.5886] | -1.407 | quantum behind (McNemar sig. + CI excludes 0) |
| BoT-IoT | OC-SVM | -0.6384 | [-0.6779, -0.5988] | -1.429 | quantum behind (McNemar sig. + CI excludes 0) |
| CICIoT2023 | Autoencoder | +0.3388 | [+0.3298, +0.3476] | +1.216 | quantum ahead (McNemar sig. + CI excludes 0) |
| CICIoT2023 | Isolation Forest | +0.0000 | [-0.0004, +0.0004] | +0.000 | equivalent (95% CI inside ±0.05 recall) |
| UNSW-NB15 | Autoencoder | +0.1176 | [+0.0831, +0.1538] | +0.252 | quantum ahead (McNemar sig. + CI excludes 0) |
| UNSW-NB15 | Isolation Forest | +0.3191 | [+0.2878, +0.3495] | +0.818 | quantum ahead (McNemar sig. + CI excludes 0) |
| UNSW-NB15 | OC-SVM | +0.3470 | [+0.3183, +0.3766] | +0.944 | quantum ahead (McNemar sig. + CI excludes 0) |

**4 ahead · 3 behind · 1 equivalent · 0 unresolved** of 8 comparisons. The direction is not uniform across datasets, which is the RQ5 result: there is no single answer to "does quantum help" — it depends on the dataset, and the table says so in both directions.

## 6. Honest limits

1. Every QS-Net number rides the Day-14 **dummy** interface — protocol final, findings provisional.
2. No seed-level claim about QS-Net is possible until Team B ships per-seed prototypes (§3).
3. Training variance is unmeasured for both arms; the row-level tests do not capture it.
4. Coverage is not the discriminator — Day 24 put 11/11 cells inside the exact band. Recall is, and it moves in both directions.
5. No quantum-advantage claim is made or implied.

Figure: `figures/w4_06_significance.png` (written) — forest plot of Δrecall with bootstrap CIs, McNemar significance marked alongside.

## Bottom line

The Week-3 protocol now runs end-to-end on the paper's real comparison: 8 + 8 exact McNemar tests and 9 paired t-tests across three declared Holm families, every p-value carrying an effect size, a stated detection floor for n = 5, and one candidate design rejected on measured evidence. The RQ5 notes name where the quantum arm wins, where it loses, and what cannot yet be claimed — with negative results left in.

CSV: `_generated/w4_06_significance.csv` · JSON: `_generated/w4_06_significance.json` · RQ5: `_generated/w4_06_rq5_honesty.md`.

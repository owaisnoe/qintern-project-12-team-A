# Week 5 · Day 29 — Table A (RQ1) FINAL: Significance vs Every Baseline + Effect Sizes

Task (`qi26_12_Week_5.pdf`): *finalise Table A (in-distribution detection) with significance markers vs every baseline; attach Cohen's d effect sizes.* Seed 42 · α = 0.05 · trio CICIoT2023, BoT-IoT, UNSW-NB15 · quantum scores: **dummy**.

Every baseline is paired with QS-Net on the face of in-distribution detection it actually shares: **XGBoost** on closed-set multiclass correctness (it is the only baseline emitting a class prediction), and **every Day-12 novelty head** on the known-split flag-vs-keep decision (the Day-22 frozen-q decisions against each head's `is_novel`, row-aligned by the Day-25 pairing). Each family is Holm-corrected separately; every test carries Cohen's h and the paired d_z (Demšar 2006). Table A final: [`_generated/w5_05_table_a.md`](_generated/w5_05_table_a.md) + [`.tex`](_generated/w5_05_table_a.tex).

## Family 1 — closed-set correctness (QS-Net vs XGBoost)

| Dataset | n_pairs | acc QS-Net | acc XGBoost | Δacc | n10/n01 | h | d_z | p (Holm) | sig |
|---|---:|---:|---:|---:|---|---:|---:|---:|:--:|
| CICIoT2023 | 18,883 | 0.9034‡ | 0.9896 | -0.0862‡ | 176/1803 | -0.427‡ | -0.276‡ | 0.00e+00‡ | **sig** |
| BoT-IoT | 18,591 | 0.9396‡ | 0.9515 | -0.0118‡ | 869/1089 | -0.052‡ | -0.036‡ | 1.45e-06‡ | **sig** |
| UNSW-NB15 | 10,086 | 0.7966‡ | 0.8020 | -0.0054‡ | 1602/1656 | -0.013‡ | -0.009‡ | 3.53e-01‡ | ns |

Holm family m = 3 (one comparison per dataset).

## Family 2 — in-distribution false alarms on the KNOWN split (QS-Net vs every head)

Correct on a known row = **not** flagged. This is the in-distribution face the novelty heads share; their zero-day (power) face is Table B / Day-25 territory and is not retested here.

| Dataset | baseline | n_pairs | FA QS-Net | FA baseline | ΔFA | h | d_z | p (Holm) | sig |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| CICIoT2023 | Isolation Forest | 18,883 | 0.0486‡ | 0.1012 | -0.0526‡ | -0.203‡ | +0.142‡ | 2.45e-84‡ | **sig** |
| CICIoT2023 | Autoencoder | 18,883 | 0.0486‡ | 0.1014 | -0.0527‡ | -0.203‡ | +0.142‡ | 3.24e-84‡ | **sig** |
| BoT-IoT | Isolation Forest | 18,591 | 0.0530‡ | 0.0978 | -0.0448‡ | -0.172‡ | +0.121‡ | 1.66e-60‡ | **sig** |
| BoT-IoT | Autoencoder | 18,591 | 0.0530‡ | 0.0968 | -0.0437‡ | -0.168‡ | +0.118‡ | 3.57e-58‡ | **sig** |
| BoT-IoT | OC-SVM | 18,591 | 0.0530‡ | 0.0971 | -0.0441‡ | -0.169‡ | +0.119‡ | 2.56e-58‡ | **sig** |
| UNSW-NB15 | Isolation Forest | 10,086 | 0.0463‡ | 0.0993 | -0.0530‡ | -0.208‡ | +0.145‡ | 3.18e-48‡ | **sig** |
| UNSW-NB15 | Autoencoder | 10,086 | 0.0463‡ | 0.1023 | -0.0560‡ | -0.217‡ | +0.152‡ | 2.80e-52‡ | **sig** |
| UNSW-NB15 | OC-SVM | 10,086 | 0.0463‡ | 0.1039 | -0.0576‡ | -0.223‡ | +0.154‡ | 6.34e-54‡ | **sig** |

Holm family m = 8 (dataset × head; CIC-IoT2023 has no OC-SVM model — a real absence from Day 12, not a missing value).

**Reading the FA family — budgets are NOT matched here, by design.** This family compares the systems at their **shipped operating points**: QS-Net at its conformal α = 0.05 (guaranteed), each head at its own frozen Day-12 threshold, which targeted a **2α = 0.10** known-FPR budget (and delivers ≈ 0.10). So the significant gaps say: *as deployed, QS-Net keeps significantly more known traffic than every head* — a deployed-behaviour statement, not a same-budget superiority claim. The like-for-like comparison at ONE shared α is Table B's recall column (Day-19 re-thresholds every head with the same conformal rule at α = 0.05); the Day-25 all-rows/zero-day families use these same shipped flags, so this family completes that triptych on the known split.

## Seed-level arm (assembled from Day 25 — not recomputed)

Classical 5-seed paired-t (metric: `zero_day_true_positive_rate`, seeds [42, 43, 44, 45, 46]), with paired d_z per row — the seed-level Cohen's d the task asks to attach:

| Dataset | pair | mean Δ | d_z | p (Holm) | sig |
|---|---|---:|---:|---:|:--:|
| CICIoT2023 | autoencoder vs isolation_forest | -0.2024 | -1.201 | 3.30e-01 | ns |
| CICIoT2023 | autoencoder vs ocsvm | -0.0751 | -0.480 | 1.00e+00 | ns |
| CICIoT2023 | isolation_forest vs ocsvm | +0.1273 | +7.449 | 6.85e-04 | **sig** |
| BoT-IoT | autoencoder vs isolation_forest | -0.0372 | -0.497 | 1.00e+00 | ns |
| BoT-IoT | autoencoder vs ocsvm | -0.0630 | -0.896 | 5.78e-01 | ns |
| BoT-IoT | isolation_forest vs ocsvm | -0.0258 | -1.271 | 3.28e-01 | ns |
| UNSW-NB15 | autoencoder vs isolation_forest | +0.0048 | +0.043 | 1.00e+00 | ns |
| UNSW-NB15 | autoencoder vs ocsvm | +0.0262 | +0.229 | 1.00e+00 | ns |
| UNSW-NB15 | isolation_forest vs ocsvm | +0.0214 | +2.531 | 3.84e-02 | **sig** |

**QS-Net cannot enter this family yet** — the Day-13 5-seed harness contains classical novelty heads only (isolation_forest / autoencoder / ocsvm); there is no per-seed quantum arm (unblocked by: Team B emitting one score directory per training seed, then rerunning this module with --scores-root <dir> per seed). With n = 5 seeds the smallest significant paired effect is d_z ≈ 1.24 (80% power: ≈ 1.68) — the floor any seed-level quantum claim must clear.

## Bottom line

Table A is final: the closed-set table with `*` markers and both effect sizes, plus the known-split false-alarm family covering **every** baseline head, each family Holm-corrected and each p-value accompanied by h and d_z. Every QS-Net cell is ‡ provisional and reprices with one flag on Team B's real prototypes — the structure, families and effect-size conventions are what carry into the manuscript.

CSV: `_generated/w5_05_table_a_effects.csv` + `_generated/w5_05_known_fa.csv` · JSON: `_generated/w5_05_table_a_effects.json` · Table A: `_generated/w5_05_table_a.md` + `.tex`.

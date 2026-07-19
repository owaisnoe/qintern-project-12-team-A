# Week 2 - Day 13: All-Dataset Baselines, One-Class SVM & Statistics Harness

**QS-Net / QuantumSentinel - Team A (Iwo)** - benchmark trio: **CIC-IoT2023 + BoT-IoT + UNSW-NB15** -
base seed **42**, five-seed harness `42..46`, `n_jobs=1`.

Day 13 extends the Day-11/12 classical baselines ([`w2_04`](w2_04_classical_baselines.md)) from one
dataset to all three mentor-locked datasets, adds a third novelty head (One-Class SVM), enriches the
metric set, stands up the statistics harness the paper needs, and confirms the splits are leakage-free.
The split contract and leakage rules are inherited unchanged from Days 8-12.

## Benchmark lock: UNSW-NB15, not TON-IoT

The task sheet lists TON-IoT for Day 13, but the mentor locked the benchmark trio to **CIC-IoT2023,
BoT-IoT, and UNSW-NB15** (TON-IoT + Edge-IIoTset set aside; see
[`../../week1/reports/17_unified_collapse_mentor_note.md`](../../week1/reports/17_unified_collapse_mentor_note.md)
and [`../README.md`](../README.md)). Day 13 therefore reports UNSW-NB15 in TON-IoT's place.

## What Day 13 adds

1. **All three datasets.** The same audited runner now fits and evaluates CIC-IoT2023, BoT-IoT, and
   UNSW-NB15 under one split/metric contract.
2. **Third novelty head - One-Class SVM.** The novelty set is now Isolation Forest + Autoencoder +
   **One-Class SVM** (RBF, `gamma=scale`, `nu=0.10`). OC-SVM training is O(n^2), so it fits a
   deterministic 6,000-row cap of the class-capped known-only subset, on train-fitted standardised
   features. Score = `-decision_function` (higher = more novel), the same orientation as the other heads.
3. **Enriched metrics.** Next to accuracy and macro-F1 the runner now emits **balanced accuracy**,
   **macro-OVR AUPRC**, per-head **zero-day AUPRC**, FPR at 95% TPR (already present), and a
   **per-held-out-attack** zero-day breakdown (AUROC / AUPRC / thresholded detection rate per family).
4. **Statistics harness.** [`scripts/stats_harness.py`](../scripts/stats_harness.py) re-runs the whole
   stack across seeds `42..46` with `n_jobs=1` and reports mean, sample std (ddof=1), and a t-based 95%
   confidence interval for every headline metric.
5. **Leakage confirmation.** [`scripts/leakage_check.py`](../scripts/leakage_check.py) confirms no
   resample-before-split or duplicate-flow leakage on all three datasets.

## Canonical-number contract

The Day-12 single-run macro-F1 **0.8043** stays the canonical seed-42 number from Owais's uploaded
CIC-IoT2023 model and predictions; `week2/baselines/CICIoT2023/` is unchanged (its derived
`results.json`/`predictions.csv` are re-scored from those same saved models and reproduce 0.8043
exactly). That single run is machine-dependent - XGBoost `hist` training is not bit-identical across
machines or thread counts (an independent rerun gives ~0.798). The Day-13 five-seed, `n_jobs=1` harness
below produces the machine-stable mean +/- std and 95% CI that **supersedes any single-run number**.
Reassuringly, the CIC five-seed mean **0.8045 +/- 0.0062** brackets the canonical 0.8043 almost exactly.

## Closed-set detector results (five-seed, n_jobs=1)

Known-only `test.csv`. Mean +/- std over seeds `42..46`; 95% CI in brackets.

| Dataset | Accuracy | Balanced acc | Macro-F1 | AUROC (OVR) | AUPRC (OVR) | Binary attack F1 |
|---|---:|---:|---:|---:|---:|---:|
| CIC-IoT2023 | 0.9896 +/- 0.0002 | 0.8001 +/- 0.0037 | **0.8045 +/- 0.0062** `[0.7968, 0.8123]` | 0.9990 | 0.8310 +/- 0.0034 | 0.9475 |
| BoT-IoT | 0.9524 +/- 0.0009 | 0.9736 +/- 0.0005 | **0.9732 +/- 0.0005** `[0.9726, 0.9738]` | 0.9956 | 0.9951 +/- 0.0001 | 0.9989 |
| UNSW-NB15 | 0.8027 +/- 0.0012 | 0.7083 +/- 0.0050 | **0.6035 +/- 0.0029** `[0.6000, 0.6071]` | 0.9699 | 0.6682 +/- 0.0018 | 0.8641 |

Read macro-F1 and balanced accuracy together with plain accuracy: CIC and UNSW are severely imbalanced,
so the ~0.99 / ~0.80 accuracies are carried by frequent classes while the rare-class macro-F1 is the real
bar. **UNSW-NB15 at macro-F1 0.60 is the hard slice** - a much tighter bar for QS-Net than the near-perfect
CIC binary scores, which are a known dataset-triviality effect.

## Zero-day novelty heads (five-seed, n_jobs=1)

Known test rows (label 0) vs held-out zero-day families (label 1); the detector never sees these families.

| Dataset | Head | Zero-day AUROC | Zero-day AUPRC | FPR at 95% TPR |
|---|---|---:|---:|---:|
| CIC-IoT2023 | Isolation Forest | **0.9952 +/- 0.0010** | **0.9775 +/- 0.0043** | **0.0097 +/- 0.0020** |
| CIC-IoT2023 | Autoencoder | 0.9341 +/- 0.0300 | 0.8028 +/- 0.0930 | 0.1484 +/- 0.0659 |
| CIC-IoT2023 | One-Class SVM | 0.9404 +/- 0.0089 | 0.9143 +/- 0.0104 | 0.3256 +/- 0.0612 |
| BoT-IoT | Isolation Forest | 0.7570 +/- 0.0149 | 0.5463 +/- 0.0070 | 0.9150 +/- 0.0381 |
| BoT-IoT | Autoencoder | 0.9185 +/- 0.0231 | 0.3648 +/- 0.0255 | 0.2900 +/- 0.1666 |
| BoT-IoT | One-Class SVM | **0.9338 +/- 0.0114** | 0.4766 +/- 0.0233 | **0.2784 +/- 0.0423** |
| UNSW-NB15 | Isolation Forest | 0.3830 +/- 0.0051 | 0.0838 +/- 0.0014 | 0.9554 +/- 0.0045 |
| UNSW-NB15 | Autoencoder | 0.3369 +/- 0.0863 | 0.0919 +/- 0.0419 | 0.9715 +/- 0.0187 |
| UNSW-NB15 | One-Class SVM | **0.4785 +/- 0.0047** | 0.0927 +/- 0.0008 | **0.7907 +/- 0.0084** |

No single head wins everywhere: Isolation Forest dominates CIC (Mirai), One-Class SVM is the most robust
on BoT-IoT (Theft) and UNSW-NB15, and the Autoencoder is the highest-variance head (see its CIC and BoT
std). The low BoT-IoT / UNSW-NB15 AUPRCs versus their AUROCs are the imbalance signal AUROC hides: Theft
is 683 of 19,274 rows and UNSW zero-day is 1,216 of 11,302, so a good ranking (AUROC) still yields low
precision at the base rate (AUPRC).

**UNSW-NB15 zero-day is below chance for every head.** The held-out Shellcode/Worms families are not
separable from known traffic by any of these unsupervised reconstruction/density heads in the 17-feature
QADCP space - a concrete, honest bar for QS-Net's conformal zero-day rejection to beat.

## Per-held-out-attack zero-day AUROC (five-seed mean)

A single mean zero-day AUROC hides which families are easy or hard, so each held-out family is scored
separately (known test = negatives, that family = positives).

| Dataset | Held-out family | rows | IsoForest | Autoencoder | One-Class SVM |
|---|---|---:|---:|---:|---:|
| CIC-IoT2023 | Mirai-greeth_flood | 4,144 | 0.995 | 0.941 | 0.971 |
| CIC-IoT2023 | Mirai-greip_flood | 3,134 | 0.995 | 0.932 | 0.949 |
| CIC-IoT2023 | Mirai-udpplain | 3,706 | 0.996 | 0.928 | 0.899 |
| BoT-IoT | Theft | 683 | 0.757 | 0.919 | 0.934 |
| UNSW-NB15 | Shellcode | 1,062 | 0.381 | 0.339 | 0.491 |
| UNSW-NB15 | Worms | 154 | 0.393 | 0.325 | 0.389 |

The three CIC Mirai variants are uniformly easy; BoT-IoT Theft is head-sensitive (Isolation Forest is
weak, kernel/reconstruction heads recover it); UNSW Shellcode and Worms are both hard for every head.

## Leakage confirmation

[`scripts/leakage_check.py`](../scripts/leakage_check.py) -> `reports/_generated/day13_leakage_check.json`,
**overall PASS**. For each dataset it hashes every row's feature vector and checks cross-split collisions:

| Dataset | train->cal | train->test | train->zeroday | cal->test | within-split dup rate |
|---|---:|---:|---:|---:|---:|
| CIC-IoT2023 | 0 | 0 | 0 | 0 | 0.000 |
| BoT-IoT | 0 | 0 | 0 | 0 | 0.000 |
| UNSW-NB15 | 0 | 0 | 0 | 0 | 0.000 |

Zero shared feature rows between any two splits and zero within-split duplication confirm there is no
resample-before-split inflation and no duplicate-flow leakage: QADCP dedups and balances inside `train`
only. Calibration and test are known-class only, and every zero-day family is disjoint from the known
set. This complements the Day-9 exchangeability report ([`w2_02`](w2_02_split_integrity.md)).

## Statistics harness

[`scripts/stats_harness.py`](../scripts/stats_harness.py) is the Day-13 statistics scaffold Weeks 3-4
build on:

- Seeds `42..46`, `n_jobs=1` - fixed thread count removes XGBoost/sklearn scheduling nondeterminism, so
  each `(dataset, seed)` pair is reproducible and the spread measures genuine seed sensitivity.
- `mean_std_ci(values)` returns mean, sample std (ddof=1), and a two-sided t 95% CI
  (`t_{0.975, n-1} * s / sqrt(n)`). CIs are reported as-is and may extend past [0, 1] for tiny `n`.
- Runs the audited `run_dataset` in memory (`save=False`); it never fits on test/zeroday and never
  overwrites the canonical seed-42 artifacts under `week2/baselines/`.

## Reproduce

From `Team A` with the pinned Python 3.12 venv (`week1/requirements.txt`: numpy 2.1.3, pandas 2.2.3,
scikit-learn 1.8.0, xgboost 3.2.0):

```bash
# all-dataset single-run artifacts (seed 42, machine-stable n_jobs=1) for BoT-IoT + UNSW-NB15
../.venv/bin/python week2/scripts/classical_baselines.py --datasets BoT-IoT UNSW-NB15 --jobs 1 --no-summary
# five-seed statistics on all three datasets
../.venv/bin/python week2/scripts/stats_harness.py
# leakage confirmation
../.venv/bin/python week2/scripts/leakage_check.py
# tests (19)
../.venv/bin/python -m unittest discover -s week2/tests
```

## Files produced

- `week2/scripts/stats_harness.py`, `week2/scripts/leakage_check.py` (new).
- `week2/scripts/classical_baselines.py`, `week2/scripts/baseline_metrics.py` (extended: OC-SVM head,
  `--seed`/`--no-summary`, balanced accuracy, AUPRC, per-attack zero-day).
- `week2/baselines/BoT-IoT/` and `week2/baselines/UNSW-NB15/` - XGBoost + Isolation Forest + Autoencoder
  + One-Class SVM models, `predictions.csv`, `results.json` (seed 42, `n_jobs=1`, three heads).
- `week2/reports/_generated/stats_harness.{json,csv}` - five-seed mean/std/CI tree.
- `week2/reports/_generated/day13_all_datasets.{json,csv}` - seed-42 all-dataset table with the new metrics.
- `week2/reports/_generated/day13_leakage_check.json` - leakage verdict.
- `week2/tests/test_stats_harness.py` (new) + extended `test_baseline_metrics.py` / `test_baseline_artifacts.py`.
- **Unchanged:** `week2/baselines/CICIoT2023/` and `week2/reports/_generated/baseline_results.{json,csv}`
  keep Owais's canonical Day-12 numbers.

## Limitations and interpretation

These stay checkpoint-scale results, not full raw-stream estimates. Near-perfect CIC/BoT binary scores are
a known dataset-triviality effect; the real bar is the hard slices this report surfaces - rare-class
macro-F1 (UNSW 0.60), per-attack zero-day (UNSW Shellcode/Worms below chance), and calibration (FPR at 95%
TPR). AUROC is ranking-based; where classes are imbalanced, read AUPRC alongside it. The five-seed CI
captures seed sensitivity at fixed package versions, not cross-machine XGBoost `hist` variation - hence the
`n_jobs=1`, pinned-version contract. Day 14 freezes these partitions and publishes the dummy score
interface for Teams B and C.

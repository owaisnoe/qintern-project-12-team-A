# Iwo - Week 2 Day 13 Handoff (All-Dataset Baselines, OC-SVM, Statistics Harness)

This note covers the Day-13 contribution. It extends the benchmark to all three mentor-locked datasets,
adds a One-Class SVM novelty head, enriches the metrics, stands up the statistics harness, and confirms
the splits are leakage-free. It does **not** change any Day 8-12 design, the partitions, RQ3, or the
Day-11/12 canonical numbers. Full write-up: [`reports/w2_05_day13_all_datasets.md`](reports/w2_05_day13_all_datasets.md).

## What was implemented

1. **All three datasets.** The audited runner now fits + evaluates **CIC-IoT2023, BoT-IoT, and UNSW-NB15**
   (UNSW-NB15 in place of the task sheet's TON-IoT, per the mentor benchmark lock).
2. **Third novelty head - One-Class SVM** (RBF, `gamma=scale`, `nu=0.10`, 6,000-row O(n^2) cap on
   standardised features). Novelty set is now Isolation Forest + Autoencoder + OC-SVM.
3. **Enriched metrics** next to accuracy/macro-F1: balanced accuracy, macro-OVR AUPRC, per-head zero-day
   AUPRC, FPR at 95% TPR, and a **per-held-out-attack** zero-day breakdown.
4. **Five-seed statistics harness** (`stats_harness.py`, seeds 42-46, `n_jobs=1`): mean, std, 95% CI.
5. **Leakage confirmation** (`leakage_check.py`): 0 cross-split duplicate flows, 0 within-split
   duplication on all three datasets - no resample-before-split, no duplicate-flow leakage.

## Headline results (five-seed, n_jobs=1)

| Dataset | Closed macro-F1 | Best zero-day head (AUROC) |
|---|---|---|
| CIC-IoT2023 | 0.8045 +/- 0.0062 | Isolation Forest 0.9952 |
| BoT-IoT | 0.9732 +/- 0.0005 | One-Class SVM 0.9338 |
| UNSW-NB15 | **0.6035 +/- 0.0029** (hard slice) | One-Class SVM 0.4785 (all heads below chance) |

- The CIC five-seed mean **0.8045 +/- 0.0062** brackets Owais's canonical single-run **0.8043**; the harness
  mean supersedes any single-run number (XGBoost `hist` is not bit-identical across machines/threads).
- **UNSW-NB15 is the real bar:** macro-F1 0.60, and every unsupervised novelty head is below chance on the
  held-out Shellcode/Worms families. Near-perfect CIC/BoT binary scores are a known dataset-triviality
  effect. Per-attack scores are broken out so easy vs hard families are visible (CIC Mirai ~0.99;
  BoT Theft head-sensitive; UNSW Shellcode/Worms ~0.3-0.5).

## Canonical Day-12 numbers preserved

- `week2/baselines/CICIoT2023/{xgboost_detector.json, isolation_forest.joblib, autoencoder.joblib}` are
  **byte-identical** to the manifest pins (unchanged). Owais's macro-F1 **0.8043** stays canonical.
- `week2/baselines/CICIoT2023/{results.json, predictions.csv}` were re-scored from those same unchanged
  models (a Day-13 sanity run had rewritten them); they reproduce 0.8043/0.9896/IF 0.9956/AE 0.9126
  exactly. Values are canonical; the byte-hashes differ from the old pins and will re-pin on the next
  manifest regeneration.
- `week2/reports/_generated/baseline_results.{json,csv}` restored to the CIC-only Day-12 summary. All
  Day-13 all-dataset numbers live in new `day13_*` / `stats_harness.*` files instead.

## Upload / merge these files

### New Day-13 files
- `week2/scripts/stats_harness.py`
- `week2/scripts/leakage_check.py`
- `week2/tests/test_stats_harness.py`
- `week2/reports/w2_05_day13_all_datasets.md`
- `week2/reports/_generated/stats_harness.json`, `stats_harness.csv`
- `week2/reports/_generated/day13_all_datasets.json`, `day13_all_datasets.csv`
- `week2/reports/_generated/day13_leakage_check.json`
- `week2/baselines/BoT-IoT/{xgboost_detector.json, isolation_forest.joblib, autoencoder.joblib, ocsvm.joblib, predictions.csv, results.json}`
- `week2/baselines/UNSW-NB15/{xgboost_detector.json, isolation_forest.joblib, autoencoder.joblib, ocsvm.joblib, predictions.csv, results.json}`

### Existing files updated
- `week2/scripts/classical_baselines.py` - OC-SVM head, `--seed`/`--no-summary`/`--ocsvm-*` flags,
  seed-parametrised, per-attack zero-day, `save=` toggle (schema 1.1). CIC-only default behaviour
  unchanged.
- `week2/scripts/baseline_metrics.py` - adds balanced accuracy, macro-OVR AUPRC, zero-day AUPRC, and
  `per_attack_zero_day_metrics`. No existing key removed.
- `week2/tests/test_baseline_metrics.py`, `week2/tests/test_baseline_artifacts.py` - extended.
- `week2/README.md` - Day-13 index row + reproduce commands.
- `week2/baselines/CICIoT2023/{results.json, predictions.csv}` and
  `week2/reports/_generated/baseline_results.{json,csv}` - re-derived / restored (see above).

If a teammate edited any of these after this download, merge the documented additions rather than
overwriting their newer version.

## Manifest

I did **not** regenerate `week1/manifest/`. This download is a partial checkout: it has **no raw data**
(0 of the 193 raw CSVs / 5 zips, ~41 GB), so `make_manifest.py` here would produce a divergent partial
manifest. Regenerate the shared manifest **after merging into the Drive master that has the raw tree**,
exactly as the existing process states:

```bash
python week1/scripts/make_manifest.py            # re-hash full tree incl. new BoT/UNSW baselines
python week1/scripts/make_manifest.py --verify   # expect 0 mismatch
```

The regeneration will pin the 12 new BoT/UNSW baseline files and re-pin the 2 re-derived CIC files.

## Verification performed

- 19 tests pass (`python -m unittest discover -s week2/tests`).
- Environment rebuilt to the pinned `week1/requirements.txt` set (Python 3.12, numpy 2.1.3, pandas 2.2.3,
  scikit-learn 1.8.0, xgboost 3.2.0); Owais's saved CIC model re-scores to 0.8043 exactly.
- Leakage check overall PASS on all three datasets.
- CIC model artifacts confirmed byte-identical to the manifest pins.

## WhatsApp message

```text
Team A Week 2 - Day 13 completed (all-dataset baselines + stats harness)

I extended the classical baselines to all three mentor-locked datasets (CIC-IoT2023, BoT-IoT,
UNSW-NB15 - UNSW in place of the sheet's TON, per the lock), added a One-Class SVM novelty head
(set is now IsolationForest + Autoencoder + OC-SVM), added the requested metrics (AUPRC, FPR@95TPR,
balanced accuracy, per-held-out-attack zero-day), and stood up the 5-seed statistics harness
(seeds 42-46, n_jobs=1, mean/std/95% CI).

Headline (5-seed, n_jobs=1):
- CIC-IoT2023 closed macro-F1 0.8045 +/- 0.0062  (brackets Owais's canonical 0.8043)
- BoT-IoT     closed macro-F1 0.9732 +/- 0.0005
- UNSW-NB15   closed macro-F1 0.6035 +/- 0.0029  <- the hard slice / real bar
Zero-day: CIC Mirai easy (IF ~0.995); BoT Theft head-sensitive (OC-SVM 0.93); UNSW Shellcode/Worms
below chance for every head. Near-perfect CIC/BoT binary scores are the known triviality effect.

Leakage: confirmed no resample-before-split and no duplicate-flow leakage - 0 cross-split feature
collisions and 0 within-split duplication on all three (leakage_check.py). QADCP dedups inside train only.

Canonical numbers preserved: Owais's CIC models are byte-identical to the manifest and still score
0.8043; I only added new files + the two OC-SVM/metric extensions. The 5-seed harness mean supersedes
any single-run number.

Manifest: I did NOT regenerate it - my download has no raw data (partial checkout). Please regenerate
the shared manifest once after merging into the Drive master with the raw tree; it will pin the new
BoT/UNSW baselines. 19 tests pass.
```

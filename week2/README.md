# QS-Net · Team A — Week 2 (Days 8–14): Partitions, RQ3, Classical Baselines & Data Freeze

Project 12 of QIntern 2026 — **QuantumSentinel / QS-Net**. This is the **Week-2 package index**.
Team A converts the Week-1 curated datasets into the exact partitions the conformal guarantee needs, plus
the adversarial/zero-day evaluation set — for the **mentor-locked benchmark trio CIC-IoT2023 + BoT-IoT +
UNSW-NB15** (TON_IoT + Edge-IIoTset set aside; see
[`../week1/reports/17_unified_collapse_mentor_note.md`](../week1/reports/17_unified_collapse_mentor_note.md)).
**Qubit budget = 8 · seed 42.**

> **Docs are unified in `week1/`** — the entry-point [`../week1/README.md`](../week1/README.md), the upload
> guide [`../week1/UPLOAD.md`](../week1/UPLOAD.md), and the **single checksum manifest**
> [`../week1/manifest/MANIFEST.md`](../week1/manifest/MANIFEST.md) all cover Week 1 **and** Week 2. This file
> is just the Week-2 index; per-package machine metadata lives beside the data (`partition_meta.json`,
> `rq3_schema.json`).

## Contents

| Day | Deliverable | Report | Data |
|---|---|---|---|
| **8** | Conformal partitions (Train/Calibration/Test/Zero-Day) | [`reports/w2_01_partition_spec.md`](reports/w2_01_partition_spec.md) | `partitions/<name>/{train,calibration,test,zeroday}.csv` + `partition_meta.json` |
| **9** | Split-integrity & conformal-exchangeability report | [`reports/w2_02_split_integrity.md`](reports/w2_02_split_integrity.md) | `reports/_generated/split_integrity.json` |
| **10** | RQ3 adversarial-vs-zero-day evaluation set | [`reports/w2_03_rq3_eval_set.md`](reports/w2_03_rq3_eval_set.md) | `rq3/<name>/{adversarial_source_pool,eval_clean}.csv` + `rq3_schema.json` |
| **11-12** | Classical detector and zero-day novelty baselines | [`reports/w2_04_classical_baselines.md`](reports/w2_04_classical_baselines.md) | `scripts/classical_baselines.py` + `scripts/baseline_metrics.py` + `baselines/<name>/` + first CIC results |
| **13** | All-dataset baselines (+ One-Class SVM), five-seed statistics harness, leakage confirmation | [`reports/w2_05_day13_all_datasets.md`](reports/w2_05_day13_all_datasets.md) | `scripts/stats_harness.py` + `scripts/leakage_check.py` + `baselines/{BoT-IoT,UNSW-NB15}/` + `reports/_generated/{stats_harness,day13_all_datasets,day13_leakage_check}.*` |
| **14** | **DATA FREEZE v1.0** + prototype-shaped dummy score interface + handover | [`reports/w2_06_data_freeze.md`](reports/w2_06_data_freeze.md) | `scripts/{freeze_package,make_dummy_scores}.py` + `FROZEN/` (v1.0 manifest) + `interface/dummy_scores/<name>/*` + `interface/dummy_scores_schema.json` + `reports/_generated/dummy_score_selfcheck.json` |

Supplementary: [`reports/w2_07_leakage_controls.md`](reports/w2_07_leakage_controls.md) — a consolidated
leakage-control summary (fit-on-train, known-only calibration, CIC duplicate-flow verification) for
mentor/reviewer reference.

Scripts: [`scripts/make_partitions.py`](scripts/make_partitions.py) ·
[`scripts/split_integrity.py`](scripts/split_integrity.py) ·
[`scripts/make_rq3_evalset.py`](scripts/make_rq3_evalset.py).
Partitions are the leakage-safe Week-1 **unified v1.0** splits re-shaped to the conformal 4-way layout
(`train` = Week-1 `train`+`val`; calibration = **known classes only**; zero-day = a full held-out class).

## Reproduce & verify

```bash
source ../.venv/bin/activate                       # Python 3.12
python week2/scripts/make_partitions.py            # Day 8 -> partitions/<name>/*.csv + spec
python week2/scripts/split_integrity.py            # Day 9 -> exchangeability + conformal coverage
python week2/scripts/make_rq3_evalset.py           # Day 10 -> rq3/<name>/ + labelling schema
python week2/scripts/classical_baselines.py        # Days 11-12 -> CIC baseline + results table
python week2/scripts/classical_baselines.py --datasets BoT-IoT UNSW-NB15 --jobs 1 --no-summary  # Day 13 -> BoT + UNSW artifacts
python week2/scripts/stats_harness.py              # Day 13 -> five-seed mean/std/95% CI (n_jobs=1)
python week2/scripts/leakage_check.py              # Day 13 -> no resample/duplicate-flow leakage
python week2/scripts/make_dummy_scores.py          # Day 14 -> interface/ dummy scores + self-check
python week2/scripts/freeze_package.py             # Day 14 -> FROZEN/ v1.0 (then --verify -> 0 mismatch)
python week1/scripts/make_manifest.py --verify     # one manifest pins Week-1 + Week-2 (0 mismatch)
```

## For Team B (QML)

- **Partitions:** `week2/partitions/<name>/` — MAQT trains on `train` (known classes), CQ-ZDR calibrates on
  `calibration` (known-only), evaluate `test` (accuracy) + `zeroday` (rejection). All three trio datasets
  are exchangeable (cal↔test two-sample AUROC ≈ 0.50, coverage ≈ 0.90 — [`w2_02`](reports/w2_02_split_integrity.md)).
  **Use marginal conformal for CIC** (4 rare classes block Mondrian).
- **RQ3:** `week2/rq3/<name>/` — perturb `adversarial_source_pool.csv` (clean known attacks) with FGSM/PGD
  in the **classical feature space before angle encoding**; keep the `origin × perturb` labels
  ([`w2_03`](reports/w2_03_rq3_eval_set.md)). **Never seed adversarials from the zero-day class.**
- **Score interface (Day 14):** `week2/interface/dummy_scores/<name>/{calibration,test,zeroday}_scores.parquet`
  is the stable, prototype-shaped contract — one row per partition row (`sample_id` = row index), with the
  full `fid__<class>` prototype-fidelity vector + `nonconformity = 1 − max_c F(ρ_x, ρ_c)`. Fill `fid__<class>`
  with real MAQT fidelities and every derived column follows (schema in `interface/dummy_scores_schema.json`;
  [`w2_06`](reports/w2_06_data_freeze.md)). Current values are synthetic placeholders (seed 42), not results.
  The **Week-3 CQ-ZDR calibration module** ([`../week3/README.md`](../week3/README.md)) consumes this
  interface directly and prices the first conformal threshold q.

## For the Day-11/12 baseline handoff

- **Detector:** `scripts/classical_baselines.py` fits a multiclass XGBoost detector on `train.csv` only.
  The emitted closed-set metrics are computed on known-only `test.csv`.
- **Novelty heads:** the same detector is paired with an Isolation Forest and a bottleneck autoencoder.
  Both heads fit known-only training rows; their thresholds come from known-only `calibration.csv` at
  `alpha=0.10`. The held-out `zeroday.csv` is never used for fitting or threshold selection.
- **Results:** `reports/_generated/baseline_results.csv` and `.json`; per-dataset models, predictions, and
  provenance live under `baselines/<name>/`. The first measured run is documented in
  [`reports/w2_04_classical_baselines.md`](reports/w2_04_classical_baselines.md).

*Note: the CSVs live under `week2/` (a self-contained deliverable), not under `datasets/<name>/`; the
unified manifest pins them by path + SHA-256 regardless of location.*

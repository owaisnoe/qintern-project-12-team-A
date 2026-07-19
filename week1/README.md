# QS-Net · Team A — Dataset Curation (Weeks 1–2)

Project 12 of QIntern 2026 — **QuantumSentinel / QS-Net**: benchmarking Variational Quantum Neural
Networks for zero-day and adversarial intrusion detection in IoT networks.
Mentors: Dr. Mohit Sajwan, Dr. Simranjit Singh · Members: Amon Koike, Mohammed Owais, Iwo Wojtakajtis.

Team A turns raw intrusion-detection datasets into standardized, reproducible, quantum-ready packages —
and (Week 2) into the exact conformal partitions + adversarial/zero-day sets QS-Net needs.

> **Benchmark scope (mentor-locked):** published results use **CIC-IoT2023 + BoT-IoT + UNSW-NB15** on the
> **v1.0 unified** schema. TON_IoT + Edge-IIoTset are **set aside** (unified zero-day collapses to 1–2 rows;
> v0.1 packages preserved for reference). See [`reports/17_unified_collapse_mentor_note.md`](reports/17_unified_collapse_mentor_note.md).
> **Qubit budget = 8.** Deterministic, **seed 42**.

## Week 1 — QADCP & standardized datasets (Days 1–7)

| Day | Deliverable | Files |
|---|---|---|
| 1 | Dataset comparison · feature inventory · attack summary (+ flaws) | [`reports/00`](reports/00_findings_and_flaws.md)–[`03`](reports/03_attack_summary.md) + [`feature_inventory.csv`](reports/feature_inventory.csv) |
| 2 | EDA · visualization dashboard · data-quality report | [`reports/04`](reports/04_eda_report.md)–[`06`](reports/06_visualization_dashboard.md) + `reports/dashboard.html` |
| 3 | Preprocessing pipeline + cleaned datasets | [`07`](reports/07_preprocessing_pipeline.md) + [`scripts/preprocess.py`](scripts/preprocess.py) → `datasets/<name>/processed/*_clean.parquet` |
| 4 | QADCP design + implementation | [`08`](reports/08_qadcp_design.md) + [`scripts/qadcp.py`](scripts/qadcp.py) → `datasets/<name>/qadcp/` (v0.1) |
| 5 | Difficulty-aware zero-day benchmark · PCA-8 baseline | [`09`](reports/09_zero_day_benchmark.md) + [`scripts/zero_day_tiers.py`](scripts/zero_day_tiers.py) · [`10`](reports/10_pca_baseline.md) + [`scripts/pca_baseline.py`](scripts/pca_baseline.py) |
| 6 | Unified feature schema (v1.0) + package | [`12`](reports/12_unified_schema.md) · [`13`](reports/13_unified_package.md) · [`METADATA.md`](METADATA.md) + [`schema/unified_schema.json`](schema/unified_schema.json) → `datasets/<name>/unified/qadcp/` |
| 7 | Final validation · handover · Team-B/C interfaces | [`14_handover_report.md`](reports/14_handover_report.md) · [`11_qsnet_interface.md`](reports/11_qsnet_interface.md) (→ B) · [`15_teamC_interface.md`](reports/15_teamC_interface.md) (→ C) · [`16_integration_meeting.md`](reports/16_integration_meeting.md) · [`scripts/validate_pipeline.py`](scripts/validate_pipeline.py) |

**Follow-ups:** [`17_unified_collapse_mentor_note.md`](reports/17_unified_collapse_mentor_note.md) (mentor benchmark
lock) · [`18_enriched_schema_exploration.md`](reports/18_enriched_schema_exploration.md) (superseded richer-schema
study; novel-dataset template) · [`19_dataset_challenges_and_strengths.md`](reports/19_dataset_challenges_and_strengths.md)
(mentor-requested challenges + strengths + novel-dataset design inputs).

## Week 2 — partitions, split integrity, RQ3, baselines, data freeze (Days 8–14)

Team-A focus: convert the curated datasets into the exact partitions the conformal guarantee needs, for the
**CIC / BoT / UNSW** trio.

| Day | Deliverable | Files |
|---|---|---|
| 8 | Partition spec + Train/Calibration/Test/Zero-Day CSVs | [`../week2/reports/w2_01_partition_spec.md`](../week2/reports/w2_01_partition_spec.md) + [`../week2/scripts/make_partitions.py`](../week2/scripts/make_partitions.py) → `week2/partitions/<name>/*.csv` |
| 9 | Split-integrity + conformal-exchangeability report | [`../week2/reports/w2_02_split_integrity.md`](../week2/reports/w2_02_split_integrity.md) + [`../week2/scripts/split_integrity.py`](../week2/scripts/split_integrity.py) |
| 10 | RQ3 adversarial-vs-zero-day eval set + labelling schema | [`../week2/reports/w2_03_rq3_eval_set.md`](../week2/reports/w2_03_rq3_eval_set.md) + [`../week2/scripts/make_rq3_evalset.py`](../week2/scripts/make_rq3_evalset.py) → `week2/rq3/<name>/` |
| 11-12 | Classical baselines (XGBoost + IsolationForest + Autoencoder) + unified metrics — the bar QS-Net must clear | [`../week2/reports/w2_04_classical_baselines.md`](../week2/reports/w2_04_classical_baselines.md) + [`../week2/scripts/classical_baselines.py`](../week2/scripts/classical_baselines.py) + [`baseline_metrics.py`](../week2/scripts/baseline_metrics.py) → `week2/baselines/<name>/` + `week2/tests/` (owned by Owais) |
| 13 | All-dataset baselines (+ One-Class SVM), 5-seed statistics harness, leakage check | [`../week2/reports/w2_05_day13_all_datasets.md`](../week2/reports/w2_05_day13_all_datasets.md) + [`../week2/scripts/stats_harness.py`](../week2/scripts/stats_harness.py) + [`leakage_check.py`](../week2/scripts/leakage_check.py) → `week2/baselines/{BoT-IoT,UNSW-NB15}/` (owned by Iwo) |
| 14 | DATA FREEZE v1.0 + prototype-shaped score interface + leakage-controls note | [`../week2/reports/w2_06_data_freeze.md`](../week2/reports/w2_06_data_freeze.md) + [`w2_07_leakage_controls.md`](../week2/reports/w2_07_leakage_controls.md) + [`../week2/scripts/make_dummy_scores.py`](../week2/scripts/make_dummy_scores.py) → `week2/FROZEN/` + `week2/interface/` (owned by Iwo) |

## Week 3 — conformal calibration (Days 15–18)

Team-A focus: own Algorithm 2 (CQ-ZDR) — split-conformal calibration on Team B's prototypes + the
coverage-verification pipeline. **CIC / BoT / UNSW.**

| Day | Deliverable | Files |
|---|---|---|
| 15 | CQ-ZDR conformal calibration module + first threshold q (CIC) | [`../week3/reports/w3_01_conformal_calibration.md`](../week3/reports/w3_01_conformal_calibration.md) + [`../week3/scripts/conformal_calibrate.py`](../week3/scripts/conformal_calibrate.py) → `q = s_(k)` on `week2/interface/` scores |
| 16–18 | Coverage harness + α-sweep → 5-seed significance protocol → all datasets | _in progress_ |

## Environment (Python 3.12 + venv)

System default is Python 3.9 — **always use the project venv (Python 3.12).**

```bash
cd qi26_12 && python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip && pip install -r requirements.txt
```

## Reproduce

```bash
source .venv/bin/activate                          # python --version -> 3.12.x
# --- Week 1 ---
python week1/scripts/preprocess.py                 # Day 3: clean -> processed/*_clean.parquet
python week1/scripts/bot_raw_resample.py           # BoT-IoT Theft recovery (rare-class raw re-run)
python week1/scripts/qadcp.py                       # Day 4: v0.1 splits -> qadcp/
python week1/scripts/pca_baseline.py && python week1/scripts/zero_day_tiers.py   # Day 5
python week1/scripts/unified_schema.py && python week1/scripts/qadcp.py --unified # Day 6: unified v1.0
python week1/scripts/pca_baseline.py --unified && python week1/scripts/zero_day_tiers.py --unified
python week1/scripts/validate_pipeline.py          # Day 7: final acceptance (ALL PASS)
# --- Week 2 (CIC / BoT / UNSW) ---
python week2/scripts/make_partitions.py            # Day 8: Train/Cal/Test/Zero-Day CSVs + spec
python week2/scripts/split_integrity.py            # Day 9: exchangeability + coverage
python week2/scripts/make_rq3_evalset.py           # Day 10: RQ3 adversarial/zero-day eval set
python week2/scripts/classical_baselines.py        # Days 11-13: baselines (+ --datasets BoT-IoT UNSW-NB15)
python week2/scripts/stats_harness.py && python week2/scripts/leakage_check.py    # Day 13: 5-seed stats + leakage
python week2/scripts/make_dummy_scores.py && python week2/scripts/freeze_package.py  # Day 14: interface + freeze
# --- Week 3 (conformal calibration) ---
python week3/scripts/conformal_calibrate.py --datasets CICIoT2023 --alpha 0.05    # Day 15: first threshold q
python week1/scripts/make_manifest.py --verify     # SHA-256 pins Weeks 1-3 (raw+curated+week2+week3 data), 0 mismatch
```

## Datasets — `datasets/<name>/{raw,processed,qadcp,unified}/` (git-ignored; pinned in `manifest/MANIFEST.md`)

`raw/` (source) · `processed/` (Day-3 clean) · `qadcp/` (v0.1 splits + `quantum/`) · `unified/` (v1.0 17-feature).
Week-2 CSVs land in `week2/partitions/<name>/` + `week2/rq3/<name>/`. All curated files carry a
**source URL + row count + SHA-256** pin — run `make_manifest.py --verify` before any experiment.

*Note: `reports/_drive_patch_q8fix_note.md` documents the Jul-2026 quantum-label fix for Team B re-sync.*

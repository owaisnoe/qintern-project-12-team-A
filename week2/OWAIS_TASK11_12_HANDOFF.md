# Owais - Week 2 Tasks 11-12 Handoff

This note covers the Task 11-12 contribution plus the existing issues found and fixed during the full
folder review. Merge the files listed under **Upload / merge** into the shared Team A folder.

## What was implemented

1. Classical baseline 1: multiclass XGBoost detector plus Isolation Forest zero-day novelty head.
2. Classical baseline 2: the same XGBoost detector plus the task-permitted bottleneck autoencoder
   zero-day novelty head.
3. Unified metrics: known-test Accuracy, F1-macro, macro OVR AUROC, binary attack metrics, and zero-day
   AUROC for known test versus held-out zero-day rows.
4. Leakage-safe split use: fit on `train`; choose marginal novelty thresholds on known-only
   `calibration`; evaluate only on `test` and `zeroday`. Zero-day data is never fit or tuned.
5. First Day-12 run on CICIoT2023, seed 42, with saved models, predictions, metrics, and provenance.

## Existing issues fixed during review

1. **Day-9 Windows execution error:** `week2/scripts/split_integrity.py` printed Greek mathematical
   symbols that crash under the default Windows `cp1252` console. Runtime log messages now use ASCII;
   the statistical methods and measured results are unchanged.
2. **Day-10 Pandas reproducibility warning:** `week2/scripts/make_rq3_evalset.py` relied on deprecated
   `DataFrameGroupBy.apply` behavior that differs across Pandas versions. It now uses an explicit,
   deterministic group loop. The three RQ3 packages were regenerated with the same row counts, class
   rules, and seed 42.
3. **Manifest coverage/path issue:** `week1/scripts/make_manifest.py` did not hash the new baseline
   artifacts and depended on platform-specific relative path separators. Baseline outputs are now pinned
   and manifest paths are normalized cross-platform.
4. **Environment documentation:** the setup instructions pointed to a nonexistent root requirements
   file. They now point to `week1/requirements.txt`, which also pins XGBoost and joblib.
5. **Prediction audit precision:** prediction scores are now written with full floating-point precision,
   so reloaded CSV scores reproduce the persisted models without serialization drift.

## Measured CICIoT2023 results

| Baseline | Accuracy | F1-macro | AUROC (macro OVR) | Zero-day AUROC |
|---|---:|---:|---:|---:|
| XGBoost + Isolation Forest | 0.9896 | 0.8043 | 0.9990 | 0.9956 |
| XGBoost + Autoencoder | 0.9896 | 0.8043 | 0.9990 | 0.9126 |

Secondary binary attack metrics: Accuracy 0.9954, F1-macro 0.9501, AUROC 0.9992.

## Upload / merge these files

### New Task 11-12 files

- `week2/OWAIS_TASK11_12_HANDOFF.md`
- `week2/scripts/baseline_metrics.py`
- `week2/scripts/classical_baselines.py`
- `week2/tests/test_baseline_metrics.py`
- `week2/tests/test_baseline_artifacts.py`
- `week2/reports/w2_04_classical_baselines.md`
- `week2/reports/_generated/baseline_results.csv`
- `week2/reports/_generated/baseline_results.json`
- `week2/baselines/CICIoT2023/autoencoder.joblib`
- `week2/baselines/CICIoT2023/isolation_forest.joblib`
- `week2/baselines/CICIoT2023/xgboost_detector.json`
- `week2/baselines/CICIoT2023/predictions.csv`
- `week2/baselines/CICIoT2023/results.json`

### Existing files intentionally updated for Tasks 11-12

- `week2/README.md` - adds Days 11-12 paths and reproduction command.
- `week1/README.md` - extends the Week-2 index through Day 12.
- `week1/UPLOAD.md` - adds the baseline handoff to the packaging list.
- `week1/requirements.txt` - pins `xgboost==3.2.0` and `joblib==1.5.3`.
- `week1/scripts/make_manifest.py` - teaches the manifest generator to include baseline artifacts and
  uses cross-platform relative paths.

If another teammate edited one of these five existing files after this folder was downloaded, merge the
small documented additions instead of overwriting their newer version.

### Existing review-fix files to update

- `week2/scripts/split_integrity.py`
- `week2/scripts/make_rq3_evalset.py`
- `week2/reports/_generated/split_integrity.json`
- `week2/reports/_generated/rq3_summary.json`
- `week2/rq3/BoT-IoT/*`
- `week2/rq3/CICIoT2023/*`
- `week2/rq3/UNSW-NB15/*`
- `datasets/*/unified/qadcp/validation_report.json` (validation refresh only; no dataset rows changed)
- `week1/reports/_generated/final_validation.json`
- `week1/manifest/manifest.json`
- `week1/manifest/MANIFEST.md`

No raw data, processed data, Week-1 split parquet, Week-2 partition CSV, Day 8-10 report, or RQ3 design
rule was changed.

## Do not upload

- `../.venv/`
- any `__pycache__/`

The archive includes the locally verified manifest snapshot. Regenerate it once after this contribution
is merged into the latest Drive master so it also reflects any newer files uploaded by other members:

```powershell
..\.venv\Scripts\python.exe week1\scripts\make_manifest.py
..\.venv\Scripts\python.exe week1\scripts\make_manifest.py --verify
```

## Verification performed

- Full CIC baseline run repeated with byte-identical model, prediction, and result hashes.
- 9 metric and persisted-artifact tests passed.
- Existing full pipeline validation passed.
- Local complete manifest verified with 434 files, 0 mismatch, 0 missing.
- Minimal smoke runs confirmed the runner accepts BoT-IoT and UNSW-NB15 for Day 13 extension.

## WhatsApp message

```text
Team A Week 2 - Days 11 and 12 completed (Classical Baselines)

I completed the classical baseline implementation and first measured run on CICIoT2023.

Deliverables:
1. week2/scripts/classical_baselines.py
   - Multiclass XGBoost detector
   - Isolation Forest zero-day novelty head
   - Bottleneck autoencoder zero-day novelty head (the permitted AE / OC-SVM option)
2. week2/scripts/baseline_metrics.py
   - Unified Accuracy, F1-macro, macro OVR AUROC, binary attack metrics, and zero-day AUROC
3. week2/reports/w2_04_classical_baselines.md
4. week2/baselines/CICIoT2023/
   - Saved XGBoost, Isolation Forest, and autoencoder models
   - Per-row test/zero-day predictions and results metadata
5. week2/reports/_generated/baseline_results.csv and .json
6. Added metric and persisted-artifact tests under week2/tests/

CICIoT2023 results (seed 42):
- XGBoost closed-set: Accuracy 0.9896, F1-macro 0.8043, macro OVR AUROC 0.9990
- Isolation Forest zero-day AUROC: 0.9956
- Autoencoder zero-day AUROC: 0.9126
- Secondary binary attack metrics: Accuracy 0.9954, F1-macro 0.9501, AUROC 0.9992

Split/leakage contract:
- Models fit on train only
- Marginal novelty thresholds selected from known-only calibration at alpha=0.10
- Test and held-out Mirai zero-day data used only for final evaluation
- No zero-day rows used for fitting or threshold tuning

Validation:
- 9 tests passed
- Full CIC run reproduced byte-identically
- Existing full pipeline validation passed
- The runner also accepts BoT-IoT and UNSW-NB15 for the Day-13 extension

I am uploading one merge package containing Tasks 11-12 plus the review fixes below. It does not change
the Day 8-10 design, reports, or partition data.
During the review I also fixed two existing reproducibility/runtime issues:
- Day-9 split_integrity.py could crash on the default Windows console because of Unicode log symbols.
- Day-10 make_rq3_evalset.py used deprecated Pandas groupby.apply behavior that produced
  version-dependent output bytes. I replaced it with deterministic grouping and regenerated the three
  RQ3 packages with unchanged counts, labels, split rules, and seed 42.

I also updated the manifest generator to hash the baseline artifacts with cross-platform paths and fixed
the requirements-file setup path. Prediction scores are stored at full precision for independent reload
checks. No raw data, partition CSVs, split parquets, or Day 8-10 reports were changed. After merging into
the latest Drive master, the shared manifest should be regenerated once.
```

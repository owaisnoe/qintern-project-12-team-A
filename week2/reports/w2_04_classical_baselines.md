# Week 2 - Days 11-12: Classical Baselines

**QS-Net / QuantumSentinel - Team A** - benchmark dataset: **CICIoT2023** - seed: **42**.

This report implements the Day-11 classical baselines and the Day-12 shared metrics wiring. The
benchmark trio and split contract are inherited unchanged from Days 8-10:
`week2/partitions/CICIoT2023/{train,calibration,test,zeroday}.csv`.

## Scope and leakage contract

| Data | Use |
|---|---|
| `train.csv` (151,049 rows) | Fit the multiclass detector and both novelty heads. Only known classes occur here. |
| `calibration.csv` (18,883 rows) | Select each novelty threshold at `alpha = 0.10`; no model fitting. |
| `test.csv` (18,883 rows) | Closed-set known-class metrics and the known side of zero-day AUROC. |
| `zeroday.csv` (10,984 rows) | Held-out Mirai families; evaluation only, never fit or tune. |

The runner hard-validates the feature order, finite numeric values, known-class membership, binary-label
consistency, and zero-day isolation before fitting. The Week-1 unified features are already robust-scaled
with train-fitted parameters; no test-derived transformation is introduced here.

## Implemented baselines

### Baseline 1 - XGBoost detector + Isolation Forest novelty head

The detector is an XGBoost `multi:softprob` classifier over the 31 known CIC classes. It uses all
151,049 training rows, 120 histogram boosting rounds, depth 6, learning rate 0.10, 0.90 row and column
subsampling, and tempered inverse-frequency sample weights. The Isolation Forest is fitted on a
deterministic class-capped (2,000 rows per known class) training subset with 300 trees and
`max_samples=2048`.

The novelty score is the negated Isolation Forest `score_samples` value, so larger means more novel.
Its threshold is the finite-sample split-conformal upper quantile of calibration scores. A row is flagged
only when its score is strictly above that threshold.

For CIC this is a **marginal** threshold over the full known calibration set, matching the Day-9
recommendation; the four known classes with fewer than ten calibration rows are not given sparse
class-conditional thresholds.

### Baseline 2 - XGBoost detector + bottleneck autoencoder novelty head

The same detector is deliberately reused so the novelty-head comparison is controlled. The autoencoder
is a train-only `17 -> 12 -> 6 -> 12 -> 17` `MLPRegressor` with ReLU activations, Adam optimisation,
early stopping, and a train-fitted `StandardScaler`. It uses the same class-capped known-only subset as
the Isolation Forest. Reconstruction MSE is the novelty score, again with the calibration-only
conformal threshold.

The task permits an Autoencoder or One-Class SVM; this package selects the autoencoder because it scales
to the shipped checkpoint sizes without an O(n^2) kernel fit. The runner's head interface makes an
OC-SVM replacement possible without changing the split or metric contract.

## Day-12 results (primary table)

Accuracy, F1-macro, and macro one-vs-rest AUROC are measured on **known-only test rows** using the
multiclass detector. Zero-day AUROC compares those known test rows (label 0) with the held-out Mirai
rows (label 1) using only the named novelty head.

| Baseline | Accuracy | F1-macro | AUROC (macro OVR) | Zero-day AUROC |
|---|---:|---:|---:|---:|
| XGBoost + Isolation Forest | 0.9896 | 0.8043 | 0.9990 | **0.9956** |
| XGBoost + Autoencoder | 0.9896 | 0.8043 | 0.9990 | 0.9126 |

The shared detector's secondary binary attack metrics are Accuracy **0.9954**, F1-macro **0.9501**,
and AUROC **0.9992** (derived from the multiclass probabilities and `label_binary`). They are emitted
in `reports/_generated/baseline_results.csv` for consumers whose comparison is threat-vs-benign rather
than per-attack-class.

## Novelty calibration diagnostics

| Head | Calibration threshold | Known-test false-positive rate | Zero-day true-positive rate | FPR at 95% TPR |
|---|---:|---:|---:|---:|
| Isolation Forest | 0.4776 | 0.1012 | **0.9998** | 0.0085 |
| Autoencoder | 0.4314 | 0.1014 | 0.6611 | 0.2262 |

The approximately 10% known rejection is expected from the `alpha=0.10` calibration target (ties can
make the empirical rate slightly exceed the target). These thresholded diagnostics are not substitutes
for AUROC; they show the operating point that Team B can reproduce.

## Reproduction

From `Team A` with the pinned environment from `../.venv`:

```bash
..\\.venv\\Scripts\\python.exe week2/scripts/classical_baselines.py --datasets CICIoT2023
```

The command writes:

- `week2/baselines/CICIoT2023/xgboost_detector.json`
- `week2/baselines/CICIoT2023/isolation_forest.joblib`
- `week2/baselines/CICIoT2023/autoencoder.joblib`
- `week2/baselines/CICIoT2023/predictions.csv`
- `week2/baselines/CICIoT2023/results.json`
- `week2/reports/_generated/baseline_results.csv` and `baseline_results.json`

All model settings, feature names, row counts, class mappings, package versions, score direction, and
the no-zero-day-fitting assertion are recorded in `results.json`. The per-row prediction file contains
the detector prediction, attack probability, both novelty scores, and calibrated flags for `test` and
`zeroday` rows.

## Limitations and interpretation

These are checkpoint-scale results, not full raw-stream estimates. CIC has a severe known-class
imbalance, so the primary F1 is macro-averaged and rare classes should be read alongside their support
in `partition_meta.json`. AUROC is ranking-based and does not imply calibrated probabilities. The
zero-day score measures rejection of the held-out Mirai families, not correct classification into a
Mirai subclass. Days 13-14 can reuse the same runner for BoT-IoT and UNSW-NB15 without changing the
feature or split contract.

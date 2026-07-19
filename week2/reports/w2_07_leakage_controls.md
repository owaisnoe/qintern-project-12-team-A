# Leakage Controls — Fit-on-Train, Known-Only Calibration, and CIC Verification

A single citable summary of how QS-Net's data pipeline prevents leakage between model fitting and threshold
selection, and how the CIC-IoT2023 leakage concern was specifically verified. Consolidates
[`../../week1/reports/08_qadcp_design.md`](../../week1/reports/08_qadcp_design.md),
[`../../week1/reports/00_findings_and_flaws.md`](../../week1/reports/00_findings_and_flaws.md),
[`w2_02_split_integrity.md`](w2_02_split_integrity.md) and
[`w2_05_day13_all_datasets.md`](w2_05_day13_all_datasets.md). Trio: CIC-IoT2023 + BoT-IoT + UNSW-NB15.

## 1. The model is fit on training data only

Everything that *learns* from data is fit on the **`train`** split and only *applied* to the others
(`08_qadcp_design.md`, split-first design):

| Fitted object | Fit on | Applied to |
|---|---|---|
| Correlation pruning (drop one of each \|r\| ≥ 0.95 pair) | train | all splits |
| Median/IQR robust scalers (`scalers.json`) | train | calibration / test / zero-day |
| Angle-encoding min/max (→ [0, π]) | train | calibration / test / zero-day |
| Feature ranking / qubit-budget selection | train | all splits |

Executing the pipeline in task-sheet order (scale, then split) would fit scalers on all data and leak; the
QADCP is deliberately **split-first, fit-on-train**.

## 2. The conformal threshold is calibrated on held-out KNOWN-class data — never on the unknown class

The calibration set is data **held out from training** (unseen by the model), but it is **known-class**
data. The unknown / zero-day class is **never** used for fitting *or* for threshold calibration — it appears
only at test time. This is by design: calibrating the threshold on the unknown class would itself leak the
very signal we are trying to detect.

- `calibration.csv` = **known classes only**, disjoint from `train`
  ([`w2_01_partition_spec.md`](w2_01_partition_spec.md)).
- CQ-ZDR threshold `q = s_(k)`, `k = ⌈(1−α)(n+1)⌉`, is the split-conformal quantile of the nonconformity
  score over that known-only calibration set ([`../../week3/reports/w3_01_conformal_calibration.md`](../../week3/reports/w3_01_conformal_calibration.md)).
- The held-out zero-day class (`zeroday.csv`) is used only to *measure* detection, never to fit or calibrate.

So neither the model nor the threshold ever sees the test set or the unknown class.

## 3. CIC-IoT2023 leakage: cause and verification

**Cause.** CIC-IoT2023's leakage vector is **repeated / near-duplicate flows**, not identifier columns —
the CIC feature set contains **no** raw IP / port / MAC / timestamp identifier columns
(`00_findings_and_flaws.md`: CIC leaky-identifier count = *none*; the 14 identifier columns belong to
BoT-IoT and the 4 to TON-IoT, and are dropped there). A naive random split of repeated flows would place
near-identical rows in both train and test.

**Prevention (Day 4).** De-duplicate on the feature columns *before* splitting so one feature vector can
land in only one split (`08_qadcp_design.md`).

**Verification (Days 9 & 13).**

| Check | Method | CIC-IoT2023 result |
|---|---|---|
| Cross-split flow overlap | feature-content hashes (`leakage_check.py`) | train↔cal, train↔test, cal↔test, *↔zeroday all **0** |
| Within-split duplication | unique feature rows / rows | train/cal/test/zeroday all **0.0** (151,049 / 18,883 / 18,883 / 10,984 unique) |
| Calibration vs test distribution | classifier two-sample test (RF, 5-fold) | AUROC **0.4999** — indistinguishable ⇒ exchangeable |
| Distribution shift | total-variation distance (cal vs test) | TVD **0.0000** |
| Split-conformal coverage | empirical coverage at α = 0.10 | **0.9019** (≈ target 0.90) |

Because disjointness is asserted on **feature-content hashes** (not row indices), a duplicated flow shared
across splits would be caught; CIC passes on every check.

## References

- Angelopoulos & Bates, *A Gentle Introduction to Conformal Prediction* (2023); Barber, Candès, Ramdas &
  Tibshirani, *Conformal Prediction Beyond Exchangeability* (Ann. Stat., 2023) — exchangeability and coverage.
- Bates, Candès, Lei, Romano & Sesia, *Testing for Outliers with Conformal p-values* (Ann. Stat., 2023) —
  the known-only-calibration novelty test.

*Reproduce: `python week2/scripts/leakage_check.py` → `reports/_generated/day13_leakage_check.json`;
`python week2/scripts/split_integrity.py` → `reports/_generated/split_integrity.json`.*

# AK — Week 4 Days 18-20 Handoff (Coverage Table, Zero-Day Recall, Conformal-vs-Heuristic Ablation)

Covers AK's Week-4 contribution: the all-datasets coverage table v1 (Day 18, the Week-3 seam into Day 24),
the zero-day detection recall + quantum-vs-classical novelty comparison (Day 19), and the heuristic-threshold
baseline + conformal ablation (Day 20). All reuse the Week-3 conformal/coverage/statistics code and Owais's
Day-16/17 harnesses. Team A owns Proposition 3 (conformal coverage); Days 18-20 are the detection-power +
ablation half. Days 21-25 (integration week with Team B) continue from here.

## What was implemented

1. **Day 18 — coverage table v1 (all datasets)** (`week3/scripts/coverage_table.py`,
   `week3/reports/w3_04_coverage_table.md`). Thin assembler over `coverage_harness.verify_dataset` (single
   source of the conformal math + exact BetaBinomial band). Per dataset: n_cal, k, q, target α, achieved
   false-zero-day rate, band, verdict. The seam into Week-4 Day 24 (RQ2, all datasets).
2. **Day 19 — zero-day recall + quantum-vs-classical** (`week4/scripts/zeroday_recall.py`,
   `week4/reports/w4_01_zeroday_recall.md`). True-zero-day recall at the calibrated α = 0.05, reported
   **together with coverage** (Proposition 3 §5.2: the guarantee bounds false alarms only). The quantum arm
   reuses the Day-15 module (zero-day rejection = recall). The classical arm reloads the frozen Day-12
   Isolation-Forest / OC-SVM / Autoencoder models (no refit) and re-thresholds them at the **same α** with the
   same rule — one primary α for both arms.
3. **Day 20 — heuristic-threshold baseline + conformal ablation** (`week4/scripts/heuristic_ablation.py`,
   `week4/reports/w4_02_heuristic_ablation.md`). The fair remove-conformal ablation: same score, heuristic =
   in-sample (1−α) quantile (no held-out split, no `+1`). Three contrasts — fixed cutoff, small-n bias, full-n
   α-sweep — plus a drift figure and the non-squared-fidelity integration spec.

## What went well

- **Pure reuse.** All three modules build on the Week-3 single-source conformal/coverage code and the frozen
  Day-12 models — no math re-implemented, no baseline refit; the full suite grew 52 → 67 tests, all green.
- **The coverage-vs-power story is clean:** every system holds coverage ≈ 1−α at the same α, and recall is the
  axis that separates them — exactly what the paper needs.
- **The ablation demonstrates the Proposition-3 upgrade concretely** — the no-`+1` heuristic is measurably
  anti-conservative at small n, and a fixed cutoff cannot track α, while conformal holds the exact band.
- **Caught the fidelity-convention trap** (libraries return F²) and turned it into a documented Team-B spec.

## Challenges and issues

1. **Dummy vs real.** Team B's real prototypes are not ready, so the quantum arm (Day 19) and all Day-20
   fidelity results are Day-14 **placeholders**; only the Day-19 classical column is real. Every output tags
   `source_kind` and reprices with `--source real --scores-root <dir>` — no code change.
2. **No `train` split in the interface.** The pure in-sample-optimism drift (Day-20 contrast C) needs a
   `train_scores.parquet`; on the dummy the in-sample is a calibration proxy, so the demonstrable-now story is
   the fixed-cutoff and small-n contrasts. The headline drift auto-sharpens on Team B's real train fidelities.
3. **CIC has no OC-SVM head** (Day-12 shipped IF + Autoencoder) — Day 19 skips it gracefully (IF + AE for CIC)
   and annotates; not synthesized.
4. **α reconciliation.** The classical baselines default to α = 0.10; Day 19 re-thresholds at α = 0.05 (α only
   sets the threshold, so reload-and-re-threshold is exact) for a like-for-like comparison.

## Concerns and recommendations

- **Team B:** the fidelity score must use **non-squared** Uhlmann F; PennyLane/Qiskit return F² — `sqrt()`
  before writing the interface or pass `--assume-fidelity-squared`. Use **one primary α** for the quantum
  detector and the classical baselines. Emit a `train` split if the in-sample-optimism drift is wanted as a
  headline before real fidelities land.
- **Report coverage AND recall together** (never recall alone); keep marginal conformal for CIC and abstain if
  a calibration split has `n < 1/α − 1`.
- **Manifest on a git clone:** `make_manifest.py --verify` reports **467 OK, 0 mismatch, 198 missing** — the
  198 raw-data/zip pins live outside git and are re-downloaded per `week1/README.md`; document as expected, or
  add a `--scope git` flag. Team decision.

## Measured results (Days 18-20, dummy interface, α = 0.05)

**Day 18 — coverage table:** CIC q 0.300551 / FZR 0.0486 / PASS; BoT 0.262934 / 0.0530 / PASS (inside the
exact 99% band, p = 0.090); UNSW 0.383380 / 0.0463 / PASS. All three hold inside the band.

**Day 19 — zero-day recall (coverage ≈ 0.95 for every row):**

| Dataset | system | scores | zero-day recall |
|---|---|---|---:|
| CIC | quantum_cqzdr | dummy | 0.9998 |
| CIC | isolation_forest | real | 0.9978 |
| CIC | autoencoder | real | 0.4994 |
| BoT | quantum_cqzdr | dummy | 0.0952 |
| BoT | isolation_forest | real | 0.7233 |
| BoT | ocsvm | real | 0.7218 |
| BoT | autoencoder | real | 0.5417 |
| UNSW | quantum_cqzdr | dummy | 0.3857 |
| UNSW | isolation_forest | real | 0.0000 |
| UNSW | ocsvm | real | 0.0033 |
| UNSW | autoencoder | real | 0.2656 |

UNSW is the hard bar — classical IF/OC-SVM ≈ 0 recall on the Shellcode+Worms zero-day. Quantum column is a
dummy placeholder; reprices on real prototypes.

**Day 20 — ablation:** fixed cutoff τ=0.5 → FZR 0.0013 / 0.0009 / 0.0075 (α-independent, 8× per-dataset
variance); in-sample no-`+1` heuristic mean FZR at n=30 ≈ 0.096 (CIC), 0.095 (BoT), 0.092 (UNSW) vs conformal
≈ 0.032 — anti-conservative, exceeds α; 60/60 α-sweep computed, conformal holds the band.

## References

- Angelopoulos & Bates 2023 (the quantile + coverage/informativeness); Bates, Candès, Lei, Romano & Sesia 2023
  (conformal outlier p-values — finite-sample Type-I control); Vovk/Gammerman/Shafer 2005 (split-conformal
  validity + the `+1`); Novello, Dalmau & Andéol 2024 (finite-sample optimism of heuristic OOD thresholds);
  Liang, Sesia & Sun 2024 (conformal OOD). Different-score baselines (a separate comparison, not this
  ablation): Hendrycks & Gimpel 2017 (MSP), Lee et al. 2018 (Mahalanobis), Liu et al. 2020 (energy).
  Fidelity conventions: Jozsa 1994 (squared) vs Nielsen & Chuang 2010 (non-squared root fidelity).

## Do not commit
- `../.venv/`, any `__pycache__/` (gitignored); the raw dataset archives (~41 GB, outside git — pinned by the
  manifest and re-downloaded from source). *(Small `_generated/` result files and the drift figure ARE
  committed, matching the repo convention, so teammates see results without re-running.)*

## Verification performed
- `python -m pytest week2/tests week3/tests week4/tests` → 67 passed.
- `coverage_table.py` → 3/3 PASS at α=0.05; `zeroday_recall.py` → 11 rows, coverage ≈ 0.95 every row, quantum
  recall reproduces `calibrate_dataset`; `heuristic_ablation.py` → heuristic anti-conservative at small n,
  conformal in-band, drift figure written.

## Chat update

```text
Team A - Week 4 Days 18 to 20 done and on the week4-ak branch.

Day 18 (coverage table v1, all datasets): conformal false-zero-day rate holds inside the exact 99 percent
band at alpha 0.05 on all three - CIC 0.0486, BoT 0.0530, UNSW 0.0463, all PASS. The seam into Day 24 RQ2.

Day 19 (zero-day recall + quantum vs classical): recall reported together with coverage (coverage controls
false alarms only). All systems calibrated at the same alpha 0.05, coverage about 0.95 everywhere, but recall
differs a lot. Classical zero-day recall: CIC IsolationForest 0.998, BoT IF 0.72 and OC-SVM 0.72, UNSW IF
0.00 and OC-SVM 0.003 - UNSW is the hard bar (Shellcode plus Worms). The quantum column is still the Day-14
dummy interface and reprices when Team B ships real fidelities.

Day 20 (conformal vs heuristic ablation): removing conformal forfeits the guarantee. A fixed cutoff is
alpha-independent and swings per dataset; the in-sample percentile with no plus-one correction is
anti-conservative (mean false-alarm about 0.096 at n=30 vs conformal 0.032). Conformal holds the exact band.
Alpha-sweep 0.01 to 0.20 plus a drift figure.

Integration spec for Team B: the fidelity score must use non-squared Uhlmann F. PennyLane qml.math.fidelity
and Qiskit state_fidelity return F squared - take the square root before writing the interface, or pass
--assume-fidelity-squared. And use one primary alpha for the quantum detector and the classical baselines.

To confirm: real CIC prototype timing from Team B; the non-squared fidelity and single-alpha agreement; and
the manifest note (a fresh git clone verifies 467 of 665 pins, the 198 raw-data files live outside git and
are re-downloaded).

Full suite 67 tests green. Days 21 to 25 (integration week) next. Thanks.
```

# QS-Net · Team A — Week 4 (Days 19–25): Conformal Integration, Zero-Day Evaluation & Significance

Project 12 of QIntern 2026 — **QuantumSentinel / QS-Net**. This is the **Week-4 package index**. Team A owns
the paper's **Proposition 3 (conformal coverage)**; Week 4 adds the **detection-power + ablation** half —
zero-day recall vs classical baselines and the conformal-vs-heuristic ablation — then hands a frozen
calibration/stats package to Team B for the integration days. Trio **CIC-IoT2023 + BoT-IoT + UNSW-NB15**;
qubit budget 8; seed 42.

> Docs are unified in `week1/` — entry point [`../week1/README.md`](../week1/README.md) and the single
> checksum manifest [`../week1/manifest/MANIFEST.md`](../week1/manifest/MANIFEST.md) cover Weeks 1–4. Day 18
> ("coverage table v1", all datasets) lands in `week3/` as the seam into Day 24. These modules consume the
> **Day-14 score interface** ([`../week2/interface/`](../week2/interface)); Team B's real prototypes reprice
> at the same schema with `--source real --scores-root <dir>` (no code change).

## Contents

| Day | Deliverable | Report | Code |
|---|---|---|---|
| **18** (week3) | Coverage table v1, all datasets — DONE | [`../week3/reports/w3_04_coverage_table.md`](../week3/reports/w3_04_coverage_table.md) | [`../week3/scripts/coverage_table.py`](../week3/scripts/coverage_table.py) |
| **19** | **Zero-day recall + quantum-vs-classical novelty** — DONE | [`reports/w4_01_zeroday_recall.md`](reports/w4_01_zeroday_recall.md) | [`scripts/zeroday_recall.py`](scripts/zeroday_recall.py) |
| **20** | **Heuristic-threshold baseline + conformal ablation** — DONE | [`reports/w4_02_heuristic_ablation.md`](reports/w4_02_heuristic_ablation.md) | [`scripts/heuristic_ablation.py`](scripts/heuristic_ablation.py) |
| **21** | **Freeze the calibration + statistics interface for integration** — DONE | [`INTEGRATION/INTEGRATION_PACKAGE.md`](INTEGRATION/INTEGRATION_PACKAGE.md) | [`scripts/freeze_integration.py`](scripts/freeze_integration.py) → `INTEGRATION/` (frozen `q` + contract + manifest) |
| **22** | **Connect conformal module to Team B inference; first end-to-end decisions** — DONE | [`reports/w4_03_conformal_integration.md`](reports/w4_03_conformal_integration.md) | [`scripts/conformal_integration.py`](scripts/conformal_integration.py) → `reports/_generated/w4_03_*` |
| **23** | **Live coverage result + exchangeability audit** — DONE | [`reports/w4_04_live_coverage.md`](reports/w4_04_live_coverage.md) | [`scripts/live_coverage.py`](scripts/live_coverage.py) → `reports/_generated/w4_04_*` (drives the Day-22 adapter; does not recalibrate) |
| **24** | RQ2 results (all datasets): recall + achieved α; Table B skeleton | _pending_ | builds on Day-18 table |
| **25** | Full significance testing QS-Net vs baselines; RQ5 honesty notes | _pending_ | reuses [`../week3/scripts/stats_protocol.py`](../week3/scripts/stats_protocol.py) |

**Day-19/20 headline (dummy interface, α = 0.05):** every system (quantum + classical) holds coverage ≈ 0.95
at the same α, but **zero-day recall differs** — the paper's separation (coverage ≠ power). UNSW is the hard
bar (classical IF/OC-SVM ≈ 0 recall on Shellcode+Worms). The no-`+1` heuristic is anti-conservative (mean FZR
≈ 0.096 at n=30 vs conformal ≈ 0.032); a fixed cutoff is α-independent and varies per dataset — conformal
holds the exact band.

**Day-23 headline:** run live through the Day-22 adapter at the **frozen** q, dataset 1 achieves FZR
0.0486 — ≤ α and inside the exact 99% band (p = 0.73) — with |Δq| = 7e-8 (pure 6-dp rounding of the
published threshold) and the per-row decisions CSV byte-consistent with the in-process run. The
exchangeability assumption survives an 18-cell Holm-corrected audit (6 tests × 3 datasets — BoT/UNSW are
audited pre-Day-24 even though only dataset 1 is frozen) with **zero violations**, and nine
injected-violation drills confirm the audit has power: calibration trimming and test-score shift roughly
double the FZR and are caught; a class-mix skew is caught by χ² (p ≈ 1e-209) *without* moving the pooled
rate — exactly the failure a coverage-only check cannot see. The `class_mix_chi2 = 0` rows are a dummy
artifact (the Day-14 generator mirrors class counts calibration→test), flagged in the report.

## Reproduce

```bash
source ../.venv/bin/activate                                                   # Python 3.12
python week3/scripts/coverage_table.py --alpha 0.05 --sweep-csv week3/reports/_generated/w3_02_alpha_sweep.csv
python week4/scripts/zeroday_recall.py     --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05 --heads isolation_forest ocsvm autoencoder
python week4/scripts/heuristic_ablation.py --datasets CICIoT2023 BoT-IoT UNSW-NB15 --alpha 0.05 --sweep 0.01 0.20 0.01 --small-n-demo 30 50 100 200
python week4/scripts/freeze_integration.py                                      # Day 21 -> INTEGRATION/ (frozen q + contract + manifest)
python week4/scripts/freeze_integration.py --verify                             # Day 21 -> re-hash, expect 0 mismatch
python week4/scripts/conformal_integration.py --datasets CICIoT2023             # Day 22 -> first end-to-end decisions (dataset 1)
python week4/scripts/live_coverage.py --alpha 0.05 --drills                     # Day 23 -> live coverage + exchangeability audit
python -m pytest week2/tests week3/tests week4/tests -q                          # full suite: 91 tests
```

## For Team B (QML) — integration spec

- **Score = non-squared Uhlmann fidelity.** The nonconformity score `s = 1 − max_c F(ρ_x, ρ_c)` requires
  amplitude fidelity `F ∈ [0,1]`, **not** F². **PennyLane `qml.math.fidelity` and Qiskit `state_fidelity`
  return the SQUARED overlap F²** → emit `sqrt()` of that into the `fid__<class>` columns, or the pipeline runs
  with `--assume-fidelity-squared`. `s`, `F_in`, and `F_out` must all use the same convention.
- **Single primary α.** Calibrate the quantum detector and the classical baselines at the **same α** (Day 19
  uses one α for both) — otherwise the Day-25 significance comparison is not like-for-like.
- **Marginal conformal for CIC** (its four ≤ 9-row known classes make class-conditional infeasible); abstain
  if a calibration split has `n < 1/α − 1` (≥ 19 at α = 0.05).
- Swap real fidelities into the Day-14 interface schema and rerun with `--source real --scores-root <your dir>`.
  For the Day-20 in-sample-optimism drift, emit a `train_scores.parquet` too (prototypes are fit on train).

*Notes: CIC-IoT2023 has no OC-SVM head (Day-12 shipped IF + Autoencoder). Edge-IIoTset / TON_IoT have no
partitions/interface and are excluded (locked trio only).*

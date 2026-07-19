# QS-Net · Team A — Week 3 (Days 15–18): Conformal Calibration, Coverage & Statistics

Project 12 of QIntern 2026 — **QuantumSentinel / QS-Net**. This is the **Week-3 package index**.
Team A owns the paper's statistical-guarantee centrepiece: implement **split-conformal calibration
(Algorithm 2 / CQ-ZDR)** on Team B's prototypes and build the **coverage-verification** pipeline, for the
mentor-locked trio **CIC-IoT2023 + BoT-IoT + UNSW-NB15**. **Qubit budget = 8 · seed 42.**

> **Docs are unified in `week1/`** — entry point [`../week1/README.md`](../week1/README.md), upload guide
> [`../week1/UPLOAD.md`](../week1/UPLOAD.md), and the single checksum manifest
> [`../week1/manifest/MANIFEST.md`](../week1/manifest/MANIFEST.md) all cover Weeks 1–3. This file is just the
> Week-3 index. The Day-15/16 modules consume the **Day-14 score interface**
> ([`../week2/interface/dummy_scores/`](../week2/interface); real prototypes swap in at the same schema).
> Per-day handoffs: [`AK_TASK15_HANDOFF.md`](AK_TASK15_HANDOFF.md) ·
> [`OWAIS_TASK16_17_HANDOFF.md`](OWAIS_TASK16_17_HANDOFF.md).

## Contents

| Day | Deliverable | Report | Code / data |
|---|---|---|---|
| **15** | **CQ-ZDR conformal calibration module + first threshold q (dataset 1 = CIC)** — DONE | [`reports/w3_01_conformal_calibration.md`](reports/w3_01_conformal_calibration.md) | [`scripts/conformal_calibrate.py`](scripts/conformal_calibrate.py) + `reports/_generated/w3_01_conformal_calibration.{json,csv}` + [`tests/test_conformal_calibrate.py`](tests/test_conformal_calibrate.py) |
| **16** | **Coverage-verification harness (exact finite-sample band) + α-sweep 0.01–0.20** — DONE | [`reports/w3_02_coverage_harness.md`](reports/w3_02_coverage_harness.md) | [`scripts/coverage_harness.py`](scripts/coverage_harness.py) + `_generated/w3_02_*` + [`figures/w3_02_coverage_curve.png`](reports/figures/w3_02_coverage_curve.png) + [`tests/test_coverage_harness.py`](tests/test_coverage_harness.py) |
| **17** | **5-seed statistics protocol (mean±std, 95% CI, paired t, McNemar, Holm–Bonferroni, d_z) + dry-run** — DONE | [`reports/w3_03_significance_dryrun.md`](reports/w3_03_significance_dryrun.md) | [`scripts/stats_protocol.py`](scripts/stats_protocol.py) + `_generated/w3_03_*` + [`tests/test_stats_protocol.py`](tests/test_stats_protocol.py) (cross-checks all 78 cells of [`../week2/scripts/stats_harness.py`](../week2/scripts/stats_harness.py)'s output) |
| **18** | Extend calibration + coverage to all three datasets; coverage table v1 | _pending — unblocked_ | both modules already run all three; `_generated/w3_02_alpha_sweep.csv` already carries the per-dataset achieved-FZR-vs-α columns coverage-table-v1 needs |

**Day-15 result (dummy interface, α = 0.05): first threshold q (CIC) = 0.300551**, known-test coverage
0.9514, false-zero-day 0.0486 (≤ α). Placeholder until Team B's real prototypes land.
**Day-16 result:** all three datasets inside the exact 99% finite-sample coverage band at every α in
0.01–0.20 (**60/60 PASS**) — including BoT-IoT's 0.0530, which violates the naive bound but is ordinary
sampling noise (p = 0.090). **Day-17 result:** protocol cross-checks all 78 of Iwo's Day-13 stat cells
(0 mismatches); Holm-corrected dry-run finds 3 real baseline gaps (|d_z| ≥ 5) and correctly kills a
spurious raw p = 0.011.

## Reproduce

```bash
source ../.venv/bin/activate                                    # Python 3.12
python week3/scripts/conformal_calibrate.py --datasets CICIoT2023 --alpha 0.05   # Day 15 -> first q + coverage
python week3/scripts/coverage_harness.py                        # Day 16 -> exact-band verdicts + sweep + figure
python week3/scripts/stats_protocol.py                          # Day 17 -> significance dry-run
python -m pytest week3/tests -q                                 # 28 tests (11 + 9 + 8)
python week1/scripts/make_manifest.py --verify                 # manifest check (see note below)
```

*Manifest note: expected `--verify` output on a **git clone** is `467 OK, 0 mismatch, 198 missing` — the 198
"missing" are the raw-data files (`datasets/*/raw/`, source zips, ~41 GB) that live outside git by design;
re-download them per the week-1 README to verify source provenance. 0 mismatch is the health signal.*

## For Team B (QML)

Calibrate CQ-ZDR on `week2/partitions/<name>/calibration` (**known classes only**); the nonconformity score
is `s = 1 − max_c F(ρ_x, ρ_c)` and the threshold is `q = s_(k)`, `k = ⌈(1−α)(n+1)⌉`; flag a test point as
zero-day iff `s > q`. **Use marginal conformal for CIC** (its four ≤ 9-row known classes make Mondrian
degenerate at α = 0.05). Build each prototype `ρ_c` from **train only** — calibration must stay out-of-sample
or the threshold is optimistic. Swap real fidelities into the Day-14 interface schema and rerun
`conformal_calibrate.py --source real --scores-root <your dir>` with no code change — **then run the Day-16
gate**: `coverage_harness.py --source real --scores-root <your dir>`. Validity (`finite_sample_ok`) should
still PASS on real prototypes; a FAIL means the plumbing broke exchangeability (e.g., prototypes touched
calibration rows), which is exactly what the gate exists to catch. The power panel is the number that
genuinely changes.

## For Team C (selectors) & the paper's results sections

The **complete comparison protocol** — mean±std/95% CI, seed-paired t-test, Cohen's d_z, exact McNemar,
Holm–Bonferroni over a declared family — lives in [`scripts/stats_protocol.py`](scripts/stats_protocol.py)
(scipy-only; per-seed CI generation stays in
[`../week2/scripts/stats_harness.py`](../week2/scripts/stats_harness.py)). Every comparison table in
Articles 1–2 should pass through `holm_bonferroni` with the family declared in the caption, and report d_z
beside every p (n = 5 seeds — see `reports/w3_03_significance_dryrun.md` §4 for the conventions).

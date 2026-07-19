# QS-Net · Team A — Week 3 (Days 15–18): Conformal Calibration, Coverage & Statistics

Project 12 of QIntern 2026 — **QuantumSentinel / QS-Net**. This is the **Week-3 package index**.
Team A owns the paper's statistical-guarantee centrepiece: implement **split-conformal calibration
(Algorithm 2 / CQ-ZDR)** on Team B's prototypes and build the **coverage-verification** pipeline, for the
mentor-locked trio **CIC-IoT2023 + BoT-IoT + UNSW-NB15**. **Qubit budget = 8 · seed 42.**

> **Docs are unified in `week1/`** — entry point [`../week1/README.md`](../week1/README.md), upload guide
> [`../week1/UPLOAD.md`](../week1/UPLOAD.md), and the single checksum manifest
> [`../week1/manifest/MANIFEST.md`](../week1/manifest/MANIFEST.md) all cover Weeks 1–3. This file is just the
> Week-3 index. The Day-15 module consumes the **Day-14 score interface**
> ([`../week2/interface/dummy_scores/`](../week2/interface); real prototypes swap in at the same schema).

## Contents

| Day | Deliverable | Report | Code / data |
|---|---|---|---|
| **15** | **CQ-ZDR conformal calibration module + first threshold q (dataset 1 = CIC)** — DONE | [`reports/w3_01_conformal_calibration.md`](reports/w3_01_conformal_calibration.md) | [`scripts/conformal_calibrate.py`](scripts/conformal_calibrate.py) + `reports/_generated/w3_01_conformal_calibration.{json,csv}` + [`tests/test_conformal_calibrate.py`](tests/test_conformal_calibrate.py) |
| **16** | Coverage-verification harness (false-zero-day ≤ α on held-out known) + α-sweep 0.01–0.20 | _pending_ | `scripts/conformal_calibrate.py --alpha-sweep` hook is in place |
| **17** | 5-seed statistics protocol (mean±std, 95% CI, paired t-test, McNemar, Holm–Bonferroni, Cohen's d) | _pending_ | reuses [`../week2/scripts/stats_harness.py`](../week2/scripts/stats_harness.py) (Team C also reuses these helpers) |
| **18** | Extend calibration + coverage to all three datasets; coverage table v1 | _pending_ | module already runs all three (`--datasets CICIoT2023 BoT-IoT UNSW-NB15`) |

**Day-15 result (dummy interface, α = 0.05): first threshold q (CIC) = 0.300551**, known-test coverage
0.9514, false-zero-day 0.0486 (≤ α). Placeholder until Team B's real prototypes land.

## Reproduce

```bash
source ../.venv/bin/activate                                    # Python 3.12
python week3/scripts/conformal_calibrate.py --datasets CICIoT2023 --alpha 0.05   # Day 15 -> first q + coverage
python -m pytest week3/tests -q                                 # 11 tests
python week1/scripts/make_manifest.py --verify                 # one manifest pins Weeks 1–3 (0 mismatch)
```

## For Team B (QML)

Calibrate CQ-ZDR on `week2/partitions/<name>/calibration` (**known classes only**); the nonconformity score
is `s = 1 − max_c F(ρ_x, ρ_c)` and the threshold is `q = s_(k)`, `k = ⌈(1−α)(n+1)⌉`; flag a test point as
zero-day iff `s > q`. **Use marginal conformal for CIC** (its four ≤ 9-row known classes make Mondrian
degenerate at α = 0.05). Build each prototype `ρ_c` from **train only** — calibration must stay out-of-sample
or the threshold is optimistic. Swap real fidelities into the Day-14 interface schema and rerun
`conformal_calibrate.py --source real --scores-root <your dir>` with no code change.

*Statistics helpers (5-seed mean/std/95% CI) live in `week2/scripts/stats_harness.py`; Team C reuses them for
the selector benchmark.*
